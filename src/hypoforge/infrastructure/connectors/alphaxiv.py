from __future__ import annotations

import json
import re
from typing import Any

import httpx

from hypoforge.domain.schemas import PaperDetail


_ARXIV_ID_PATTERN = re.compile(r"\b\d{4}\.\d{4,5}(?:v\d+)?\b")
_YEAR_PATTERN = re.compile(r"\b(19|20)\d{2}\b")


class AlphaXivMCPClient:
    """Minimal JSON-RPC client for the alphaXiv MCP endpoint."""

    def __init__(
        self,
        *,
        endpoint: str,
        access_token: str,
        client: httpx.Client | None = None,
    ) -> None:
        self._endpoint = endpoint
        self._access_token = access_token
        self._client = client or httpx.Client(timeout=90.0)
        self._request_id = 0
        self._initialized = False

    def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        self._ensure_initialized()
        payload = self._rpc_sse(
            {
                "jsonrpc": "2.0",
                "id": self._next_request_id(),
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments,
                },
            }
        )
        return self._extract_result(payload, tool_name=tool_name)

    def _next_request_id(self) -> int:
        self._request_id += 1
        return self._request_id

    def _ensure_initialized(self) -> None:
        if self._initialized:
            return
        payload = self._rpc_sse(
            {
                "jsonrpc": "2.0",
                "id": self._next_request_id(),
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "hypoforge",
                        "version": "0.1.0",
                    },
                },
            }
        )
        self._extract_result(payload, tool_name="initialize")
        response = self._client.post(
            self._endpoint,
            headers=self._headers(),
            json={
                "jsonrpc": "2.0",
                "method": "notifications/initialized",
                "params": {},
            },
        )
        response.raise_for_status()
        self._initialized = True

    def _rpc_sse(self, payload: dict[str, Any]) -> dict[str, Any]:
        with self._client.stream(
            "POST",
            self._endpoint,
            headers=self._headers(),
            json=payload,
        ) as response:
            response.raise_for_status()
            event_payload = self._read_first_sse_message(response)
        return event_payload

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._access_token}",
            "Accept": "application/json, text/event-stream",
            "Content-Type": "application/json",
            "MCP-Protocol-Version": "2025-06-18",
        }

    def _read_first_sse_message(self, response: httpx.Response) -> dict[str, Any]:
        data_lines: list[str] = []
        for line in response.iter_lines():
            if not line:
                if data_lines:
                    return json.loads("\n".join(data_lines))
                continue
            if isinstance(line, bytes):
                line = line.decode("utf-8")
            if line.startswith("data:"):
                data_lines.append(line.split(":", 1)[1].strip())
        raise RuntimeError("alphaXiv MCP stream closed before a message was received")

    def _extract_result(self, payload: dict[str, Any], *, tool_name: str) -> dict[str, Any]:
        if "error" in payload:
            raise RuntimeError(f"alphaXiv MCP error for {tool_name}: {payload['error']}")
        result = payload.get("result")
        if not isinstance(result, dict):
            raise RuntimeError(f"alphaXiv MCP returned unexpected result for {tool_name}: {payload}")
        if result.get("isError"):
            raise RuntimeError(f"alphaXiv tool {tool_name} failed: {result}")
        return result


