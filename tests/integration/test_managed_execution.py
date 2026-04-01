from __future__ import annotations

from pathlib import Path

from hypoforge.agents.validation_base import ValidationAgent, ValidationAgentRegistry
from hypoforge.application.coordinator import RunCoordinator
from hypoforge.config import ReflectionSettings, ValidationSettings
from hypoforge.domain.schemas import (
    ConflictCluster,
    CriticSummary,
    EvidenceCard,
    PaperDetail,
    PlannerSummary,
    RetrievalSummary,
    ReviewSummary,
)
from hypoforge.domain.validation import ValidationContext, ValidationIssue, ValidationResult
from hypoforge.infrastructure.db.repository import RunRepository
from tests.helpers.reflection_helpers import (
    build_reflection_test_services,
    make_three_test_hypotheses,
)


class ScriptedReviewValidator(ValidationAgent):
    def __init__(self, *, repository: RunRepository) -> None:
        super().__init__(repository=repository)
        self.call_count = 0

    @property
    def validation_type(self) -> str:
        return "scripted_review_validation"

    @property
    def target_stage(self):
        return "review"

    async def validate(self, context: ValidationContext) -> ValidationResult:
        self.call_count += 1
        if self.call_count == 1:
            return ValidationResult(
                valid=False,
                score=0.2,
                issues=[
                    ValidationIssue(
                        issue_type="evidence_extraction",
                        severity="high",
                        description="Evidence extraction lacks depth",
                        suggested_fix="Extract richer intervention/outcome details",
                    )
                ],
                backtrack_recommendation=self.create_backtrack_recommendation(
                    target_stage="review",
                    reason="Need richer evidence extraction",
                    priority="high",
                    estimated_impact=0.8,
                ),
                validation_type=self.validation_type,
                validated_count=1,
                passed_count=0,
            )
        return ValidationResult(
            valid=True,
            score=0.9,
            issues=[],
            validation_type=self.validation_type,
            validated_count=1,
            passed_count=1,
        )


class CountingReviewValidator(ValidationAgent):
    def __init__(self, *, repository: RunRepository) -> None:
        super().__init__(repository=repository)
        self.call_count = 0

    @property
    def validation_type(self) -> str:
        return "counting_review_validation"

    @property
    def target_stage(self):
        return "review"

    async def validate(self, context: ValidationContext) -> ValidationResult:
        del context
        self.call_count += 1
        return ValidationResult(
            valid=True,
            score=0.9,
            issues=[],
            validation_type=self.validation_type,
            validated_count=1,
            passed_count=1,
        )


def test_reflection_retry_injects_previous_iteration_feedback(tmp_path: Path) -> None:
    repo, agent, settings = build_reflection_test_services(
        tmp_path,
        quality_scores_by_stage={
            "retrieval": [0.3, 0.8],
            "review": [0.8],
            "critic": [0.8],
            "planner": [0.8],
        },
        reflection_enabled=True,
    )
    retrieval_contexts: list[dict] = []

    def retrieval(run_id: str, topic: str, constraints, *, execution_context=None) -> RetrievalSummary:
        del constraints
        retrieval_contexts.append(dict(execution_context or {}))
        repo.save_selected_papers(
            run_id,
            [
                PaperDetail(
                    paper_id=f"p{i}",
                    title=f"Paper {i}",
                    year=2024,
                    provenance=["test"],
                )
                for i in range(6)
            ],
            "seed",
        )
        return RetrievalSummary(
            canonical_topic=topic,
            query_variants_used=[topic],
            search_notes=[],
            selected_paper_ids=[f"p{i}" for i in range(6)],
            excluded_paper_ids=[],
            coverage_assessment="medium",
            needs_broader_search=False,
        )

    def review(run_id: str, *, execution_context=None) -> ReviewSummary:
        del execution_context
        repo.save_evidence_cards(
            run_id,
            [
                EvidenceCard(
                    evidence_id=f"e{i}",
                    paper_id="p1",
                    title=f"Evidence {i}",
                    claim_text="Claim",
                    system_or_material="System",
                    intervention="Intervention",
                    outcome="Outcome",
                    direction="positive",
                    confidence=0.8,
                )
                for i in range(5)
            ],
        )
        return ReviewSummary(
            papers_processed=5,
            evidence_cards_created=5,
            coverage_summary="good",
            dominant_axes=["axis"],
            low_confidence_paper_ids=[],
        )

    def critic(run_id: str, *, execution_context=None) -> CriticSummary:
        del execution_context
        repo.save_conflict_clusters(
            run_id,
            [
                ConflictCluster(
                    cluster_id="c1",
                    topic_axis="axis",
                    supporting_evidence_ids=["e1"],
                    conflicting_evidence_ids=["e2"],
                    conflict_type="weak_evidence_gap",
                    critic_summary="gap",
                    confidence=0.7,
                )
            ],
        )
        return CriticSummary(clusters_created=1, top_axes=["axis"], critic_notes=[])

    def planner(run_id: str, *, execution_context=None) -> PlannerSummary:
        del execution_context
        repo.save_hypotheses(run_id, make_three_test_hypotheses())
        repo.save_report_markdown(run_id, "# Report")
        return PlannerSummary(hypotheses_created=3, report_rendered=True, top_axes=["axis"], planner_notes=[])

    coordinator = RunCoordinator(
        repository=repo,
        retrieval_agent=retrieval,
        review_agent=review,
        critic_agent=critic,
        planner_agent=planner,
        reflection_agent=agent,
        reflection_settings=settings,
    )

    result = coordinator.run_topic("test topic")

    assert result.status == "done"
    assert len(retrieval_contexts) == 2
    assert retrieval_contexts[0]["iteration_number"] == 1
    assert retrieval_contexts[0]["is_retry"] is False
    assert "previous_iteration_feedback" not in retrieval_contexts[0]
    assert retrieval_contexts[1]["iteration_number"] == 2
    assert retrieval_contexts[1]["is_retry"] is True
    assert "previous_iteration_feedback" in retrieval_contexts[1]
    retrieval_summary = next(
        summary for summary in result.stage_summaries if summary.stage_name == "retrieval"
    )
    assert retrieval_summary.attempt == 2
    assert len(repo.load_reflection_history(result.run_id, "retrieval")) == 2


