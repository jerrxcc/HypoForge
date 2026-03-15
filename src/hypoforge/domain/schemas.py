from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator


RunStatus = Literal[
    "queued",
    "retrieving",
    "reviewing",
    "criticizing",
    "planning",
    "reflecting",
    "done",
    "failed",
]
StageName = Literal["retrieval", "review", "critic", "planner"]
StageStatus = Literal["started", "completed", "degraded", "failed"]
IterationStatus = Literal["pending", "in_progress", "completed", "max_iterations_reached", "quality_threshold_met", "backtracked"]
Severity = Literal["low", "medium", "high", "critical"]

# Priority ordering for severity levels (lower = higher priority)
SEVERITY_PRIORITY: dict[Severity, int] = {"critical": 0, "high": 1, "medium": 2, "low": 3}

Direction = Literal["positive", "negative", "mixed", "null", "unclear"]
EvidenceKind = Literal[
    "review",
    "meta_analysis",
    "experiment",
    "simulation",
    "benchmark",
    "theory",
    "unknown",
]
ConflictType = Literal[
    "direct_conflict",
    "conditional_divergence",
    "weak_evidence_gap",
]


class RunConstraints(BaseModel):
    year_from: int = 2018
    year_to: int = 2026
    open_access_only: bool = False
    max_selected_papers: int = 36
    novelty_weight: float = 0.5
    feasibility_weight: float = 0.5
    lab_mode: Literal["wet", "dry", "either"] = "either"

    @model_validator(mode="after")
    def validate_weights(self) -> "RunConstraints":
        if self.novelty_weight < 0 or self.novelty_weight > 1:
            raise ValueError("novelty_weight must be between 0 and 1")
        if self.feasibility_weight < 0 or self.feasibility_weight > 1:
            raise ValueError("feasibility_weight must be between 0 and 1")
        total = self.novelty_weight + self.feasibility_weight
        if round(total, 6) != 1.0:
            raise ValueError("novelty_weight and feasibility_weight must sum to 1.0")
        if self.year_from > self.year_to:
            raise ValueError("year_from must be less than or equal to year_to")
        return self


class RunRequest(BaseModel):
    topic: str = Field(min_length=1)
    constraints: RunConstraints = Field(default_factory=RunConstraints)

    @model_validator(mode="after")
    def validate_topic(self) -> "RunRequest":
        if not self.topic.strip():
            raise ValueError("topic must contain non-whitespace characters")
        return self


class RunState(BaseModel):
    run_id: str
    topic: str
    constraints: RunConstraints
    status: RunStatus
    error_message: str | None = None
    selected_paper_ids: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    conflict_cluster_ids: list[str] = Field(default_factory=list)
    hypothesis_ids: list[str] = Field(default_factory=list)
    final_report_md: str | None = None
    trace_path: str | None = None


class RunSummary(BaseModel):
    run_id: str
    topic: str
    status: RunStatus
    created_at: datetime
    updated_at: datetime
    selected_paper_count: int = Field(ge=0)
    evidence_card_count: int = Field(ge=0)
    conflict_cluster_count: int = Field(ge=0)
    hypothesis_count: int = Field(ge=0)
    error_message: str | None = None


class PaperDetail(BaseModel):
    paper_id: str
    external_ids: dict[str, str | int | None] = Field(default_factory=dict)
    doi: str | None = None
    title: str
    abstract: str | None = None
    year: int | None = None
    authors: list[str] = Field(default_factory=list)
    venue: str | None = None
    citation_count: int | None = None
    publication_type: str | None = None
    fields_of_study: list[str] = Field(default_factory=list)
    topic_labels: list[str] = Field(default_factory=list)
    source: str | None = None
    url: str | None = None
    source_urls: dict[str, str] = Field(default_factory=dict)
    provenance: list[str] = Field(default_factory=list)


class EvidenceCard(BaseModel):
    evidence_id: str
    paper_id: str
    title: str
    claim_text: str
    system_or_material: str
    intervention: str
    comparator: str = ""
    outcome: str
    direction: Direction
    evidence_kind: EvidenceKind = "unknown"
    conditions: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    grounding_notes: list[str] = Field(default_factory=list)


