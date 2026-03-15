"""Feedback Synthesizer Agent.

This module provides the FeedbackSynthesizer agent that consolidates feedback
from multiple validation agents into actionable improvement suggestions.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from hypoforge.agents.validation_base import ValidationAgent
from hypoforge.domain.validation import (
    FeedbackPool,
    Issue,
    SynthesizedFeedback,
    ValidationContext,
    ValidationResult,
)
from hypoforge.domain.schemas import StageName, Severity

if TYPE_CHECKING:
    from hypoforge.config import ValidationSettings
    from hypoforge.infrastructure.db.repository import RunRepository


logger = logging.getLogger(__name__)


# System prompt for feedback synthesis
FEEDBACK_SYNTHESIS_PROMPT = """You are an expert at synthesizing feedback for scientific research pipelines.

Your task is to consolidate feedback from multiple validation sources into:
1. **Avoid Patterns**: Things that went wrong and should be avoided
2. **Focus Areas**: Key areas that need improvement
3. **Context Enhancements**: Additional context to provide to agents
4. **Priority Issues**: Issues sorted by urgency and impact

Guidelines:
- Be specific and actionable
- Prioritize issues that have the most impact on quality
- Provide concrete suggestions, not vague advice
- Consider the iteration history and avoid repeating failed approaches

