"""Unit tests for validation agents.

Tests for EvidenceValidator, ConflictDetector, QualityAssessor,
and FeedbackSynthesizer agents.
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
)
from hypoforge.domain.validation import (
    ValidationContext,
    ValidationResult,
    FeedbackPool,
    SynthesizedFeedback,
    Issue,
)
from hypoforge.agents.evidence_validator import EvidenceValidator
from hypoforge.agents.conflict_detector import ConflictDetector
from hypoforge.agents.quality_assessor import QualityAssessor
from hypoforge.agents.feedback_synthesizer import FeedbackSynthesizer
from hypoforge.config import ValidationSettings


# Fixtures
@pytest.fixture
def validation_settings():
    """Create validation settings for tests."""
    return ValidationSettings(
        enable_validation_agents=True,
        min_valid_evidence=5,
        min_conflict_coverage=0.5,
        min_quality_score=0.6,
        evidence_completeness_threshold=0.7,
        evidence_accuracy_threshold=0.6,
        evidence_relevance_threshold=0.5,
    )


@pytest.fixture
def mock_repository():
    """Create a mock repository."""
    repo = MagicMock()
    repo.load_evidence_cards = MagicMock(return_value=[])
    repo.load_selected_papers = MagicMock(return_value=[])
    repo.load_conflict_clusters = MagicMock(return_value=[])
    repo.load_hypotheses = MagicMock(return_value=[])
    return repo


@pytest.fixture
def sample_evidence_cards():
    """Create sample evidence cards for testing."""
    return [
        EvidenceCard(
            evidence_id="e1",
            paper_id="p1",
            title="Evidence 1",
            claim_text="This intervention improves outcomes significantly in the tested system",
            system_or_material="Battery electrolyte",
            intervention="New additive X",
            outcome="Energy density",
            direction="positive",
            confidence=0.85,
        ),
        EvidenceCard(
            evidence_id="e2",
            paper_id="p1",
            title="Evidence 2",
            claim_text="The control group showed no improvement",
            system_or_material="Battery electrolyte",
            intervention="No additive",
            outcome="Energy density",
            direction="null",
            confidence=0.90,
        ),
        EvidenceCard(
            evidence_id="e3",
            paper_id="p2",
            title="Evidence 3",
            claim_text="Additive X reduced performance under high temperature",
            system_or_material="Battery electrolyte",
            intervention="New additive X",
            outcome="Energy density",
            direction="negative",
            confidence=0.75,
        ),
    ]


@pytest.fixture
def sample_papers():
    """Create sample papers for testing."""
    return [
        PaperDetail(
            paper_id="p1",
            title="Effects of Additive X on Battery Performance",
            abstract="We tested additive X in battery electrolytes and found significant improvements.",
            year=2024,
            authors=["Author A"],
            provenance=["test"],
        ),
        PaperDetail(
            paper_id="p2",
            title="Temperature Effects on Battery Additives",
            abstract="High temperature conditions showed reduced performance with additive X.",
            year=2023,
            authors=["Author B"],
            provenance=["test"],
        ),
    ]


@pytest.fixture
def sample_conflict_clusters():
    """Create sample conflict clusters for testing."""
    return [
        ConflictCluster(
            cluster_id="c1",
            topic_axis="Additive X performance",
            supporting_evidence_ids=["e1"],
            conflicting_evidence_ids=["e3"],
            conflict_type="conditional_divergence",
            likely_explanations=["Temperature conditions differ"],
            missing_controls=["Temperature baseline"],
            critic_summary="Performance varies with temperature",
            confidence=0.7,
        ),
    ]


@pytest.fixture
def sample_hypotheses():
    """Create sample hypotheses for testing."""
    return [
        Hypothesis(
            rank=1,
            title="Temperature-dependent Additive Performance",
            hypothesis_statement="Additive X improves battery performance at room temperature but degrades at high temperature",
            why_plausible="Evidence shows positive effects at normal conditions and negative at high temperature",
            why_not_obvious="The temperature threshold is not well-defined",
            supporting_evidence_ids=["e1", "e2", "e3"],
            counterevidence_ids=["e3"],
            prediction="Performance will peak at 25°C and decline above 40°C",
            minimal_experiment=MinimalExperiment(
                system="Battery cell with additive X",
                design="Test at multiple temperatures from 20°C to 60°C",
                control="Battery cell without additive",
                readouts=["Energy density", "Cycle life"],
                success_criteria="Clear temperature threshold identified",
                failure_interpretation="No clear temperature effect",
            ),
            risks=["Temperature control complexity"],
            novelty_score=0.7,
            feasibility_score=0.8,
            overall_score=0.75,
        ),
    ]


@pytest.fixture
def validation_context(sample_evidence_cards, sample_papers, sample_conflict_clusters, sample_hypotheses):
    """Create a validation context for testing."""
    return ValidationContext(
        run_id="test-run-001",
        topic="Battery electrolyte additives",
        current_stage="review",
        iteration_number=1,
        previous_feedback=[],
        stage_output={},
        selected_paper_ids=["p1", "p2"],
        evidence_ids=["e1", "e2", "e3"],
        conflict_cluster_ids=["c1"],
        hypothesis_ids=["h1"],
    )


# EvidenceValidator Tests
class TestEvidenceValidator:
    """Tests for EvidenceValidator agent."""

    def test_init(self, mock_repository, validation_settings):
        """Test EvidenceValidator initialization."""
        validator = EvidenceValidator(
            repository=mock_repository,
            settings=validation_settings,
        )
        assert validator.validation_type == "evidence_validation"
        assert validator.target_stage == "review"

    @pytest.mark.asyncio
    async def test_validate_empty_evidence(self, mock_repository, validation_settings, validation_context):
        """Test validation with no evidence cards."""
        mock_repository.load_evidence_cards.return_value = []

        validator = EvidenceValidator(
            repository=mock_repository,
            settings=validation_settings,
        )

        result = await validator.validate(validation_context)

        assert result.valid is False
        assert result.score == 0.0
        assert any("no_evidence" in i.issue_type.lower() for i in result.issues)

    @pytest.mark.asyncio
    async def test_validate_complete_evidence(
        self, mock_repository, validation_settings, validation_context,
        sample_evidence_cards, sample_papers
    ):
        """Test validation with complete evidence cards."""
        mock_repository.load_evidence_cards.return_value = sample_evidence_cards
        mock_repository.load_selected_papers.return_value = sample_papers

        validator = EvidenceValidator(
            repository=mock_repository,
            settings=validation_settings,
        )

        result = await validator.validate(validation_context)

        assert result.validated_count == 3
        assert result.score > 0
        assert len(result.issues) >= 0

    @pytest.mark.asyncio
    async def test_validate_incomplete_evidence(self, mock_repository, validation_settings, validation_context):
        """Test validation with incomplete evidence cards."""
        incomplete_evidence = [
            EvidenceCard(
                evidence_id="e1",
                paper_id="p1",
                title="",
                claim_text="Short",
                system_or_material="",
                intervention="",
                outcome="",
                direction="positive",
                confidence=0.3,
            ),
        ]
        mock_repository.load_evidence_cards.return_value = incomplete_evidence

        validator = EvidenceValidator(
            repository=mock_repository,
            settings=validation_settings,
        )

        result = await validator.validate(validation_context)

        assert result.valid is False
        assert len(result.issues) > 0

    def test_check_completeness(self, mock_repository, validation_settings):
        """Test completeness checking."""
        validator = EvidenceValidator(
            repository=mock_repository,
            settings=validation_settings,
        )

        complete_card = EvidenceCard(
            evidence_id="e1",
            paper_id="p1",
            title="Complete Evidence",
            claim_text="A complete and well-formed claim with sufficient detail",
            system_or_material="System A",
            intervention="Intervention B",
            outcome="Outcome C",
            direction="positive",
            confidence=0.9,
        )

        score, issues = validator._check_completeness(complete_card)
        assert score > 0.7
        assert len(issues) == 0

    def test_detect_conflict_hints(self, mock_repository, validation_settings, sample_evidence_cards):
        """Test conflict hint detection."""
        validator = EvidenceValidator(
            repository=mock_repository,
            settings=validation_settings,
        )

        hints = validator._detect_conflict_hints(sample_evidence_cards)

        # Should detect conflict between positive and negative evidence
        assert len(hints) > 0
        assert hints[0].conflict_type == "directional_conflict"


# ConflictDetector Tests
class TestConflictDetector:
    """Tests for ConflictDetector agent."""

    def test_init(self, mock_repository, validation_settings):
        """Test ConflictDetector initialization."""
        detector = ConflictDetector(
            repository=mock_repository,
            settings=validation_settings,
        )
        assert detector.validation_type == "conflict_detection"
        assert detector.target_stage == "critic"

    @pytest.mark.asyncio
    async def test_validate_no_evidence(self, mock_repository, validation_settings, validation_context):
        """Test conflict detection with no evidence."""
        mock_repository.load_evidence_cards.return_value = []

        detector = ConflictDetector(
            repository=mock_repository,
            settings=validation_settings,
        )

        result = await detector.validate(validation_context)

        assert result.valid is False
        assert result.score == 0.0

    @pytest.mark.asyncio
    async def test_validate_with_conflicts(
        self, mock_repository, validation_settings, validation_context,
        sample_evidence_cards, sample_conflict_clusters
    ):
        """Test conflict detection with existing conflicts."""
        mock_repository.load_evidence_cards.return_value = sample_evidence_cards
        mock_repository.load_conflict_clusters.return_value = sample_conflict_clusters

        detector = ConflictDetector(
            repository=mock_repository,
            settings=validation_settings,
        )

        result = await detector.validate(validation_context)

        assert result.validated_count == 1
        assert result.score > 0

    def test_calculate_homogeneity_score(self, mock_repository, validation_settings, sample_evidence_cards):
        """Test homogeneity score calculation."""
        detector = ConflictDetector(
            repository=mock_repository,
            settings=validation_settings,
        )

        score = detector._calculate_homogeneity_score(sample_evidence_cards)

        # Score should be between 0 and 1
        assert 0 <= score <= 1

    def test_calculate_coverage_score(self, mock_repository, validation_settings, sample_evidence_cards, sample_conflict_clusters):
        """Test coverage score calculation."""
        detector = ConflictDetector(
            repository=mock_repository,
            settings=validation_settings,
        )

        score = detector._calculate_coverage_score(sample_evidence_cards, sample_conflict_clusters)

        # Should have some coverage since conflict references evidence
        assert 0 <= score <= 1


# QualityAssessor Tests
class TestQualityAssessor:
    """Tests for QualityAssessor agent."""

    def test_init(self, mock_repository, validation_settings):
        """Test QualityAssessor initialization."""
        assessor = QualityAssessor(
            repository=mock_repository,
            settings=validation_settings,
        )
        assert assessor.validation_type == "quality_assessment"
        assert assessor.target_stage == "planner"

    @pytest.mark.asyncio
    async def test_validate_no_hypotheses(self, mock_repository, validation_settings, validation_context):
        """Test quality assessment with no hypotheses."""
        mock_repository.load_hypotheses.return_value = []

        assessor = QualityAssessor(
            repository=mock_repository,
            settings=validation_settings,
        )

        result = await assessor.validate(validation_context)

        assert result.valid is False
        assert result.score == 0.0

    @pytest.mark.asyncio
    async def test_validate_with_hypotheses(
        self, mock_repository, validation_settings, validation_context,
        sample_hypotheses, sample_evidence_cards, sample_conflict_clusters
    ):
        """Test quality assessment with hypotheses."""
        mock_repository.load_hypotheses.return_value = sample_hypotheses
        mock_repository.load_evidence_cards.return_value = sample_evidence_cards
        mock_repository.load_conflict_clusters.return_value = sample_conflict_clusters

        assessor = QualityAssessor(
            repository=mock_repository,
            settings=validation_settings,
        )

        result = await assessor.validate(validation_context)

        assert result.validated_count == 1
        assert result.score > 0

    def test_assess_novelty(self, mock_repository, validation_settings, sample_hypotheses):
        """Test novelty assessment."""
        assessor = QualityAssessor(
            repository=mock_repository,
            settings=validation_settings,
        )

        score, issues, suggestions = assessor._assess_novelty(
            sample_hypotheses[0],
            "Battery additives"
        )

        assert 0 <= score <= 1

    def test_assess_feasibility(self, mock_repository, validation_settings, sample_hypotheses):
        """Test feasibility assessment."""
        assessor = QualityAssessor(
            repository=mock_repository,
            settings=validation_settings,
        )

        score, issues, suggestions = assessor._assess_feasibility(sample_hypotheses[0])

        assert 0 <= score <= 1

    def test_assess_evidence_support(self, mock_repository, validation_settings, sample_hypotheses, sample_evidence_cards):
        """Test evidence support assessment."""
        assessor = QualityAssessor(
            repository=mock_repository,
            settings=validation_settings,
        )

        score, issues, suggestions = assessor._assess_evidence_support(
            sample_hypotheses[0],
            sample_evidence_cards
        )

        assert 0 <= score <= 1


# FeedbackSynthesizer Tests
class TestFeedbackSynthesizer:
    """Tests for FeedbackSynthesizer agent."""

    def test_init(self, mock_repository, validation_settings):
        """Test FeedbackSynthesizer initialization."""
        synthesizer = FeedbackSynthesizer(
            repository=mock_repository,
            settings=validation_settings,
        )
        assert synthesizer.validation_type == "feedback_synthesis"

    def test_synthesize(self, mock_repository, validation_settings, validation_context):
        """Test feedback synthesis."""
        synthesizer = FeedbackSynthesizer(
            repository=mock_repository,
            settings=validation_settings,
        )

        # Create sample validation results
        validation_results = [
            ValidationResult(
                valid=False,
                score=0.4,
                issues=[],
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

        feedback = synthesizer.synthesize(validation_results, validation_context)

        assert isinstance(feedback, SynthesizedFeedback)
        assert len(feedback.avoid_patterns) >= 0
        assert len(feedback.focus_areas) >= 0
        assert len(feedback.priority_issues) >= 0

    def test_collect_issues(self, mock_repository, validation_settings):
        """Test issue collection."""
        synthesizer = FeedbackSynthesizer(
            repository=mock_repository,
            settings=validation_settings,
        )

        from hypoforge.domain.validation import ValidationIssue

        results = [
            ValidationResult(
                valid=False,
                score=0.3,
                issues=[
                    ValidationIssue(
                        issue_type="test_issue",
                        severity="high",
                        description="Test issue description",
                    )
                ],
                validation_type="test",
                validated_count=1,
                passed_count=0,
            ),
        ]

        issues = synthesizer._collect_issues(results)

        assert len(issues) == 1
        assert issues[0].source == "test"
        assert issues[0].priority == "high"

    def test_create_feedback_for_stage(self, mock_repository, validation_settings, validation_context):
        """Test stage-specific feedback creation."""
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
                        issue_type="evidence_extraction",
                        severity="medium",
                        description="Incomplete evidence extraction",
                    )
                ],
                validation_type="evidence_validation",
                validated_count=10,
                passed_count=5,
            ),
        ]

        feedback = synthesizer.create_feedback_for_stage(
            target_stage="review",
            validation_results=results,
            context=validation_context,
        )

        assert isinstance(feedback, SynthesizedFeedback)
        assert len(feedback.avoid_patterns) > 0 or len(feedback.focus_areas) > 0


# FeedbackPool Tests
class TestFeedbackPool:
    """Tests for FeedbackPool."""

    def test_add_feedback(self):
        """Test adding feedback to pool."""
        pool = FeedbackPool(run_id="test-run")

        feedback = SynthesizedFeedback(
            avoid_patterns=["pattern1"],
            focus_areas=["area1"],
            context_enhancements=["enhancement1"],
            priority_issues=[],
        )

        pool.add_feedback(feedback)

        assert pool.iteration_count == 1
        assert "pattern1" in pool.accumulated_avoid_patterns
        assert "area1" in pool.accumulated_focus_areas

    def test_get_latest_feedback(self):
        """Test getting latest feedback."""
        pool = FeedbackPool(run_id="test-run")

        feedback1 = SynthesizedFeedback(
            avoid_patterns=["pattern1"],
            focus_areas=[],
            context_enhancements=[],
            priority_issues=[],
        )
        feedback2 = SynthesizedFeedback(
            avoid_patterns=["pattern2"],
            focus_areas=[],
            context_enhancements=[],
            priority_issues=[],
        )

        pool.add_feedback(feedback1)
        pool.add_feedback(feedback2)

        latest = pool.get_latest_feedback()
        assert latest is not None
        assert "pattern2" in latest.avoid_patterns

    def test_get_issues_by_priority(self):
        """Test filtering issues by priority."""
        pool = FeedbackPool(run_id="test-run")

        feedback = SynthesizedFeedback(
            avoid_patterns=[],
            focus_areas=[],
            context_enhancements=[],
            priority_issues=[
                Issue(source="test", description="critical issue", priority="critical"),
                Issue(source="test", description="medium issue", priority="medium"),
                Issue(source="test", description="another critical", priority="critical"),
            ],
        )

        pool.add_feedback(feedback)

        critical_issues = pool.get_issues_by_priority("critical")
        assert len(critical_issues) == 2


# ValidationContext Tests
class TestValidationContext:
    """Tests for ValidationContext."""

    def test_create_context(self):
        """Test creating validation context."""
        context = ValidationContext(
            run_id="test-run",
            topic="Test topic",
            current_stage="review",
            iteration_number=1,
        )

        assert context.run_id == "test-run"
        assert context.topic == "Test topic"
        assert context.current_stage == "review"
        assert context.iteration_number == 1

    def test_context_with_feedback(self):
        """Test context with previous feedback."""
        feedback = SynthesizedFeedback(
            avoid_patterns=["avoid1"],
            focus_areas=["focus1"],
            context_enhancements=[],
            priority_issues=[],
        )

        context = ValidationContext(
            run_id="test-run",
            topic="Test",
            current_stage="review",
            previous_feedback=[feedback],
        )

        assert len(context.previous_feedback) == 1
        assert "avoid1" in context.previous_feedback[0].avoid_patterns
