from fastapi.testclient import TestClient

from hypoforge.api.app import create_app
from hypoforge.config import Settings


def test_healthz_returns_ok() -> None:
    client = TestClient(create_app())

    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_cors_allows_configured_frontend_origin() -> None:
    client = TestClient(
        create_app(
            settings=Settings(frontend_allowed_origins=["http://127.0.0.1:3000"])
        )
    )

    response = client.options(
        "/v1/runs",
        headers={
            "Origin": "http://127.0.0.1:3000",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:3000"
