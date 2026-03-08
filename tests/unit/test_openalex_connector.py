import httpx

from hypoforge.infrastructure.connectors.openalex import OpenAlexConnector


def test_openalex_search_normalizes_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "results": [
                    {
                        "id": "https://openalex.org/W123",
                        "doi": "https://doi.org/10.1/example",
                        "title": "Paper A",
                        "publication_year": 2024,
                        "cited_by_count": 42,
                        "primary_location": {
                            "source": {"display_name": "Nature"},
                            "landing_page_url": "https://example.org/paper-a",
                        },
                        "authorships": [
                            {"author": {"display_name": "Ada"}},
                        ],
                        "abstract_inverted_index": {"Paper": [0], "A": [1]},
                        "concepts": [{"display_name": "Battery"}],
                    }
                ]
            },
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    connector = OpenAlexConnector(client=client)

    papers = connector.search_works("battery", 2018, 2026, 5)

    assert len(papers) == 1
    assert papers[0].paper_id == "oa:W123"
    assert papers[0].abstract == "Paper A"

