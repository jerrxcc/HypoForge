"""End-to-end tests for the reflection-correction loop system.

Tests complete realistic scenarios:
- Full pipeline with reflection enabled
- Quality evaluation at each stage
- Feedback recording and retrieval
- Iteration state tracking
"""

from pathlib import Path

import pytest

from hypoforge.application.coordinator import RunCoordinator
from hypoforge.application.stage_graph import StageNavigator
from hypoforge.config import ReflectionSettings
from hypoforge.domain.schemas import (
    ConflictCluster,
    CriticSummary,
    EvidenceCard,
    PaperDetail,
    PlannerSummary,
    RetrievalSummary,
    ReviewSummary,
)
from hypoforge.infrastructure.db.repository import RunRepository
from tests.helpers.reflection_helpers import (
    ScriptedReflectionAgent,
    build_reflection_test_services,
    make_three_test_hypotheses,
)


def test_full_e2e_with_reflection_enabled(tmp_path: Path) -> None:
    """Test full pipeline with reflection enabled.

    Scenario:
    1. All stages pass with good quality
    2. Pipeline completes successfully
    3. Feedback is recorded for each stage
    """
    repo, agent, settings = build_reflection_test_services(
        tmp_path,
        quality_scores_by_stage={
            "retrieval": [0.75],
            "review": [0.8],
            "critic": [0.8],
            "planner": [0.8],
        },
        reflection_settings=ReflectionSettings(
            enable_reflection=True,
            max_stage_iterations=3,
            max_cross_stage_iterations=2,
        ),
        reflection_enabled=True,
    )

    call_history: list[str] = []

    def retrieval(run_id: str, topic: str, constraints) -> RetrievalSummary:
        call_history.append("retrieval")
        repo.save_selected_papers(
            run_id,
            [
                PaperDetail(
                    paper_id=f"p{i}",
                    title=f"Paper {i}",
                    abstract=f"Abstract {i}",
                    year=2024,
                    authors=[f"Author {i}"],
                    provenance=["test"],
                )
                for i in range(12)
            ],
            "seed",
        )
        return RetrievalSummary(
            canonical_topic=topic,
            query_variants_used=[topic],
            search_notes=[],
            selected_paper_ids=[f"p{i}" for i in range(12)],
            excluded_paper_ids=[],
            coverage_assessment="good",
            needs_broader_search=False,
        )

    def review(run_id: str) -> ReviewSummary:
        call_history.append("review")
        papers = repo.load_selected_papers(run_id)

        cards = [
            EvidenceCard(
                evidence_id=f"e{i}",
                paper_id=papers[i % len(papers)].paper_id,
                title=f"Evidence {i}",
                claim_text=f"Claim {i}",
                system_or_material=f"System {i}",
                intervention=f"Intervention {i}",
                outcome=f"Outcome {i}",
                direction="positive",
                confidence=0.8,
            )
            for i in range(len(papers) * 2)
        ]
        repo.save_evidence_cards(run_id, cards)
        return ReviewSummary(
            papers_processed=len(papers),
            evidence_cards_created=len(cards),
            coverage_summary="good coverage",
            dominant_axes=["axis1", "axis2"],
            low_confidence_paper_ids=[],
        )

    def critic(run_id: str) -> CriticSummary:
        call_history.append("critic")
        evidence = repo.load_evidence_cards(run_id)

        clusters = [
            ConflictCluster(
                cluster_id=f"c{i}",
                topic_axis=f"axis{i}",
                supporting_evidence_ids=[evidence[i * 2].evidence_id],
                conflicting_evidence_ids=[evidence[i * 2 + 1].evidence_id if len(evidence) > i * 2 + 1 else evidence[0].evidence_id],
                conflict_type="weak_evidence_gap",
                likely_explanations=[f"Explanation {i}"],
                critic_summary=f"Conflict {i}",
                confidence=0.7,
            )
            for i in range(min(3, len(evidence) // 2))
        ]
        repo.save_conflict_clusters(run_id, clusters)
        return CriticSummary(
            clusters_created=len(clusters),
            top_axes=[c.topic_axis for c in clusters],
            critic_notes=[],
        )

    def planner(run_id: str) -> PlannerSummary:
        call_history.append("planner")
        repo.save_hypotheses(run_id, make_three_test_hypotheses())
        repo.save_report_markdown(run_id, "# Final Report\n\nGenerated hypotheses.")
        return PlannerSummary(
            hypotheses_created=3,
            report_rendered=True,
            top_axes=["axis1"],
            planner_notes=[],
        )

    coordinator = RunCoordinator(
        repository=repo,
        retrieval_agent=retrieval,
        review_agent=review,
        critic_agent=critic,
        planner_agent=planner,
        reflection_agent=agent,
        reflection_settings=settings,
    )

    result = coordinator.run_topic("protein binder design")

    # Verify successful completion
    assert result.status == "done"
    assert len(result.hypotheses) == 3

    # Verify each stage was called
    assert "retrieval" in call_history
    assert "review" in call_history
    assert "critic" in call_history
    assert "planner" in call_history

    # Verify feedback was recorded for each stage
    all_feedback = repo.load_reflection_history(result.run_id)
    assert len(all_feedback) == 4  # One for each stage

    # Verify iteration state exists
    iteration_state = repo.load_iteration_state(result.run_id)
    assert iteration_state is not None
    assert iteration_state.reflection_enabled is True


def test_full_e2e_with_mixed_quality_scores(tmp_path: Path) -> None:
    """Test full pipeline with varying quality scores.

    Scenario:
    1. Retrieval has medium quality
    2. Review has high quality
    3. Critic has low quality
    4. Planner has high quality
    5. Pipeline completes with feedback recorded
    """
    repo, agent, settings = build_reflection_test_services(
        tmp_path,
        quality_scores_by_stage={
            "retrieval": [0.5],  # Medium
            "review": [0.8],  # High
            "critic": [0.3],  # Low
            "planner": [0.8],  # High
        },
        reflection_settings=ReflectionSettings(
            enable_reflection=True,
            max_stage_iterations=3,
            max_cross_stage_iterations=2,
        ),
        reflection_enabled=True,
    )

    def retrieval(run_id: str, topic: str, constraints) -> RetrievalSummary:
        repo.save_selected_papers(
            run_id,
            [
                PaperDetail(
                    paper_id=f"p{i}",
                    title=f"Paper {i}",
                    year=2024,
                    provenance=["test"],
                )
                for i in range(6)
            ],
            "seed",
        )
        return RetrievalSummary(
            canonical_topic=topic,
            query_variants_used=[topic],
            search_notes=[],
            selected_paper_ids=[f"p{i}" for i in range(6)],
            excluded_paper_ids=[],
            coverage_assessment="medium",
            needs_broader_search=False,
        )

    def review(run_id: str) -> ReviewSummary:
        repo.save_evidence_cards(
            run_id,
            [
                EvidenceCard(
                    evidence_id=f"e{i}",
                    paper_id="p1",
                    title=f"Evidence {i}",
                    claim_text="Claim",
                    system_or_material="System",
                    intervention="Intervention",
                    outcome="Outcome",
                    direction="positive",
                    confidence=0.8,
                )
                for i in range(5)
            ],
        )
        return ReviewSummary(
            papers_processed=5,
            evidence_cards_created=5,
            coverage_summary="good",
            dominant_axes=["axis"],
            low_confidence_paper_ids=[],
        )

    def critic(run_id: str) -> CriticSummary:
        repo.save_conflict_clusters(
            run_id,
            [
                ConflictCluster(
                    cluster_id="c1",
                    topic_axis="axis",
                    supporting_evidence_ids=["e1"],
                    conflicting_evidence_ids=["e2"],
                    conflict_type="weak_evidence_gap",
                    critic_summary="Conflict",
                    confidence=0.5,
                )
            ],
        )
        return CriticSummary(clusters_created=1, top_axes=["axis"], critic_notes=[])

    def planner(run_id: str) -> PlannerSummary:
        repo.save_hypotheses(run_id, make_three_test_hypotheses())
        repo.save_report_markdown(run_id, "# Report")
        return PlannerSummary(hypotheses_created=3, report_rendered=True, top_axes=["axis"], planner_notes=[])

    coordinator = RunCoordinator(
        repository=repo,
        retrieval_agent=retrieval,
        review_agent=review,
        critic_agent=critic,
        planner_agent=planner,
        reflection_agent=agent,
        reflection_settings=settings,
    )

    result = coordinator.run_topic("enzyme engineering")

    # Verify successful completion
    assert result.status == "done"

    # Verify all feedback was recorded
    all_feedback = repo.load_reflection_history(result.run_id)
    assert len(all_feedback) == 4

    # Verify feedback has correct quality scores
    retrieval_feedback = [f for f in all_feedback if f.target_stage == "retrieval"][0]
    assert retrieval_feedback.quality_scores["overall"] == 0.5

    critic_feedback = [f for f in all_feedback if f.target_stage == "critic"][0]
    assert critic_feedback.quality_scores["overall"] == 0.3


def test_full_e2e_with_backtrack_recommendation(tmp_path: Path) -> None:
    """Test full pipeline with backtracking recommendation recorded in feedback.

    Scenario:
    1. Critic detects issue and recommends backtrack
    2. Pipeline records the backtrack recommendation in feedback
    3. Pipeline completes without actual backtracking (no StageNavigator)
    """
    repo, agent, settings = build_reflection_test_services(
        tmp_path,
        quality_scores_by_stage={
            "retrieval": [0.8],
            "review": [0.8],
            "critic": [0.25],  # Low quality triggers backtrack recommendation
            "planner": [0.8],
        },
        backtrack_decisions={
            "critic": ["retrieval"],
        },
        severity_override={
            "critic": "high",
        },
        reflection_settings=ReflectionSettings(
            enable_reflection=True,
            max_stage_iterations=3,
            max_cross_stage_iterations=2,
        ),
        reflection_enabled=True,
    )

    def retrieval(run_id: str, topic: str, constraints) -> RetrievalSummary:
        repo.save_selected_papers(
            run_id,
            [
                PaperDetail(
                    paper_id=f"p{i}",
                    title=f"Paper {i}",
                    year=2024,
                    provenance=["test"],
                )
                for i in range(10)
            ],
            "seed",
        )
        return RetrievalSummary(
            canonical_topic=topic,
            query_variants_used=[topic],
            search_notes=[],
            selected_paper_ids=[f"p{i}" for i in range(10)],
            excluded_paper_ids=[],
            coverage_assessment="good",
            needs_broader_search=False,
        )

    def review(run_id: str) -> ReviewSummary:
        repo.save_evidence_cards(
            run_id,
            [
                EvidenceCard(
                    evidence_id=f"e{i}",
                    paper_id="p1",
                    title=f"Evidence {i}",
                    claim_text="Claim",
                    system_or_material="System",
                    intervention="Intervention",
                    outcome="Outcome",
                    direction="positive",
                    confidence=0.8,
                )
                for i in range(5)
            ],
        )
        return ReviewSummary(
            papers_processed=5,
            evidence_cards_created=5,
            coverage_summary="ok",
            dominant_axes=["axis"],
            low_confidence_paper_ids=[],
        )

    def critic(run_id: str) -> CriticSummary:
        repo.save_conflict_clusters(
            run_id,
            [
                ConflictCluster(
                    cluster_id="c1",
                    topic_axis="axis",
                    supporting_evidence_ids=["e1"],
                    conflicting_evidence_ids=["e2"],
                    conflict_type="weak_evidence_gap",
                    critic_summary="Conflict",
                    confidence=0.5,
                )
            ],
        )
        return CriticSummary(clusters_created=1, top_axes=["axis"], critic_notes=[])

    def planner(run_id: str) -> PlannerSummary:
        repo.save_hypotheses(run_id, make_three_test_hypotheses())
        repo.save_report_markdown(run_id, "# Report")
        return PlannerSummary(hypotheses_created=3, report_rendered=True, top_axes=["axis"], planner_notes=[])

    # Note: We don't pass stage_navigator, so backtracking won't actually happen
    # but the recommendation should still be recorded in feedback
    coordinator = RunCoordinator(
        repository=repo,
        retrieval_agent=retrieval,
        review_agent=review,
        critic_agent=critic,
        planner_agent=planner,
        reflection_agent=agent,
        reflection_settings=settings,
        # stage_navigator not passed - no actual backtracking
    )

    result = coordinator.run_topic("CRISPR gene editing")

    # Verify successful completion
    assert result.status == "done"

    # Verify critic feedback has backtrack recommendation
    critic_feedback = repo.load_reflection_history(result.run_id, "critic")
    assert len(critic_feedback) >= 1
    assert critic_feedback[0].recommended_backtrack_stage == "retrieval"


def test_full_e2e_iteration_state_tracking(tmp_path: Path) -> None:
    """Test that iteration state is properly tracked throughout the pipeline."""
    repo, agent, settings = build_reflection_test_services(
        tmp_path,
        quality_scores_by_stage={
            "retrieval": [0.7],
            "review": [0.7],
            "critic": [0.7],
            "planner": [0.7],
        },
        reflection_settings=ReflectionSettings(
            enable_reflection=True,
            max_stage_iterations=3,
            max_cross_stage_iterations=2,
        ),
        reflection_enabled=True,
    )

    def retrieval(run_id: str, topic: str, constraints) -> RetrievalSummary:
        repo.save_selected_papers(
            run_id,
            [PaperDetail(paper_id="p1", title=topic, year=2024, provenance=["test"])],
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
                    title="Evidence",
                    claim_text="Claim",
                    system_or_material="System",
                    intervention="Intervention",
                    outcome="Outcome",
                    direction="positive",
                    confidence=0.7,
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
        repo.save_conflict_clusters(
            run_id,
            [
                ConflictCluster(
                    cluster_id="c1",
                    topic_axis="axis",
                    supporting_evidence_ids=["e1"],
                    conflicting_evidence_ids=["e1"],
                    conflict_type="weak_evidence_gap",
                    critic_summary="Conflict",
                    confidence=0.7,
                )
            ],
        )
        return CriticSummary(clusters_created=1, top_axes=["axis"], critic_notes=[])

    def planner(run_id: str) -> PlannerSummary:
        repo.save_hypotheses(run_id, make_three_test_hypotheses())
        repo.save_report_markdown(run_id, "# Report")
        return PlannerSummary(hypotheses_created=3, report_rendered=True, top_axes=["axis"], planner_notes=[])

    coordinator = RunCoordinator(
        repository=repo,
        retrieval_agent=retrieval,
        review_agent=review,
        critic_agent=critic,
        planner_agent=planner,
        reflection_agent=agent,
        reflection_settings=settings,
    )

    result = coordinator.run_topic("test topic")

    # Verify successful completion
    assert result.status == "done"

    # Verify iteration state was saved
    iteration_state = repo.load_iteration_state(result.run_id)
    assert iteration_state is not None

    # Verify stage states
    assert len(iteration_state.stage_iterations) == 4

    # Verify each stage has an iteration state
    assert "retrieval" in iteration_state.stage_iterations
    assert "review" in iteration_state.stage_iterations
    assert "critic" in iteration_state.stage_iterations
    assert "planner" in iteration_state.stage_iterations

    # Verify settings are correctly stored
    assert iteration_state.max_cross_stage_iterations == 2
    assert iteration_state.reflection_enabled is True


def test_full_e2e_coordinator_api_methods(tmp_path: Path) -> None:
    """Test that coordinator API methods work correctly with reflection."""
    repo, agent, settings = build_reflection_test_services(
        tmp_path,
        quality_scores_by_stage={
            "retrieval": [0.8],
            "review": [0.8],
            "critic": [0.8],
            "planner": [0.8],
        },
        reflection_enabled=True,
    )

    def retrieval(run_id: str, topic: str, constraints) -> RetrievalSummary:
        repo.save_selected_papers(
            run_id,
            [PaperDetail(paper_id="p1", title=topic, year=2024, provenance=["test"])],
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
                    title="Evidence",
                    claim_text="Claim",
                    system_or_material="System",
                    intervention="Intervention",
                    outcome="Outcome",
                    direction="positive",
                    confidence=0.8,
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
        repo.save_conflict_clusters(
            run_id,
            [
                ConflictCluster(
                    cluster_id="c1",
                    topic_axis="axis",
                    supporting_evidence_ids=["e1"],
                    conflicting_evidence_ids=["e1"],
                    conflict_type="weak_evidence_gap",
                    critic_summary="Conflict",
                    confidence=0.7,
                )
            ],
        )
        return CriticSummary(clusters_created=1, top_axes=["axis"], critic_notes=[])

    def planner(run_id: str) -> PlannerSummary:
        repo.save_hypotheses(run_id, make_three_test_hypotheses())
        repo.save_report_markdown(run_id, "# Report")
        return PlannerSummary(hypotheses_created=3, report_rendered=True, top_axes=["axis"], planner_notes=[])

    coordinator = RunCoordinator(
        repository=repo,
        retrieval_agent=retrieval,
        review_agent=review,
        critic_agent=critic,
        planner_agent=planner,
        reflection_agent=agent,
        reflection_settings=settings,
    )

    result = coordinator.run_topic("test topic")

    # Test get_reflection_history API
    history = coordinator.get_reflection_history(result.run_id)
    assert len(history) == 4

    # Test get_reflection_history with stage filter
    retrieval_history = coordinator.get_reflection_history(result.run_id, "retrieval")
    assert len(retrieval_history) == 1
    assert retrieval_history[0].target_stage == "retrieval"

    # Test get_iteration_state API
    iteration_state = coordinator.get_iteration_state(result.run_id)
    assert iteration_state is not None
    assert iteration_state.reflection_enabled is True
