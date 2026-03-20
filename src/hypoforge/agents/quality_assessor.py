"""Quality Assessor Agent.

This module provides the QualityAssessor agent that evaluates hypothesis quality
using LLM-driven multi-dimensional assessment after the Planner stage.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Literal

from hypoforge.agents.validation_base import ValidationAgent
from hypoforge.domain.validation import (
    QualityAssessmentReport,
    QualityIssue,
    ValidationContext,
    ValidationIssue,
    ValidationResult,
)
from hypoforge.domain.schemas import StageName, Severity

if TYPE_CHECKING:
    from hypoforge.config import ValidationSettings
    from hypoforge.infrastructure.db.repository import RunRepository


logger = logging.getLogger(__name__)


# System prompt for quality assessment
QUALITY_ASSESSMENT_PROMPT = """You are an expert evaluator of scientific hypotheses.

Your task is to assess the quality of research hypotheses across multiple dimensions:

1. **Novelty**: Does the hypothesis propose genuinely new insights?
   - Not just incremental improvements
   - Challenges existing assumptions
   - Opens new research directions

2. **Feasibility**: Can the hypothesis be tested with realistic experiments?
   - Clear experimental design
   - Achievable with available methods
   - Reasonable resource requirements

3. **Evidence Support**: Is the hypothesis well-grounded in the evidence?
   - References actual evidence IDs
   - Consistent with supporting evidence
   - Addresses counterevidence appropriately

4. **Conflict Utilization**: Does the hypothesis leverage identified conflicts?
   - Explains contradictions
   - Proposes resolution mechanisms
   - Uses conflicts as research opportunities

For each hypothesis, provide:
- Dimension scores (0.0-1.0)
- Specific issues found
- Improvement suggestions

