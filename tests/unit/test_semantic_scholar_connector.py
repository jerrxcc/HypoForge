import httpx

from hypoforge.infrastructure.connectors.semantic_scholar import SemanticScholarConnector


def test_semantic_scholar_search_normalizes_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "data": [
                    {
                        "paperId": "abc123",
                        "externalIds": {"DOI": "10.1/example"},
                        "title": "Paper B",
                        "abstract": "Abstract B",
                        "year": 2023,
                        "citationCount": 12,
                        "venue": "Science",
                        "authors": [{"name": "Grace"}],
                        "fieldsOfStudy": ["Chemistry"],
                        "url": "https://example.org/paper-b",
                    }
                ]
            },
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    connector = SemanticScholarConnector(client=client)

    papers = connector.search_papers("solid-state battery", 2018, 2026, 5)

    assert len(papers) == 1
    assert papers[0].paper_id == "S2:abc123"
    assert papers[0].doi == "10.1/example"

