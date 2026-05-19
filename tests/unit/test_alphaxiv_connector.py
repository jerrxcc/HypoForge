import pytest
import httpx

from hypoforge.infrastructure.connectors.alphaxiv import AlphaXivConnector, AlphaXivMCPClient, AlphaXivToolError


def test_alphaxiv_mcp_client_sends_bearer_token_and_jsonrpc_payload() -> None:
    seen: dict[str, object] = {}
    call_count = {"value": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        call_count["value"] += 1
        seen["auth"] = request.headers.get("Authorization")
        seen["accept"] = request.headers.get("Accept")
        seen[f"body_{call_count['value']}"] = request.read().decode()
        if call_count["value"] == 2:
            return httpx.Response(202, text="")
        return httpx.Response(
            200,
            headers={"content-type": "text/event-stream"},
            text='event: message\ndata: {"jsonrpc":"2.0","id":1,"result":{"structuredContent":{"papers":[{"title":"Alpha paper","abstract":"Useful abstract","publicationDate":"2024-02-01","arxivId":"2401.12345","authors":["Ada"]}]}}}\n\n',
        )

    client = AlphaXivMCPClient(
        endpoint="https://api.alphaxiv.org/mcp/v1",
        access_token="jwt.token.value",
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    result = client.call_tool("embedding_similarity_search", {"query": "battery"})

    assert seen["auth"] == "Bearer jwt.token.value"
    assert '"method":"initialize"' in str(seen["body_1"])
    assert '"method":"notifications/initialized"' in str(seen["body_2"])
    assert '"method":"tools/call"' in str(seen["body_3"])
    assert result["structuredContent"]["papers"][0]["arxivId"] == "2401.12345"


def test_alphaxiv_connector_normalizes_structured_search_response() -> None:
    class FakeClient:
        def call_tool(self, tool_name: str, arguments: dict):
            del tool_name, arguments
            return {
                "structuredContent": {
                    "papers": [
                        {
                            "title": "Alpha paper",
                            "abstract": "Useful abstract",
                            "publicationDate": "2024-02-01",
                            "arxivId": "2401.12345",
                            "alphaXivUrl": "https://alphaxiv.org/overview/2401.12345",
                            "githubUrl": "https://github.com/example/repo",
                            "authors": [{"name": "Ada"}],
                            "organizations": "MIT",
                            "likes": 42,
                        },
                        {
                            "title": "Too old",
                            "abstract": "Ignore me",
                            "publicationDate": "2016-01-01",
                            "arxivId": "1601.00001",
                        },
                    ]
                }
            }

    connector = AlphaXivConnector(client=FakeClient(), access_token="jwt.token.value")

    papers = connector.search_agentic_paper_retrieval(["battery"], "battery", 4, 2018, 2026, 5)

    assert len(papers) == 1
    assert papers[0].paper_id == "ax:2401.12345"
    assert papers[0].source == "alphaxiv"
    assert papers[0].provenance == ["alphaxiv.discover_papers"]
    assert papers[0].source_urls["github"] == "https://github.com/example/repo"
    assert papers[0].source_urls["arxiv"] == "https://arxiv.org/abs/2401.12345"


def test_alphaxiv_connector_normalizes_discover_text_response() -> None:
    class FakeClient:
        def call_tool(self, tool_name: str, arguments: dict):
            assert tool_name == "discover_papers"
            assert arguments["keywords"]
            return {
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "1. [ID=2402.04095] **Two-step growth mechanism of the solid "
                            "electrolyte interphase in argyrodyte/Li-metal contacts**. "
                            "Published 2024-02-06 by CEA: The structure and growth of the SEI region.\n"
                            "2. [ID=2412.02433] **Ab initio Study on Lithium Anode Interface Instability**. "
                            "Published 2024-12-03 by NTUST: Emerging superionic conductors are promising."
                        ),
                    }
                ]
            }

    connector = AlphaXivConnector(client=FakeClient(), access_token="jwt.token.value")

    papers = connector.search_agentic_paper_retrieval(
        ["solid-state battery", "electrolyte interfaces"],
        "solid-state battery electrolyte interfaces",
        4,
        2024,
        2026,
        5,
    )

    assert [paper.paper_id for paper in papers] == ["ax:2402.04095", "ax:2412.02433"]
    assert papers[0].title == "Two-step growth mechanism of the solid electrolyte interphase in argyrodyte/Li-metal contacts"
    assert papers[0].abstract == "The structure and growth of the SEI region."


def test_alphaxiv_connector_reads_text_tool_results() -> None:
    class FakeClient:
        def call_tool(self, tool_name: str, arguments: dict):
            del tool_name, arguments
            return {"content": [{"type": "text", "text": "full paper content"}]}

    connector = AlphaXivConnector(client=FakeClient(), access_token="jwt.token.value")

    result = connector.get_paper_content("https://arxiv.org/abs/2401.12345")

    assert result == "full paper content"


def test_alphaxiv_connector_wraps_pdf_query_inputs_as_arrays() -> None:
    seen: dict[str, dict] = {}

    class FakeClient:
        def call_tool(self, tool_name: str, arguments: dict):
            seen["tool"] = {"name": tool_name, "arguments": arguments}
            return {"content": [{"type": "text", "text": "answer"}]}

    connector = AlphaXivConnector(client=FakeClient(), access_token="jwt.token.value")

    result = connector.answer_pdf_queries("https://arxiv.org/abs/2401.12345", "What datasets were used?")

    assert result == "answer"
    assert seen["tool"]["name"] == "answer_pdf_queries"
    assert seen["tool"]["arguments"] == {
        "url": "https://arxiv.org/abs/2401.12345",
        "queries": ["What datasets were used?"],
    }


def test_alphaxiv_mcp_client_raises_tool_error_for_tool_level_failure() -> None:
    call_count = {"value": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        call_count["value"] += 1
        if call_count["value"] == 2:
            return httpx.Response(202, text="")
        if call_count["value"] == 3:
            return httpx.Response(
                200,
                headers={"content-type": "text/event-stream"},
                text='event: message\ndata: {"jsonrpc":"2.0","id":2,"result":{"isError":true,"content":[{"type":"text","text":"Invalid file type: text/html;charset=UTF-8"}]}}\n\n',
            )
        return httpx.Response(
            200,
            headers={"content-type": "text/event-stream"},
            text='event: message\ndata: {"jsonrpc":"2.0","id":1,"result":{"protocolVersion":"2025-06-18","capabilities":{}}}\n\n',
        )

    client = AlphaXivMCPClient(
        endpoint="https://api.alphaxiv.org/mcp/v1",
        access_token="jwt.token.value",
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    with pytest.raises(AlphaXivToolError) as exc_info:
        client.call_tool("answer_pdf_queries", {"url": "https://doi.org/10.1/example", "queries": ["Q"]})

    assert exc_info.value.tool_name == "answer_pdf_queries"
    assert exc_info.value.message == "Invalid file type: text/html;charset=UTF-8"