class AlphaXivConnector:
    DEFAULT_ENDPOINT = "https://api.alphaxiv.org/mcp/v1"

    def __init__(
        self,
        *,
        client: AlphaXivMCPClient | None = None,
        endpoint: str | None = None,
        access_token: str | None = None,
        http_client: httpx.Client | None = None,
    ) -> None:
        resolved_endpoint = endpoint or self.DEFAULT_ENDPOINT
        self.enabled = bool(access_token)
        self._client = client or AlphaXivMCPClient(
            endpoint=resolved_endpoint,
            access_token=access_token or "",
            client=http_client,
        )

    def search_embedding_similarity(
        self,
        query: str,
        year_from: int,
        year_to: int,
        limit: int,
    ) -> list[PaperDetail]:
        result = self._client.call_tool("embedding_similarity_search", {"query": query})
        return self._normalize_search_result(
            result,
            year_from=year_from,
            year_to=year_to,
            limit=limit,
            provenance="alphaxiv.embedding_similarity_search",
        )

    def search_full_text_papers(
        self,
        query: str,
        year_from: int,
        year_to: int,
        limit: int,
    ) -> list[PaperDetail]:
        result = self._client.call_tool("full_text_papers_search", {"query": query})
        return self._normalize_search_result(
            result,
            year_from=year_from,
            year_to=year_to,
            limit=limit,
            provenance="alphaxiv.full_text_papers_search",
        )

    def search_agentic_paper_retrieval(
        self,
        query: str,
        year_from: int,
        year_to: int,
        limit: int,
    ) -> list[PaperDetail]:
        result = self._client.call_tool("agentic_paper_retrieval", {"query": query})
        return self._normalize_search_result(
            result,
            year_from=year_from,
            year_to=year_to,
            limit=limit,
            provenance="alphaxiv.agentic_paper_retrieval",
        )

    def get_paper_content(self, url: str, full_text: bool = False) -> str:
        result = self._client.call_tool("get_paper_content", {"url": url, "fullText": full_text})
        return _tool_result_text(result)

    def answer_pdf_queries(self, url: str, query: str) -> str:
        result = self._client.call_tool("answer_pdf_queries", {"urls": [url], "queries": [query]})
        return _tool_result_text(result)

    def read_files_from_github_repository(self, github_url: str, path: str) -> dict[str, Any] | str:
        result = self._client.call_tool(
            "read_files_from_github_repository",
            {"githubUrl": github_url, "path": path},
        )
        structured = result.get("structuredContent")
        if structured is not None:
            return structured
        return _tool_result_text(result)

    def _normalize_search_result(
        self,
        result: dict[str, Any],
        *,
        year_from: int,
        year_to: int,
        limit: int,
        provenance: str,
    ) -> list[PaperDetail]:
        papers: list[PaperDetail] = []
        for item in _extract_search_items(result):
            paper = _normalize_search_item(item, provenance=provenance)
            if paper is None:
                continue
            if paper.year is not None and not (year_from <= paper.year <= year_to):
                continue
            papers.append(paper)
            if len(papers) >= limit:
                break
        return papers


def _extract_search_items(result: dict[str, Any]) -> list[dict[str, Any]]:
    structured = result.get("structuredContent")
    if isinstance(structured, list):
        return [item for item in structured if isinstance(item, dict)]
    if isinstance(structured, dict):
        for key in ("papers", "results", "items", "data"):
            value = structured.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
        if _looks_like_search_item(structured):
            return [structured]

    content = result.get("content")
    if isinstance(content, list):
        text_parts = [
            item.get("text", "")
            for item in content
            if isinstance(item, dict) and item.get("type") == "text"
        ]
        text = "\n".join(part for part in text_parts if part)
        if text:
            parsed = _parse_text_or_json_items(text)
            if parsed:
                return parsed

    return []


def _parse_text_or_json_items(text: str) -> list[dict[str, Any]]:
    stripped = text.strip()
    if not stripped:
        return []
    try:
        payload = json.loads(stripped)
    except json.JSONDecodeError:
        return _parse_text_blocks(stripped)
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        for key in ("papers", "results", "items", "data"):
            value = payload.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
        if _looks_like_search_item(payload):
            return [payload]
    return []


def _parse_text_blocks(text: str) -> list[dict[str, Any]]:
    blocks = [block.strip() for block in re.split(r"\n\s*\n", text) if block.strip()]
    items: list[dict[str, Any]] = []
    for block in blocks:
        lines = [line.strip(" -*\t") for line in block.splitlines() if line.strip()]
        if not lines:
            continue
        joined = "\n".join(lines)
        arxiv_id = _extract_arxiv_id(joined)
        title = re.sub(r"^\d+[.)]\s*", "", lines[0]).strip()
        abstract = ""
        authors: list[str] = []
        year = _extract_year(joined)
        url = None
        for line in lines[1:]:
            lower = line.lower()
            if lower.startswith("authors:"):
                authors = [part.strip() for part in line.split(":", 1)[1].split(",") if part.strip()]
            elif lower.startswith("abstract"):
                abstract = line.split(":", 1)[1].strip() if ":" in line else line
            elif line.startswith("http://") or line.startswith("https://"):
                url = line
        if not abstract and len(lines) > 1:
            abstract = max(lines[1:], key=len)
        items.append(
            {
                "title": title,
                "abstract": abstract,
                "authors": authors,
                "year": year,
                "arxivId": arxiv_id,
                "url": url,
            }
        )
    return items


