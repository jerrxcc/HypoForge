"""Tests for reflection backtracking mechanism.

Tests that:
- StageNavigator can validate backtracking
- Backtrack data identification works
- Downstream data clearing works
- Feedback backtrack logic works
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
    RunConstraints,
    RunRequest,
    StageName,
)
from hypoforge.infrastructure.db.repository import RunRepository
from tests.helpers.reflection_helpers import (
    ScriptedReflectionAgent,
    build_reflection_test_services,
    make_three_test_hypotheses,
)


def test_stage_navigator_can_validate_backtrack(tmp_path: Path) -> None:
    """Test that StageNavigator can validate backtrack requests."""
    # Repository is required by constructor but not used for validation methods
    repo = RunRepository.from_sqlite_path(tmp_path / "app.db")
    navigator = StageNavigator(repository=repo)

    # Test valid backtrack scenarios
    assert navigator.can_backtrack_to("critic", "retrieval") is True
    assert navigator.can_backtrack_to("critic", "review") is True
    assert navigator.can_backtrack_to("planner", "retrieval") is True
    assert navigator.can_backtrack_to("planner", "review") is True
    assert navigator.can_backtrack_to("planner", "critic") is True

    # Test invalid backtrack (forward movement)
    assert navigator.can_backtrack_to("retrieval", "review") is False
    assert navigator.can_backtrack_to("review", "critic") is False


def test_stage_navigator_gets_data_to_regenerate(tmp_path: Path) -> None:
    """Test that StageNavigator correctly identifies data to regenerate."""
    repo = RunRepository.from_sqlite_path(tmp_path / "app.db")
    navigator = StageNavigator(repository=repo)

    # Test critic -> retrieval backtrack
    data = navigator.get_data_to_regenerate("critic", "retrieval")
    assert "selected_papers" in data

    # Test planner -> review backtrack
    data = navigator.get_data_to_regenerate("planner", "review")
    assert "evidence_cards" in data


def test_stage_navigator_gets_data_to_preserve(tmp_path: Path) -> None:
    """Test that StageNavigator correctly identifies data to preserve."""
    repo = RunRepository.from_sqlite_path(tmp_path / "app.db")
    navigator = StageNavigator(repository=repo)

    # Test critic -> retrieval backtrack
    data = navigator.get_data_to_preserve("critic", "retrieval")
    assert "topic" in data
    assert "constraints" in data

    # Test planner -> review backtrack
    data = navigator.get_data_to_preserve("planner", "review")
    assert "selected_papers" in data


def test_stage_navigator_get_stage_dependencies(tmp_path: Path) -> None:
    """Test that StageNavigator correctly identifies stage dependencies."""
    repo = RunRepository.from_sqlite_path(tmp_path / "app.db")
    navigator = StageNavigator(repository=repo)

    # Test stage dependencies
    assert navigator.get_stage_dependencies("retrieval") == []
    assert navigator.get_stage_dependencies("review") == ["retrieval"]
    assert navigator.get_stage_dependencies("critic") == ["retrieval", "review"]
    assert navigator.get_stage_dependencies("planner") == ["retrieval", "review", "critic"]


def test_stage_navigator_get_dependent_stages(tmp_path: Path) -> None:
    """Test that StageNavigator correctly identifies dependent stages."""
    repo = RunRepository.from_sqlite_path(tmp_path / "app.db")
    navigator = StageNavigator(repository=repo)

    # Test dependent stages
    assert navigator.get_dependent_stages("retrieval") == ["review", "critic", "planner"]
    assert navigator.get_dependent_stages("review") == ["critic", "planner"]
    assert navigator.get_dependent_stages("critic") == ["planner"]
    assert navigator.get_dependent_stages("planner") == []


def test_downstream_data_cleared_on_backtrack(tmp_path: Path) -> None:
    """Test that clear_downstream_data properly clears data."""
    repo = RunRepository.from_sqlite_path(tmp_path / "app.db")

    # Create a run and add data
    request = RunRequest(topic="test", constraints=RunConstraints())
    run = repo.create_run(request)

    # Add papers
    repo.save_selected_papers(
        run.run_id,
        [PaperDetail(paper_id="p1", title="Paper", year=2024, provenance=["test"])],
        "seed",
    )

    # Add evidence cards
    repo.save_evidence_cards(
        run.run_id,
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

    # Add conflict clusters
    repo.save_conflict_clusters(
        run.run_id,
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

    # Verify data exists
    assert len(repo.load_selected_papers(run.run_id)) == 1
    assert len(repo.load_evidence_cards(run.run_id)) == 1
    assert len(repo.load_conflict_clusters(run.run_id)) == 1

    # Clear from review (should clear evidence cards, clusters, hypotheses but not papers)
    repo.clear_downstream_data(run.run_id, "review")

    # Papers should still exist, downstream should be cleared
    assert len(repo.load_selected_papers(run.run_id)) == 1
    assert len(repo.load_evidence_cards(run.run_id)) == 0
    assert len(repo.load_conflict_clusters(run.run_id)) == 0


def test_feedback_should_backtrack_logic() -> None:
    """Test that ReflectionFeedback.should_backtrack() works correctly."""
    from hypoforge.domain.schemas import ReflectionFeedback

    # High severity with backtrack recommendation
    feedback1 = ReflectionFeedback(
        target_stage="critic",
        issues_found=["test"],
        severity="high",
        suggested_actions=["test"],
        recommended_backtrack_stage="retrieval",
        quality_scores={"overall": 0.3},
        iteration_number=1,
    )
    assert feedback1.should_backtrack() is True

    # Critical severity with backtrack recommendation
    feedback2 = ReflectionFeedback(
        target_stage="critic",
        issues_found=["test"],
        severity="critical",
        suggested_actions=["test"],
        recommended_backtrack_stage="retrieval",
        quality_scores={"overall": 0.2},
        iteration_number=1,
    )
    assert feedback2.should_backtrack() is True

    # Medium severity - should not backtrack even with recommendation
    feedback3 = ReflectionFeedback(
        target_stage="critic",
        issues_found=["test"],
        severity="medium",
        suggested_actions=["test"],
        recommended_backtrack_stage="retrieval",
        quality_scores={"overall": 0.4},
        iteration_number=1,
    )
    assert feedback3.should_backtrack() is False

    # High severity but no backtrack recommendation
    feedback4 = ReflectionFeedback(
        target_stage="critic",
        issues_found=["test"],
        severity="high",
        suggested_actions=["test"],
        recommended_backtrack_stage=None,
        quality_scores={"overall": 0.3},
        iteration_number=1,
    )
    assert feedback4.should_backtrack() is False


def test_max_backtrack_limit_configuration(tmp_path: Path) -> None:
    """Test that max cross-stage iterations limit is configured correctly."""
    max_cross_stage = 1
    repo, agent, settings = build_reflection_test_services(
        tmp_path,
        quality_scores_by_stage={
            "retrieval": [0.8],
            "review": [0.8],
            "critic": [0.8],
            "planner": [0.8],
        },
        reflection_settings=ReflectionSettings(
            enable_reflection=True,
            max_stage_iterations=3,
            max_cross_stage_iterations=max_cross_stage,
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

    # Run should complete
    assert result.status == "done"

    # Verify iteration state respects max backtrack setting
    iteration_state = repo.load_iteration_state(result.run_id)
    if iteration_state:
        assert iteration_state.max_cross_stage_iterations == max_cross_stage


def test_run_iteration_state_can_backtrack() -> None:
    """Test RunIterationState.can_backtrack() method."""
    from hypoforge.domain.schemas import RunIterationState

    state = RunIterationState(
        run_id="test_run",
        max_cross_stage_iterations=2,
    )

    # Should be able to backtrack initially
    assert state.can_backtrack() is True

    # After one backtrack
    state.cross_stage_iterations = 1
    assert state.can_backtrack() is True

    # After reaching max
    state.cross_stage_iterations = 2
    assert state.can_backtrack() is False


def test_run_iteration_state_record_backtrack() -> None:
    """Test RunIterationState.record_backtrack() method."""
    from hypoforge.domain.schemas import RunIterationState

    state = RunIterationState(
        run_id="test_run",
        max_cross_stage_iterations=2,
    )

    # Record a backtrack
    state.record_backtrack("critic", "retrieval", "insufficient papers")

    assert state.cross_stage_iterations == 1
    assert len(state.backtracking_history) == 1

    # Verify backtrack record structure
    record = state.backtracking_history[0]
    assert record["from_stage"] == "critic"
    assert record["to_stage"] == "retrieval"
    assert record["reason"] == "insufficient papers"
    assert record["iteration"] == 1
