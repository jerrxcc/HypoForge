"""Conflict Detector Agent.

This module provides the ConflictDetector agent that enhances conflict detection
after the Critic stage, identifying implicit conflicts and evidence gaps.
"""

from __future__ import annotations

import logging
import math
from typing import TYPE_CHECKING, Any

from hypoforge.agents.validation_base import ValidationAgent
from hypoforge.domain.validation import (
    EnhancedConflictReport,
    WeakEvidenceGap,
    ValidationContext,
    ValidationIssue,
    ValidationResult,
)
from hypoforge.domain.schemas import StageName, Severity

if TYPE_CHECKING:
    from hypoforge.config import ValidationSettings
    from hypoforge.infrastructure.db.repository import RunRepository


logger = logging.getLogger(__name__)


# System prompt for conflict detection enhancement
CONFLICT_DETECTION_PROMPT = """You are an expert at identifying conflicts and contradictions in scientific evidence.

Your task is to analyze evidence cards and conflict clusters to:
1. **Confirm existing conflicts**: Validate that identified conflicts are genuine
2. **Discover new conflicts**: Find implicit conflicts not yet identified
3. **Identify gaps**: Find areas where evidence is missing or weak
4. **Assess homogeneity**: Check if evidence is too similar (lacking diversity)

For each conflict, provide:
- Conflict type (direct_conflict, conditional_divergence, weak_evidence_gap)
- Intensity score (0.0-1.0)
- Evidence involved
- Likely explanations

Focus on finding:
- Methodological differences that explain contradictory results
- Conditional factors that change outcomes
- Missing control conditions
- Areas lacking diverse evidence

Return your analysis as structured JSON with conflict and gap findings."""