Return your assessment as structured JSON with scores and detailed feedback for each hypothesis."""


class QualityAssessor(ValidationAgent):
    """Evaluates hypothesis quality using multi-dimensional assessment.

    This validator runs after the Planner stage to ensure hypotheses
    meet quality standards before final delivery.

    Assessment Dimensions:
    - Novelty: New insights and originality
    - Feasibility: Testability and practicality
    - Evidence Support: Grounding in evidence
    - Conflict Utilization: Use of identified conflicts
    """

    def __init__(
        self,
        *,
        repository: RunRepository,
        settings: ValidationSettings,
        provider: Any | None = None,
    ) -> None:
        """Initialize the quality assessor.

        Args:
            repository: The run repository for loading data
            settings: Validation settings for thresholds
            provider: Optional LLM provider for enhanced assessment
        """
        super().__init__(
            repository=repository,
            thresholds={
                "min_quality": settings.min_quality_score,
                "novelty_weight": settings.novelty_weight,
                "feasibility_weight": settings.feasibility_weight,
                "evidence_weight": settings.evidence_support_weight,
                "conflict_weight": settings.conflict_utilization_weight,
            },
            model_name=settings.model_quality_assessor,
        )
        self._settings = settings
        self._provider = provider

    @property
    def validation_type(self) -> str:
        return "quality_assessment"

    @property
    def target_stage(self) -> StageName:
        return "planner"

    async def validate(self, context: ValidationContext) -> ValidationResult:
        """Validate hypothesis quality.

        Args:
            context: Validation context with run data

        Returns:
            ValidationResult with quality assessment report
        """
        run_id = context.run_id
        topic = context.topic

        self._logger.info(
            "Starting quality assessment",
            extra={"run_id": run_id, "topic": topic},
        )

        # Load data
        hypotheses = self._load_hypotheses(run_id)
        evidence_cards = self._load_evidence_cards(run_id)
        conflict_clusters = self._load_conflict_clusters(run_id)

        if not hypotheses:
            return self._create_no_hypotheses_result(run_id)

        # Assess each hypothesis
        dimension_scores: dict[str, float] = {}
        all_issues: list[QualityIssue] = []
        all_suggestions: list[str] = []

        for hypothesis in hypotheses:
            scores, issues, suggestions = self._assess_single_hypothesis(
                hypothesis=hypothesis,
                evidence_cards=evidence_cards,
                conflict_clusters=conflict_clusters,
                topic=topic,
            )

            # Aggregate dimension scores
            for dim, score in scores.items():
                if dim not in dimension_scores:
                    dimension_scores[dim] = []
                dimension_scores[dim].append(score)

            all_issues.extend(issues)
            all_suggestions.extend(suggestions)

        # Calculate average dimension scores
        avg_dimension_scores = {
            dim: sum(scores) / len(scores)
            for dim, scores in dimension_scores.items()
        }

        # Calculate overall score with weights
        overall_score = self._calculate_weighted_score(avg_dimension_scores)

        # Determine confidence level
        confidence_level = self._determine_confidence_level(
            overall_score=overall_score,
            issue_count=len(all_issues),
        )

        # Create report
        report = QualityAssessmentReport(
            overall_score=overall_score,
            dimension_scores=avg_dimension_scores,
            issues=all_issues,
            suggestions=list(dict.fromkeys(all_suggestions)),  # Dedupe
            confidence_level=confidence_level,
            meets_threshold=overall_score >= self._thresholds["min_quality"],
            threshold=self._thresholds["min_quality"],
        )

        # Determine if valid
        is_valid = report.meets_threshold

        # Create issues list
        issues = self._create_issues_list(report=report, hypotheses=hypotheses)

        # Determine backtrack recommendation
        backtrack = None
        if not is_valid:
            backtrack = self._determine_backtrack(
                report=report,
                context=context,
            )

        self._logger.info(
            "Quality assessment completed",
            extra={
                "run_id": run_id,
                "valid": is_valid,
                "score": overall_score,
                "dimensions": avg_dimension_scores,
            },
        )

        return ValidationResult(
            valid=is_valid,
            score=overall_score,
            issues=issues,
            backtrack_recommendation=backtrack,
            validation_type=self.validation_type,
            validated_count=len(hypotheses),
            passed_count=sum(1 for h in hypotheses if h.overall_score >= self._thresholds["min_quality"]),
        )

    def _assess_single_hypothesis(
        self,
        hypothesis: Any,
        evidence_cards: list[Any],
        conflict_clusters: list[Any],
        topic: str,
    ) -> tuple[dict[str, float], list[QualityIssue], list[str]]:
        """Assess a single hypothesis across all dimensions.

        Args:
            hypothesis: The hypothesis to assess
            evidence_cards: All evidence cards
            conflict_clusters: All conflict clusters
            topic: The research topic

        Returns:
            Tuple of (dimension scores, issues, suggestions)
        """
        issues: list[QualityIssue] = []
        suggestions: list[str] = []

        # Assess novelty
        novelty_score, novelty_issues, novelty_suggestions = self._assess_novelty(
            hypothesis, topic
        )
        issues.extend(novelty_issues)
        suggestions.extend(novelty_suggestions)

        # Assess feasibility
        feasibility_score, feasibility_issues, feasibility_suggestions = self._assess_feasibility(
            hypothesis
        )
        issues.extend(feasibility_issues)
        suggestions.extend(feasibility_suggestions)

        # Assess evidence support
        evidence_score, evidence_issues, evidence_suggestions = self._assess_evidence_support(
            hypothesis, evidence_cards
        )
        issues.extend(evidence_issues)
        suggestions.extend(evidence_suggestions)

        # Assess conflict utilization
        conflict_score, conflict_issues, conflict_suggestions = self._assess_conflict_utilization(
            hypothesis, conflict_clusters
        )
        issues.extend(conflict_issues)
        suggestions.extend(conflict_suggestions)

        scores = {
            "novelty": novelty_score,
            "feasibility": feasibility_score,
            "evidence_support": evidence_score,
            "conflict_utilization": conflict_score,
        }

        return scores, issues, suggestions

    def _assess_novelty(
        self,
        hypothesis: Any,
        topic: str,
    ) -> tuple[float, list[QualityIssue], list[str]]:
        """Assess hypothesis novelty.

        Args:
            hypothesis: The hypothesis to assess
            topic: The research topic

        Returns:
            Tuple of (score, issues, suggestions)
        """
        issues: list[QualityIssue] = []
        suggestions: list[str] = []

        # Use hypothesis's own novelty score as base
        base_score = hypothesis.novelty_score if hasattr(hypothesis, "novelty_score") else 0.5
        score = base_score

        # Check for novelty indicators in statement
        statement = hypothesis.hypothesis_statement.lower()
        why_plausible = hypothesis.why_plausible.lower() if hypothesis.why_plausible else ""
        why_not_obvious = hypothesis.why_not_obvious.lower() if hypothesis.why_not_obvious else ""

        # Novelty indicators
        novelty_indicators = [
            "novel", "new", "first", "unprecedented", "previously unknown",
            "contrary to", "challenges", "redefines", "paradigm",
        ]
        novelty_count = sum(1 for ind in novelty_indicators if ind in statement or ind in why_plausible)

        # Obviousness indicators (negative for novelty)
        obvious_indicators = [
            "well-known", "established", "conventional", "standard",
            "widely accepted", "common", "traditional",
        ]
        obvious_count = sum(1 for ind in obvious_indicators if ind in statement)

        # Adjust score
        score += min(0.2, novelty_count * 0.05)
        score -= min(0.3, obvious_count * 0.1)

        # Check why_not_obvious quality
        if why_not_obvious and len(why_not_obvious) > 50:
            score += 0.05
        elif not why_not_obvious or len(why_not_obvious) < 20:
            issues.append(QualityIssue(
                dimension="novelty",
                severity="medium",
                description=f"Hypothesis {hypothesis.rank} lacks clear non-obviousness explanation",
                affected_hypothesis_ranks=[hypothesis.rank],
                suggested_improvement="Explain why this hypothesis is not immediately obvious",
            ))
            score -= 0.1

        # Check for incremental vs transformative
        if "incremental" in statement or "minor" in statement:
            issues.append(QualityIssue(
                dimension="novelty",
                severity="low",
                description=f"Hypothesis {hypothesis.rank} appears incremental",
                affected_hypothesis_ranks=[hypothesis.rank],
                suggested_improvement="Consider more transformative research directions",
            ))

        suggestions.append("Emphasize unique aspects that differentiate from existing work")

        return max(0.0, min(1.0, score)), issues, suggestions

    def _assess_feasibility(
        self,
        hypothesis: Any,
    ) -> tuple[float, list[QualityIssue], list[str]]:
        """Assess hypothesis feasibility.

        Args:
            hypothesis: The hypothesis to assess

        Returns:
            Tuple of (score, issues, suggestions)
        """
        issues: list[QualityIssue] = []
        suggestions: list[str] = []

        # Use hypothesis's own feasibility score as base
        base_score = hypothesis.feasibility_score if hasattr(hypothesis, "feasibility_score") else 0.5
        score = base_score

        # Check minimal experiment quality
        experiment = hypothesis.minimal_experiment if hasattr(hypothesis, "minimal_experiment") else None

        if not experiment:
            issues.append(QualityIssue(
                dimension="feasibility",
                severity="high",
                description=f"Hypothesis {hypothesis.rank} lacks minimal experiment design",
                affected_hypothesis_ranks=[hypothesis.rank],
                suggested_improvement="Define a concrete experimental approach",
            ))
            return 0.3, issues, suggestions

        # Check experiment components
        experiment_score = 0.0

        if experiment.system and len(experiment.system) > 5:
            experiment_score += 0.25
        else:
            issues.append(QualityIssue(
                dimension="feasibility",
                severity="medium",
                description=f"Hypothesis {hypothesis.rank} has vague system/material definition",
                affected_hypothesis_ranks=[hypothesis.rank],
                suggested_improvement="Specify the exact system or material to test",
            ))

        if experiment.design and len(experiment.design) > 20:
            experiment_score += 0.25
        else:
            issues.append(QualityIssue(
                dimension="feasibility",
                severity="medium",
                description=f"Hypothesis {hypothesis.rank} has insufficient experimental design",
                affected_hypothesis_ranks=[hypothesis.rank],
                suggested_improvement="Provide detailed experimental methodology",
            ))

        if experiment.control and len(experiment.control) > 5:
            experiment_score += 0.2
        else:
            issues.append(QualityIssue(
                dimension="feasibility",
                severity="low",
                description=f"Hypothesis {hypothesis.rank} lacks clear control condition",
                affected_hypothesis_ranks=[hypothesis.rank],
                suggested_improvement="Define appropriate control conditions",
            ))

        if experiment.readouts and len(experiment.readouts) > 0:
            experiment_score += 0.15
        else:
            issues.append(QualityIssue(
                dimension="feasibility",
                severity="medium",
                description=f"Hypothesis {hypothesis.rank} has no defined readouts",
                affected_hypothesis_ranks=[hypothesis.rank],
                suggested_improvement="Specify measurable outcomes",
            ))

        if experiment.success_criteria and len(experiment.success_criteria) > 10:
            experiment_score += 0.15
        else:
            issues.append(QualityIssue(
                dimension="feasibility",
                severity="low",
                description=f"Hypothesis {hypothesis.rank} has vague success criteria",
                affected_hypothesis_ranks=[hypothesis.rank],
                suggested_improvement="Define clear success/failure criteria",
            ))

        # Combine scores
        score = base_score * 0.5 + experiment_score * 0.5

        # Check for unrealistic requirements
        design_lower = experiment.design.lower() if experiment.design else ""
        unrealistic_indicators = [
            "impossible", "infinite", "perfect", "all possible", "every condition",
        ]
        if any(ind in design_lower for ind in unrealistic_indicators):
            issues.append(QualityIssue(
                dimension="feasibility",
                severity="high",
                description=f"Hypothesis {hypothesis.rank} may have unrealistic requirements",
                affected_hypothesis_ranks=[hypothesis.rank],
                suggested_improvement="Ensure experimental design is practically achievable",
            ))
            score -= 0.2

        suggestions.append("Ensure experimental design can be completed with standard resources")

        return max(0.0, min(1.0, score)), issues, suggestions

    def _assess_evidence_support(
        self,
        hypothesis: Any,
        evidence_cards: list[Any],
    ) -> tuple[float, list[QualityIssue], list[str]]:
        """Assess hypothesis evidence support.

        Args:
            hypothesis: The hypothesis to assess
            evidence_cards: All evidence cards

        Returns:
            Tuple of (score, issues, suggestions)
        """
        issues: list[QualityIssue] = []
        suggestions: list[str] = []

        evidence_ids = {card.evidence_id for card in evidence_cards}
        score = 0.0

        # Check supporting evidence
        supporting = hypothesis.supporting_evidence_ids if hasattr(hypothesis, "supporting_evidence_ids") else []
        valid_supporting = [eid for eid in supporting if eid in evidence_ids]

        if len(valid_supporting) >= 5:
            score += 0.4
        elif len(valid_supporting) >= 3:
            score += 0.3
        elif len(valid_supporting) >= 1:
            score += 0.15
        else:
            issues.append(QualityIssue(
                dimension="evidence_support",
                severity="critical",
                description=f"Hypothesis {hypothesis.rank} has no valid supporting evidence",
                affected_hypothesis_ranks=[hypothesis.rank],
                suggested_improvement="Add evidence IDs that support the hypothesis",
            ))

        # Check for invalid evidence references
        invalid_supporting = [eid for eid in supporting if eid not in evidence_ids]
        if invalid_supporting:
            issues.append(QualityIssue(
                dimension="evidence_support",
                severity="high",
                description=f"Hypothesis {hypothesis.rank} references non-existent evidence: {invalid_supporting[:3]}",
                affected_hypothesis_ranks=[hypothesis.rank],
                suggested_improvement="Remove or replace invalid evidence references",
            ))
            score -= 0.1

        # Check counterevidence
        counterevidence = hypothesis.counterevidence_ids if hasattr(hypothesis, "counterevidence_ids") else []
        valid_counter = [eid for eid in counterevidence if eid in evidence_ids]

        if valid_counter:
            score += 0.2
        else:
            issues.append(QualityIssue(
                dimension="evidence_support",
                severity="medium",
                description=f"Hypothesis {hypothesis.rank} lacks counterevidence consideration",
                affected_hypothesis_ranks=[hypothesis.rank],
                suggested_improvement="Include counterevidence to strengthen the hypothesis",
            ))

        # Check evidence grounding in statement
        statement = hypothesis.hypothesis_statement if hasattr(hypothesis, "hypothesis_statement") else ""
        why_plausible = hypothesis.why_plausible if hasattr(hypothesis, "why_plausible") else ""

        if len(valid_supporting) > 0:
            # Check if evidence is referenced in explanation
            evidence_referenced = any(eid in statement or eid in why_plausible for eid in valid_supporting[:3])
            if evidence_referenced:
                score += 0.2
            else:
                score += 0.1

        # Check evidence diversity
        supporting_evidence = [card for card in evidence_cards if card.evidence_id in valid_supporting]
        if supporting_evidence:
            systems = set(card.system_or_material for card in supporting_evidence if card.system_or_material)
            if len(systems) >= 2:
                score += 0.2
            else:
                issues.append(QualityIssue(
                    dimension="evidence_support",
                    severity="low",
                    description=f"Hypothesis {hypothesis.rank} relies on single-system evidence",
                    affected_hypothesis_ranks=[hypothesis.rank],
                    suggested_improvement="Diversify evidence sources",
                ))

        suggestions.append("Ensure all evidence references are valid and properly cited")

        return max(0.0, min(1.0, score)), issues, suggestions

    def _assess_conflict_utilization(
        self,
        hypothesis: Any,
        conflict_clusters: list[Any],
    ) -> tuple[float, list[QualityIssue], list[str]]:
        """Assess how well hypothesis utilizes identified conflicts.

        Args:
            hypothesis: The hypothesis to assess
            conflict_clusters: All conflict clusters

        Returns:
            Tuple of (score, issues, suggestions)
        """
        issues: list[QualityIssue] = []
        suggestions: list[str] = []

        if not conflict_clusters:
            # No conflicts to utilize
            return 0.5, issues, suggestions

        score = 0.0

        # Get conflict axes
        conflict_axes = set(cluster.topic_axis for cluster in conflict_clusters if cluster.topic_axis)

        # Check if hypothesis addresses conflicts
        statement = hypothesis.hypothesis_statement.lower() if hasattr(hypothesis, "hypothesis_statement") else ""
        why_plausible = hypothesis.why_plausible.lower() if hasattr(hypothesis, "why_plausible") else ""

        # Check for conflict-related terms
        conflict_terms = ["conflict", "contradiction", "discrepancy", "inconsistency", "divergence"]
        has_conflict_awareness = any(term in statement or term in why_plausible for term in conflict_terms)

        if has_conflict_awareness:
            score += 0.3
        else:
            issues.append(QualityIssue(
                dimension="conflict_utilization",
                severity="low",
                description=f"Hypothesis {hypothesis.rank} does not explicitly address conflicts",
                affected_hypothesis_ranks=[hypothesis.rank],
                suggested_improvement="Connect hypothesis to identified conflicts",
            ))

        # Check if hypothesis uses evidence from conflicts
        supporting_ids = set(hypothesis.supporting_evidence_ids) if hasattr(hypothesis, "supporting_evidence_ids") else set()
        conflict_evidence = set()
        for cluster in conflict_clusters:
            conflict_evidence.update(cluster.supporting_evidence_ids)
            conflict_evidence.update(cluster.conflicting_evidence_ids)

        overlap = supporting_ids & conflict_evidence
        if overlap:
            utilization_ratio = len(overlap) / len(conflict_evidence) if conflict_evidence else 0
            score += min(0.4, utilization_ratio * 2)
        else:
            score += 0.1  # Base score for having hypotheses

        # Check why_not_obvious for conflict resolution
        why_not_obvious = hypothesis.why_not_obvious.lower() if hasattr(hypothesis, "why_not_obvious") else ""
        if any(axis.lower() in why_not_obvious for axis in conflict_axes):
            score += 0.3
        else:
            suggestions.append("Consider how the hypothesis resolves identified conflicts")

        return max(0.0, min(1.0, score)), issues, suggestions

    def _calculate_weighted_score(self, dimension_scores: dict[str, float]) -> float:
        """Calculate weighted overall score.

        Args:
            dimension_scores: Scores for each dimension

        Returns:
            Weighted overall score
        """
        weights = {
            "novelty": self._thresholds["novelty_weight"],
            "feasibility": self._thresholds["feasibility_weight"],
            "evidence_support": self._thresholds["evidence_weight"],
            "conflict_utilization": self._thresholds["conflict_weight"],
        }

        total = 0.0
        for dim, score in dimension_scores.items():
            weight = weights.get(dim, 0.25)
            total += score * weight

        return total

    def _determine_confidence_level(
        self,
        overall_score: float,
        issue_count: int,
    ) -> Literal["high", "medium", "low"]:
        """Determine confidence level of assessment.

        Args:
            overall_score: Overall quality score
            issue_count: Number of issues found

        Returns:
            Confidence level string
        """
        if overall_score >= 0.8 and issue_count <= 2:
            return "high"
        elif overall_score >= 0.6 and issue_count <= 5:
            return "medium"
        else:
            return "low"

    def _create_no_hypotheses_result(self, run_id: str) -> ValidationResult:
        """Create result when no hypotheses are available."""
        return ValidationResult(
            valid=False,
            score=0.0,
            issues=[ValidationIssue(
                issue_type="no_hypotheses",
                severity="critical",
                description="No hypotheses available for quality assessment",
                affected_ids=[],
                suggested_fix="Re-run planner stage to generate hypotheses",
            )],
            backtrack_recommendation=self.create_backtrack_recommendation(
                target_stage="planner",
                reason="No hypotheses generated",
                priority="critical",
                estimated_impact=0.9,
            ),
            validation_type=self.validation_type,
            validated_count=0,
            passed_count=0,
        )

    def _create_issues_list(
        self,
        report: QualityAssessmentReport,
        hypotheses: list[Any],
    ) -> list[ValidationIssue]:
        """Create list of validation issues from report."""
        issues: list[ValidationIssue] = []

        # Overall quality issue
        if not report.meets_threshold:
            issues.append(ValidationIssue(
                issue_type="low_quality",
                severity="high" if report.overall_score < 0.5 else "medium",
                description=f"Overall quality score {report.overall_score:.2f} below threshold {report.threshold}",
                affected_ids=[],
                suggested_fix="Improve hypothesis grounding and novelty",
            ))

        # Convert quality issues to validation issues
        for qi in report.issues[:10]:  # Limit to top 10
            issues.append(ValidationIssue(
                issue_type=f"quality_{qi.dimension}",
                severity=qi.severity,
                description=qi.description,
                affected_ids=[f"h{rank}" for rank in qi.affected_hypothesis_ranks],
                suggested_fix=qi.suggested_improvement,
            ))

        # Dimension-specific issues
        for dim, score in report.dimension_scores.items():
            if score < 0.5:
                issues.append(ValidationIssue(
                    issue_type=f"low_{dim}",
                    severity="medium",
                    description=f"Low {dim.replace('_', ' ')} score: {score:.2f}",
                    affected_ids=[],
                    suggested_fix=f"Focus on improving {dim.replace('_', ' ')}",
                ))

        return issues

    def _determine_backtrack(
        self,
        report: QualityAssessmentReport,
        context: ValidationContext,
    ) -> Any:
        """Determine backtrack recommendation."""
        from hypoforge.domain.validation import BacktrackRecommendation

        # Critical evidence issues: backtrack to review
        evidence_issues = [qi for qi in report.issues if qi.dimension == "evidence_support"]
        if any(qi.severity == "critical" for qi in evidence_issues):
            return BacktrackRecommendation(
                target_stage="review",
                reason="Hypotheses lack proper evidence support. Need better evidence extraction.",
                priority="high",
                estimated_impact=0.7,
            )

        # Low novelty/feasibility: re-run planner
        if report.dimension_scores.get("novelty", 1.0) < 0.4:
            return BacktrackRecommendation(
                target_stage="planner",
                reason="Hypotheses lack novelty. Generate more innovative hypotheses.",
                priority="medium",
                estimated_impact=0.5,
            )

        # Low conflict utilization: backtrack to critic
        if report.dimension_scores.get("conflict_utilization", 1.0) < 0.3:
            return BacktrackRecommendation(
                target_stage="critic",
                reason="Hypotheses don't utilize conflicts. Improve conflict analysis.",
                priority="medium",
                estimated_impact=0.5,
            )

        # General quality issues: re-run planner
        if report.overall_score < self._thresholds["min_quality"]:
            return BacktrackRecommendation(
                target_stage="planner",
                reason=f"Overall quality ({report.overall_score:.2f}) below threshold. Regenerate hypotheses.",
                priority="medium",
                estimated_impact=0.6,
            )

        return None
