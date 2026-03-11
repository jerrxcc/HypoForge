"""Test helpers for reflection system tests.

This module provides utilities for testing the reflection-correction loop:
- ScriptedReflectionAgent: Mock agent with predetermined quality scores
- Test service builders for configurable test scenarios
- Helper functions for creating test data
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable

from hypoforge.agents.reflection import ReflectionAgent
from hypoforge.application.coordinator import RunCoordinator
from hypoforge.config import ReflectionSettings
from hypoforge.domain.schemas import (
    ConflictCluster,
    EvidenceCard,
    Hypothesis,
    IterationState,
    MinimalExperiment,
    PaperDetail,
    ReflectionFeedback,
    ReflectionSummary,
    RunIterationState,
    StageName,
)
from hypoforge.infrastructure.db.repository import RunRepository

if TYPE_CHECKING:
    pass


@dataclass
class ScriptedReflectionAgent:
    """Mock ReflectionAgent that returns predetermined quality scores.

    This agent allows tests to control:
    - Quality scores for each stage evaluation
    - Backtrack decisions for cross-stage logic
    - Severity levels for feedback

    Example:
        agent = ScriptedReflectionAgent(
            repository=repo,
            quality_scores_by_stage={
                "retrieval": [0.4, 0.7],  # Low quality first, then acceptable
                "review": [0.8],
            },
        )
        # First retrieval evaluation returns 0.4, second returns 0.7
    """

    repository: RunRepository
    quality_scores_by_stage: dict[StageName, list[float]] = field(default_factory=dict)
    call_count: dict[StageName, int] = field(default_factory=dict)
    backtrack_decisions: dict[StageName, list[StageName | None]] = field(default_factory=dict)
    severity_override: dict[StageName, str] = field(default_factory=dict)

    def evaluate_stage(
        self,
        run_id: str,
        stage_name: StageName,
        iteration_state: IterationState,
        stage_output: dict[str, Any],
    ) -> ReflectionSummary:
        """Return predetermined quality score for the stage."""
        # Track call count
        if stage_name not in self.call_count:
            self.call_count[stage_name] = 0
        self.call_count[stage_name] += 1

        # Get quality score from predetermined list
        scores = self.quality_scores_by_stage.get(stage_name, [0.8])
        score_index = min(self.call_count[stage_name] - 1, len(scores) - 1)
        quality_score = scores[score_index]

        # Determine threshold
        thresholds = {
            "retrieval": 0.6,
            "review": 0.5,
            "critic": 0.5,
            "planner": 0.6,
        }
        threshold = thresholds.get(stage_name, 0.5)
        meets_threshold = quality_score >= threshold

        # Get backtrack decision
        backtrack_list = self.backtrack_decisions.get(stage_name, [None])
        backtrack_index = min(self.call_count[stage_name] - 1, len(backtrack_list) - 1)
        backtrack_to = backtrack_list[backtrack_index]

        # Generate issues based on quality
        issues = []
        if not meets_threshold:
            issues.append(f"Quality score {quality_score:.2f} below threshold {threshold}")
        if backtrack_to:
            issues.append(f"Recommending backtrack to {backtrack_to}")

        return ReflectionSummary(
            stage_name=stage_name,
            quality_score=quality_score,
            meets_threshold=meets_threshold,
            issues=issues,
            suggestions=[f"Improve {stage_name} quality"] if not meets_threshold else [],
            backtrack_recommendation=backtrack_to,
            should_rerun=not meets_threshold and iteration_state.can_iterate(),
        )

    def create_feedback(
        self,
        summary: ReflectionSummary,
        iteration_number: int,
    ) -> ReflectionFeedback:
        """Create feedback from reflection summary."""
        # Determine severity
        severity = self.severity_override.get(summary.stage_name)
        if not severity:
            if summary.quality_score < 0.3:
                severity = "critical"
            elif summary.quality_score < 0.5:
                severity = "high"
            elif summary.quality_score < 0.7:
                severity = "medium"
            else:
                severity = "low"

        return ReflectionFeedback(
            target_stage=summary.stage_name,
            issues_found=summary.issues,
            severity=severity,  # type: ignore
            suggested_actions=summary.suggestions,
            recommended_backtrack_stage=summary.backtrack_recommendation,
            quality_scores={"overall": summary.quality_score},
            iteration_number=iteration_number,
        )


def build_reflection_test_services(
    tmp_path: Path,
    *,
    quality_scores_by_stage: dict[StageName, list[float]] | None = None,
    backtrack_decisions: dict[StageName, list[StageName | None]] | None = None,
    severity_override: dict[StageName, str] | None = None,
    reflection_settings: ReflectionSettings | None = None,
    reflection_enabled: bool = True,
) -> tuple[RunRepository, ScriptedReflectionAgent, ReflectionSettings]:
    """Build test services for reflection testing.

    Args:
        tmp_path: Path for temporary database
        quality_scores_by_stage: Predetermined quality scores per stage
        backtrack_decisions: Predetermined backtrack decisions per stage
        severity_override: Override severity for specific stages
        reflection_settings: Custom reflection settings
        reflection_enabled: Whether reflection is enabled

    Returns:
        Tuple of (repository, scripted_agent, settings)
    """
    repo = RunRepository.from_sqlite_path(tmp_path / "app.db")

    agent = ScriptedReflectionAgent(
        repository=repo,
        quality_scores_by_stage=quality_scores_by_stage or {},
        backtrack_decisions=backtrack_decisions or {},
        severity_override=severity_override or {},
    )

    settings = reflection_settings or ReflectionSettings(
        enable_reflection=reflection_enabled,
        max_stage_iterations=3,
        max_cross_stage_iterations=2,
    )

    return repo, agent, settings


def make_test_paper(paper_id: str = "p1", title: str = "Test Paper") -> PaperDetail:
    """Create a test paper detail."""
    return PaperDetail(
        paper_id=paper_id,
        title=title,
        abstract="Test abstract",
        year=2024,
        authors=["Test Author"],
        provenance=["test"],
    )


def make_test_evidence(
    evidence_id: str = "e1",
    paper_id: str = "p1",
    confidence: float = 0.8,
) -> EvidenceCard:
    """Create a test evidence card."""
    return EvidenceCard(
        evidence_id=evidence_id,
        paper_id=paper_id,
        title="Test Evidence",
        claim_text="Test claim",
        system_or_material="Test System",
        intervention="Test Intervention",
        outcome="Test Outcome",
        direction="positive",
        confidence=confidence,
    )


def make_test_cluster(
    cluster_id: str = "c1",
    supporting_ids: list[str] | None = None,
    conflicting_ids: list[str] | None = None,
) -> ConflictCluster:
    """Create a test conflict cluster."""
    return ConflictCluster(
        cluster_id=cluster_id,
        topic_axis="test_axis",
        supporting_evidence_ids=supporting_ids or ["e1"],
        conflicting_evidence_ids=conflicting_ids or ["e2"],
        conflict_type="weak_evidence_gap",
        likely_explanations=["test explanation"],
        critic_summary="Test conflict",
        confidence=0.7,
    )


def make_test_hypothesis(
    rank: int = 1,
    supporting_ids: list[str] | None = None,
    counter_ids: list[str] | None = None,
) -> Hypothesis:
    """Create a test hypothesis."""
    return Hypothesis(
        rank=rank,
        title=f"Test Hypothesis {rank}",
        hypothesis_statement=f"Test statement {rank}",
        why_plausible="Test plausibility",
        why_not_obvious="Test non-obviousness",
        supporting_evidence_ids=supporting_ids or ["e1", "e2", "e3"],
        counterevidence_ids=counter_ids or ["e4"],
        prediction="Test prediction",
        minimal_experiment=MinimalExperiment(
            system="Test System",
            design="Test Design",
            control="Test Control",
            readouts=["Test Readout"],
            success_criteria="Test Success",
            failure_interpretation="Test Failure",
        ),
        novelty_score=0.7,
        feasibility_score=0.8,
        overall_score=0.75,
    )


def make_three_test_hypotheses() -> list[Hypothesis]:
    """Create three test hypotheses for planner output."""
    return [
        make_test_hypothesis(rank=1),
        make_test_hypothesis(rank=2),
        make_test_hypothesis(rank=3),
    ]