Return synthesized feedback as structured JSON with clear categorization."""


class FeedbackSynthesizer(ValidationAgent):
    """Synthesizes feedback from multiple validation sources.

    This agent consolidates feedback from EvidenceValidator, ConflictDetector,
    and QualityAssessor into unified, actionable improvement suggestions.

    Responsibilities:
    - Aggregate feedback from multiple validators
    - Prioritize issues by impact and urgency
    - Generate avoid patterns from failures
    - Identify focus areas for improvement
    - Create context enhancements for next iteration
    """

    def __init__(
        self,
        *,
        repository: RunRepository,
        settings: ValidationSettings,
        provider: Any | None = None,
    ) -> None:
        """Initialize the feedback synthesizer.

        Args:
            repository: The run repository for loading data
            settings: Validation settings
            provider: Optional LLM provider for enhanced synthesis
        """
        super().__init__(
            repository=repository,
            thresholds={
                "max_issues": 10,
                "max_patterns": 5,
                "max_focus_areas": 5,
            },
            model_name=settings.model_feedback_synthesizer,
        )
        self._settings = settings
        self._provider = provider

    @property
    def validation_type(self) -> str:
        return "feedback_synthesis"

    @property
    def target_stage(self) -> StageName:
        # Feedback synthesizer runs after all validations
        return "planner"

    async def validate(self, context: ValidationContext) -> ValidationResult:
        """Synthesize feedback from validation results.

        Note: This method is called for interface compatibility, but
        the primary use is through synthesize() method.

        Args:
            context: Validation context

        Returns:
            ValidationResult containing synthesized feedback
        """
        # This validator doesn't produce traditional validation results
        # It's used to synthesize feedback from other validators
        return ValidationResult(
            valid=True,
            score=1.0,
            issues=[],
            validation_type=self.validation_type,
            validated_count=0,
            passed_count=0,
        )

    def synthesize(
        self,
        validation_results: list[ValidationResult],
        context: ValidationContext,
        feedback_pool: FeedbackPool | None = None,
    ) -> SynthesizedFeedback:
        """Synthesize feedback from validation results.

        Args:
            validation_results: Results from all validators
            context: Validation context
            feedback_pool: Optional existing feedback pool for history

        Returns:
            SynthesizedFeedback with consolidated improvement suggestions
        """
        run_id = context.run_id
        iteration = context.iteration_number

        self._logger.info(
            "Synthesizing feedback",
            extra={
                "run_id": run_id,
                "iteration": iteration,
                "result_count": len(validation_results),
            },
        )

        # Collect all issues
        all_issues = self._collect_issues(validation_results)

        # Prioritize issues
        priority_issues = self._prioritize_issues(all_issues, context)

        # Generate avoid patterns
        avoid_patterns = self._generate_avoid_patterns(
            validation_results=validation_results,
            previous_feedback=feedback_pool.feedback_history if feedback_pool else [],
        )

        # Generate focus areas
        focus_areas = self._generate_focus_areas(
            priority_issues=priority_issues,
            context=context,
        )

        # Generate context enhancements
        context_enhancements = self._generate_context_enhancements(
            validation_results=validation_results,
            priority_issues=priority_issues,
        )

        feedback = SynthesizedFeedback(
            avoid_patterns=avoid_patterns[:self._thresholds["max_patterns"]],
            focus_areas=focus_areas[:self._thresholds["max_focus_areas"]],
            context_enhancements=context_enhancements,
            priority_issues=priority_issues[:self._thresholds["max_issues"]],
        )

        self._logger.info(
            "Feedback synthesis completed",
            extra={
                "run_id": run_id,
                "iteration": iteration,
                "avoid_patterns": len(avoid_patterns),
                "focus_areas": len(focus_areas),
                "priority_issues": len(priority_issues),
            },
        )

        return feedback

    def _collect_issues(
        self,
        validation_results: list[ValidationResult],
    ) -> list[Issue]:
        """Collect all issues from validation results.

        Args:
            validation_results: Results from validators

        Returns:
            List of all issues with source information
        """
        issues: list[Issue] = []

        for result in validation_results:
            for issue in result.issues:
                # Determine priority from severity
                priority_map: dict[str, str] = {
                    "critical": "critical",
                    "high": "high",
                    "medium": "medium",
                    "low": "low",
                }
                priority = priority_map.get(issue.severity, "medium")

                issues.append(Issue(
                    source=result.validation_type,
                    description=issue.description,
                    priority=priority,
                    actionable=bool(issue.suggested_fix),
                    related_stage=self._infer_related_stage(issue.issue_type),
                ))

        return issues

    def _infer_related_stage(self, issue_type: str) -> StageName | None:
        """Infer which stage an issue relates to.

        Args:
            issue_type: The type of issue

        Returns:
            Related stage name or None
        """
        stage_keywords: dict[StageName, list[str]] = {
            "retrieval": ["paper", "search", "retrieval", "source", "coverage"],
            "review": ["evidence", "extraction", "card", "review"],
            "critic": ["conflict", "cluster", "critic", "contradiction"],
            "planner": ["hypothesis", "novelty", "feasibility", "planner"],
        }

        issue_lower = issue_type.lower()
        for stage, keywords in stage_keywords.items():
            if any(kw in issue_lower for kw in keywords):
                return stage

        return None

    def _prioritize_issues(
        self,
        issues: list[Issue],
        context: ValidationContext,
    ) -> list[Issue]:
        """Prioritize issues by impact and urgency.

        Args:
            issues: All collected issues
            context: Validation context

        Returns:
            Sorted list of issues by priority
        """
        # Sort by priority (critical first) then by actionability
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}

        sorted_issues = sorted(
            issues,
            key=lambda i: (
                priority_order.get(i.priority, 3),
                0 if i.actionable else 1,
                0 if i.related_stage else 1,
            ),
        )

        # In later iterations, boost issues that haven't been addressed
        if context.iteration_number > 1 and context.previous_feedback:
            previous_descriptions = set()
            for fb in context.previous_feedback:
                previous_descriptions.update(fb.avoid_patterns)

            # Boost novel issues
            boosted: list[Issue] = []
            for issue in sorted_issues:
                is_novel = not any(
                    desc.lower() in issue.description.lower()
                    for desc in previous_descriptions
                )
                if is_novel:
                    boosted.insert(0, issue)
                else:
                    boosted.append(issue)

            return boosted

        return sorted_issues

    def _generate_avoid_patterns(
        self,
        validation_results: list[ValidationResult],
        previous_feedback: list[SynthesizedFeedback],
    ) -> list[str]:
        """Generate patterns to avoid in next iteration.

        Args:
            validation_results: Results from validators
            previous_feedback: Previous feedback history

        Returns:
            List of patterns to avoid
        """
        patterns: list[str] = []

        # Extract patterns from failed validations
        for result in validation_results:
            if not result.valid:
                # Generate avoid pattern from failure
                if result.validation_type == "evidence_validation":
                    patterns.append("Incomplete evidence extraction - ensure all required fields are populated")
                elif result.validation_type == "conflict_detection":
                    patterns.append("Insufficient conflict coverage - analyze more evidence pairs")
                elif result.validation_type == "quality_assessment":
                    patterns.append("Low hypothesis quality - focus on novelty and evidence grounding")

        # Extract patterns from critical issues
        for result in validation_results:
            for issue in result.issues:
                if issue.severity in ("critical", "high"):
                    pattern = self._issue_to_avoid_pattern(issue)
                    if pattern and pattern not in patterns:
                        patterns.append(pattern)

        # Include patterns from previous feedback that are still relevant
        for fb in previous_feedback[-2:]:  # Last 2 iterations
            for pattern in fb.avoid_patterns:
                if pattern not in patterns:
                    patterns.append(pattern)

        return patterns

    def _issue_to_avoid_pattern(self, issue: Any) -> str | None:
        """Convert an issue to an avoid pattern.

        Args:
            issue: The validation issue

        Returns:
            Avoid pattern string or None
        """
        issue_type = issue.issue_type.lower()

        pattern_map = {
            "insufficient_valid_evidence": "Avoid shallow evidence extraction - extract complete evidence cards",
            "low_conflict_coverage": "Avoid superficial conflict analysis - explore all evidence relationships",
            "low_quality": "Avoid generic hypotheses - ground in specific evidence",
            "invalid_evidence": "Avoid unvalidated evidence references - verify all evidence IDs",
            "evidence_homogeneity": "Avoid single-source evidence - diversify paper selection",
            "no_evidence": "Avoid skipping evidence extraction - ensure review completes",
            "no_hypotheses": "Avoid premature planning completion - generate all 3 hypotheses",
        }

        for key, pattern in pattern_map.items():
            if key in issue_type:
                return pattern

        return None

    def _generate_focus_areas(
        self,
        priority_issues: list[Issue],
        context: ValidationContext,
    ) -> list[str]:
        """Generate focus areas for next iteration.

        Args:
            priority_issues: Prioritized issues
            context: Validation context

        Returns:
            List of focus areas
        """
        focus_areas: list[str] = []

        # Group issues by related stage
        stage_issues: dict[StageName, list[Issue]] = {}
        for issue in priority_issues:
            if issue.related_stage:
                if issue.related_stage not in stage_issues:
                    stage_issues[issue.related_stage] = []
                stage_issues[issue.related_stage].append(issue)

        # Generate focus areas for each stage with issues
        stage_focus_templates: dict[StageName, list[str]] = {
            "retrieval": [
                "Broaden paper search scope",
                "Include more diverse sources",
                "Extend year range for coverage",
            ],
            "review": [
                "Extract complete evidence cards",
                "Improve claim specificity",
                "Strengthen evidence grounding",
            ],
            "critic": [
                "Identify implicit conflicts",
                "Explore conditional divergence",
                "Analyze methodology differences",
            ],
            "planner": [
                "Enhance hypothesis novelty",
                "Improve experimental design",
                "Strengthen evidence utilization",
            ],
        }

        for stage, issues in stage_issues.items():
            critical_count = sum(1 for i in issues if i.priority in ("critical", "high"))
            if critical_count > 0:
                templates = stage_focus_templates.get(stage, [])
                focus_areas.extend(templates[:2])

        # Add topic-specific focus if available
        if context.topic:
            focus_areas.append(f"Focus on {context.topic}-specific evidence")

        return focus_areas

    def _generate_context_enhancements(
        self,
        validation_results: list[ValidationResult],
        priority_issues: list[Issue],
    ) -> list[str]:
        """Generate context enhancements for next iteration.

        Args:
            validation_results: Results from validators
            priority_issues: Prioritized issues

        Returns:
            List of context enhancements
        """
        enhancements: list[str] = []

        # Add specific guidance from validation results
        for result in validation_results:
            if result.backtrack_recommendation:
                enhancements.append(
                    f"Previous {result.validation_type} identified: {result.backtrack_recommendation.reason}"
                )

        # Add guidance from high-priority issues
        for issue in priority_issues[:5]:
            if issue.priority in ("critical", "high"):
                enhancements.append(f"Address: {issue.description}")

        # Add iteration-specific guidance
        if len(validation_results) > 1:
            failed_validators = [r for r in validation_results if not r.valid]
            if len(failed_validators) > 1:
                enhancements.append(
                    "Multiple validation failures detected - consider comprehensive re-execution"
                )

        return enhancements

    def create_feedback_for_stage(
        self,
        target_stage: StageName,
        validation_results: list[ValidationResult],
        context: ValidationContext,
    ) -> SynthesizedFeedback:
        """Create stage-specific feedback for backtracking.

        Args:
            target_stage: The stage to create feedback for
            validation_results: Results from validators
            context: Validation context

        Returns:
            Stage-specific synthesized feedback
        """
        # Filter issues relevant to target stage
        relevant_issues = [
            issue
            for result in validation_results
            for issue in result.issues
            if self._is_relevant_to_stage(issue, target_stage)
        ]

        # Convert to Issue objects
        issues = self._collect_issues([
            ValidationResult(
                valid=True,
                score=1.0,
                issues=relevant_issues,
                validation_type="stage_filtered",
                validated_count=0,
                passed_count=0,
            )
        ])

        # Generate stage-specific patterns
        stage_patterns = self._get_stage_patterns(target_stage, relevant_issues)

        return SynthesizedFeedback(
            avoid_patterns=stage_patterns["avoid"],
            focus_areas=stage_patterns["focus"],
            context_enhancements=stage_patterns["context"],
            priority_issues=issues,
        )

    def _is_relevant_to_stage(self, issue: Any, stage: StageName) -> bool:
        """Check if an issue is relevant to a stage.

        Args:
            issue: The validation issue
            stage: The target stage

        Returns:
            True if relevant
        """
        related = self._infer_related_stage(issue.issue_type)
        return related == stage or related is None

    def _get_stage_patterns(
        self,
        stage: StageName,
        issues: list[Any],
    ) -> dict[str, list[str]]:
        """Get stage-specific patterns.

        Args:
            stage: Target stage
            issues: Relevant issues

        Returns:
            Dict with avoid, focus, and context patterns
        """
        stage_templates: dict[StageName, dict[str, list[str]]] = {
            "retrieval": {
                "avoid": [
                    "Avoid narrow search queries",
                    "Avoid single-source retrieval",
                ],
                "focus": [
                    "Expand search term variations",
                    "Include multiple databases",
                ],
                "context": [
                    "Previous retrieval had insufficient coverage",
                ],
            },
            "review": {
                "avoid": [
                    "Avoid incomplete evidence extraction",
                    "Avoid vague claim descriptions",
                ],
                "focus": [
                    "Extract complete PICO elements",
                    "Strengthen evidence grounding",
                ],
                "context": [
                    "Evidence cards need better completeness",
                ],
            },
            "critic": {
                "avoid": [
                    "Avoid superficial conflict analysis",
                    "Avoid missing implicit conflicts",
                ],
                "focus": [
                    "Explore all evidence pairings",
                    "Identify conditional factors",
                ],
                "context": [
                    "Conflict coverage needs improvement",
                ],
            },
            "planner": {
                "avoid": [
                    "Avoid generic hypotheses",
                    "Avoid weak evidence grounding",
                ],
                "focus": [
                    "Enhance novelty and originality",
                    "Strengthen experimental design",
                ],
                "context": [
                    "Hypotheses need better quality scores",
                ],
            },
        }

        return stage_templates.get(stage, {
            "avoid": [],
            "focus": [],
            "context": [],
        })
