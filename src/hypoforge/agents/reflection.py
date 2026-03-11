"""Reflection Agent for quality evaluation and feedback generation.

This module provides the ReflectionAgent that evaluates pipeline stage outputs
and generates actionable feedback for improvement iterations.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from hypoforge.agents.prompts import REFLECTION_PROMPT, MULTI_PERSPECTIVE_PROMPTS
from hypoforge.domain.quality import (
    CriticQualityMetrics,
    PlannerQualityMetrics,
    QualityAssessment,
    RetrievalQualityMetrics,
    ReviewQualityMetrics,
)
from hypoforge.domain.schemas import (
    AggregatedCritique,
    IterationState,
    MultiPerspectiveCritique,
    ReflectionFeedback,
    ReflectionSummary,
    RunIterationState,
    StageName,
)

if TYPE_CHECKING:
    from hypoforge.infrastructure.db.repository import RunRepository


logger = logging.getLogger(__name__)


class ReflectionAgent:
    """Agent that evaluates pipeline stage quality and generates feedback.

    The ReflectionAgent performs quality assessments on stage outputs,
    generates multi-perspective critiques when enabled, and determines
    whether re-execution or backtracking is necessary.
    """

    def __init__(
        self,
        *,
        repository: RunRepository,
        quality_thresholds: dict[StageName, float] | None = None,
        enable_multi_perspective: bool = True,
        perspectives: list[str] | None = None,
    ) -> None:
        self._repository = repository
        self._quality_thresholds = quality_thresholds or {
            "retrieval": 0.6,
            "review": 0.5,
            "critic": 0.5,
            "planner": 0.6,
        }
        self._enable_multi_perspective = enable_multi_perspective
        self._perspectives = perspectives or ["methodological", "statistical", "domain"]
        self._logger = logging.getLogger(__name__)

    def evaluate_stage(
        self,
        run_id: str,
        stage_name: StageName,
        iteration_state: IterationState,
        stage_output: dict[str, Any],
    ) -> ReflectionSummary:
        """Evaluate a single stage's output quality.

        Args:
            run_id: The run identifier
            stage_name: The stage being evaluated
            iteration_state: Current iteration state for the stage
            stage_output: The output from the stage execution

        Returns:
            ReflectionSummary with quality score and recommendations
        """
        self._logger.info(
            "Evaluating stage quality",
            extra={"run_id": run_id, "stage": stage_name, "iteration": iteration_state.iteration_number},
        )

        # Calculate quality metrics based on stage type
        metrics = self._calculate_quality_metrics(stage_name, run_id, stage_output)

        # Determine threshold
        threshold = self._quality_thresholds.get(stage_name, 0.5)
        meets_threshold = metrics.overall_score >= threshold

        # Identify issues
        issues = self._identify_issues(stage_name, metrics, stage_output)

        # Generate suggestions
        suggestions = self._generate_suggestions(stage_name, metrics, issues)

        # Determine if backtracking is needed
        backtrack_recommendation = self._determine_backtrack(stage_name, metrics, issues)

        return ReflectionSummary(
            stage_name=stage_name,
            quality_score=metrics.overall_score,
            meets_threshold=meets_threshold,
            issues=issues,
            suggestions=suggestions,
            backtrack_recommendation=backtrack_recommendation,
            should_rerun=not meets_threshold and iteration_state.can_iterate(),
        )

    def evaluate_cross_stage(
        self,
        run_id: str,
        iteration_state: RunIterationState,
        current_stage: StageName,
    ) -> ReflectionSummary | None:
        """Evaluate cross-stage quality and identify backtracking needs.

        This method checks if downstream stages reveal issues that require
        re-execution of earlier stages.

        Args:
            run_id: The run identifier
            iteration_state: Complete iteration state for the run
            current_stage: The current stage being processed

        Returns:
            ReflectionSummary if backtracking is needed, None otherwise
        """
        if not iteration_state.can_backtrack():
            return None

        # Load current state data
        papers = self._repository.load_selected_papers(run_id)
        evidence_cards = self._repository.load_evidence_cards(run_id)
        clusters = self._repository.load_conflict_clusters(run_id)

        # Check for cross-stage issues
        issues: list[str] = []

        # Planner looking back: check if evidence base supports hypotheses
        if current_stage == "planner" and len(evidence_cards) < 6:
            issues.append("Insufficient evidence cards to support robust hypothesis generation")
            return ReflectionSummary(
                stage_name=current_stage,
                quality_score=0.4,
                meets_threshold=False,
                issues=issues,
                suggestions=[
                    "Expand evidence extraction from existing papers",
                    "Consider backtracking to review stage for deeper analysis",
                ],
                backtrack_recommendation="review",
                should_rerun=True,
            )

        # Critic looking back: check if evidence coverage is adequate
        if current_stage == "critic" and len(papers) < 6:
            issues.append("Insufficient paper coverage for conflict analysis")
            return ReflectionSummary(
                stage_name=current_stage,
                quality_score=0.4,
                meets_threshold=False,
                issues=issues,
                suggestions=[
                    "Broaden paper search scope",
                    "Backtrack to retrieval for additional papers",
                ],
                backtrack_recommendation="retrieval",
                should_rerun=True,
            )

        return None

    def multi_perspective_critique(
        self,
        run_id: str,
        stage_name: StageName,
        content: dict[str, Any],
    ) -> AggregatedCritique:
        """Generate critiques from multiple perspectives.

        Args:
            run_id: The run identifier
            stage_name: The stage being critiqued
            content: The content to critique

        Returns:
            AggregatedCritique with all perspective critiques combined
        """
        if not self._enable_multi_perspective:
            return AggregatedCritique(
                critiques=[],
                consensus_issues=[],
                overall_quality_score=0.5,
            )

        critiques: list[MultiPerspectiveCritique] = []

        for perspective in self._perspectives:
            critique = self._critique_from_perspective(
                perspective=perspective,
                stage_name=stage_name,
                content=content,
            )
            critiques.append(critique)

        return self._aggregate_critiques(critiques)

    def aggregate_critiques(
        self,
        critiques: list[MultiPerspectiveCritique],
    ) -> AggregatedCritique:
        """Aggregate multiple critiques into a combined assessment.

        Args:
            critiques: List of critiques from different perspectives

        Returns:
            AggregatedCritique with combined findings
        """
        return self._aggregate_critiques(critiques)

    def create_feedback(
        self,
        summary: ReflectionSummary,
        iteration_number: int,
    ) -> ReflectionFeedback:
        """Create feedback from a reflection summary.

        Args:
            summary: The reflection summary
            iteration_number: Current iteration number

        Returns:
            ReflectionFeedback for injection into next iteration
        """
        severity = self._determine_severity(summary)

        return ReflectionFeedback(
            target_stage=summary.stage_name,
            issues_found=summary.issues,
            severity=severity,
            suggested_actions=summary.suggestions,
            recommended_backtrack_stage=summary.backtrack_recommendation,
            quality_scores={"overall": summary.quality_score},
            iteration_number=iteration_number,
        )

    def _calculate_quality_metrics(
        self,
        stage_name: StageName,
        run_id: str,
        stage_output: dict[str, Any],
    ) -> QualityAssessment:
        """Calculate quality metrics for a stage."""
        if stage_name == "retrieval":
            return self._calculate_retrieval_metrics(run_id, stage_output)
        elif stage_name == "review":
            return self._calculate_review_metrics(run_id, stage_output)
        elif stage_name == "critic":
            return self._calculate_critic_metrics(run_id, stage_output)
        elif stage_name == "planner":
            return self._calculate_planner_metrics(run_id, stage_output)
        else:
            raise ValueError(f"Unknown stage: {stage_name}")

    def _calculate_retrieval_metrics(
        self,
        run_id: str,
        output: dict[str, Any],
    ) -> QualityAssessment:
        """Calculate quality metrics for retrieval stage."""
        papers = self._repository.load_selected_papers(run_id)
        paper_count = len(papers)

        # Calculate paper count score (normalized to target of 12-36)
        target_min = 12
        target_max = 36
        if paper_count >= target_min:
            paper_count_score = min(1.0, paper_count / target_max)
        else:
            paper_count_score = paper_count / target_min * 0.5

        # Calculate diversity score based on sources
        sources = set()
        venues = set()
        years = []
        for paper in papers:
            for prov in paper.provenance:
                sources.add(prov)
            if paper.venue:
                venues.add(paper.venue)
            if paper.year:
                years.append(paper.year)

        source_coverage = len(sources) / 3.0 if papers else 0  # OpenAlex, S2, recommendations
        venue_diversity = min(1.0, len(venues) / max(1, len(papers)) * 5)
        year_range = (max(years) - min(years)) if years else 0
        recency_score = min(1.0, year_range / 10) if years else 0

        diversity_score = (source_coverage + venue_diversity) / 2

        # Calculate relevance (based on coverage assessment)
        coverage = output.get("coverage_assessment", "low")
        relevance_score = {"good": 0.8, "medium": 0.5, "low": 0.2}.get(coverage, 0.3)

        # Overall score with weights
        overall_score = (
            paper_count_score * 0.3 +
            diversity_score * 0.25 +
            relevance_score * 0.25 +
            recency_score * 0.1 +
            source_coverage * 0.1
        )

        metrics = RetrievalQualityMetrics(
            paper_count=paper_count,
            paper_count_score=paper_count_score,
            diversity_score=diversity_score,
            relevance_score=relevance_score,
            recency_score=recency_score,
            source_coverage=source_coverage,
            overall_score=overall_score,
        )

        return QualityAssessment(
            stage_name="retrieval",
            metrics=metrics,
            meets_threshold=overall_score >= self._quality_thresholds["retrieval"],
        )

    def _calculate_review_metrics(
        self,
        run_id: str,
        output: dict[str, Any],
    ) -> QualityAssessment:
        """Calculate quality metrics for review stage."""
        papers = self._repository.load_selected_papers(run_id)
        evidence_cards = self._repository.load_evidence_cards(run_id)

        papers_processed = output.get("papers_processed", len(papers))
        evidence_count = len(evidence_cards)

        # Extraction completeness
        extraction_completeness = min(1.0, evidence_count / max(1, papers_processed) / 4)  # ~4 cards per paper expected

        # Evidence depth (average confidence)
        if evidence_cards:
            avg_confidence = sum(card.confidence for card in evidence_cards) / len(evidence_cards)
        else:
            avg_confidence = 0.0

        # Grounding score (cards with grounding notes)
        grounded_cards = sum(1 for card in evidence_cards if card.grounding_notes)
        grounding_score = grounded_cards / max(1, evidence_count)

        # Confidence distribution
        confidence_dist: dict[str, int] = {"high": 0, "medium": 0, "low": 0}
        for card in evidence_cards:
            if card.confidence >= 0.8:
                confidence_dist["high"] += 1
            elif card.confidence >= 0.5:
                confidence_dist["medium"] += 1
            else:
                confidence_dist["low"] += 1

        # Overall score
        overall_score = (
            extraction_completeness * 0.35 +
            avg_confidence * 0.25 +
            grounding_score * 0.2 +
            (confidence_dist["high"] / max(1, evidence_count)) * 0.2
        )

        metrics = ReviewQualityMetrics(
            papers_processed=papers_processed,
            evidence_count=evidence_count,
            extraction_completeness=extraction_completeness,
            evidence_depth=avg_confidence,
            grounding_score=grounding_score,
            confidence_distribution=confidence_dist,
            overall_score=overall_score,
        )

        return QualityAssessment(
            stage_name="review",
            metrics=metrics,
            meets_threshold=overall_score >= self._quality_thresholds["review"],
        )

    def _calculate_critic_metrics(
        self,
        run_id: str,
        output: dict[str, Any],
    ) -> QualityAssessment:
        """Calculate quality metrics for critic stage."""
        evidence_cards = self._repository.load_evidence_cards(run_id)
        clusters = self._repository.load_conflict_clusters(run_id)

        clusters_count = len(clusters)

        # Conflict detection quality
        conflict_score = min(1.0, clusters_count / 3) if clusters_count > 0 else 0.0

        # Explanation depth (average explanations per cluster)
        if clusters:
            avg_explanations = sum(len(c.likely_explanations) for c in clusters) / len(clusters)
            explanation_depth = min(1.0, avg_explanations / 3)
        else:
            explanation_depth = 0.0

        # Evidence coverage
        covered_evidence = set()
        for cluster in clusters:
            covered_evidence.update(cluster.supporting_evidence_ids)
            covered_evidence.update(cluster.conflicting_evidence_ids)
        evidence_coverage = len(covered_evidence) / max(1, len(evidence_cards))

        # Axis diversity
        axes = set(cluster.topic_axis for cluster in clusters if cluster.topic_axis)
        axis_diversity = min(1.0, len(axes) / 3)

        # Overall score
        overall_score = (
            conflict_score * 0.3 +
            explanation_depth * 0.25 +
            evidence_coverage * 0.25 +
            axis_diversity * 0.2
        )

        metrics = CriticQualityMetrics(
            clusters_count=clusters_count,
            conflict_detection_score=conflict_score,
            explanation_depth=explanation_depth,
            evidence_coverage=evidence_coverage,
            axis_diversity=axis_diversity,
            overall_score=overall_score,
        )

        return QualityAssessment(
            stage_name="critic",
            metrics=metrics,
            meets_threshold=overall_score >= self._quality_thresholds["critic"],
        )

    def _calculate_planner_metrics(
        self,
        run_id: str,
        output: dict[str, Any],
    ) -> QualityAssessment:
        """Calculate quality metrics for planner stage."""
        hypotheses = self._repository.load_hypotheses(run_id)
        evidence_cards = self._repository.load_evidence_cards(run_id)
        clusters = self._repository.load_conflict_clusters(run_id)

        hypotheses_count = len(hypotheses)

        if not hypotheses:
            return QualityAssessment(
                stage_name="planner",
                metrics=PlannerQualityMetrics(
                    hypotheses_count=0,
                    novelty_score=0.0,
                    feasibility_score=0.0,
                    experiment_clarity=0.0,
                    evidence_grounding=0.0,
                    conflict_utilization=0.0,
                    overall_score=0.0,
                ),
                meets_threshold=False,
            )

        # Average novelty and feasibility
        avg_novelty = sum(h.novelty_score for h in hypotheses) / len(hypotheses)
        avg_feasibility = sum(h.feasibility_score for h in hypotheses) / len(hypotheses)

        # Experiment clarity (readouts present)
        experiments_with_readouts = sum(1 for h in hypotheses if h.minimal_experiment.readouts)
        experiment_clarity = experiments_with_readouts / len(hypotheses)

        # Evidence grounding
        all_evidence_ids = set(e.evidence_id for e in evidence_cards)
        used_evidence = set()
        for h in hypotheses:
            used_evidence.update(h.supporting_evidence_ids)
            used_evidence.update(h.counterevidence_ids)
        evidence_grounding = len(used_evidence & all_evidence_ids) / max(1, len(all_evidence_ids))

        # Conflict utilization
        conflict_axes = set(c.topic_axis for c in clusters)
        hypothesis_axes = set()
        for h in hypotheses:
            hypothesis_axes.update(h.why_plausible.lower().split())
        conflict_utilization = len(conflict_axes & hypothesis_axes) / max(1, len(conflict_axes)) if conflict_axes else 0.5

        # Overall score
        overall_score = (
            avg_novelty * 0.25 +
            avg_feasibility * 0.25 +
            experiment_clarity * 0.2 +
            evidence_grounding * 0.2 +
            conflict_utilization * 0.1
        )

        metrics = PlannerQualityMetrics(
            hypotheses_count=hypotheses_count,
            novelty_score=avg_novelty,
            feasibility_score=avg_feasibility,
            experiment_clarity=experiment_clarity,
            evidence_grounding=evidence_grounding,
            conflict_utilization=conflict_utilization,
            overall_score=overall_score,
        )

        return QualityAssessment(
            stage_name="planner",
            metrics=metrics,
            meets_threshold=overall_score >= self._quality_thresholds["planner"],
        )

    def _identify_issues(
        self,
        stage_name: StageName,
        metrics: QualityAssessment,
        output: dict[str, Any],
    ) -> list[str]:
        """Identify issues from quality metrics."""
        issues: list[str] = []

        if stage_name == "retrieval":
            m = metrics.metrics
            if isinstance(m, RetrievalQualityMetrics):
                if m.paper_count < 6:
                    issues.append(f"Low paper count: {m.paper_count} papers selected")
                if m.diversity_score < 0.4:
                    issues.append("Low source diversity in selected papers")
                if m.relevance_score < 0.5:
                    issues.append("Papers may not be well-aligned with research topic")

        elif stage_name == "review":
            m = metrics.metrics
            if isinstance(m, ReviewQualityMetrics):
                if m.extraction_completeness < 0.5:
                    issues.append("Incomplete evidence extraction from papers")
                if m.evidence_depth < 0.6:
                    issues.append("Evidence cards have low average confidence")
                if m.grounding_score < 0.3:
                    issues.append("Evidence cards lack proper grounding notes")

        elif stage_name == "critic":
            m = metrics.metrics
            if isinstance(m, CriticQualityMetrics):
                if m.clusters_count == 0:
                    issues.append("No conflict clusters identified")
                if m.evidence_coverage < 0.3:
                    issues.append("Low evidence coverage in conflict analysis")
                if m.explanation_depth < 0.5:
                    issues.append("Conflict explanations lack depth")

        elif stage_name == "planner":
            m = metrics.metrics
            if isinstance(m, PlannerQualityMetrics):
                if m.hypotheses_count < 3:
                    issues.append(f"Only {m.hypotheses_count} hypotheses generated (expected 3)")
                if m.novelty_score < 0.5:
                    issues.append("Hypotheses have low novelty scores")
                if m.feasibility_score < 0.5:
                    issues.append("Hypotheses have low feasibility scores")

        return issues

    def _generate_suggestions(
        self,
        stage_name: StageName,
        metrics: QualityAssessment,
        issues: list[str],
    ) -> list[str]:
        """Generate actionable suggestions based on issues."""
        suggestions: list[str] = []

        if stage_name == "retrieval":
            if "Low paper count" in str(issues):
                suggestions.append("Broaden search queries to include more papers")
                suggestions.append("Extend year range to capture more literature")
            if "diversity" in str(issues).lower():
                suggestions.append("Search additional databases (OpenAlex, Semantic Scholar)")
                suggestions.append("Include papers from diverse venues")

        elif stage_name == "review":
            if "incomplete" in str(issues).lower():
                suggestions.append("Re-process papers with deeper analysis")
                suggestions.append("Focus on extracting more evidence per paper")
            if "confidence" in str(issues).lower():
                suggestions.append("Strengthen evidence grounding with more specific claims")

        elif stage_name == "critic":
            if "No conflict clusters" in str(issues):
                suggestions.append("Look for subtle conflicts in methodology or conditions")
                suggestions.append("Consider conditional divergence patterns")
            if "coverage" in str(issues).lower():
                suggestions.append("Include more evidence in conflict analysis")

        elif stage_name == "planner":
            if "hypotheses" in str(issues).lower():
                suggestions.append("Generate hypotheses from different conflict angles")
            if "novelty" in str(issues).lower():
                suggestions.append("Focus on less explored research directions")
            if "feasibility" in str(issues).lower():
                suggestions.append("Design more practical experimental approaches")

        return suggestions

    def _determine_backtrack(
        self,
        stage_name: StageName,
        metrics: QualityAssessment,
        issues: list[str],
    ) -> StageName | None:
        """Determine if backtracking to a previous stage is needed."""
        if metrics.meets_threshold:
            return None

        # Backtrack rules based on severity
        if stage_name == "planner":
            if metrics.overall_score < 0.3:
                # Severe planner issues often stem from poor evidence
                return "review"
        elif stage_name == "critic":
            if metrics.overall_score < 0.3:
                # Severe critic issues may stem from insufficient papers
                return "retrieval"
        elif stage_name == "review":
            if metrics.overall_score < 0.3:
                # Severe review issues may stem from poor retrieval
                return "retrieval"

        return None

    def _determine_severity(self, summary: ReflectionSummary) -> str:
        """Determine severity level from reflection summary."""
        if summary.quality_score < 0.3:
            return "critical"
        elif summary.quality_score < 0.5:
            return "high"
        elif summary.quality_score < 0.7:
            return "medium"
        return "low"

    def _critique_from_perspective(
        self,
        perspective: str,
        stage_name: StageName,
        content: dict[str, Any],
    ) -> MultiPerspectiveCritique:
        """Generate a critique from a specific perspective.

        Note: This is a simplified implementation. In production, this would
        call an LLM with the perspective-specific prompt.
        """
        prompt = MULTI_PERSPECTIVE_PROMPTS.get(perspective, "")

        # Placeholder: In production, call LLM here
        # For now, return a basic critique based on perspective
        issues: list[str] = []
        strengths: list[str] = []
        recommendations: list[str] = []

        if perspective == "methodological":
            if stage_name == "review":
                issues.append("Check for control conditions in evidence extraction")
                recommendations.append("Ensure intervention/comparator pairs are well-defined")
            strengths.append("Systematic approach to evidence extraction")

        elif perspective == "statistical":
            if stage_name == "critic":
                issues.append("Consider statistical power in conflict explanations")
                recommendations.append("Include sample size considerations")
            strengths.append("Quantitative analysis approach")

        elif perspective == "domain":
            if stage_name == "planner":
                issues.append("Verify domain-specific terminology usage")
                recommendations.append("Align hypotheses with field conventions")
            strengths.append("Domain-aware hypothesis generation")

        return MultiPerspectiveCritique(
            perspective_name=perspective,
            issues_found=issues,
            strengths=strengths,
            recommendations=recommendations,
            confidence=0.7,
        )

    def _aggregate_critiques(
        self,
        critiques: list[MultiPerspectiveCritique],
    ) -> AggregatedCritique:
        """Aggregate multiple critiques into combined assessment."""
        if not critiques:
            return AggregatedCritique(
                critiques=[],
                consensus_issues=[],
                overall_quality_score=0.5,
            )

        # Find consensus issues (mentioned by multiple perspectives)
        all_issues: dict[str, int] = {}
        for critique in critiques:
            for issue in critique.issues_found:
                all_issues[issue] = all_issues.get(issue, 0) + 1

        consensus_issues = [
            issue for issue, count in all_issues.items()
            if count >= 2
        ]

        # Find conflicting views
        conflicting_views: list[dict] = []
        # Simplified: check for contradictory recommendations
        # In production, would do semantic analysis

        # Combine all recommendations
        combined_recommendations: list[str] = []
        for critique in critiques:
            combined_recommendations.extend(critique.recommendations)

        # Calculate overall quality score
        avg_confidence = sum(c.confidence for c in critiques) / len(critiques)
        issue_penalty = min(0.3, len(consensus_issues) * 0.1)
        overall_quality_score = max(0.0, min(1.0, avg_confidence - issue_penalty))

        return AggregatedCritique(
            critiques=critiques,
            consensus_issues=consensus_issues,
            conflicting_views=conflicting_views,
            overall_quality_score=overall_quality_score,
            combined_recommendations=combined_recommendations,
        )
