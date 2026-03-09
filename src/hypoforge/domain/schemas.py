from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator


RunStatus = Literal[
    "queued",
    "retrieving",
    "reviewing",
    "criticizing",
    "planning",
    "done",
    "failed",
]
StageName = Literal["retrieval", "review", "critic", "planner"]
StageStatus = Literal["started", "completed", "degraded", "failed"]

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
        total = self.novelty_weight + self.feasibility_weight
        if round(total, 6) != 1.0:
            raise ValueError("novelty_weight and feasibility_weight must sum to 1.0")
        if self.year_from > self.year_to:
            raise ValueError("year_from must be less than or equal to year_to")
        return self


class RunRequest(BaseModel):
    topic: str = Field(min_length=1)
    constraints: RunConstraints = Field(default_factory=RunConstraints)


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
        if len(self.supporting_evidence_ids) < 3:
            raise ValueError("each hypothesis requires at least 3 supporting evidence ids")
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
    status: RunStatus
    selected_papers: list[PaperDetail] = Field(default_factory=list)
    evidence_cards: list[EvidenceCard] = Field(default_factory=list)
    conflict_clusters: list[ConflictCluster] = Field(default_factory=list)
    hypotheses: list[Hypothesis] = Field(default_factory=list)
    report_markdown: str | None = None
    trace_url: str | None = None
    stage_summaries: list[StageSummary] = Field(default_factory=list)
