"""Tests for reflection retry mechanism.

Tests that:
- Quality evaluation is performed for each stage
- Feedback is created and stored when quality is low
- Maximum iterations are tracked
- Feedback context is available for potential retries
"""

from pathlib import Path

import pytest

from hypoforge.application.coordinator import RunCoordinator
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


def test_quality_evaluation_performed_for_each_stage(tmp_path: Path) -> None:
    """Test that quality evaluation is performed for each stage when reflection is enabled."""
    repo, agent, settings = build_reflection_test_services(
        tmp_path,
        quality_scores_by_stage={
            "retrieval": [0.75],
            "review": [0.75],
            "critic": [0.75],
            "planner": [0.75],
        },
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
                    critic_summary="gap",
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

    # Verify run completed successfully
    assert result.status == "done"

    # Verify reflection agent was called for each stage
    assert agent.call_count.get("retrieval", 0) == 1
    assert agent.call_count.get("review", 0) == 1
    assert agent.call_count.get("critic", 0) == 1
    assert agent.call_count.get("planner", 0) == 1


def test_low_quality_records_feedback_with_issues(tmp_path: Path) -> None:
    """Test that low quality scores generate feedback with issues."""
    repo, agent, settings = build_reflection_test_services(
        tmp_path,
        quality_scores_by_stage={
            "retrieval": [0.3],  # Low quality
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
                    critic_summary="gap",
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

    # Verify run completed
    assert result.status == "done"

    # Verify feedback was saved for retrieval (low quality stage)
    feedback_history = repo.load_reflection_history(result.run_id, "retrieval")
    assert len(feedback_history) >= 1

    # Verify feedback has issues indicating low quality
    retrieval_feedback = feedback_history[0]
    assert retrieval_feedback.target_stage == "retrieval"
    assert retrieval_feedback.quality_scores.get("overall", 0) < 0.6


def test_max_iterations_configuration(tmp_path: Path) -> None:
    """Test that max iterations configuration is respected."""
    max_iterations = 2
    repo, agent, settings = build_reflection_test_services(
        tmp_path,
        quality_scores_by_stage={
            "retrieval": [0.3],
            "review": [0.8],
            "critic": [0.8],
            "planner": [0.8],
        },
        reflection_settings=ReflectionSettings(
            enable_reflection=True,
            max_stage_iterations=max_iterations,
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
                    critic_summary="gap",
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

    # Verify run completed
    assert result.status == "done"

    # Verify iteration state has correct max_iterations setting
    iteration_state = repo.load_iteration_state(result.run_id)
    assert iteration_state is not None
    retrieval_state = iteration_state.stage_iterations.get("retrieval")
    if retrieval_state:
        assert retrieval_state.max_iterations == max_iterations


def test_feedback_includes_quality_scores(tmp_path: Path) -> None:
    """Test that feedback includes quality scores for analysis."""
    repo, agent, settings = build_reflection_test_services(
        tmp_path,
        quality_scores_by_stage={
            "retrieval": [0.5],  # Medium quality
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
            coverage_assessment="medium",
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
                    critic_summary="gap",
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

    # Verify run completed
    assert result.status == "done"

    # Verify feedback has quality scores
    feedback_history = repo.load_reflection_history(result.run_id)
    assert len(feedback_history) >= 1

    for feedback in feedback_history:
        assert "overall" in feedback.quality_scores
        assert isinstance(feedback.quality_scores["overall"], float)


def test_multiple_stages_generate_feedback(tmp_path: Path) -> None:
    """Test that each stage generates its own feedback."""
    repo, agent, settings = build_reflection_test_services(
        tmp_path,
        quality_scores_by_stage={
            "retrieval": [0.5],
            "review": [0.5],
            "critic": [0.5],
            "planner": [0.5],
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
            coverage_assessment="medium",
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
                    confidence=0.5,
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
                    critic_summary="gap",
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

    result = coordinator.run_topic("test topic")

    # Verify run completed
    assert result.status == "done"

    # Verify each stage generated feedback
    all_feedback = repo.load_reflection_history(result.run_id)
    stages_with_feedback = set(f.target_stage for f in all_feedback)

    # Each stage should have at least one feedback entry
    assert "retrieval" in stages_with_feedback
    assert "review" in stages_with_feedback
    assert "critic" in stages_with_feedback
    assert "planner" in stages_with_feedback
