"""Unit tests for reflection quality metrics.

Tests the quality metrics calculation for each pipeline stage:
- RetrievalQualityMetrics
- ReviewQualityMetrics
- CriticQualityMetrics
- PlannerQualityMetrics
"""

import pytest

from hypoforge.domain.quality import (
    CriticQualityMetrics,
    PlannerQualityMetrics,
    RetrievalQualityMetrics,
    ReviewQualityMetrics,
)


class TestRetrievalQualityMetrics:
    """Tests for RetrievalQualityMetrics."""

    def test_retrieval_quality_metrics_calculation(self) -> None:
        """Test retrieval quality metrics are calculated correctly."""
        metrics = RetrievalQualityMetrics(
            paper_count=12,
            paper_count_score=0.8,
            diversity_score=0.7,
            relevance_score=0.8,
            recency_score=0.6,
            source_coverage=0.9,
            overall_score=0.75,
        )

        assert metrics.paper_count == 12
        assert metrics.paper_count_score == 0.8
        assert metrics.diversity_score == 0.7
        assert metrics.relevance_score == 0.8
        assert metrics.recency_score == 0.6
        assert metrics.source_coverage == 0.9
        assert metrics.overall_score == 0.75

    def test_retrieval_quality_is_acceptable_high_score(self) -> None:
        """Test retrieval quality is acceptable with high scores."""
        metrics = RetrievalQualityMetrics(
            paper_count=10,
            paper_count_score=0.8,
            diversity_score=0.7,
            relevance_score=0.8,
            recency_score=0.6,
            source_coverage=0.9,
            overall_score=0.75,
        )

        assert metrics.is_acceptable is True

    def test_retrieval_quality_is_acceptable_low_score(self) -> None:
        """Test retrieval quality is not acceptable with low overall score."""
        metrics = RetrievalQualityMetrics(
            paper_count=10,
            paper_count_score=0.4,
            diversity_score=0.3,
            relevance_score=0.4,
            recency_score=0.3,
            source_coverage=0.3,
            overall_score=0.35,
        )

        assert metrics.is_acceptable is False

    def test_retrieval_quality_is_acceptable_low_paper_count(self) -> None:
        """Test retrieval quality is not acceptable with low paper count."""
        metrics = RetrievalQualityMetrics(
            paper_count=4,  # Below threshold of 6
            paper_count_score=0.5,
            diversity_score=0.7,
            relevance_score=0.8,
            recency_score=0.6,
            source_coverage=0.9,
            overall_score=0.7,  # Above threshold
        )

        assert metrics.is_acceptable is False

    def test_retrieval_quality_is_acceptable_boundary(self) -> None:
        """Test retrieval quality at exact threshold."""
        metrics = RetrievalQualityMetrics(
            paper_count=6,  # Exactly at threshold
            paper_count_score=0.6,
            diversity_score=0.6,
            relevance_score=0.6,
            recency_score=0.6,
            source_coverage=0.6,
            overall_score=0.6,  # Exactly at threshold
        )

        assert metrics.is_acceptable is True


class TestReviewQualityMetrics:
    """Tests for ReviewQualityMetrics."""

    def test_review_quality_metrics_calculation(self) -> None:
        """Test review quality metrics are calculated correctly."""
        metrics = ReviewQualityMetrics(
            papers_processed=10,
            evidence_count=15,
            extraction_completeness=0.8,
            evidence_depth=0.7,
            grounding_score=0.6,
            confidence_distribution={"high": 8, "medium": 5, "low": 2},
            overall_score=0.72,
        )

        assert metrics.papers_processed == 10
        assert metrics.evidence_count == 15
        assert metrics.extraction_completeness == 0.8
        assert metrics.evidence_depth == 0.7
        assert metrics.grounding_score == 0.6
        assert metrics.confidence_distribution == {"high": 8, "medium": 5, "low": 2}
        assert metrics.overall_score == 0.72

    def test_review_quality_is_acceptable_high_score(self) -> None:
        """Test review quality is acceptable with high scores."""
        metrics = ReviewQualityMetrics(
            papers_processed=10,
            evidence_count=10,
            extraction_completeness=0.8,
            evidence_depth=0.7,
            grounding_score=0.6,
            confidence_distribution={"high": 5, "medium": 3, "low": 2},
            overall_score=0.7,
        )

        assert metrics.is_acceptable is True

    def test_review_quality_is_acceptable_low_score(self) -> None:
        """Test review quality is not acceptable with low overall score."""
        metrics = ReviewQualityMetrics(
            papers_processed=5,
            evidence_count=2,
            extraction_completeness=0.3,
            evidence_depth=0.3,
            grounding_score=0.2,
            confidence_distribution={"high": 0, "medium": 1, "low": 1},
            overall_score=0.25,
        )

        assert metrics.is_acceptable is False

    def test_review_quality_is_acceptable_low_evidence_count(self) -> None:
        """Test review quality is not acceptable with low evidence count."""
        metrics = ReviewQualityMetrics(
            papers_processed=10,
            evidence_count=2,  # Below threshold of 3
            extraction_completeness=0.8,
            evidence_depth=0.7,
            grounding_score=0.6,
            confidence_distribution={"high": 1, "medium": 1, "low": 0},
            overall_score=0.7,  # Above threshold
        )

        assert metrics.is_acceptable is False

    def test_review_quality_is_acceptable_boundary(self) -> None:
        """Test review quality at exact threshold."""
        metrics = ReviewQualityMetrics(
            papers_processed=5,
            evidence_count=3,  # Exactly at threshold
            extraction_completeness=0.5,
            evidence_depth=0.5,
            grounding_score=0.5,
            confidence_distribution={"high": 1, "medium": 1, "low": 1},
            overall_score=0.5,  # Exactly at threshold
        )

        assert metrics.is_acceptable is True


