from hypoforge.domain.schemas import RunRequest
from hypoforge.infrastructure.db.repository import RunRepository
from hypoforge.tools.scholarly_tools import ScholarlyTools
import httpx


class FakeOpenAlexConnector:
    def search_works(self, query: str, year_from: int, year_to: int, limit: int):
        return []


class FakeSemanticScholarConnector:
    def search_papers(self, query: str, year_from: int, year_to: int, limit: int):
        return []

    def recommend_papers(self, positive_paper_ids: list[str], limit: int):
        return []

    def get_paper_details(self, paper_ids: list[str]):
        return []


class FailingSemanticScholarConnector:
    def search_papers(self, query: str, year_from: int, year_to: int, limit: int):
        request = httpx.Request("GET", "https://api.semanticscholar.org/graph/v1/paper/search")
        response = httpx.Response(429, request=request)
        raise httpx.HTTPStatusError("rate limited", request=request, response=response)

    def recommend_papers(self, positive_paper_ids: list[str], limit: int):
        return []

    def get_paper_details(self, paper_ids: list[str]):
        return []


def test_save_selected_papers_tool_persists_records(tmp_path) -> None:
    repo = RunRepository.from_sqlite_path(tmp_path / "app.db")
    run = repo.create_run(RunRequest(topic="protein binder design"))
    tools = ScholarlyTools(
        openalex=FakeOpenAlexConnector(),
        semantic_scholar=FakeSemanticScholarConnector(),
        repository=repo,
    )

    result = tools.save_selected_papers(
        run.run_id,
        {
            "papers": [
                {
                    "paper_id": "p1",
                    "title": "Paper 1",
                    "abstract": "Abstract 1",
                    "authors": ["A"],
                    "year": 2024,
                }
            ],
            "selection_reason": "seed",
        },
    )

    assert result["paper_ids"] == ["p1"]
    assert len(repo.load_selected_papers(run.run_id)) == 1


def test_save_selected_papers_can_resolve_ids_from_candidate_pool(tmp_path) -> None:
    repo = RunRepository.from_sqlite_path(tmp_path / "app.db")
    run = repo.create_run(RunRequest(topic="protein binder design"))

    def lookup(paper_ids: list[str]):
        return [
            {
                "paper_id": "p1",
                "title": "Paper 1",
                "abstract": "Abstract 1",
                "authors": ["A"],
                "year": 2024,
            }
        ]

    tools = ScholarlyTools(
        openalex=FakeOpenAlexConnector(),
        semantic_scholar=FakeSemanticScholarConnector(),
        repository=repo,
        paper_lookup=lookup,
    )

    result = tools.save_selected_papers(
        run.run_id,
        {
            "paper_ids": ["p1"],
            "selection_reason": "model selection",
        },
    )

    assert result["paper_ids"] == ["p1"]
    assert repo.load_selected_papers(run.run_id)[0].paper_id == "p1"


def test_search_semantic_scholar_returns_empty_payload_on_http_error(tmp_path) -> None:
    repo = RunRepository.from_sqlite_path(tmp_path / "app.db")
    tools = ScholarlyTools(
        openalex=FakeOpenAlexConnector(),
        semantic_scholar=FailingSemanticScholarConnector(),
        repository=repo,
    )

    result = tools.search_semantic_scholar_papers(
        {
            "query": "solid-state battery electrolyte",
            "year_from": 2018,
            "year_to": 2026,
            "limit": 10,
        }
    )

    assert result["papers"] == []
    assert result["error"]["status_code"] == 429