class ConflictDetector(ValidationAgent):
    """Enhances conflict detection and identifies evidence gaps.

    This validator runs after the Critic stage to validate and enhance
    the conflict analysis, ensuring comprehensive conflict coverage.

    Detection Methods:
    - Semantic conflicts: Opposing conclusions on similar interventions
    - Methodological conflicts: Different methods yielding different results
    - Result conflicts: Direct contradictions in outcomes
    - Weak evidence gaps: Areas lacking diverse evidence
    """

    def __init__(
        self,
        *,
        repository: RunRepository,
        settings: ValidationSettings,
        provider: Any | None = None,
    ) -> None:
        """Initialize the conflict detector.

        Args:
            repository: The run repository for loading data
            settings: Validation settings for thresholds
            provider: Optional LLM provider for enhanced detection
        """
        super().__init__(
            repository=repository,
            thresholds={
                "min_coverage": settings.min_conflict_coverage,
                "intensity_threshold": settings.conflict_intensity_threshold,
                "max_homogeneity": settings.max_homogeneity_score,
            },
            model_name=settings.model_conflict_detector,
        )
        self._settings = settings
        self._provider = provider

    @property
    def validation_type(self) -> str:
        return "conflict_detection"

    @property
    def target_stage(self) -> StageName:
        return "critic"

    async def validate(self, context: ValidationContext) -> ValidationResult:
        """Validate and enhance conflict detection.

        Args:
            context: Validation context with run data

        Returns:
            ValidationResult with conflict detection report
        """
        run_id = context.run_id
        topic = context.topic

        self._logger.info(
            "Starting conflict detection validation",
            extra={"run_id": run_id, "topic": topic},
        )

        # Load data
        evidence_cards = self._load_evidence_cards(run_id)
        conflict_clusters = self._load_conflict_clusters(run_id)

        if not evidence_cards:
            return self._create_no_evidence_result(run_id)

        # Analyze existing conflicts
        confirmed_conflicts = self._confirm_existing_conflicts(conflict_clusters, evidence_cards)

        # Discover new conflicts
        new_conflicts = self._discover_new_conflicts(evidence_cards, conflict_clusters)

        # Identify weak evidence gaps
        weak_gaps = self._identify_weak_gaps(evidence_cards, conflict_clusters, topic)

        # Calculate metrics
        conflict_intensity_scores = self._calculate_conflict_intensities(
            conflict_clusters, evidence_cards
        )
        homogeneity_score = self._calculate_homogeneity_score(evidence_cards)
        coverage_score = self._calculate_coverage_score(evidence_cards, conflict_clusters)

        # Overall score
        overall_score = self._calculate_overall_score(
            coverage_score=coverage_score,
            homogeneity_score=homogeneity_score,
            conflict_count=len(confirmed_conflicts) + len(new_conflicts),
            gap_count=len(weak_gaps),
        )

        # Create report
        report = EnhancedConflictReport(
            confirmed_conflicts=confirmed_conflicts,
            new_conflicts=new_conflicts,
            weak_evidence_gaps=weak_gaps,
            conflict_intensity_scores=conflict_intensity_scores,
            evidence_homogeneity_score=homogeneity_score,
            coverage_score=coverage_score,
            overall_score=overall_score,
        )

        # Determine if valid
        is_valid = (
            coverage_score >= self._thresholds["min_coverage"] and
            homogeneity_score <= self._thresholds["max_homogeneity"]
        )

        # Create issues
        issues = self._create_issues_list(
            report=report,
            evidence_count=len(evidence_cards),
        )

        # Determine backtrack recommendation
        backtrack = None
        if not is_valid:
            backtrack = self._determine_backtrack(
                report=report,
                context=context,
            )

        self._logger.info(
            "Conflict detection validation completed",
            extra={
                "run_id": run_id,
                "valid": is_valid,
                "score": overall_score,
                "confirmed": len(confirmed_conflicts),
                "new": len(new_conflicts),
                "gaps": len(weak_gaps),
            },
        )

        return ValidationResult(
            valid=is_valid,
            score=overall_score,
            issues=issues,
            backtrack_recommendation=backtrack,
            validation_type=self.validation_type,
            validated_count=len(conflict_clusters),
            passed_count=len(confirmed_conflicts),
        )

    def _confirm_existing_conflicts(
        self,
        conflict_clusters: list[Any],
        evidence_cards: list[Any],
    ) -> list[str]:
        """Confirm that existing conflict clusters are valid.

        Args:
            conflict_clusters: Existing conflict clusters
            evidence_cards: All evidence cards

        Returns:
            List of confirmed conflict cluster IDs
        """
        evidence_ids = {card.evidence_id for card in evidence_cards}
        confirmed: list[str] = []

        for cluster in conflict_clusters:
            # Check that referenced evidence exists
            supporting_exists = all(
                eid in evidence_ids
                for eid in cluster.supporting_evidence_ids
            )
            conflicting_exists = all(
                eid in evidence_ids
                for eid in cluster.conflicting_evidence_ids
            )

            if supporting_exists and conflicting_exists:
                confirmed.append(cluster.cluster_id)
            else:
                self._logger.warning(
                    f"Cluster {cluster.cluster_id} references non-existent evidence"
                )

        return confirmed

    def _discover_new_conflicts(
        self,
        evidence_cards: list[Any],
        existing_clusters: list[Any],
    ) -> list[str]:
        """Discover new implicit conflicts.

        This method identifies conflicts that weren't detected by the Critic.

        Args:
            evidence_cards: All evidence cards
            existing_clusters: Existing conflict clusters

        Returns:
            List of newly discovered conflict indicators (simplified)
        """
        # Get already covered evidence
        covered_evidence = set()
        for cluster in existing_clusters:
            covered_evidence.update(cluster.supporting_evidence_ids)
            covered_evidence.update(cluster.conflicting_evidence_ids)

        # Group evidence by system/material
        by_system: dict[str, list[Any]] = {}
        for card in evidence_cards:
            key = card.system_or_material.lower() if card.system_or_material else "unknown"
            if key not in by_system:
                by_system[key] = []
            by_system[key].append(card)

        new_conflict_indicators: list[str] = []

        # Look for unreported conflicts
        for system, cards in by_system.items():
            if len(cards) < 2:
                continue

            # Check for direction conflicts not in existing clusters
            directions = {}
            for card in cards:
                outcome_key = card.outcome.lower() if card.outcome else "unknown"
                if outcome_key not in directions:
                    directions[outcome_key] = {"positive": [], "negative": [], "mixed": [], "null": []}
                directions[outcome_key][card.direction].append(card.evidence_id)

            # Find outcomes with conflicting directions
            for outcome, dirs in directions.items():
                if dirs["positive"] and dirs["negative"]:
                    # Check if this conflict is already covered
                    uncovered_positive = [eid for eid in dirs["positive"] if eid not in covered_evidence]
                    uncovered_negative = [eid for eid in dirs["negative"] if eid not in covered_evidence]

                    if uncovered_positive and uncovered_negative:
                        new_conflict_indicators.append(
                            f"implicit_conflict:{system}:{outcome}"
                        )

        return new_conflict_indicators

    def _identify_weak_gaps(
        self,
        evidence_cards: list[Any],
        conflict_clusters: list[Any],
        topic: str,
    ) -> list[WeakEvidenceGap]:
        """Identify gaps in evidence coverage.

        Args:
            evidence_cards: All evidence cards
            conflict_clusters: Existing conflict clusters
            topic: The research topic

        Returns:
            List of identified weak evidence gaps
        """
        gaps: list[WeakEvidenceGap] = []

        # Analyze topic axes coverage
        axes_covered: dict[str, int] = {}
        for card in evidence_cards:
            axis = card.system_or_material if card.system_or_material else "unknown"
            axes_covered[axis] = axes_covered.get(axis, 0) + 1

        # Find underrepresented axes
        total_evidence = len(evidence_cards)
        for axis, count in axes_covered.items():
            coverage_ratio = count / total_evidence if total_evidence > 0 else 0
            if coverage_ratio < 0.05 and count < 3:
                gaps.append(WeakEvidenceGap(
                    topic_axis=axis,
                    description=f"Limited evidence for {axis} ({count} cards)",
                    missing_evidence_types=["experimental", "comparative"],
                    suggested_search_terms=[axis, f"{axis} {topic}"],
                    impact_on_hypotheses=["May miss important variations in " + axis],
                ))

        # Check for missing intervention types
        interventions = set()
        for card in evidence_cards:
            if card.intervention:
                interventions.add(card.intervention.lower())

        # Check for missing control/comparator evidence
        has_controls = any(
            card.comparator and card.comparator.strip()
            for card in evidence_cards
        )
        if not has_controls:
            gaps.append(WeakEvidenceGap(
                topic_axis="methodology",
                description="No control/comparator conditions identified",
                missing_evidence_types=["controlled_experiment", "comparative_study"],
                suggested_search_terms=[f"{topic} control", f"{topic} baseline"],
                impact_on_hypotheses=["Hypotheses may lack proper grounding in controlled comparisons"],
            ))

        # Check evidence type diversity
        evidence_kinds: dict[str, int] = {}
        for card in evidence_cards:
            kind = card.evidence_kind if hasattr(card, "evidence_kind") else "unknown"
            evidence_kinds[kind] = evidence_kinds.get(kind, 0) + 1

        if len(evidence_kinds) < 2:
            gaps.append(WeakEvidenceGap(
                topic_axis="evidence_diversity",
                description="Limited diversity in evidence types",
                missing_evidence_types=list(set(["experiment", "simulation", "meta_analysis"]) - set(evidence_kinds.keys())),
                suggested_search_terms=[f"{topic} review", f"{topic} meta-analysis"],
                impact_on_hypotheses=["Hypotheses may be biased toward single evidence type"],
            ))

        return gaps

    def _calculate_conflict_intensities(
        self,
        conflict_clusters: list[Any],
        evidence_cards: list[Any],
    ) -> dict[str, float]:
        """Calculate intensity scores for each conflict.

        Args:
            conflict_clusters: Conflict clusters
            evidence_cards: Evidence cards

        Returns:
            Dict mapping cluster ID to intensity score
        """
        intensities: dict[str, float] = {}

        for cluster in conflict_clusters:
            # Base intensity from cluster confidence
            base = cluster.confidence if hasattr(cluster, "confidence") else 0.5

            # Boost for more evidence involved
            total_evidence = (
                len(cluster.supporting_evidence_ids) +
                len(cluster.conflicting_evidence_ids)
            )
            evidence_boost = min(0.2, total_evidence * 0.02)

            # Boost for explanation depth
            explanation_boost = min(0.15, len(cluster.likely_explanations) * 0.03)

            intensities[cluster.cluster_id] = min(1.0, base + evidence_boost + explanation_boost)

        return intensities

    def _calculate_homogeneity_score(self, evidence_cards: list[Any]) -> float:
        """Calculate how homogeneous the evidence is.

        Lower scores mean more diversity (better).

        Args:
            evidence_cards: Evidence cards

        Returns:
            Homogeneity score (0.0 = diverse, 1.0 = all same)
        """
        if not evidence_cards:
            return 0.0

        # Count unique values for key fields
        systems = set()
        interventions = set()
        outcomes = set()
        directions = {"positive": 0, "negative": 0, "mixed": 0, "null": 0, "unclear": 0}

        for card in evidence_cards:
            if card.system_or_material:
                systems.add(card.system_or_material.lower())
            if card.intervention:
                interventions.add(card.intervention.lower())
            if card.outcome:
                outcomes.add(card.outcome.lower())
            directions[card.direction] = directions.get(card.direction, 0) + 1

        # Calculate diversity metrics
        system_diversity = len(systems) / max(1, len(evidence_cards))
        intervention_diversity = len(interventions) / max(1, len(evidence_cards))
        outcome_diversity = len(outcomes) / max(1, len(evidence_cards))

        # Direction entropy
        total = sum(directions.values())
        direction_entropy = 0.0
        for count in directions.values():
            if count > 0:
                p = count / total
                direction_entropy -= p * math.log2(p)

        # Normalize entropy (max entropy for 5 directions is log2(5) ≈ 2.32)
        max_entropy = 2.32
        normalized_entropy = direction_entropy / max_entropy if max_entropy > 0 else 0

        # Combine into homogeneity score (inverse of diversity)
        diversity = (
            system_diversity * 0.3 +
            intervention_diversity * 0.2 +
            outcome_diversity * 0.2 +
            normalized_entropy * 0.3
        )

        return 1.0 - diversity

    def _calculate_coverage_score(
        self,
        evidence_cards: list[Any],
        conflict_clusters: list[Any],
    ) -> float:
        """Calculate how well conflicts cover the evidence.

        Args:
            evidence_cards: Evidence cards
            conflict_clusters: Conflict clusters

        Returns:
            Coverage score (0.0-1.0)
        """
        if not evidence_cards:
            return 0.0

        if not conflict_clusters:
            return 0.0

        # Get all evidence involved in conflicts
        covered_evidence = set()
        for cluster in conflict_clusters:
            covered_evidence.update(cluster.supporting_evidence_ids)
            covered_evidence.update(cluster.conflicting_evidence_ids)

        # Calculate coverage ratio
        coverage = len(covered_evidence) / len(evidence_cards)

        return coverage

    def _calculate_overall_score(
        self,
        coverage_score: float,
        homogeneity_score: float,
        conflict_count: int,
        gap_count: int,
    ) -> float:
        """Calculate overall conflict detection score.

        Args:
            coverage_score: Evidence coverage in conflicts
            homogeneity_score: Evidence homogeneity (lower is better)
            conflict_count: Number of conflicts found
            gap_count: Number of gaps identified

        Returns:
            Overall score (0.0-1.0)
        """
        # Base score from coverage
        score = coverage_score * 0.4

        # Penalize homogeneity (want diversity)
        diversity_score = 1.0 - homogeneity_score
        score += diversity_score * 0.25

        # Reward finding conflicts (up to a point)
        conflict_score = min(1.0, conflict_count / 3)
        score += conflict_score * 0.2

        # Penalize gaps
        gap_penalty = min(0.3, gap_count * 0.05)
        score -= gap_penalty

        return max(0.0, min(1.0, score))

    def _create_no_evidence_result(self, run_id: str) -> ValidationResult:
        """Create result when no evidence is available."""
        return ValidationResult(
            valid=False,
            score=0.0,
            issues=[ValidationIssue(
                issue_type="no_evidence",
                severity="critical",
                description="No evidence cards available for conflict detection",
                affected_ids=[],
                suggested_fix="Backtrack to review stage to extract evidence",
            )],
            backtrack_recommendation=self.create_backtrack_recommendation(
                target_stage="review",
                reason="No evidence available for conflict analysis",
                priority="critical",
                estimated_impact=0.8,
            ),
            validation_type=self.validation_type,
            validated_count=0,
            passed_count=0,
        )

    def _create_issues_list(
        self,
        report: EnhancedConflictReport,
        evidence_count: int,
    ) -> list[ValidationIssue]:
        """Create list of validation issues from report."""
        issues: list[ValidationIssue] = []

        # Low coverage issue
        if report.coverage_score < self._thresholds["min_coverage"]:
            issues.append(ValidationIssue(
                issue_type="low_conflict_coverage",
                severity="high" if report.coverage_score < 0.3 else "medium",
                description=f"Only {report.coverage_score:.0%} of evidence covered by conflicts",
                affected_ids=[],
                suggested_fix="Expand conflict analysis to include more evidence",
            ))

        # High homogeneity issue
        if report.evidence_homogeneity_score > self._thresholds["max_homogeneity"]:
            issues.append(ValidationIssue(
                issue_type="evidence_homogeneity",
                severity="medium",
                description="Evidence is too homogeneous, lacking diversity",
                affected_ids=[],
                suggested_fix="Backtrack to retrieval for more diverse papers",
            ))

        # New conflicts discovered
        if report.new_conflicts:
            issues.append(ValidationIssue(
                issue_type="undiscovered_conflicts",
                severity="low",
                description=f"Found {len(report.new_conflicts)} implicit conflicts not identified by Critic",
                affected_ids=report.new_conflicts[:5],
                suggested_fix="Re-run critic with enhanced conflict detection",
            ))

        # Weak evidence gaps
        for gap in report.weak_evidence_gaps[:3]:
            issues.append(ValidationIssue(
                issue_type="weak_evidence_gap",
                severity="low",
                description=gap.description,
                affected_ids=[],
                suggested_fix=f"Search for: {', '.join(gap.suggested_search_terms[:2])}",
            ))

        return issues

    def _determine_backtrack(
        self,
        report: EnhancedConflictReport,
        context: ValidationContext,
    ) -> Any:
        """Determine backtrack recommendation."""
        from hypoforge.domain.validation import BacktrackRecommendation

        # High homogeneity: need more diverse papers
        if report.evidence_homogeneity_score > self._thresholds["max_homogeneity"]:
            return BacktrackRecommendation(
                target_stage="retrieval",
                reason="Evidence is too homogeneous. Need more diverse paper sources.",
                priority="medium",
                estimated_impact=0.6,
            )

        # Low coverage: need better conflict analysis or more evidence
        if report.coverage_score < self._thresholds["min_coverage"] / 2:
            return BacktrackRecommendation(
                target_stage="review",
                reason="Very low conflict coverage. Need more evidence extraction.",
                priority="high",
                estimated_impact=0.7,
            )

        # Moderate issues: re-run critic
        if report.coverage_score < self._thresholds["min_coverage"]:
            return BacktrackRecommendation(
                target_stage="critic",
                reason="Insufficient conflict coverage. Re-analyze with broader scope.",
                priority="medium",
                estimated_impact=0.5,
            )

        return None
