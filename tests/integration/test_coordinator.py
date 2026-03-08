from hypoforge.application.coordinator import RunCoordinator
from hypoforge.domain.schemas import (
    ConflictCluster,
    EvidenceCard,
    Hypothesis,
    MinimalExperiment,
    PaperDetail,
    RetrievalSummary,
    ReviewSummary,
    CriticSummary,
    PlannerSummary,
)
from hypoforge.infrastructure.db.repository import RunRepository


def test_coordinator_runs_all_stages_in_order(tmp_path) -> None:
    repo = RunRepository.from_sqlite_path(tmp_path / "app.db")
    stage_calls: list[str] = []

    def retrieval(run_id: str, topic: str, constraints) -> RetrievalSummary:
        del constraints
        stage_calls.append("retrieval")
        repo.save_selected_papers(
            run_id,
            [
                PaperDetail(
                    paper_id="p1",
                    title=topic,
                    abstract="Abstract",
                    year=2024,
                    authors=["A"],
                )
            ],
            "seed",
        )
        return RetrievalSummary(
            canonical_topic=topic,
            query_variants_used=[topic],
            search_notes=[],
            selected_paper_ids=["p1"],
            excluded_paper_ids=[],
            coverage_assessment="good",
            needs_broader_search=False,
        )

    def review(run_id: str) -> ReviewSummary:
        stage_calls.append("review")
        repo.save_evidence_cards(
            run_id,
            [
                EvidenceCard(
                    evidence_id="e1",
                    paper_id="p1",
                    title="Paper",
                    claim_text="Claim",
                    system_or_material="System",
                    intervention="Intervention",
                    outcome="Outcome",
                    direction="positive",
                    confidence=0.9,
                )
            ],
        )
        return ReviewSummary(
            papers_processed=1,
            evidence_cards_created=1,
            coverage_summary="ok",
            dominant_axes=["axis"],
            low_confidence_paper_ids=[],
        )

    def critic(run_id: str) -> CriticSummary:
        stage_calls.append("critic")
        repo.save_conflict_clusters(
            run_id,
            [
                ConflictCluster(
                    cluster_id="c1",
                    topic_axis="axis",
                    supporting_evidence_ids=["e1"],
                    conflicting_evidence_ids=["e1"],
                    conflict_type="weak_evidence_gap",
                    critic_summary="gap",
                    confidence=0.5,
                )
            ],
        )
        return CriticSummary(clusters_created=1, top_axes=["axis"], critic_notes=[])

    def planner(run_id: str) -> PlannerSummary:
        stage_calls.append("planner")
        repo.save_hypotheses(
            run_id,
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
                        readouts=["Readout"],
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
                        readouts=["Readout"],
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
                        readouts=["Readout"],
                        success_criteria="Success",
                        failure_interpretation="Failure",
                    ),
                    novelty_score=0.7,
                    feasibility_score=0.8,
                    overall_score=0.75,
                ),
            ],
        )
        repo.save_report_markdown(run_id, "# Report")
        return PlannerSummary(hypotheses_created=3, report_rendered=True, top_axes=["axis"], planner_notes=[])

    coordinator = RunCoordinator(
        repository=repo,
        retrieval_agent=retrieval,
        review_agent=review,
        critic_agent=critic,
        planner_agent=planner,
    )

    result = coordinator.run_topic("protein binder design")

    assert stage_calls == ["retrieval", "review", "critic", "planner"]
    assert result.status == "done"
    assert result.hypotheses[0].rank == 1
    assert [summary.stage_name for summary in result.stage_summaries] == [
        "retrieval",
        "review",
        "critic",
        "planner",
    ]
    assert result.stage_summaries[0].summary["selected_paper_ids"] == ["p1"]
    assert result.stage_summaries[1].summary["evidence_cards_created"] == 1
