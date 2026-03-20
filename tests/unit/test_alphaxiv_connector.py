import httpx

from hypoforge.infrastructure.connectors.alphaxiv import AlphaXivConnector, AlphaXivMCPClient


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

    papers = connector.search_embedding_similarity("battery", 2018, 2026, 5)

    assert len(papers) == 1
    assert papers[0].paper_id == "ax:2401.12345"
    assert papers[0].source == "alphaxiv"
    assert papers[0].provenance == ["alphaxiv.embedding_similarity_search"]
    assert papers[0].source_urls["github"] == "https://github.com/example/repo"
    assert papers[0].source_urls["arxiv"] == "https://arxiv.org/abs/2401.12345"


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
        "urls": ["https://arxiv.org/abs/2401.12345"],
        "queries": ["What datasets were used?"],
    }
