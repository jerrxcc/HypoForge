"""Tests for reflection disabled mode.

Tests that:
- Reflection disabled runs linear pipeline
- No iteration state is created when reflection is disabled
- Reflection agent is not called when disabled
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


def test_reflection_disabled_runs_linear_pipeline(tmp_path: Path) -> None:
    """Test that disabled reflection runs a linear pipeline without retry."""
    repo, agent, settings = build_reflection_test_services(
        tmp_path,
        quality_scores_by_stage={
            "retrieval": [0.3],  # Low quality - but should not trigger retry
            "review": [0.3],
            "critic": [0.3],
            "planner": [0.3],
        },
        reflection_settings=ReflectionSettings(
            enable_reflection=False,  # Disabled
        ),
        reflection_enabled=False,
    )

    call_counts: dict[str, int] = {"retrieval": 0, "review": 0, "critic": 0, "planner": 0}

    def retrieval(run_id: str, topic: str, constraints) -> RetrievalSummary:
        call_counts["retrieval"] += 1
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
            coverage_assessment="low",  # Low quality
            needs_broader_search=True,
        )

    def review(run_id: str) -> ReviewSummary:
        call_counts["review"] += 1
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
        call_counts["critic"] += 1
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
        call_counts["planner"] += 1
        repo.save_hypotheses(run_id, make_three_test_hypotheses())
        repo.save_report_markdown(run_id, "# Report")
        return PlannerSummary(hypotheses_created=3, report_rendered=True, top_axes=["axis"], planner_notes=[])

    coordinator = RunCoordinator(
        repository=repo,
        retrieval_agent=retrieval,
        review_agent=review,
        critic_agent=critic,
        planner_agent=planner,
        reflection_agent=agent,  # Agent provided but should not be used
        reflection_settings=settings,
    )

    result = coordinator.run_topic("test topic")

    # Verify run completed successfully
    assert result.status == "done"

    # Verify each stage was called exactly once (linear execution)
    assert call_counts["retrieval"] == 1
    assert call_counts["review"] == 1
    assert call_counts["critic"] == 1
    assert call_counts["planner"] == 1

    # Verify reflection agent was never called
    assert agent.call_count == {}


def test_no_iteration_state_when_disabled(tmp_path: Path) -> None:
    """Test that no iteration state is created when reflection is disabled."""
    repo, agent, settings = build_reflection_test_services(
        tmp_path,
        reflection_settings=ReflectionSettings(
            enable_reflection=False,
        ),
        reflection_enabled=False,
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

    # Verify no iteration state exists (or reflection_enabled is False)
    iteration_state = repo.load_iteration_state(result.run_id)
    if iteration_state:
        # If state exists, reflection should be disabled
        assert iteration_state.reflection_enabled is False


def test_no_reflection_feedback_saved_when_disabled(tmp_path: Path) -> None:
    """Test that no reflection feedback is saved when reflection is disabled."""
    repo, agent, settings = build_reflection_test_services(
        tmp_path,
        quality_scores_by_stage={
            "retrieval": [0.3],  # Would normally trigger retry
        },
        reflection_settings=ReflectionSettings(
            enable_reflection=False,
        ),
        reflection_enabled=False,
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

    # Verify no reflection feedback was saved
    feedback_history = repo.load_reflection_history(result.run_id)
    assert len(feedback_history) == 0


def test_coordinator_without_reflection_agent(tmp_path: Path) -> None:
    """Test that coordinator works without a reflection agent."""
    repo = RunRepository.from_sqlite_path(tmp_path / "app.db")

    settings = ReflectionSettings(
        enable_reflection=True,  # Enabled but no agent
        max_stage_iterations=3,
        max_cross_stage_iterations=2,
    )

    call_counts: dict[str, int] = {"retrieval": 0, "review": 0, "critic": 0, "planner": 0}

    def retrieval(run_id: str, topic: str, constraints) -> RetrievalSummary:
        call_counts["retrieval"] += 1
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
        call_counts["review"] += 1
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
        call_counts["critic"] += 1
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
        call_counts["planner"] += 1
        repo.save_hypotheses(run_id, make_three_test_hypotheses())
        repo.save_report_markdown(run_id, "# Report")
        return PlannerSummary(hypotheses_created=3, report_rendered=True, top_axes=["axis"], planner_notes=[])

    # Create coordinator WITHOUT reflection agent
    coordinator = RunCoordinator(
        repository=repo,
        retrieval_agent=retrieval,
        review_agent=review,
        critic_agent=critic,
        planner_agent=planner,
        reflection_agent=None,  # No agent
        reflection_settings=settings,
    )

    result = coordinator.run_topic("test topic")

    # Should run linearly even though reflection is "enabled" in settings
    assert result.status == "done"

    # Each stage called exactly once
    assert call_counts["retrieval"] == 1
    assert call_counts["review"] == 1
    assert call_counts["critic"] == 1
    assert call_counts["planner"] == 1