def test_validation_only_reruns_target_stage_with_stage_scoped_feedback(tmp_path: Path) -> None:
    repo = RunRepository.from_sqlite_path(tmp_path / "app.db")
    registry = ValidationAgentRegistry()
    validator = ScriptedReviewValidator(repository=repo)
    registry.register(validator)

    review_contexts: list[dict] = []
    critic_contexts: list[dict] = []
    call_counts = {"retrieval": 0, "review": 0, "critic": 0, "planner": 0}

    def retrieval(run_id: str, topic: str, constraints, *, execution_context=None) -> RetrievalSummary:
        del constraints, execution_context
        call_counts["retrieval"] += 1
        repo.save_selected_papers(
            run_id,
            [PaperDetail(paper_id="p1", title=topic, year=2024, provenance=["test"])],
            "seed",
        )
        return RetrievalSummary(
            canonical_topic=topic,
            query_variants_used=[topic],
            search_notes=[],
            selected_paper_ids=["p1"],
            excluded_paper_ids=[],
            coverage_assessment="good",
            needs_broader_search=False,
        )

    def review(run_id: str, *, execution_context=None) -> ReviewSummary:
        call_counts["review"] += 1
        review_contexts.append(dict(execution_context or {}))
        repo.save_evidence_cards(
            run_id,
            [
                EvidenceCard(
                    evidence_id=f"e{call_counts['review']}",
                    paper_id="p1",
                    title="Evidence",
                    claim_text="Claim",
                    system_or_material="System",
                    intervention="Intervention",
                    outcome="Outcome",
                    direction="positive",
                    confidence=0.8,
                )
            ],
        )
        return ReviewSummary(
            papers_processed=1,
            evidence_cards_created=1,
            coverage_summary="good",
            dominant_axes=["axis"],
            low_confidence_paper_ids=[],
        )

    def critic(run_id: str, *, execution_context=None) -> CriticSummary:
        call_counts["critic"] += 1
        critic_contexts.append(dict(execution_context or {}))
        repo.save_conflict_clusters(
            run_id,
            [
                ConflictCluster(
                    cluster_id="c1",
                    topic_axis="axis",
                    supporting_evidence_ids=["e1"],
                    conflicting_evidence_ids=["e1"],
                    conflict_type="weak_evidence_gap",
                    critic_summary="gap",
                    confidence=0.7,
                )
            ],
        )
        return CriticSummary(clusters_created=1, top_axes=["axis"], critic_notes=[])

    def planner(run_id: str, *, execution_context=None) -> PlannerSummary:
        del execution_context
        call_counts["planner"] += 1
        repo.save_hypotheses(run_id, make_three_test_hypotheses())
        repo.save_report_markdown(run_id, "# Report")
        return PlannerSummary(hypotheses_created=3, report_rendered=True, top_axes=["axis"], planner_notes=[])

    coordinator = RunCoordinator(
        repository=repo,
        retrieval_agent=retrieval,
        review_agent=review,
        critic_agent=critic,
        planner_agent=planner,
        reflection_settings=ReflectionSettings(enable_reflection=False),
        validation_registry=registry,
        validation_settings=ValidationSettings(enable_validation_agents=True, max_total_backtrack=1),
    )

    result = coordinator.run_topic("test topic")

    assert result.status == "done"
    assert validator.call_count == 2
    assert call_counts == {"retrieval": 1, "review": 2, "critic": 1, "planner": 1}
    assert review_contexts[0]["is_retry"] is False
    assert "validation_feedback" not in review_contexts[0]
    assert review_contexts[1]["is_retry"] is True
    assert review_contexts[1]["validation_feedback"]["avoid_patterns"]
    assert "validation_feedback" not in critic_contexts[0]
    review_summary = next(
        summary for summary in result.stage_summaries if summary.stage_name == "review"
    )
    assert review_summary.attempt == 2


