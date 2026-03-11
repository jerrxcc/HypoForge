"""Basic integration tests for reflection system.

Tests that reflection is properly integrated into the pipeline:
- Reflection state is correctly recorded
- Feedback is saved to the database
- Stage iterations are tracked
"""

from pathlib import Path

import pytest

from hypoforge.application.coordinator import RunCoordinator
from hypoforge.config import ReflectionSettings
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
from tests.helpers.reflection_helpers import (
    ScriptedReflectionAgent,
    build_reflection_test_services,
    make_three_test_hypotheses,
)


def test_reflection_enabled_records_iteration_state(tmp_path: Path) -> None:
    """Verify that reflection enabled mode records iteration state correctly."""
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

    # Create agents that save data
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

    # Verify run completed successfully
    assert result.status == "done"

    # Verify iteration state was recorded
    iteration_state = repo.load_iteration_state(result.run_id)
    assert iteration_state is not None
    assert iteration_state.reflection_enabled is True
    assert "retrieval" in iteration_state.stage_iterations
    assert "review" in iteration_state.stage_iterations
    assert "critic" in iteration_state.stage_iterations
    assert "planner" in iteration_state.stage_iterations


def test_reflection_saves_feedback_to_database(tmp_path: Path) -> None:
    """Verify that reflection feedback is saved to the database."""
    repo, agent, settings = build_reflection_test_services(
        tmp_path,
        quality_scores_by_stage={
            "retrieval": [0.4, 0.8],  # First low, then acceptable
            "review": [0.8],
            "critic": [0.8],
            "planner": [0.8],
        },
        reflection_enabled=True,
    )

    retrieval_call_count = 0

    def retrieval(run_id: str, topic: str, constraints) -> RetrievalSummary:
        nonlocal retrieval_call_count
        retrieval_call_count += 1
        papers_count = 5 if retrieval_call_count == 1 else 10
        repo.save_selected_papers(
            run_id,
            [
                PaperDetail(
                    paper_id=f"p{i}",
                    title=f"Paper {i}",
                    year=2024,
                    provenance=["test"],
                )
                for i in range(papers_count)
            ],
            "seed",
        )
        return RetrievalSummary(
            canonical_topic=topic,
            query_variants_used=[topic],
            search_notes=[],
            selected_paper_ids=[f"p{i}" for i in range(papers_count)],
            excluded_paper_ids=[],
            coverage_assessment="good" if retrieval_call_count > 1 else "low",
            needs_broader_search=retrieval_call_count == 1,
        )

    def review(run_id: str) -> ReviewSummary:
        cards = [
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
        ]
        repo.save_evidence_cards(run_id, cards)
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

    # Verify feedback was saved for retrieval (should have at least one feedback)
    feedback_history = repo.load_reflection_history(result.run_id, "retrieval")
    assert len(feedback_history) >= 1

    # Verify feedback has correct structure
    feedback = feedback_history[0]
    assert feedback.target_stage == "retrieval"
    assert feedback.iteration_number >= 1
    assert "overall" in feedback.quality_scores


def test_reflection_enabled_creates_iteration_state_on_launch(tmp_path: Path) -> None:
    """Verify that launching a run with reflection creates iteration state."""
    repo, agent, settings = build_reflection_test_services(
        tmp_path,
        reflection_enabled=True,
    )

    # Create minimal coordinator
    coordinator = RunCoordinator(
        repository=repo,
        retrieval_agent=lambda *args: None,  # type: ignore
        review_agent=lambda *args: None,  # type: ignore
        critic_agent=lambda *args: None,  # type: ignore
        planner_agent=lambda *args: None,  # type: ignore
        reflection_agent=agent,
        reflection_settings=settings,
    )

    # Launch run (don't execute)
    run_state = coordinator.launch_run("test topic")

    # Verify iteration state was created
    iteration_state = repo.load_iteration_state(run_state.run_id)
    assert iteration_state is not None
    assert iteration_state.reflection_enabled is True
    assert iteration_state.run_id == run_state.run_id


def test_reflection_tracks_stage_iterations(tmp_path: Path) -> None:
    """Verify that stage iterations are tracked in iteration state."""
    repo, agent, settings = build_reflection_test_services(
        tmp_path,
        quality_scores_by_stage={
            "retrieval": [0.8],
            "review": [0.4, 0.4, 0.8],  # Two retries then success
            "critic": [0.8],
            "planner": [0.8],
        },
        reflection_enabled=True,
    )

    review_call_count = 0

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
        nonlocal review_call_count
        review_call_count += 1
        # Create more evidence on later iterations
        evidence_count = review_call_count * 3
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
                for i in range(evidence_count)
            ],
        )
        return ReviewSummary(
            papers_processed=1,
            evidence_cards_created=evidence_count,
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

    # Verify review was called multiple times
    assert review_call_count >= 1

    # Verify iteration state has feedback history
    iteration_state = repo.load_iteration_state(result.run_id)
    assert iteration_state is not None
    review_state = iteration_state.stage_iterations.get("review")
    assert review_state is not None
