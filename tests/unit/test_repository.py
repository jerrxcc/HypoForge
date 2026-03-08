from hypoforge.domain.schemas import (
    ConflictCluster,
    EvidenceCard,
    Hypothesis,
    MinimalExperiment,
    PaperDetail,
    RunRequest,
)
from hypoforge.infrastructure.db.repository import RunRepository


def test_repository_creates_and_loads_run(tmp_path) -> None:
    repo = RunRepository.from_sqlite_path(tmp_path / "app.db")

    run = repo.create_run(RunRequest(topic="protein binder design"))
    loaded = repo.get_run(run.run_id)

    assert loaded.run_id == run.run_id
    assert loaded.status == "queued"
    assert loaded.constraints.max_selected_papers == 36


def test_repository_stores_tool_trace(tmp_path) -> None:
    repo = RunRepository.from_sqlite_path(tmp_path / "app.db")
    run = repo.create_run(RunRequest(topic="CRISPR delivery lipid nanoparticles"))

    repo.record_tool_trace(
        run_id=run.run_id,
        agent_name="retrieval",
        tool_name="search_openalex_works",
        args={"query": "crispr delivery lipid nanoparticles"},
        result_summary={"count": 4},
        latency_ms=120,
        model_name="gpt-5.4",
        success=True,
    )

    traces = repo.list_tool_traces(run.run_id)

    assert len(traces) == 1
    assert traces[0]["tool_name"] == "search_openalex_works"


def test_repository_persists_error_message_on_status_update(tmp_path) -> None:
    repo = RunRepository.from_sqlite_path(tmp_path / "app.db")
    run = repo.create_run(RunRequest(topic="CRISPR delivery lipid nanoparticles"))

    repo.update_run_status(run.run_id, "failed", error_message="planner unavailable")

    loaded = repo.get_run(run.run_id)

    assert loaded.status == "failed"
    assert loaded.error_message == "planner unavailable"


def test_repository_builds_final_result(tmp_path) -> None:
    repo = RunRepository.from_sqlite_path(tmp_path / "app.db")
    run = repo.create_run(RunRequest(topic="solid-state battery electrolyte"))

    repo.save_selected_papers(
        run.run_id,
        papers=[
            PaperDetail(
                paper_id="p1",
                title="Paper 1",
                abstract="Abstract 1",
                year=2024,
                authors=["A. Author"],
            )
        ],
        selection_reason="seed",
    )
    repo.save_evidence_cards(
        run.run_id,
        [
            EvidenceCard(
                evidence_id="e1",
                paper_id="p1",
                title="Paper 1",
                claim_text="Claim",
                system_or_material="System",
                intervention="Intervention",
                outcome="Outcome",
                direction="positive",
                confidence=0.8,
            )
        ],
    )
    repo.save_conflict_clusters(
        run.run_id,
        [
            ConflictCluster(
                cluster_id="c1",
                topic_axis="axis",
                supporting_evidence_ids=["e1"],
                conflicting_evidence_ids=["e1"],
                conflict_type="weak_evidence_gap",
                critic_summary="Limited evidence",
                confidence=0.5,
            )
        ],
    )
    repo.save_hypotheses(
        run.run_id,
        [
            Hypothesis(
                rank=1,
                title="H1",
                hypothesis_statement="Statement",
                why_plausible="Plausible",
                why_not_obvious="Not obvious",
                supporting_evidence_ids=["e1", "e2", "e3"],
                counterevidence_ids=["e4"],
                prediction="Prediction",
                minimal_experiment=MinimalExperiment(
                    system="System",
                    design="Design",
                    control="Control",
                    readouts=["R1"],
                    success_criteria="Success",
                    failure_interpretation="Failure",
                ),
                novelty_score=0.7,
                feasibility_score=0.8,
                overall_score=0.75,
            ),
            Hypothesis(
                rank=2,
                title="H2",
                hypothesis_statement="Statement",
                why_plausible="Plausible",
                why_not_obvious="Not obvious",
                supporting_evidence_ids=["e1", "e2", "e3"],
                counterevidence_ids=["e4"],
                prediction="Prediction",
                minimal_experiment=MinimalExperiment(
                    system="System",
                    design="Design",
                    control="Control",
                    readouts=["R1"],
                    success_criteria="Success",
                    failure_interpretation="Failure",
                ),
                novelty_score=0.7,
                feasibility_score=0.8,
                overall_score=0.75,
            ),
            Hypothesis(
                rank=3,
                title="H3",
                hypothesis_statement="Statement",
                why_plausible="Plausible",
                why_not_obvious="Not obvious",
                supporting_evidence_ids=["e1", "e2", "e3"],
                counterevidence_ids=["e4"],
                prediction="Prediction",
                minimal_experiment=MinimalExperiment(
                    system="System",
                    design="Design",
                    control="Control",
                    readouts=["R1"],
                    success_criteria="Success",
                    failure_interpretation="Failure",
                ),
                novelty_score=0.7,
                feasibility_score=0.8,
                overall_score=0.75,
            ),
        ],
    )
    repo.save_report_markdown(run.run_id, "# Report")
    repo.update_run_status(run.run_id, "done")

    result = repo.build_final_result(run.run_id)

    assert result.status == "done"
    assert len(result.selected_papers) == 1
    assert len(result.hypotheses) == 3
    assert result.report_markdown == "# Report"
