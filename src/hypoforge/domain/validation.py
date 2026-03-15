"""Validation domain models for the validation agents system.

This module provides models for validation results, backtrack recommendations,
and feedback synthesis used by the validation agents pipeline.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field

from hypoforge.domain.schemas import StageName, Severity


class ValidationIssue(BaseModel):
    """A single issue found during validation."""

    issue_id: str = Field(default_factory=lambda: f"vi_{uuid4().hex[:12]}")
    issue_type: str = Field(description="Category of the issue (e.g., 'missing_field', 'inconsistency', 'low_relevance')")
    severity: Severity = Field(default="medium")
    description: str
    affected_ids: list[str] = Field(default_factory=list, description="IDs of affected entities")
    suggested_fix: str | None = None


class BacktrackRecommendation(BaseModel):
    """Recommendation for backtracking to a previous stage."""

    target_stage: StageName
    reason: str
    feedback: SynthesizedFeedback | None = None
    priority: Literal["low", "medium", "high", "critical"] = "medium"
    estimated_impact: float = Field(default=0.5, ge=0.0, le=1.0, description="Expected quality improvement")


class ValidationResult(BaseModel):
    """Result of a validation agent's evaluation."""

    valid: bool
    score: float = Field(ge=0.0, le=1.0)
    issues: list[ValidationIssue] = Field(default_factory=list)
    backtrack_recommendation: BacktrackRecommendation | None = None
    validation_type: str = Field(description="Type of validation performed")
    validated_count: int = Field(default=0, description="Number of entities validated")
    passed_count: int = Field(default=0, description="Number of entities that passed validation")

    def should_backtrack(self) -> bool:
        """Determine if backtracking is recommended."""
        return self.backtrack_recommendation is not None and not self.valid


class ConflictHint(BaseModel):
    """A hint about potential conflict between evidence."""

    evidence_id_1: str
    evidence_id_2: str
    conflict_type: str
    description: str
    confidence: float = Field(ge=0.0, le=1.0)


class InvalidEvidence(BaseModel):
    """Record of invalid evidence with reason."""

    evidence_id: str
    reason: str
    severity: Severity
    suggested_action: str | None = None


class EvidenceValidationReport(BaseModel):
    """Detailed report from evidence validation."""

    valid_evidence_ids: list[str] = Field(default_factory=list)
    invalid_evidence_ids: list[InvalidEvidence] = Field(default_factory=list)
    conflict_hints: list[ConflictHint] = Field(default_factory=list)
    quality_scores: dict[str, float] = Field(default_factory=dict)
    completeness_score: float = Field(default=0.0, ge=0.0, le=1.0)
    accuracy_score: float = Field(default=0.0, ge=0.0, le=1.0)
    relevance_score: float = Field(default=0.0, ge=0.0, le=1.0)
    overall_score: float = Field(default=0.0, ge=0.0, le=1.0)

    @property
    def total_evidence(self) -> int:
        return len(self.valid_evidence_ids) + len(self.invalid_evidence_ids)


class WeakEvidenceGap(BaseModel):
    """Identified gap in evidence coverage."""

    gap_id: str = Field(default_factory=lambda: f"gap_{uuid4().hex[:12]}")
    topic_axis: str
    description: str
    missing_evidence_types: list[str] = Field(default_factory=list)
    suggested_search_terms: list[str] = Field(default_factory=list)
    impact_on_hypotheses: list[str] = Field(default_factory=list)


class EnhancedConflictReport(BaseModel):
    """Detailed report from conflict detection enhancement."""

    confirmed_conflicts: list[str] = Field(default_factory=list, description="IDs of confirmed conflict clusters")
    new_conflicts: list[str] = Field(default_factory=list, description="IDs of newly discovered conflicts")
    weak_evidence_gaps: list[WeakEvidenceGap] = Field(default_factory=list)
    conflict_intensity_scores: dict[str, float] = Field(default_factory=dict)
    evidence_homogeneity_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Lower is more diverse")
    coverage_score: float = Field(default=0.0, ge=0.0, le=1.0)
    overall_score: float = Field(default=0.0, ge=0.0, le=1.0)


