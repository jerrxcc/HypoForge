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


class CachedLikeOpenAlexConnector:
    def __init__(self) -> None:
        self.last_cache_hit = False

    def search_works(self, query: str, year_from: int, year_to: int, limit: int):
        del query, year_from, year_to, limit
        self.last_cache_hit = True
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


def test_search_openalex_surfaces_cache_hit_metadata(tmp_path) -> None:
    repo = RunRepository.from_sqlite_path(tmp_path / "app.db")
    connector = CachedLikeOpenAlexConnector()
    tools = ScholarlyTools(
        openalex=connector,
        semantic_scholar=FakeSemanticScholarConnector(),
        repository=repo,
    )

    result = tools.search_openalex_works(
        {
            "query": "solid-state battery electrolyte",
            "year_from": 2018,
            "year_to": 2026,
            "limit": 10,
        }
    )

    assert result["papers"] == []
    assert result["cache_hit"] is True
