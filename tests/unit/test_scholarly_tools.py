from hypoforge.domain.schemas import PaperDetail, RunRequest
from hypoforge.application.budget import BudgetExceededError
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


class DetailReturningSemanticScholarConnector(FakeSemanticScholarConnector):
    def get_paper_details(self, paper_ids: list[str]):
        return [
            PaperDetail(
                paper_id=paper_id,
                title=f"Resolved {paper_id}",
                abstract="Abstract",
                authors=["A"],
                year=2024,
            )
            for paper_id in paper_ids
        ]


class FakeAlphaXivConnector:
    last_cache_hit = False

    def search_embedding_similarity(self, query: str, year_from: int, year_to: int, limit: int):
        del year_from, year_to, limit
        return [
            PaperDetail(
                paper_id="ax:2401.12345",
                title=query,
                abstract="Abstract A",
                authors=["Ada"],
                year=2024,
            )
        ]

    def search_full_text_papers(self, query: str, year_from: int, year_to: int, limit: int):
        return self.search_embedding_similarity(query, year_from, year_to, limit)

    def search_agentic_paper_retrieval(self, query: str, year_from: int, year_to: int, limit: int):
        return self.search_embedding_similarity(query, year_from, year_to, limit)

    def get_paper_content(self, url: str, full_text: bool = False):
        return f"{url}:{full_text}"

    def answer_pdf_queries(self, url: str, query: str):
        return f"{url}:{query}"

    def read_files_from_github_repository(self, github_url: str, path: str):
        return {"github_url": github_url, "path": path}


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


class BudgetFailingOpenAlexConnector:
    def __init__(self) -> None:
        self.last_cache_hit = False

    def search_works(self, query: str, year_from: int, year_to: int, limit: int):
        del query, year_from, year_to, limit
        raise BudgetExceededError(source="openalex", message="budget exceeded")


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


def test_save_selected_papers_fetches_missing_semantic_scholar_details(tmp_path) -> None:
    repo = RunRepository.from_sqlite_path(tmp_path / "app.db")
    run = repo.create_run(RunRequest(topic="protein binder design"))

    def lookup(paper_ids: list[str]):
        del paper_ids
        return []

    tools = ScholarlyTools(
        openalex=FakeOpenAlexConnector(),
        semantic_scholar=DetailReturningSemanticScholarConnector(),
        repository=repo,
        paper_lookup=lookup,
    )

    result = tools.save_selected_papers(
        run.run_id,
        {
            "paper_ids": ["S2:abc123"],
            "selection_reason": "model selection",
        },
    )

    assert result["paper_ids"] == ["S2:abc123"]
    assert repo.load_selected_papers(run.run_id)[0].paper_id == "S2:abc123"


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


def test_search_openalex_returns_budget_exceeded_payload(tmp_path) -> None:
    repo = RunRepository.from_sqlite_path(tmp_path / "app.db")
    tools = ScholarlyTools(
        openalex=BudgetFailingOpenAlexConnector(),
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
    assert result["error"]["type"] == "budget_exceeded"
    assert result["error"]["source"] == "openalex"


def test_get_alphaxiv_paper_content_returns_payload(tmp_path) -> None:
    repo = RunRepository.from_sqlite_path(tmp_path / "app.db")
    tools = ScholarlyTools(
        openalex=FakeOpenAlexConnector(),
        semantic_scholar=FakeSemanticScholarConnector(),
        alphaxiv=FakeAlphaXivConnector(),
        repository=repo,
    )

    result = tools.get_alphaxiv_paper_content(
        {
            "url": "https://arxiv.org/abs/2401.12345",
            "fullText": True,
        }
    )

    assert result["paper_content"] == "https://arxiv.org/abs/2401.12345:True"


def test_read_alphaxiv_github_repository_returns_structured_payload(tmp_path) -> None:
    repo = RunRepository.from_sqlite_path(tmp_path / "app.db")
    tools = ScholarlyTools(
        openalex=FakeOpenAlexConnector(),
        semantic_scholar=FakeSemanticScholarConnector(),
        alphaxiv=FakeAlphaXivConnector(),
        repository=repo,
    )

    result = tools.read_alphaxiv_github_repository(
        {
            "githubUrl": "https://github.com/example/repo",
            "path": "/",
        }
    )

    assert result["repository_content"]["github_url"] == "https://github.com/example/repo"
