#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import secrets
import threading
import time
import webbrowser
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlencode, urlparse

import httpx


AUTH_SERVER = "https://clerk.alphaxiv.org"
RESOURCE = "https://api.alphaxiv.org"
AUTHORIZATION_ENDPOINT = f"{AUTH_SERVER}/oauth/authorize"
TOKEN_ENDPOINT = f"{AUTH_SERVER}/oauth/token"
REGISTRATION_ENDPOINT = f"{AUTH_SERVER}/oauth/register"


@dataclass
class CallbackResult:
    code: str | None = None
    state: str | None = None
    error: str | None = None
    error_description: str | None = None


class CallbackHandler(BaseHTTPRequestHandler):
    result: CallbackResult | None = None
    event: threading.Event | None = None

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path != "/callback":
            self.send_error(404, "Not Found")
            return

        params = parse_qs(parsed.query)
        CallbackHandler.result = CallbackResult(
            code=_first(params.get("code")),
            state=_first(params.get("state")),
            error=_first(params.get("error")),
            error_description=_first(params.get("error_description")),
        )
        if CallbackHandler.event is not None:
            CallbackHandler.event.set()

        body = _success_page(CallbackHandler.result)
        encoded = body.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, format: str, *args: object) -> None:
        del format, args


def main() -> int:
    args = _parse_args()
    output_path = Path(args.output).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    redirect_uri = f"http://127.0.0.1:{args.port}/callback"
    with httpx.Client(timeout=30.0, follow_redirects=False) as client:
        registration = register_client(
            client=client,
            redirect_uri=redirect_uri,
            client_name=args.client_name,
        )
        code_verifier = _generate_code_verifier()
        code_challenge = _pkce_challenge(code_verifier)
        state = secrets.token_urlsafe(24)
        auth_url = build_authorization_url(
            client_id=registration["client_id"],
            redirect_uri=redirect_uri,
            state=state,
            code_challenge=code_challenge,
            scope=args.scope,
        )

        print(f"Registered alphaXiv client_id: {registration['client_id']}")
        print(f"Redirect URI: {redirect_uri}")
        print(f"Authorization URL:\n{auth_url}\n")

        callback = wait_for_callback(
            port=args.port,
            expected_state=state,
            timeout_seconds=args.timeout,
            open_browser=not args.no_browser,
            auth_url=auth_url,
        )

        token_payload = exchange_code_for_token(
            client=client,
            client_id=registration["client_id"],
            code=callback.code,
            redirect_uri=redirect_uri,
            code_verifier=code_verifier,
        )

    payload = {
        "resource": RESOURCE,
        "authorization_server": AUTH_SERVER,
        "registered_client": registration,
        "redirect_uri": redirect_uri,
        "scope": args.scope,
        "issued_at": int(time.time()),
        "token_response": token_payload,
    }
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    access_token = token_payload.get("access_token", "")
    refresh_token = token_payload.get("refresh_token", "")
    print(f"Saved token payload to {output_path}")
    print(f"Access token length: {len(access_token)}")
    if access_token:
        print(f"Export for current shell:\nexport ALPHAXIV_ACCESS_TOKEN='{access_token}'")
    if refresh_token:
        print(f"Refresh token length: {len(refresh_token)}")
    return 0


def register_client(*, client: httpx.Client, redirect_uri: str, client_name: str) -> dict[str, Any]:
    response = client.post(
        REGISTRATION_ENDPOINT,
        json={
            "client_name": client_name,
            "redirect_uris": [redirect_uri],
            "grant_types": ["authorization_code", "refresh_token"],
            "response_types": ["code"],
            "token_endpoint_auth_method": "none",
            "application_type": "native",
        },
    )
    response.raise_for_status()
    payload = response.json()
    if "client_id" not in payload:
        raise RuntimeError(f"registration failed: {payload}")
    return payload


def build_authorization_url(
    *,
    client_id: str,
    redirect_uri: str,
    state: str,
    code_challenge: str,
    scope: str,
) -> str:
    query = urlencode(
        {
            "response_type": "code",
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "scope": scope,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
            "state": state,
            "resource": RESOURCE,
        }
    )
    return f"{AUTHORIZATION_ENDPOINT}?{query}"


def wait_for_callback(
    *,
    port: int,
    expected_state: str,
    timeout_seconds: int,
    open_browser: bool,
    auth_url: str,
) -> CallbackResult:
    event = threading.Event()
    CallbackHandler.event = event
    CallbackHandler.result = None
    server = ThreadingHTTPServer(("127.0.0.1", port), CallbackHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        if open_browser:
            webbrowser.open(auth_url, new=1, autoraise=True)
        print(f"Waiting for OAuth callback on http://127.0.0.1:{port}/callback ...")
        if not event.wait(timeout_seconds):
            raise TimeoutError(f"timed out waiting for callback after {timeout_seconds}s")

        result = CallbackHandler.result
        if result is None:
            raise RuntimeError("callback server returned no result")
        if result.error:
            raise RuntimeError(f"OAuth error: {result.error} ({result.error_description or 'no description'})")
        if result.state != expected_state:
            raise RuntimeError("state mismatch in OAuth callback")
        if not result.code:
            raise RuntimeError("OAuth callback did not include a code")
        return result
    finally:
        server.shutdown()
        server.server_close()


def exchange_code_for_token(
    *,
    client: httpx.Client,
    client_id: str,
    code: str,
    redirect_uri: str,
    code_verifier: str,
) -> dict[str, Any]:
    response = client.post(
        TOKEN_ENDPOINT,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "grant_type": "authorization_code",
            "client_id": client_id,
            "code": code,
            "redirect_uri": redirect_uri,
            "code_verifier": code_verifier,
            "resource": RESOURCE,
        },
    )
    response.raise_for_status()
    payload = response.json()
    if "access_token" not in payload:
        raise RuntimeError(f"token exchange failed: {payload}")
    return payload


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Temporary alphaXiv OAuth client")
    parser.add_argument(
        "--port",
        type=int,
        default=8765,
        help="Local callback port. Default: 8765",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=600,
        help="Seconds to wait for the browser callback. Default: 600",
    )
    parser.add_argument(
        "--scope",
        default="profile email",
        help="OAuth scopes to request.",
    )
    parser.add_argument(
        "--client-name",
        default="HypoForge alphaXiv temp client",
        help="Dynamic client registration display name.",
    )
    parser.add_argument(
        "--output",
        default="tmp/alphaxiv_token.json",
        help="Where to save the token payload.",
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Do not try to open the browser automatically.",
    )
    return parser.parse_args()


def _generate_code_verifier() -> str:
    return secrets.token_urlsafe(64)


def _pkce_challenge(code_verifier: str) -> str:
    digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")


def _first(values: list[str] | None) -> str | None:
    if not values:
        return None
    return values[0]


def _success_page(result: CallbackResult) -> str:
    if result.error:
        message = f"OAuth failed: {result.error}"
    else:
        message = "alphaXiv OAuth completed. You can return to the terminal."
    return f"""<!doctype html>
<html>
  <head><meta charset="utf-8"><title>alphaXiv OAuth</title></head>
  <body style="font-family: sans-serif; padding: 32px;">
    <h1>{message}</h1>
  </body>
</html>
"""


if __name__ == "__main__":
    raise SystemExit(main())
