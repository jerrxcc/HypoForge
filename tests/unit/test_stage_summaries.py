from hypoforge.domain.schemas import RetrievalSummary, RunRequest
from hypoforge.infrastructure.db.repository import RunRepository


def test_repository_persists_stage_summaries(tmp_path) -> None:
    repo = RunRepository.from_sqlite_path(tmp_path / "app.db")
    run = repo.create_run(RunRequest(topic="solid-state battery electrolyte"))

    repo.start_stage(run.run_id, "retrieval")
    repo.finish_stage(
        run.run_id,
        "retrieval",
        summary=RetrievalSummary(
            canonical_topic="solid-state battery electrolyte",
            query_variants_used=["solid-state battery electrolyte"],
            search_notes=["broad query"],
            selected_paper_ids=["p1"],
            excluded_paper_ids=[],
            coverage_assessment="good",
            needs_broader_search=False,
        ).model_dump(),
    )

    summaries = repo.list_stage_summaries(run.run_id)

    assert len(summaries) == 1
    assert summaries[0].stage_name == "retrieval"
    assert summaries[0].status == "completed"
    assert summaries[0].summary["selected_paper_ids"] == ["p1"]
    assert summaries[0].started_at is not None
    assert summaries[0].completed_at is not None