class QualityIssue(BaseModel):
    """A quality issue found in hypothesis assessment."""

    issue_id: str = Field(default_factory=lambda: f"qi_{uuid4().hex[:12]}")
    dimension: Literal["novelty", "feasibility", "evidence_support", "conflict_utilization", "clarity"]
    severity: Severity
    description: str
    affected_hypothesis_ranks: list[int] = Field(default_factory=list)
    suggested_improvement: str | None = None


class QualityAssessmentReport(BaseModel):
    """Detailed report from quality assessment."""

    overall_score: float = Field(ge=0.0, le=1.0)
    dimension_scores: dict[str, float] = Field(default_factory=dict)
    issues: list[QualityIssue] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)
    confidence_level: Literal["high", "medium", "low"] = "medium"
    meets_threshold: bool = False
    threshold: float = Field(default=0.65)


class Issue(BaseModel):
    """A prioritized issue for feedback synthesis."""

    issue_id: str = Field(default_factory=lambda: f"issue_{uuid4().hex[:12]}")
    source: str = Field(description="Which validator identified this issue")
    description: str
    priority: Literal["critical", "high", "medium", "low"]
    actionable: bool = Field(default=True)
    related_stage: StageName | None = None


class SynthesizedFeedback(BaseModel):
    """Synthesized feedback from multiple validation sources."""

    feedback_id: str = Field(default_factory=lambda: f"sf_{uuid4().hex[:12]}")
    avoid_patterns: list[str] = Field(
        default_factory=list,
        description="Patterns to avoid in next iteration"
    )
    focus_areas: list[str] = Field(
        default_factory=list,
        description="Areas to focus on for improvement"
    )
    context_enhancements: list[str] = Field(
        default_factory=list,
        description="Additional context to provide to agents"
    )
    priority_issues: list[Issue] = Field(
        default_factory=list,
        description="Issues sorted by priority"
    )
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    def get_critical_issues(self) -> list[Issue]:
        """Get all critical priority issues."""
        return [i for i in self.priority_issues if i.priority == "critical"]

    def get_actionable_issues(self) -> list[Issue]:
        """Get all actionable issues."""
        return [i for i in self.priority_issues if i.actionable]


class ValidationContext(BaseModel):
    """Context provided to validation agents."""

    run_id: str
    topic: str
    current_stage: StageName
    iteration_number: int = Field(default=1)
    previous_feedback: list[SynthesizedFeedback] = Field(default_factory=list)
    stage_output: dict = Field(default_factory=dict)

    # Available data for validation
    selected_paper_ids: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    conflict_cluster_ids: list[str] = Field(default_factory=list)
    hypothesis_ids: list[str] = Field(default_factory=list)


class FeedbackPool(BaseModel):
    """Pool of accumulated feedback across iterations."""

    run_id: str
    feedback_history: list[SynthesizedFeedback] = Field(default_factory=list)
    accumulated_avoid_patterns: list[str] = Field(default_factory=list)
    accumulated_focus_areas: list[str] = Field(default_factory=list)
    iteration_count: int = Field(default=0)

    def add_feedback(self, feedback: SynthesizedFeedback) -> None:
        """Add new feedback to the pool."""
        self.feedback_history.append(feedback)
        self.iteration_count += 1

        # Accumulate patterns (deduplicate)
        existing_patterns = set(self.accumulated_avoid_patterns)
        self.accumulated_avoid_patterns = list(existing_patterns | set(feedback.avoid_patterns))

        existing_areas = set(self.accumulated_focus_areas)
        self.accumulated_focus_areas = list(existing_areas | set(feedback.focus_areas))

    def get_latest_feedback(self) -> SynthesizedFeedback | None:
        """Get the most recent feedback."""
        return self.feedback_history[-1] if self.feedback_history else None

    def get_issues_by_priority(self, priority: str) -> list[Issue]:
        """Get all issues of a specific priority across all feedback."""
        issues = []
        for feedback in self.feedback_history:
            issues.extend(i for i in feedback.priority_issues if i.priority == priority)
        return issues
