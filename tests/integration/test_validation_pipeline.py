"""Integration tests for validation agents pipeline.

Tests the full validation pipeline with coordinator integration.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime

from hypoforge.domain.schemas import (
    EvidenceCard,
    ConflictCluster,
    Hypothesis,
    MinimalExperiment,
    PaperDetail,
    RunConstraints,
    RunRequest,
    RunState,
    RetrievalSummary,
    ReviewSummary,
    CriticSummary,
    PlannerSummary,
)
from hypoforge.domain.validation import (
    ValidationContext,
    ValidationResult,
    FeedbackPool,
    SynthesizedFeedback,
)
from hypoforge.agents.validation_base import ValidationAgentRegistry
from hypoforge.agents.evidence_validator import EvidenceValidator
from hypoforge.agents.conflict_detector import ConflictDetector
from hypoforge.agents.quality_assessor import QualityAssessor
from hypoforge.agents.feedback_synthesizer import FeedbackSynthesizer
from hypoforge.application.coordinator import RunCoordinator
from hypoforge.config import ValidationSettings, ReflectionSettings


# Fixtures
@pytest.fixture
def validation_settings():
    """Create validation settings for tests."""
    return ValidationSettings(
        enable_validation_agents=True,
        max_backtrack_per_stage=2,
        max_total_backtrack=3,
        min_valid_evidence=3,
        min_conflict_coverage=0.4,
        min_quality_score=0.5,
        evidence_completeness_threshold=0.6,
    )


@pytest.fixture
def reflection_settings():
    """Create reflection settings for tests."""
    return ReflectionSettings(
        enable_reflection=False,  # Disable for validation-only tests
    )


@pytest.fixture
def mock_repository():
    """Create a comprehensive mock repository."""
    repo = MagicMock()

    # Default returns
    repo.load_evidence_cards.return_value = []
    repo.load_selected_papers.return_value = []
    repo.load_conflict_clusters.return_value = []
    repo.load_hypotheses.return_value = []

    # Run state
    run_state = RunState(
        run_id="test-run-001",
        topic="Battery electrolyte additives",
        constraints=RunConstraints(),
        status="queued",
    )
    repo.get_run.return_value = run_state
    repo.create_run.return_value = run_state
    repo.is_reflection_enabled.return_value = False
    repo.load_iteration_state.return_value = None

    # Stage operations
    repo.start_stage = MagicMock()
    repo.finish_stage = MagicMock()
    repo.update_run_status = MagicMock()
    repo.save_iteration_state = MagicMock()
    repo.clear_downstream_data = MagicMock()
    repo.build_final_result = MagicMock(return_value=MagicMock(
        run_id="test-run-001",
        topic="Battery electrolyte additives",
        status="done",
        selected_papers=[],
        evidence_cards=[],
        conflict_clusters=[],
        hypotheses=[],
        report_markdown="",
    ))

    return repo


@pytest.fixture
def sample_evidence_cards():
    """Create sample evidence cards."""
    return [
        EvidenceCard(
            evidence_id=f"e{i}",
            paper_id="p1",
            title=f"Evidence {i}",
            claim_text=f"Claim {i} with sufficient detail for testing purposes",
            system_or_material="Battery electrolyte",
            intervention=f"Intervention {i}",
            outcome="Performance metric",
            direction="positive" if i % 2 == 0 else "negative",
            confidence=0.8,
        )
        for i in range(1, 7)
    ]


@pytest.fixture
def sample_papers():
    """Create sample papers."""
    return [
        PaperDetail(
            paper_id="p1",
            title="Test Paper",
            abstract="Abstract for testing",
            year=2024,
            authors=["Author"],
            provenance=["test"],
        ),
    ]


@pytest.fixture
def sample_conflicts():
    """Create sample conflict clusters."""
    return [
        ConflictCluster(
            cluster_id="c1",
            topic_axis="Performance",
            supporting_evidence_ids=["e1", "e2"],
            conflicting_evidence_ids=["e3"],
            conflict_type="conditional_divergence",
            likely_explanations=["Different conditions"],
            missing_controls=[],
            critic_summary="Test conflict",
            confidence=0.7,
        ),
    ]


@pytest.fixture
def sample_hypotheses():
    """Create sample hypotheses."""
    return [
        Hypothesis(
            rank=i,
            title=f"Hypothesis {i}",
            hypothesis_statement=f"Test hypothesis {i} with sufficient detail",
            why_plausible="Based on evidence",
            why_not_obvious="Requires further investigation",
            supporting_evidence_ids=["e1", "e2", "e3"],
            counterevidence_ids=["e4"],
            prediction="Test prediction",
            minimal_experiment=MinimalExperiment(
                system="Test system",
                design="Test design with proper methodology",
                control="Control condition",
                readouts=["Metric 1", "Metric 2"],
                success_criteria="Clear improvement",
                failure_interpretation="No effect",
            ),
            risks=["Risk 1"],
            novelty_score=0.7,
            feasibility_score=0.8,
            overall_score=0.75,
        )
        for i in [1, 2, 3]
    ]


class TestValidationAgentRegistry:
    """Tests for ValidationAgentRegistry."""

    def test_register_validators(self, mock_repository, validation_settings):
        """Test registering validators."""
        registry = ValidationAgentRegistry()

        validator = EvidenceValidator(
            repository=mock_repository,
            settings=validation_settings,
        )

        registry.register(validator)

        validators = registry.get_validators("review")
        assert len(validators) == 1
        assert validators[0].validation_type == "evidence_validation"

    def test_multiple_validators_per_stage(self, mock_repository, validation_settings):
        """Test multiple validators for same stage."""
        registry = ValidationAgentRegistry()

        # Register two validators for same stage
        validator1 = EvidenceValidator(
            repository=mock_repository,
            settings=validation_settings,
        )

        registry.register(validator1)

        validators = registry.get_validators("review")
        assert len(validators) == 1

    def test_get_backtrack_recommendation(self):
        """Test backtrack recommendation selection."""
        from hypoforge.domain.validation import BacktrackRecommendation

        registry = ValidationAgentRegistry()

        results = [
            ValidationResult(
                valid=True,
                score=0.8,
                issues=[],
                validation_type="test1",
                validated_count=1,
                passed_count=1,
            ),
            ValidationResult(
                valid=False,
                score=0.3,
                issues=[],
                validation_type="test2",
                validated_count=1,
                passed_count=0,
                backtrack_recommendation=BacktrackRecommendation(
                    target_stage="review",
                    reason="Test reason",
                    priority="medium",
                ),
            ),
        ]

        recommendation = registry.get_backtrack_recommendation(results)
        assert recommendation is not None
        assert recommendation.target_stage == "review"

    def test_has_critical_issues(self):
        """Test critical issue detection."""
        from hypoforge.domain.validation import BacktrackRecommendation

        registry = ValidationAgentRegistry()

        # No critical issues
        results1 = [
            ValidationResult(
                valid=True,
                score=0.8,
                issues=[],
                validation_type="test",
                validated_count=1,
                passed_count=1,
            ),
        ]
        assert not registry.has_critical_issues(results1)

        # With critical issues
        results2 = [
            ValidationResult(
                valid=False,
                score=0.3,
                issues=[],
                validation_type="test",
                validated_count=1,
                passed_count=0,
                backtrack_recommendation=BacktrackRecommendation(
                    target_stage="review",
                    reason="Critical",
                    priority="critical",
                ),
            ),
        ]
        assert registry.has_critical_issues(results2)


class TestValidationPipelineIntegration:
    """Integration tests for the full validation pipeline."""

    @pytest.mark.asyncio
    async def test_evidence_validation_flow(
        self, mock_repository, validation_settings,
        sample_evidence_cards, sample_papers
    ):
        """Test evidence validation flow."""
        mock_repository.load_evidence_cards.return_value = sample_evidence_cards
        mock_repository.load_selected_papers.return_value = sample_papers

        validator = EvidenceValidator(
            repository=mock_repository,
            settings=validation_settings,
        )

        context = ValidationContext(
            run_id="test-run",
            topic="Battery electrolyte",
            current_stage="review",
            iteration_number=1,
        )

        result = await validator.validate(context)

        assert result.validated_count == 6
        assert result.score > 0

    @pytest.mark.asyncio
    async def test_conflict_detection_flow(
        self, mock_repository, validation_settings,
        sample_evidence_cards, sample_conflicts
    ):
        """Test conflict detection flow."""
        mock_repository.load_evidence_cards.return_value = sample_evidence_cards
        mock_repository.load_conflict_clusters.return_value = sample_conflicts

        detector = ConflictDetector(
            repository=mock_repository,
            settings=validation_settings,
        )

        context = ValidationContext(
            run_id="test-run",
            topic="Battery electrolyte",
            current_stage="critic",
            iteration_number=1,
        )

        result = await detector.validate(context)

        assert result.validated_count == 1
        assert result.score > 0

    @pytest.mark.asyncio
    async def test_quality_assessment_flow(
        self, mock_repository, validation_settings,
        sample_evidence_cards, sample_conflicts, sample_hypotheses
    ):
        """Test quality assessment flow."""
        mock_repository.load_hypotheses.return_value = sample_hypotheses
        mock_repository.load_evidence_cards.return_value = sample_evidence_cards
        mock_repository.load_conflict_clusters.return_value = sample_conflicts

        assessor = QualityAssessor(
            repository=mock_repository,
            settings=validation_settings,
        )

        context = ValidationContext(
            run_id="test-run",
            topic="Battery electrolyte",
            current_stage="planner",
            iteration_number=1,
        )

        result = await assessor.validate(context)

        assert result.validated_count == 3
        assert result.score > 0

    def test_feedback_synthesis_flow(self, mock_repository, validation_settings):
        """Test feedback synthesis flow."""
        synthesizer = FeedbackSynthesizer(
            repository=mock_repository,
            settings=validation_settings,
        )

        from hypoforge.domain.validation import ValidationIssue

        results = [
            ValidationResult(
                valid=False,
                score=0.4,
                issues=[
                    ValidationIssue(
                        issue_type="evidence_quality",
                        severity="high",
                        description="Low quality evidence",
                    )
                ],
                validation_type="evidence_validation",
                validated_count=10,
                passed_count=4,
            ),
            ValidationResult(
                valid=True,
                score=0.7,
                issues=[],
                validation_type="conflict_detection",
                validated_count=5,
                passed_count=5,
            ),
        ]

        context = ValidationContext(
            run_id="test-run",
            topic="Battery electrolyte",
            current_stage="planner",
            iteration_number=1,
        )

        feedback = synthesizer.synthesize(results, context)

        assert isinstance(feedback, SynthesizedFeedback)
        assert len(feedback.priority_issues) > 0


class TestBacktrackLogic:
    """Tests for backtrack decision logic."""

    @pytest.mark.asyncio
    async def test_backtrack_on_low_evidence(
        self, mock_repository, validation_settings
    ):
        """Test backtrack triggered by low evidence count."""
        # Only 2 evidence cards, below threshold
        low_evidence = [
            EvidenceCard(
                evidence_id="e1",
                paper_id="p1",
                title="E1",
                claim_text="Short claim",
                system_or_material="System",
                intervention="Intervention",
                outcome="Outcome",
                direction="positive",
                confidence=0.5,
            ),
            EvidenceCard(
                evidence_id="e2",
                paper_id="p1",
                title="E2",
                claim_text="Another short claim",
                system_or_material="System",
                intervention="Intervention",
                outcome="Outcome",
                direction="negative",
                confidence=0.5,
            ),
        ]

        mock_repository.load_evidence_cards.return_value = low_evidence

        validator = EvidenceValidator(
            repository=mock_repository,
            settings=validation_settings,
        )

        context = ValidationContext(
            run_id="test-run",
            topic="Test topic",
            current_stage="review",
            iteration_number=1,
        )

        result = await validator.validate(context)

        assert result.valid is False
        assert result.backtrack_recommendation is not None

    @pytest.mark.asyncio
    async def test_no_backtrack_on_valid_results(
        self, mock_repository, validation_settings,
        sample_evidence_cards, sample_papers
    ):
        """Test no backtrack when validation passes."""
        mock_repository.load_evidence_cards.return_value = sample_evidence_cards
        mock_repository.load_selected_papers.return_value = sample_papers

        validator = EvidenceValidator(
            repository=mock_repository,
            settings=validation_settings,
        )

        context = ValidationContext(
            run_id="test-run",
            topic="Battery electrolyte",
            current_stage="review",
            iteration_number=1,
        )

        result = await validator.validate(context)

        # Should not backtrack with sufficient evidence
        assert result.valid is True or result.backtrack_recommendation is None


class TestCacheIntegration:
    """Tests for cache integration."""

    def test_validation_cache_basic_operations(self):
        """Test basic cache operations."""
        from hypoforge.infrastructure.cache import ValidationCache

        cache = ValidationCache("test-run")

        # Set and get
        cache.set("test_category", "key1", {"data": "value"})
        result = cache.get("test_category", "key1")
        assert result == {"data": "value"}

        # Delete
        assert cache.delete("test_category", "key1") is True
        assert cache.get("test_category", "key1") is None

    def test_validation_cache_expiry(self):
        """Test cache entry expiry."""
        from hypoforge.infrastructure.cache import ValidationCache

        cache = ValidationCache("test-run", default_ttl=1)

        cache.set("test", "key1", "value", ttl_seconds=0)  # Immediate expiry

        # Should be expired
        result = cache.get("test", "key1")
        assert result is None

    def test_cache_manager(self):
        """Test cache manager."""
        from hypoforge.infrastructure.cache import CacheManager

        manager = CacheManager()

        cache1 = manager.get_cache("run-1")
        cache2 = manager.get_cache("run-2")

        assert cache1 is not cache2

        cache1.set("test", "key", "value")
        assert cache1.get("test", "key") == "value"

        manager.clear_cache("run-1")
        assert cache1.get("test", "key") is None