def test_combined_mode_validates_after_reflection_stabilizes_stage(tmp_path: Path) -> None:
    repo, agent, settings = build_reflection_test_services(
        tmp_path,
        quality_scores_by_stage={
            "retrieval": [0.8],
            "review": [0.3, 0.8],
            "critic": [0.8],
            "planner": [0.8],
        },
        reflection_enabled=True,
    )
    registry = ValidationAgentRegistry()
    validator = CountingReviewValidator(repository=repo)
    registry.register(validator)

    review_call_count = 0

    def retrieval(run_id: str, topic: str, constraints, *, execution_context=None) -> RetrievalSummary:
        del constraints, execution_context
        repo.save_selected_papers(
            run_id,
            [PaperDetail(paper_id="p1", title=topic, year=2024, provenance=["test"])],
            "seed",
        )
        return RetrievalSummary(
            canonical_topic=topic,
            query_variants_used=[topic],
            search_notes=[],
            selected_paper_ids=["p1"],
            excluded_paper_ids=[],
            coverage_assessment="good",
            needs_broader_search=False,
        )

    def review(run_id: str, *, execution_context=None) -> ReviewSummary:
        nonlocal review_call_count
        review_call_count += 1
        repo.save_evidence_cards(
            run_id,
            [
                EvidenceCard(
                    evidence_id=f"e{review_call_count}",
                    paper_id="p1",
                    title="Evidence",
                    claim_text="Claim",
                    system_or_material="System",
                    intervention="Intervention",
                    outcome="Outcome",
                    direction="positive",
                    confidence=0.8,
                )
            ],
        )
        return ReviewSummary(
            papers_processed=1,
            evidence_cards_created=1,
            coverage_summary="good",
            dominant_axes=["axis"],
            low_confidence_paper_ids=[],
        )

    def critic(run_id: str, *, execution_context=None) -> CriticSummary:
        del execution_context
        repo.save_conflict_clusters(
            run_id,
            [
                ConflictCluster(
                    cluster_id="c1",
                    topic_axis="axis",
                    supporting_evidence_ids=["e1"],
                    conflicting_evidence_ids=["e1"],
                    conflict_type="weak_evidence_gap",
                    critic_summary="gap",
                    confidence=0.7,
                )
            ],
        )
        return CriticSummary(clusters_created=1, top_axes=["axis"], critic_notes=[])

    def planner(run_id: str, *, execution_context=None) -> PlannerSummary:
        del execution_context
        repo.save_hypotheses(run_id, make_three_test_hypotheses())
        repo.save_report_markdown(run_id, "# Report")
        return PlannerSummary(hypotheses_created=3, report_rendered=True, top_axes=["axis"], planner_notes=[])

    coordinator = RunCoordinator(
        repository=repo,
        retrieval_agent=retrieval,
        review_agent=review,
        critic_agent=critic,
        planner_agent=planner,
        reflection_agent=agent,
        reflection_settings=settings,
        validation_registry=registry,
        validation_settings=ValidationSettings(enable_validation_agents=True),
    )

    result = coordinator.run_topic("test topic")

    assert result.status == "done"
    assert review_call_count == 2
    assert validator.call_count == 1
