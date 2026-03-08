from hypoforge.domain.schemas import RunRequest
from hypoforge.infrastructure.db.repository import RunRepository
from hypoforge.tools.scholarly_tools import ScholarlyTools


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
