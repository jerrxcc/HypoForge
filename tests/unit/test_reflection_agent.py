from hypoforge.agents.reflection import ReflectionAgent
from hypoforge.domain.schemas import PaperDetail, RunRequest
from hypoforge.infrastructure.db.repository import RunRepository


def test_reflection_agent_uses_dynamic_retrieval_channel_count(tmp_path) -> None:
    repo = RunRepository.from_sqlite_path(tmp_path / "app.db")
    run = repo.create_run(RunRequest(topic="battery"))
    repo.save_selected_papers(
        run.run_id,
        [
            PaperDetail(
                paper_id="p1",
                title="Paper 1",
                abstract="Abstract",
                year=2024,
                provenance=["openalex.search", "alphaxiv.discover_papers"],
            )
        ],
        "seed",
    )

    agent = ReflectionAgent(
        repository=repo,
        retrieval_channels=[
            "openalex.search",
            "semantic_scholar.search",
            "semantic_scholar.recommend",
            "alphaxiv.discover_papers",
        ],
    )

    assessment = agent._calculate_retrieval_metrics(
        run.run_id,
        {"coverage_assessment": "medium"},
    )

    assert round(assessment.metrics.source_coverage, 4) == round(2 / 4, 4)


def test_reflection_agent_accepts_legacy_provenance_labels(tmp_path) -> None:
    repo = RunRepository.from_sqlite_path(tmp_path / "app.db")
    run = repo.create_run(RunRequest(topic="battery"))
    repo.save_selected_papers(
        run.run_id,
        [
            PaperDetail(
                paper_id="p1",
                title="Paper 1",
                abstract="Abstract",
                year=2024,
                provenance=["openalex", "semantic_scholar"],
            )
        ],
        "seed",
    )

    agent = ReflectionAgent(repository=repo)

    assessment = agent._calculate_retrieval_metrics(
        run.run_id,
        {"coverage_assessment": "good"},
    )

    assert round(assessment.metrics.source_coverage, 4) == round(2 / 3, 4)