class ConflictCluster(BaseModel):
    cluster_id: str
    topic_axis: str
    supporting_evidence_ids: list[str] = Field(default_factory=list)
    conflicting_evidence_ids: list[str] = Field(default_factory=list)
    conflict_type: ConflictType
    likely_explanations: list[str] = Field(default_factory=list)
    missing_controls: list[str] = Field(default_factory=list)
    critic_summary: str
    confidence: float = Field(ge=0.0, le=1.0)


class MinimalExperiment(BaseModel):
    system: str
    design: str
    control: str
    readouts: list[str] = Field(default_factory=list)
    success_criteria: str
    failure_interpretation: str


class Hypothesis(BaseModel):
    rank: int = Field(ge=1, le=3)
    title: str
    hypothesis_statement: str
    why_plausible: str
    why_not_obvious: str
    supporting_evidence_ids: list[str] = Field(default_factory=list)
    counterevidence_ids: list[str] = Field(default_factory=list)
    prediction: str
    minimal_experiment: MinimalExperiment
    limitations: list[str] = Field(default_factory=list)
    uncertainty_notes: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    novelty_score: float = Field(ge=0.0, le=1.0)
    feasibility_score: float = Field(ge=0.0, le=1.0)
    overall_score: float = Field(ge=0.0, le=1.0)

    @model_validator(mode="after")
    def validate_grounding(self) -> "Hypothesis":
        if len(dict.fromkeys(self.supporting_evidence_ids)) < 3:
            raise ValueError("each hypothesis requires at least 3 distinct supporting evidence ids")
        if len(self.counterevidence_ids) < 1:
            raise ValueError("each hypothesis requires at least 1 counterevidence id")
        if not self.minimal_experiment.readouts:
            raise ValueError("minimal_experiment.readouts must not be empty")
        return self


class RetrievalSummary(BaseModel):
    canonical_topic: str
    query_variants_used: list[str] = Field(default_factory=list)
    search_notes: list[str] = Field(default_factory=list)
    selected_paper_ids: list[str] = Field(default_factory=list)
    excluded_paper_ids: list[str] = Field(default_factory=list)
    coverage_assessment: Literal["good", "medium", "low"]
    needs_broader_search: bool = False


class ReviewSummary(BaseModel):
    papers_processed: int = Field(ge=0)
    evidence_cards_created: int = Field(ge=0)
    coverage_summary: str
    dominant_axes: list[str] = Field(default_factory=list)
    low_confidence_paper_ids: list[str] = Field(default_factory=list)
    failed_paper_ids: list[str] = Field(default_factory=list)


class CriticSummary(BaseModel):
    clusters_created: int = Field(ge=0, le=8)
    top_axes: list[str] = Field(default_factory=list)
    critic_notes: list[str] = Field(default_factory=list)


class PlannerSummary(BaseModel):
    hypotheses_created: int
    report_rendered: bool
    top_axes: list[str] = Field(default_factory=list)
    planner_notes: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_hypothesis_count(self) -> "PlannerSummary":
        if self.hypotheses_created != 3:
            raise ValueError("PlannerSummary requires hypotheses_created to equal 3")
        return self


class StageSummary(BaseModel):
    stage_name: StageName
    status: StageStatus
    summary: dict[str, object] = Field(default_factory=dict)
    error_message: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None


class RunResult(BaseModel):
    run_id: str
    topic: str
    status: RunStatus
    selected_papers: list[PaperDetail] = Field(default_factory=list)
    evidence_cards: list[EvidenceCard] = Field(default_factory=list)
    conflict_clusters: list[ConflictCluster] = Field(default_factory=list)
    hypotheses: list[Hypothesis] = Field(default_factory=list)
    report_markdown: str | None = None
    trace_url: str | None = None
    stage_summaries: list[StageSummary] = Field(default_factory=list)


