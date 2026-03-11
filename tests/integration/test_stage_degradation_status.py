from hypoforge.application.coordinator import RunCoordinator
from hypoforge.application.report_renderer import ReportRenderer
from hypoforge.domain.schemas import (
    ConflictCluster,
    CriticSummary,
    EvidenceCard,
    Hypothesis,
    MinimalExperiment,
    PaperDetail,
    PlannerSummary,
    RetrievalSummary,
    ReviewSummary,
)
from hypoforge.infrastructure.db.repository import RunRepository


def test_stage_summaries_mark_retrieval_and_review_degradation(tmp_path) -> None:
    repo = RunRepository.from_sqlite_path(tmp_path / "app.db")

    def retrieval(run_id: str, topic: str, constraints) -> RetrievalSummary:
        del constraints
        repo.save_selected_papers(
            run_id,
            [PaperDetail(paper_id=f"p{i}", title=f"{topic} {i}") for i in range(1, 7)],
            "seed",
        )
        return RetrievalSummary(
            canonical_topic=topic,
            query_variants_used=[topic],
            search_notes=["low evidence mode after broadened retrieval"],
            selected_paper_ids=[f"p{i}" for i in range(1, 7)],
            excluded_paper_ids=[],
            coverage_assessment="low",
            needs_broader_search=True,
        )

    def review(run_id: str) -> ReviewSummary:
        repo.save_evidence_cards(
            run_id,
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
                    confidence=0.9,
                )
            ],
        )
        return ReviewSummary(
            papers_processed=1,
            evidence_cards_created=1,
            coverage_summary="processed 1/6 selected papers across 3 batches; 2 failed batches degraded to partial extraction",
            dominant_axes=["axis"],
            low_confidence_paper_ids=[],
            failed_paper_ids=["p2", "p3", "p4", "p5", "p6"],
        )

    def critic(run_id: str) -> CriticSummary:
        del run_id
        return CriticSummary(clusters_created=0, top_axes=[], critic_notes=[])

    def planner(run_id: str) -> PlannerSummary:
        repo.save_hypotheses(run_id, [_hypothesis(1), _hypothesis(2), _hypothesis(3)])
        repo.save_report_markdown(run_id, "# Report")
        return PlannerSummary(hypotheses_created=3, report_rendered=True, top_axes=[], planner_notes=[])

    coordinator = RunCoordinator(
        repository=repo,
        retrieval_agent=retrieval,
        review_agent=review,
        critic_agent=critic,
        planner_agent=planner,
        report_renderer=ReportRenderer(),
    )

    result = coordinator.run_topic("protein binder design")

    assert result.status == "done"
    summaries = {summary.stage_name: summary for summary in result.stage_summaries}
    assert summaries["retrieval"].status == "degraded"
    assert summaries["review"].status == "degraded"
    assert summaries["critic"].status == "completed"
    assert summaries["planner"].status == "completed"


def test_stage_summaries_mark_critic_and_planner_budget_recovery_as_degraded(tmp_path) -> None:
    repo = RunRepository.from_sqlite_path(tmp_path / "app.db")

    def retrieval(run_id: str, topic: str, constraints) -> RetrievalSummary:
        del constraints
        repo.save_selected_papers(
            run_id,
            [PaperDetail(paper_id="p1", title=topic)],
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
        repo.save_evidence_cards(
            run_id,
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
                    confidence=0.9,
                )
            ],
        )
        return ReviewSummary(
            papers_processed=1,
            evidence_cards_created=1,
            coverage_summary="ok",
            dominant_axes=[],
            low_confidence_paper_ids=[],
        )

    def critic(run_id: str) -> CriticSummary:
        repo.save_conflict_clusters(
            run_id,
            [
                ConflictCluster(
                    cluster_id="cluster_1",
                    topic_axis="axis",
                    supporting_evidence_ids=["e1"],
                    conflicting_evidence_ids=[],
                    conflict_type="weak_evidence_gap",
                    critic_summary="partial",
                    confidence=0.5,
                )
            ],
        )
        return CriticSummary(
            clusters_created=1,
            top_axes=["axis"],
            critic_notes=["critic tool step budget exceeded; returning saved clusters"],
        )

    def planner(run_id: str) -> PlannerSummary:
        repo.save_hypotheses(run_id, [_hypothesis(1), _hypothesis(2), _hypothesis(3)])
        repo.save_report_markdown(run_id, "# Report")
        return PlannerSummary(
            hypotheses_created=3,
            report_rendered=True,
            top_axes=["axis"],
            planner_notes=["planner tool step budget exceeded; returning saved hypotheses"],
        )

    coordinator = RunCoordinator(
        repository=repo,
        retrieval_agent=retrieval,
        review_agent=review,
        critic_agent=critic,
        planner_agent=planner,
        report_renderer=ReportRenderer(),
    )

    result = coordinator.run_topic("protein binder design")

    summaries = {summary.stage_name: summary for summary in result.stage_summaries}
    assert summaries["critic"].status == "degraded"
    assert summaries["planner"].status == "degraded"


def test_retrieval_medium_coverage_warning_does_not_force_degraded_status(tmp_path) -> None:
    repo = RunRepository.from_sqlite_path(tmp_path / "app.db")

    def retrieval(run_id: str, topic: str, constraints) -> RetrievalSummary:
        del constraints
        repo.save_selected_papers(
            run_id,
            [PaperDetail(paper_id=f"p{i}", title=f"{topic} {i}") for i in range(1, 13)],
            "seed",
        )
        return RetrievalSummary(
            canonical_topic=topic,
            query_variants_used=[topic],
            search_notes=["single-source fallback used after Semantic Scholar rate limiting"],
            selected_paper_ids=[f"p{i}" for i in range(1, 13)],
            excluded_paper_ids=[],
            coverage_assessment="medium",
            needs_broader_search=True,
        )

    def review(run_id: str) -> ReviewSummary:
        repo.save_evidence_cards(
            run_id,
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
                    confidence=0.9,
                )
            ],
        )
        return ReviewSummary(
            papers_processed=12,
            evidence_cards_created=1,
            coverage_summary="processed 12/12 selected papers",
            dominant_axes=["axis"],
            low_confidence_paper_ids=[],
        )

    def critic(run_id: str) -> CriticSummary:
        del run_id
        return CriticSummary(clusters_created=0, top_axes=[], critic_notes=[])

    def planner(run_id: str) -> PlannerSummary:
        repo.save_hypotheses(run_id, [_hypothesis(1), _hypothesis(2), _hypothesis(3)])
        repo.save_report_markdown(run_id, "# Report")
        return PlannerSummary(hypotheses_created=3, report_rendered=True, top_axes=[], planner_notes=[])

    coordinator = RunCoordinator(
        repository=repo,
        retrieval_agent=retrieval,
        review_agent=review,
        critic_agent=critic,
        planner_agent=planner,
        report_renderer=ReportRenderer(),
    )

    result = coordinator.run_topic("CRISPR delivery lipid nanoparticles")

    summaries = {summary.stage_name: summary for summary in result.stage_summaries}
    assert summaries["retrieval"].status == "completed"


def _hypothesis(rank: int) -> Hypothesis:
    return Hypothesis(
        rank=rank,
        title=f"H{rank}",
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
    )