def _normalize_search_item(item: dict[str, Any], *, provenance: str) -> PaperDetail | None:
    title = _coerce_text(item.get("title") or item.get("paperTitle") or item.get("name"))
    if not title:
        return None

    arxiv_id = _extract_arxiv_id(
        _coerce_text(
            item.get("arxivId")
            or item.get("arxiv_id")
            or item.get("id")
            or item.get("url")
            or item.get("alphaXivUrl")
            or item.get("alphaXivURL")
        )
    )
    paper_url = _coerce_text(
        item.get("url")
        or item.get("alphaXivUrl")
        or item.get("alphaXivURL")
        or item.get("paperUrl")
    )
    alpha_url = _coerce_text(item.get("alphaXivUrl") or item.get("alphaXivURL"))
    github_url = _coerce_text(item.get("githubUrl") or item.get("github_url"))
    year = _extract_year(
        _coerce_text(
            item.get("publicationDate")
            or item.get("publication_date")
            or item.get("date")
            or item.get("published")
            or item.get("publishedAt")
            or item.get("year")
        )
    )
    abstract = _coerce_text(
        item.get("abstract")
        or item.get("abstractPreview")
        or item.get("abstract_preview")
        or item.get("summary")
    )
    authors = _coerce_text_list(item.get("authors"))
    if not authors and isinstance(item.get("author"), str):
        authors = [item["author"]]
    venue = _coerce_text(
        item.get("venue")
        or item.get("journal")
        or item.get("organizations")
        or item.get("organization")
    )
    citation_count = _coerce_int(item.get("visitCount") or item.get("visit_count") or item.get("likes"))

    external_ids: dict[str, str | int | None] = {}
    source_urls: dict[str, str] = {}
    if arxiv_id:
        external_ids["arxiv"] = arxiv_id
        source_urls["arxiv"] = f"https://arxiv.org/abs/{arxiv_id}"
        source_urls["alphaxiv"] = alpha_url or f"https://alphaxiv.org/overview/{arxiv_id}"
    if paper_url:
        source_urls.setdefault("alphaxiv", paper_url)
    if github_url:
        source_urls["github"] = github_url

    paper_id = f"ax:{arxiv_id}" if arxiv_id else f"ax:title:{_slugify_title(title)}"
    return PaperDetail(
        paper_id=paper_id,
        external_ids=external_ids,
        title=title,
        abstract=abstract or None,
        year=year,
        authors=authors,
        venue=venue or None,
        citation_count=citation_count,
        source="alphaxiv",
        url=source_urls.get("arxiv") or paper_url or alpha_url or None,
        source_urls=source_urls,
        provenance=[provenance],
    )


def _looks_like_search_item(payload: dict[str, Any]) -> bool:
    return any(key in payload for key in ("title", "paperTitle", "arxivId", "abstract", "authors"))


def _tool_result_text(result: dict[str, Any]) -> str:
    structured = result.get("structuredContent")
    if isinstance(structured, str):
        return structured
    if structured is not None:
        return json.dumps(structured, ensure_ascii=True, sort_keys=True)

    content = result.get("content")
    if isinstance(content, list):
        text_parts = [
            item.get("text", "")
            for item in content
            if isinstance(item, dict) and item.get("type") == "text"
        ]
        joined = "\n".join(part for part in text_parts if part).strip()
        if joined:
            return joined
    return json.dumps(result, ensure_ascii=True, sort_keys=True)


def _coerce_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    return str(value).strip()


def _coerce_text_list(value: Any) -> list[str]:
    if isinstance(value, list):
        items: list[str] = []
        for item in value:
            if isinstance(item, str):
                text = item.strip()
                if text:
                    items.append(text)
            elif isinstance(item, dict):
                for key in ("name", "author", "displayName"):
                    text = _coerce_text(item.get(key))
                    if text:
                        items.append(text)
                        break
        return items
    if isinstance(value, str):
        return [part.strip() for part in value.split(",") if part.strip()]
    return []


def _coerce_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _extract_arxiv_id(value: str) -> str | None:
    match = _ARXIV_ID_PATTERN.search(value or "")
    return match.group(0) if match else None


def _extract_year(value: str) -> int | None:
    match = _YEAR_PATTERN.search(value or "")
    if match is None:
        return None
    return int(match.group(0))


def _slugify_title(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return slug[:80] or "paper"