class ReflectionFeedback(BaseModel):
    """Feedback generated by the reflection agent for a specific stage."""

    feedback_id: str = Field(default_factory=lambda: f"fb_{uuid4().hex[:12]}")
    target_stage: StageName
    issues_found: list[str] = Field(default_factory=list)
    severity: Severity = "medium"
    suggested_actions: list[str] = Field(default_factory=list)
    recommended_backtrack_stage: StageName | None = None
    quality_scores: dict[str, float] = Field(default_factory=dict)
    iteration_number: int = Field(ge=1)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    def should_backtrack(self) -> bool:
        """Determine if this feedback requires backtracking."""
        return self.recommended_backtrack_stage is not None and self.severity in ("high", "critical")


class IterationState(BaseModel):
    """State tracking for a single stage's iterations."""

    iteration_id: str = Field(default_factory=lambda: f"iter_{uuid4().hex[:12]}")
    run_id: str
    stage_name: StageName
    iteration_number: int = Field(default=1, ge=1)
    max_iterations: int = Field(default=3)
    quality_threshold: float = Field(default=0.5)
    current_quality_score: float | None = None
    feedback_history: list[ReflectionFeedback] = Field(default_factory=list)
    learnings: list[str] = Field(default_factory=list)
    status: IterationStatus = "pending"

    def can_iterate(self) -> bool:
        """Check if more iterations are allowed."""
        return self.iteration_number < self.max_iterations and self.status not in ("completed", "quality_threshold_met")

    def meets_threshold(self) -> bool:
        """Check if current quality meets the threshold."""
        if self.current_quality_score is None:
            return False
        return self.current_quality_score >= self.quality_threshold

    def add_feedback(self, feedback: ReflectionFeedback) -> None:
        """Add feedback from an iteration."""
        self.feedback_history.append(feedback)
        self.learnings.extend(feedback.suggested_actions)


class RunIterationState(BaseModel):
    """Complete iteration state for an entire run."""

    run_id: str
    stage_iterations: dict[StageName, IterationState] = Field(default_factory=dict)
    cross_stage_iterations: int = 0
    max_cross_stage_iterations: int = Field(default=2)
    accumulated_learnings: list[str] = Field(default_factory=list)
    backtracking_history: list[dict] = Field(default_factory=list)
    reflection_enabled: bool = True

    def get_stage_state(self, stage_name: StageName) -> IterationState:
        """Get or create iteration state for a stage."""
        if stage_name not in self.stage_iterations:
            self.stage_iterations[stage_name] = IterationState(
                run_id=self.run_id,
                stage_name=stage_name,
            )
        return self.stage_iterations[stage_name]

    def can_backtrack(self) -> bool:
        """Check if more cross-stage backtracking is allowed."""
        return self.cross_stage_iterations < self.max_cross_stage_iterations

    def record_backtrack(self, from_stage: StageName, to_stage: StageName, reason: str) -> None:
        """Record a backtracking event."""
        self.cross_stage_iterations += 1
        self.backtracking_history.append({
            "from_stage": from_stage,
            "to_stage": to_stage,
            "reason": reason,
            "iteration": self.cross_stage_iterations,
            "timestamp": datetime.now(UTC).isoformat(),
        })


class ReflectionSummary(BaseModel):
    """Summary of a reflection evaluation."""

    stage_name: StageName
    quality_score: float = Field(ge=0.0, le=1.0)
    meets_threshold: bool
    issues: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)
    backtrack_recommendation: StageName | None = None
    should_rerun: bool = False


class MultiPerspectiveCritique(BaseModel):
    """Result of a multi-perspective critique."""

    perspective_name: str
    issues_found: list[str] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)


class AggregatedCritique(BaseModel):
    """Aggregated result from multiple critique perspectives."""

    critiques: list[MultiPerspectiveCritique] = Field(default_factory=list)
    consensus_issues: list[str] = Field(default_factory=list, description="Issues found by multiple perspectives")
    conflicting_views: list[dict] = Field(default_factory=list, description="Disagreements between perspectives")
    overall_quality_score: float = Field(ge=0.0, le=1.0)
    combined_recommendations: list[str] = Field(default_factory=list)