class TestCriticQualityMetrics:
    """Tests for CriticQualityMetrics."""

    def test_critic_quality_metrics_calculation(self) -> None:
        """Test critic quality metrics are calculated correctly."""
        metrics = CriticQualityMetrics(
            clusters_count=3,
            conflict_detection_score=0.8,
            explanation_depth=0.7,
            evidence_coverage=0.6,
            axis_diversity=0.5,
            overall_score=0.65,
        )

        assert metrics.clusters_count == 3
        assert metrics.conflict_detection_score == 0.8
        assert metrics.explanation_depth == 0.7
        assert metrics.evidence_coverage == 0.6
        assert metrics.axis_diversity == 0.5
        assert metrics.overall_score == 0.65

    def test_critic_quality_is_acceptable_high_score(self) -> None:
        """Test critic quality is acceptable with high score."""
        metrics = CriticQualityMetrics(
            clusters_count=3,
            conflict_detection_score=0.8,
            explanation_depth=0.7,
            evidence_coverage=0.6,
            axis_diversity=0.5,
            overall_score=0.65,
        )

        assert metrics.is_acceptable is True

    def test_critic_quality_is_acceptable_low_score(self) -> None:
        """Test critic quality is not acceptable with low score."""
        metrics = CriticQualityMetrics(
            clusters_count=0,
            conflict_detection_score=0.0,
            explanation_depth=0.0,
            evidence_coverage=0.0,
            axis_diversity=0.0,
            overall_score=0.3,
        )

        assert metrics.is_acceptable is False

    def test_critic_quality_is_acceptable_boundary(self) -> None:
        """Test critic quality at exact threshold."""
        metrics = CriticQualityMetrics(
            clusters_count=1,
            conflict_detection_score=0.5,
            explanation_depth=0.5,
            evidence_coverage=0.5,
            axis_diversity=0.5,
            overall_score=0.5,  # Exactly at threshold
        )

        assert metrics.is_acceptable is True


class TestPlannerQualityMetrics:
    """Tests for PlannerQualityMetrics."""

    def test_planner_quality_metrics_calculation(self) -> None:
        """Test planner quality metrics are calculated correctly."""
        metrics = PlannerQualityMetrics(
            hypotheses_count=3,
            novelty_score=0.8,
            feasibility_score=0.7,
            experiment_clarity=0.9,
            evidence_grounding=0.6,
            conflict_utilization=0.5,
            overall_score=0.7,
        )

        assert metrics.hypotheses_count == 3
        assert metrics.novelty_score == 0.8
        assert metrics.feasibility_score == 0.7
        assert metrics.experiment_clarity == 0.9
        assert metrics.evidence_grounding == 0.6
        assert metrics.conflict_utilization == 0.5
        assert metrics.overall_score == 0.7

    def test_planner_quality_is_acceptable_high_score(self) -> None:
        """Test planner quality is acceptable with correct hypothesis count."""
        metrics = PlannerQualityMetrics(
            hypotheses_count=3,  # Exactly as required
            novelty_score=0.8,
            feasibility_score=0.7,
            experiment_clarity=0.9,
            evidence_grounding=0.6,
            conflict_utilization=0.5,
            overall_score=0.7,
        )

        assert metrics.is_acceptable is True

    def test_planner_quality_is_acceptable_low_score(self) -> None:
        """Test planner quality is not acceptable with low score."""
        metrics = PlannerQualityMetrics(
            hypotheses_count=3,
            novelty_score=0.3,
            feasibility_score=0.3,
            experiment_clarity=0.3,
            evidence_grounding=0.3,
            conflict_utilization=0.3,
            overall_score=0.35,
        )

        assert metrics.is_acceptable is False

    def test_planner_quality_is_acceptable_wrong_hypothesis_count(self) -> None:
        """Test planner quality is not acceptable with wrong hypothesis count."""
        metrics = PlannerQualityMetrics(
            hypotheses_count=2,  # Not exactly 3
            novelty_score=0.8,
            feasibility_score=0.7,
            experiment_clarity=0.9,
            evidence_grounding=0.6,
            conflict_utilization=0.5,
            overall_score=0.7,  # Above threshold
        )

        assert metrics.is_acceptable is False

    def test_planner_quality_is_acceptable_too_many_hypotheses(self) -> None:
        """Test planner quality is not acceptable with too many hypotheses."""
        metrics = PlannerQualityMetrics(
            hypotheses_count=4,  # Not exactly 3
            novelty_score=0.8,
            feasibility_score=0.7,
            experiment_clarity=0.9,
            evidence_grounding=0.6,
            conflict_utilization=0.5,
            overall_score=0.7,
        )

        assert metrics.is_acceptable is False

    def test_planner_quality_is_acceptable_boundary(self) -> None:
        """Test planner quality at exact threshold."""
        metrics = PlannerQualityMetrics(
            hypotheses_count=3,
            novelty_score=0.6,
            feasibility_score=0.6,
            experiment_clarity=0.6,
            evidence_grounding=0.6,
            conflict_utilization=0.6,
            overall_score=0.6,  # Exactly at threshold
        )

        assert metrics.is_acceptable is True


