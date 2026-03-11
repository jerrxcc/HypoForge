"""Multi-perspective critique system for scientific evidence evaluation.

This module provides perspectives for critique and an aggregator for
combining multiple critiques into a unified assessment.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from hypoforge.domain.schemas import (
    AggregatedCritique,
    MultiPerspectiveCritique,
    StageName,
)

if TYPE_CHECKING:
    from hypoforge.infrastructure.db.repository import RunRepository


logger = logging.getLogger(__name__)


@dataclass
class PerspectiveConfig:
    """Configuration for a critique perspective."""
    name: str
    description: str
    focus_areas: list[str]
    weight: float = 1.0


# Default perspective configurations
DEFAULT_PERSPECTIVES: dict[str, PerspectiveConfig] = {
    "methodological": PerspectiveConfig(
        name="methodological",
        description="Evaluates experimental design and methodology",
        focus_areas=[
            "Experimental design validity",
            "Control group appropriateness",
            "Measurement reliability",
            "Potential confounds and biases",
            "Reproducibility",
        ],
        weight=1.0,
    ),
    "statistical": PerspectiveConfig(
        name="statistical",
        description="Evaluates statistical rigor and interpretation",
        focus_areas=[
            "Sample size adequacy",
            "Statistical test appropriateness",
            "Effect size interpretation",
            "Multiple comparison corrections",
            "Confidence intervals",
        ],
        weight=1.0,
    ),
    "domain": PerspectiveConfig(
        name="domain",
        description="Evaluates domain-specific accuracy and relevance",
        focus_areas=[
            "Terminology accuracy",
            "Domain convention adherence",
            "Professional interpretation",
            "Field relevance",
            "State-of-the-art awareness",
        ],
        weight=1.0,
    ),
}


class CritiquePerspective(ABC):
    """Abstract base class for critique perspectives."""

    def __init__(self, config: PerspectiveConfig) -> None:
        self.config = config
        self._logger = logging.getLogger(f"{__name__}.{config.name}")

    @property
    def name(self) -> str:
        return self.config.name

    @abstractmethod
    def evaluate(
        self,
        stage_name: StageName,
        content: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> MultiPerspectiveCritique:
        """Evaluate content from this perspective.

        Args:
            stage_name: The pipeline stage being evaluated
            content: The content to evaluate
            context: Optional additional context

        Returns:
            MultiPerspectiveCritique with findings
        """
        ...

    def _extract_key_metrics(self, content: dict[str, Any]) -> dict[str, Any]:
        """Extract key metrics from content for evaluation.

        Args:
            content: The content dictionary

        Returns:
            Dictionary of extracted metrics
        """
        metrics: dict[str, Any] = {}

        # Common extractions
        if "papers_processed" in content:
            metrics["papers_processed"] = content["papers_processed"]
        if "evidence_cards_created" in content:
            metrics["evidence_cards_created"] = content["evidence_cards_created"]
        if "clusters_created" in content:
            metrics["clusters_created"] = content["clusters_created"]
        if "hypotheses_created" in content:
            metrics["hypotheses_created"] = content["hypotheses_created"]

        return metrics


class MethodologicalPerspective(CritiquePerspective):
    """Methodological critique perspective."""

    def __init__(self) -> None:
        super().__init__(DEFAULT_PERSPECTIVES["methodological"])

    def evaluate(
        self,
        stage_name: StageName,
        content: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> MultiPerspectiveCritique:
        issues: list[str] = []
        strengths: list[str] = []
        recommendations: list[str] = []

        if stage_name == "review":
            # Check evidence extraction methodology
            evidence_count = content.get("evidence_cards_created", 0)
            papers_processed = content.get("papers_processed", 1)

            ratio = evidence_count / max(1, papers_processed)
            if ratio < 2:
                issues.append("Low evidence extraction rate per paper")
                recommendations.append("Consider deeper analysis of each paper")
            else:
                strengths.append(f"Good evidence extraction rate: {ratio:.1f} cards per paper")

            # Check for failed papers
            failed = content.get("failed_paper_ids", [])
            if failed:
                issues.append(f"{len(failed)} papers failed processing")
                recommendations.append("Review failed papers for common issues")

        elif stage_name == "critic":
            # Check conflict detection methodology
            clusters = content.get("clusters_created", 0)
            if clusters == 0:
                issues.append("No conflict clusters identified")
                recommendations.append("Review evidence for potential conflicts")
            else:
                strengths.append(f"Identified {clusters} conflict clusters")

            # Check explanation depth
            critic_notes = content.get("critic_notes", [])
            if len(critic_notes) < 2:
                issues.append("Limited conflict analysis depth")
                recommendations.append("Provide more detailed conflict explanations")

        elif stage_name == "planner":
            # Check hypothesis grounding
            hypotheses = content.get("hypotheses_created", 0)
            if hypotheses != 3:
                issues.append(f"Expected 3 hypotheses, got {hypotheses}")
            else:
                strengths.append("Generated required 3 hypotheses")

            # Check experiment design
            planner_notes = content.get("planner_notes", [])
            if not planner_notes:
                recommendations.append("Add more experimental design details")

        return MultiPerspectiveCritique(
            perspective_name=self.name,
            issues_found=issues,
            strengths=strengths,
            recommendations=recommendations,
            confidence=self._calculate_confidence(issues, strengths),
        )

    def _calculate_confidence(
        self,
        issues: list[str],
        strengths: list[str],
    ) -> float:
        """Calculate confidence score based on findings."""
        if not issues and not strengths:
            return 0.5
        # More strengths = higher confidence
        total = len(issues) + len(strengths)
        return max(0.3, min(0.9, 0.5 + (len(strengths) - len(issues)) * 0.1))


class StatisticalPerspective(CritiquePerspective):
    """Statistical critique perspective."""

    def __init__(self) -> None:
        super().__init__(DEFAULT_PERSPECTIVES["statistical"])

    def evaluate(
        self,
        stage_name: StageName,
        content: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> MultiPerspectiveCritique:
        issues: list[str] = []
        strengths: list[str] = []
        recommendations: list[str] = []

        if stage_name == "retrieval":
            # Check sample size adequacy
            paper_count = len(content.get("selected_paper_ids", []))
            if paper_count < 10:
                issues.append(f"Low paper count ({paper_count}) may limit statistical power")
                recommendations.append("Consider broadening search to increase sample")
            elif paper_count >= 20:
                strengths.append(f"Adequate paper sample size: {paper_count}")

        elif stage_name == "review":
            # Check confidence distribution
            papers = content.get("papers_processed", 0)
            evidence = content.get("evidence_cards_created", 0)

            if papers > 0:
                avg_evidence = evidence / papers
                if avg_evidence < 3:
                    issues.append("Low average evidence per paper may indicate extraction issues")
                else:
                    strengths.append(f"Good evidence density: {avg_evidence:.1f} per paper")

        elif stage_name == "critic":
            # Check conflict coverage
            top_axes = content.get("top_axes", [])
            if len(top_axes) < 2:
                issues.append("Limited conflict axis diversity")
                recommendations.append("Explore additional dimensions of conflict")
            else:
                strengths.append(f"Diverse conflict axes identified: {len(top_axes)}")

        elif stage_name == "planner":
            # Check hypothesis scoring distribution
            hypotheses = content.get("hypotheses_created", 0)
            if hypotheses == 3:
                strengths.append("Correct number of hypotheses for statistical comparison")

        return MultiPerspectiveCritique(
            perspective_name=self.name,
            issues_found=issues,
            strengths=strengths,
            recommendations=recommendations,
            confidence=self._calculate_confidence(issues, strengths),
        )

    def _calculate_confidence(
        self,
        issues: list[str],
        strengths: list[str],
    ) -> float:
        """Calculate confidence score based on findings."""
        if not issues and not strengths:
            return 0.5
        total = len(issues) + len(strengths)
        return max(0.3, min(0.9, 0.5 + (len(strengths) - len(issues)) * 0.1))


class DomainPerspective(CritiquePerspective):
    """Domain expert critique perspective."""

    def __init__(self) -> None:
        super().__init__(DEFAULT_PERSPECTIVES["domain"])

    def evaluate(
        self,
        stage_name: StageName,
        content: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> MultiPerspectiveCritique:
        issues: list[str] = []
        strengths: list[str] = []
        recommendations: list[str] = []

        if stage_name == "retrieval":
            # Check topic coverage
            coverage = content.get("coverage_assessment", "low")
            if coverage == "low":
                issues.append("Low topic coverage may miss domain-relevant papers")
                recommendations.append("Expand search with domain-specific terms")
            elif coverage == "good":
                strengths.append("Good topic coverage achieved")

            # Check for domain-specific sources
            canonical_topic = content.get("canonical_topic", "")
            if canonical_topic:
                strengths.append(f"Topic properly canonicalized: {canonical_topic[:50]}...")

        elif stage_name == "review":
            # Check evidence extraction quality
            coverage_summary = content.get("coverage_summary", "")
            if "partial" in coverage_summary.lower():
                issues.append("Partial review may miss domain-specific evidence")
            else:
                strengths.append("Complete review coverage")

            # Check dominant axes
            axes = content.get("dominant_axes", [])
            if len(axes) >= 2:
                strengths.append(f"Multiple dominant axes identified: {len(axes)}")
            else:
                recommendations.append("Look for additional domain-relevant axes")

        elif stage_name == "critic":
            # Check conflict explanations
            notes = content.get("critic_notes", [])
            if notes:
                strengths.append("Conflict analysis includes explanatory notes")

        elif stage_name == "planner":
            # Check hypothesis domain relevance
            top_axes = content.get("top_axes", [])
            if top_axes:
                strengths.append("Hypotheses aligned with identified conflict axes")

            planner_notes = content.get("planner_notes", [])
            if planner_notes:
                strengths.append("Hypotheses include domain-specific considerations")

        return MultiPerspectiveCritique(
            perspective_name=self.name,
            issues_found=issues,
            strengths=strengths,
            recommendations=recommendations,
            confidence=self._calculate_confidence(issues, strengths),
        )

    def _calculate_confidence(
        self,
        issues: list[str],
        strengths: list[str],
    ) -> float:
        """Calculate confidence score based on findings."""
        if not issues and not strengths:
            return 0.5
        return max(0.3, min(0.9, 0.5 + (len(strengths) - len(issues)) * 0.1))


class CritiqueAggregator:
    """Aggregates multiple critiques into a unified assessment.

    The aggregator:
    - Combines issues from multiple perspectives
    - Identifies consensus issues (mentioned by multiple perspectives)
    - Detects conflicting views between perspectives
    - Calculates overall quality scores
    """

    def __init__(
        self,
        perspectives: list[CritiquePerspective] | None = None,
    ) -> None:
        self._perspectives = perspectives or [
            MethodologicalPerspective(),
            StatisticalPerspective(),
            DomainPerspective(),
        ]
        self._logger = logging.getLogger(__name__)

    def aggregate(
        self,
        critiques: list[MultiPerspectiveCritique],
    ) -> AggregatedCritique:
        """Aggregate multiple critiques.

        Args:
            critiques: List of critiques to aggregate

        Returns:
            AggregatedCritique with combined findings
        """
        if not critiques:
            return AggregatedCritique(
                critiques=[],
                consensus_issues=[],
                overall_quality_score=0.5,
            )

        # Count issue occurrences
        issue_counts: dict[str, int] = {}
        for critique in critiques:
            for issue in critique.issues_found:
                # Normalize issue text for comparison
                normalized = issue.lower().strip()
                issue_counts[normalized] = issue_counts.get(normalized, 0) + 1

        # Identify consensus issues (mentioned by 2+ perspectives)
        consensus_issues = [
            issue for issue, count in issue_counts.items()
            if count >= 2
        ]

        # Detect conflicting views
        conflicting_views = self._detect_conflicts(critiques)

        # Combine recommendations
        combined_recommendations: list[str] = []
        seen_recommendations: set[str] = set()
        for critique in critiques:
            for rec in critique.recommendations:
                normalized = rec.lower().strip()
                if normalized not in seen_recommendations:
                    combined_recommendations.append(rec)
                    seen_recommendations.add(normalized)

        # Calculate overall quality score
        overall_score = self._calculate_overall_score(critiques, consensus_issues)

        return AggregatedCritique(
            critiques=critiques,
            consensus_issues=consensus_issues,
            conflicting_views=conflicting_views,
            overall_quality_score=overall_score,
            combined_recommendations=combined_recommendations,
        )

    def evaluate_all_perspectives(
        self,
        stage_name: StageName,
        content: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> AggregatedCritique:
        """Evaluate content from all configured perspectives.

        Args:
            stage_name: The pipeline stage being evaluated
            content: The content to evaluate
            context: Optional additional context

        Returns:
            AggregatedCritique with all perspective findings
        """
        critiques: list[MultiPerspectiveCritique] = []

        for perspective in self._perspectives:
            self._logger.debug(
                "Evaluating from perspective",
                extra={
                    "perspective": perspective.name,
                    "stage": stage_name,
                },
            )
            critique = perspective.evaluate(stage_name, content, context)
            critiques.append(critique)

        return self.aggregate(critiques)

    def _detect_conflicts(
        self,
        critiques: list[MultiPerspectiveCritique],
    ) -> list[dict]:
        """Detect conflicting views between perspectives.

        Args:
            critiques: List of critiques to analyze

        Returns:
            List of detected conflicts
        """
        conflicts: list[dict] = []

        # Check for perspectives that mark the same issue differently
        # This is a simplified implementation
        perspective_issues: dict[str, set[str]] = {}
        for critique in critiques:
            perspective_issues[critique.perspective_name] = {
                issue.lower() for issue in critique.issues_found
            }

        # Check for perspective with issue where another has strength
        for i, critique_a in enumerate(critiques):
            for critique_b in critiques[i + 1:]:
                # Check if A has an issue that B marks as a strength
                for issue in critique_a.issues_found:
                    issue_keywords = set(issue.lower().split())
                    for strength in critique_b.strengths:
                        strength_keywords = set(strength.lower().split())
                        overlap = issue_keywords & strength_keywords
                        if len(overlap) >= 2:  # Significant keyword overlap
                            conflicts.append({
                                "perspective_a": critique_a.perspective_name,
                                "perspective_b": critique_b.perspective_name,
                                "issue": issue,
                                "strength": strength,
                                "type": "disagreement",
                            })

        return conflicts

    def _calculate_overall_score(
        self,
        critiques: list[MultiPerspectiveCritique],
        consensus_issues: list[str],
    ) -> float:
        """Calculate overall quality score.

        Args:
            critiques: List of critiques
            consensus_issues: Issues found by multiple perspectives

        Returns:
            Overall quality score (0.0 to 1.0)
        """
        if not critiques:
            return 0.5

        # Average confidence from all perspectives
        avg_confidence = sum(c.confidence for c in critiques) / len(critiques)

        # Penalty for consensus issues (these are more serious)
        consensus_penalty = min(0.3, len(consensus_issues) * 0.1)

        # Bonus for perspectives finding strengths
        total_strengths = sum(len(c.strengths) for c in critiques)
        strength_bonus = min(0.2, total_strengths * 0.02)

        score = avg_confidence - consensus_penalty + strength_bonus
        return max(0.0, min(1.0, score))
