"""Quality metrics and evaluation models for the reflection-correction loop.

This module defines quality indicators for each pipeline stage:
- RetrievalQualityMetrics: Paper count, diversity, relevance, recency
- ReviewQualityMetrics: Extraction completeness, evidence depth, grounding
- CriticQualityMetrics: Conflict detection quality, explanation depth, coverage
- PlannerQualityMetrics: Hypothesis novelty, feasibility, experimental clarity
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class RetrievalQualityMetrics(BaseModel):
    """Quality metrics for the retrieval stage."""

    paper_count: int = Field(ge=0, description="Number of papers selected")
    paper_count_score: float = Field(ge=0.0, le=1.0, description="Score based on paper count relative to threshold")
    diversity_score: float = Field(ge=0.0, le=1.0, description="Diversity of sources, venues, years")
    relevance_score: float = Field(ge=0.0, le=1.0, description="Relevance to the research topic")
    recency_score: float = Field(ge=0.0, le=1.0, description="Recency of papers within year constraints")
    source_coverage: float = Field(ge=0.0, le=1.0, description="Coverage across data sources")
    overall_score: float = Field(ge=0.0, le=1.0, description="Weighted overall quality score")

    @property
    def is_acceptable(self) -> bool:
        """Check if retrieval quality meets minimum threshold."""
        return self.overall_score >= 0.6 and self.paper_count >= 6


class ReviewQualityMetrics(BaseModel):
    """Quality metrics for the review stage."""

    papers_processed: int = Field(ge=0, description="Number of papers reviewed")
    evidence_count: int = Field(ge=0, description="Number of evidence cards created")
    extraction_completeness: float = Field(ge=0.0, le=1.0, description="Completeness of evidence extraction")
    evidence_depth: float = Field(ge=0.0, le=1.0, description="Depth of evidence details")
    grounding_score: float = Field(ge=0.0, le=1.0, description="How well evidence is grounded in source material")
    confidence_distribution: dict[str, int] = Field(
        default_factory=dict,
        description="Distribution of confidence levels (high/medium/low)",
    )
    overall_score: float = Field(ge=0.0, le=1.0, description="Weighted overall quality score")

    @property
    def is_acceptable(self) -> bool:
        """Check if review quality meets minimum threshold."""
        return self.overall_score >= 0.5 and self.evidence_count >= 3


class CriticQualityMetrics(BaseModel):
    """Quality metrics for the critic stage."""

    clusters_count: int = Field(ge=0, description="Number of conflict clusters identified")
    conflict_detection_score: float = Field(ge=0.0, le=1.0, description="Quality of conflict detection")
    explanation_depth: float = Field(ge=0.0, le=1.0, description="Depth of conflict explanations")
    evidence_coverage: float = Field(ge=0.0, le=1.0, description="Percentage of evidence cards covered by clusters")
    axis_diversity: float = Field(ge=0.0, le=1.0, description="Diversity of conflict axes identified")
    overall_score: float = Field(ge=0.0, le=1.0, description="Weighted overall quality score")

    @property
    def is_acceptable(self) -> bool:
        """Check if critic quality meets minimum threshold."""
        return self.overall_score >= 0.5


class PlannerQualityMetrics(BaseModel):
    """Quality metrics for the planner stage."""

    hypotheses_count: int = Field(ge=0, description="Number of hypotheses generated")
    novelty_score: float = Field(ge=0.0, le=1.0, description="Average novelty score of hypotheses")
    feasibility_score: float = Field(ge=0.0, le=1.0, description="Average feasibility score")
    experiment_clarity: float = Field(ge=0.0, le=1.0, description="Clarity of minimal experiments")
    evidence_grounding: float = Field(ge=0.0, le=1.0, description="How well hypotheses are grounded in evidence")
    conflict_utilization: float = Field(ge=0.0, le=1.0, description="How well conflicts are utilized in hypotheses")
    overall_score: float = Field(ge=0.0, le=1.0, description="Weighted overall quality score")

    @property
    def is_acceptable(self) -> bool:
        """Check if planner quality meets minimum threshold."""
        return self.overall_score >= 0.6 and self.hypotheses_count == 3


QualityMetrics = RetrievalQualityMetrics | ReviewQualityMetrics | CriticQualityMetrics | PlannerQualityMetrics


class QualityAssessment(BaseModel):
    """Complete quality assessment for a pipeline stage."""

    stage_name: str
    metrics: QualityMetrics
    issues_found: list[str] = Field(default_factory=list)
    suggested_improvements: list[str] = Field(default_factory=list)
    meets_threshold: bool

    @property
    def overall_score(self) -> float:
        """Get the overall score from metrics."""
        return self.metrics.overall_score