class TestQualityMetricsAcceptableLogic:
    """Tests for is_acceptable threshold logic across all metrics."""

    def test_retrieval_requires_both_conditions(self) -> None:
        """Test retrieval requires both overall_score >= 0.6 AND paper_count >= 6."""
        # Low score, high count
        m1 = RetrievalQualityMetrics(
            paper_count=10,
            paper_count_score=0.3,
            diversity_score=0.3,
            relevance_score=0.3,
            recency_score=0.3,
            source_coverage=0.3,
            overall_score=0.3,
        )
        assert m1.is_acceptable is False

        # High score, low count
        m2 = RetrievalQualityMetrics(
            paper_count=3,
            paper_count_score=0.8,
            diversity_score=0.8,
            relevance_score=0.8,
            recency_score=0.8,
            source_coverage=0.8,
            overall_score=0.8,
        )
        assert m2.is_acceptable is False

        # Both conditions met
        m3 = RetrievalQualityMetrics(
            paper_count=10,
            paper_count_score=0.7,
            diversity_score=0.7,
            relevance_score=0.7,
            recency_score=0.7,
            source_coverage=0.7,
            overall_score=0.7,
        )
        assert m3.is_acceptable is True

    def test_review_requires_both_conditions(self) -> None:
        """Test review requires both overall_score >= 0.5 AND evidence_count >= 3."""
        # Low score, high count
        m1 = ReviewQualityMetrics(
            papers_processed=10,
            evidence_count=10,
            extraction_completeness=0.3,
            evidence_depth=0.3,
            grounding_score=0.3,
            confidence_distribution={"high": 5, "medium": 3, "low": 2},
            overall_score=0.3,
        )
        assert m1.is_acceptable is False

        # High score, low count
        m2 = ReviewQualityMetrics(
            papers_processed=5,
            evidence_count=2,
            extraction_completeness=0.8,
            evidence_depth=0.8,
            grounding_score=0.8,
            confidence_distribution={"high": 1, "medium": 1, "low": 0},
            overall_score=0.8,
        )
        assert m2.is_acceptable is False

        # Both conditions met
        m3 = ReviewQualityMetrics(
            papers_processed=10,
            evidence_count=5,
            extraction_completeness=0.7,
            evidence_depth=0.7,
            grounding_score=0.7,
            confidence_distribution={"high": 3, "medium": 1, "low": 1},
            overall_score=0.7,
        )
        assert m3.is_acceptable is True

    def test_planner_requires_both_conditions(self) -> None:
        """Test planner requires both overall_score >= 0.6 AND hypotheses_count == 3."""
        # Low score, correct count
        m1 = PlannerQualityMetrics(
            hypotheses_count=3,
            novelty_score=0.3,
            feasibility_score=0.3,
            experiment_clarity=0.3,
            evidence_grounding=0.3,
            conflict_utilization=0.3,
            overall_score=0.3,
        )
        assert m1.is_acceptable is False

        # High score, wrong count
        m2 = PlannerQualityMetrics(
            hypotheses_count=5,
            novelty_score=0.8,
            feasibility_score=0.8,
            experiment_clarity=0.8,
            evidence_grounding=0.8,
            conflict_utilization=0.8,
            overall_score=0.8,
        )
        assert m2.is_acceptable is False

        # Both conditions met
        m3 = PlannerQualityMetrics(
            hypotheses_count=3,
            novelty_score=0.7,
            feasibility_score=0.7,
            experiment_clarity=0.7,
            evidence_grounding=0.7,
            conflict_utilization=0.7,
            overall_score=0.7,
        )
        assert m3.is_acceptable is True
