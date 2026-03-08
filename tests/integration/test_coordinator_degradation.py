from hypoforge.application.coordinator import RunCoordinator
from hypoforge.application.report_renderer import ReportRenderer
from hypoforge.domain.schemas import (
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


def test_coordinator_continues_when_critic_fails(tmp_path) -> None:
    repo = RunRepository.from_sqlite_path(tmp_path / "app.db")

    def retrieval(run_id: str, topic: str, constraints) -> RetrievalSummary:
        del constraints
        repo.save_selected_papers(
            run_id,
            [PaperDetail(paper_id="p1", title=topic, abstract="Abstract", year=2024, authors=["A"])],
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
        del run_id
        raise RuntimeError("critic unavailable")

    def planner(run_id: str) -> PlannerSummary:
        repo.save_hypotheses(
            run_id,
            [
                _hypothesis(rank=1),
                _hypothesis(rank=2),
                _hypothesis(rank=3),
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
        report_renderer=ReportRenderer(),
    )

    result = coordinator.run_topic("protein binder design")

    assert result.status == "done"
    assert len(result.hypotheses) == 3


def test_coordinator_returns_partial_result_when_planner_fails(tmp_path) -> None:
    repo = RunRepository.from_sqlite_path(tmp_path / "app.db")

    def retrieval(run_id: str, topic: str, constraints) -> RetrievalSummary:
        del constraints
        repo.save_selected_papers(
            run_id,
            [PaperDetail(paper_id="p1", title=topic, abstract="Abstract", year=2024, authors=["A"])],
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
        del run_id
        return CriticSummary(clusters_created=0, top_axes=[], critic_notes=["skipped"])

    def planner(run_id: str) -> PlannerSummary:
        del run_id
        raise RuntimeError("planner unavailable")

    coordinator = RunCoordinator(
        repository=repo,
        retrieval_agent=retrieval,
        review_agent=review,
        critic_agent=critic,
        planner_agent=planner,
        report_renderer=ReportRenderer(),
    )

    result = coordinator.run_topic("protein binder design")

    assert result.status == "failed"
    assert len(result.selected_papers) == 1
    assert len(result.evidence_cards) == 1
    assert result.report_markdown is not None
    assert repo.get_run(result.run_id).error_message == "planner unavailable"


def test_coordinator_can_rerun_planner_after_failure(tmp_path) -> None:
    repo = RunRepository.from_sqlite_path(tmp_path / "app.db")
    planner_attempts = 0

    def retrieval(run_id: str, topic: str, constraints) -> RetrievalSummary:
        del constraints
        repo.save_selected_papers(
            run_id,
            [PaperDetail(paper_id="p1", title=topic, abstract="Abstract", year=2024, authors=["A"])],
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
        del run_id
        return CriticSummary(clusters_created=0, top_axes=[], critic_notes=["skipped"])

    def planner(run_id: str) -> PlannerSummary:
        nonlocal planner_attempts
        planner_attempts += 1
        if planner_attempts == 1:
            raise RuntimeError("planner unavailable")
        repo.save_hypotheses(run_id, [_hypothesis(1), _hypothesis(2), _hypothesis(3)])
        repo.save_report_markdown(run_id, "# Report")
        return PlannerSummary(hypotheses_created=3, report_rendered=True, top_axes=["axis"], planner_notes=["rerun"])

    coordinator = RunCoordinator(
        repository=repo,
        retrieval_agent=retrieval,
        review_agent=review,
        critic_agent=critic,
        planner_agent=planner,
        report_renderer=ReportRenderer(),
    )

    failed_result = coordinator.run_topic("protein binder design")
    rerun_result = coordinator.rerun_planner(failed_result.run_id)

    assert failed_result.status == "failed"
    assert rerun_result.status == "done"
    assert len(rerun_result.hypotheses) == 3
    assert planner_attempts == 2
    assert repo.get_run(rerun_result.run_id).error_message is None
    planner_summary = {summary.stage_name: summary for summary in rerun_result.stage_summaries}["planner"]
    assert planner_summary.status == "completed"


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
