"""Base class for validation agents.

This module provides the abstract base class for all validation agents,
defining the common interface and backtrack decision logic.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from hypoforge.domain.validation import (
    BacktrackRecommendation,
    SynthesizedFeedback,
    ValidationContext,
    ValidationResult,
)
from hypoforge.domain.schemas import StageName, SEVERITY_PRIORITY

if TYPE_CHECKING:
    from hypoforge.infrastructure.db.repository import RunRepository


logger = logging.getLogger(__name__)


class ValidationAgent(ABC):
    """Abstract base class for validation agents.

    Validation agents evaluate pipeline stage outputs and determine
    whether backtracking is needed. Each validator focuses on a specific
    aspect of the pipeline output.

    Attributes:
        provider: The LLM provider for making API calls
        thresholds: Quality thresholds for validation decisions
    """

    def __init__(
        self,
        *,
        repository: RunRepository,
        thresholds: dict[str, float] | None = None,
        model_name: str = "gpt-5-mini",
    ) -> None:
        """Initialize the validation agent.

        Args:
            repository: The run repository for loading data
            thresholds: Quality thresholds for validation decisions
            model_name: The model to use for validation
        """
        self._repository = repository
        self._thresholds = thresholds or self._default_thresholds()
        self._model_name = model_name
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @staticmethod
    def _default_thresholds() -> dict[str, float]:
        """Get default quality thresholds."""
        return {
            "min_score": 0.5,
            "backtrack_score": 0.3,
            "critical_issue_count": 3,
        }

    @property
    @abstractmethod
    def validation_type(self) -> str:
        """Return the type of validation this agent performs."""
        pass

    @property
    @abstractmethod
    def target_stage(self) -> StageName:
        """Return the stage this validator runs after."""
        pass

    @abstractmethod
    async def validate(self, context: ValidationContext) -> ValidationResult:
        """Execute validation and return results.

        Args:
            context: The validation context with run data

        Returns:
            ValidationResult with score, issues, and backtrack recommendation
        """
        pass

    def should_backtrack(self, result: ValidationResult) -> bool:
        """Determine if backtracking is needed based on validation result.

        Args:
            result: The validation result to evaluate

        Returns:
            True if backtracking should occur
        """
        return result.should_backtrack()

    def create_backtrack_recommendation(
        self,
        target_stage: StageName,
        reason: str,
        feedback: SynthesizedFeedback | None = None,
        priority: str = "medium",
        estimated_impact: float = 0.5,
    ) -> BacktrackRecommendation:
        """Create a backtrack recommendation.

        Args:
            target_stage: The stage to backtrack to
            reason: Why backtracking is needed
            feedback: Synthesized feedback for the target stage
            priority: Priority level of the backtrack
            estimated_impact: Expected quality improvement

        Returns:
            A BacktrackRecommendation instance
        """
        return BacktrackRecommendation(
            target_stage=target_stage,
            reason=reason,
            feedback=feedback,
            priority=priority,
            estimated_impact=estimated_impact,
        )

    def _load_evidence_cards(self, run_id: str) -> list[Any]:
        """Load evidence cards for a run."""
        return self._repository.load_evidence_cards(run_id)

    def _load_selected_papers(self, run_id: str) -> list[Any]:
        """Load selected papers for a run."""
        return self._repository.load_selected_papers(run_id)

    def _load_conflict_clusters(self, run_id: str) -> list[Any]:
        """Load conflict clusters for a run."""
        return self._repository.load_conflict_clusters(run_id)

    def _load_hypotheses(self, run_id: str) -> list[Any]:
        """Load hypotheses for a run."""
        return self._repository.load_hypotheses(run_id)


class ValidationAgentRegistry:
    """Registry for validation agents.

    Maps stages to their corresponding validation agents and
    provides a unified interface for running validations.
    """

    def __init__(self) -> None:
        """Initialize the registry."""
        self._validators: dict[StageName, list[ValidationAgent]] = {}
        self._logger = logging.getLogger(__name__)

    def register(self, agent: ValidationAgent) -> None:
        """Register a validation agent.

        Args:
            agent: The validation agent to register
        """
        stage = agent.target_stage
        if stage not in self._validators:
            self._validators[stage] = []
        self._validators[stage].append(agent)
        self._logger.info(
            f"Registered {agent.validation_type} validator for stage {stage}"
        )

    def get_validators(self, stage: StageName) -> list[ValidationAgent]:
        """Get all validators for a stage.

        Args:
            stage: The stage to get validators for

        Returns:
            List of validation agents for the stage
        """
        return self._validators.get(stage, [])

    async def validate_stage(
        self,
        stage: StageName,
        context: ValidationContext,
    ) -> list[ValidationResult]:
        """Run all validators for a stage.

        Args:
            stage: The stage to validate
            context: The validation context

        Returns:
            List of validation results from all validators
        """
        validators = self.get_validators(stage)
        results = []

        for validator in validators:
            try:
                result = await validator.validate(context)
                results.append(result)
                self._logger.info(
                    f"Validation {validator.validation_type} completed",
                    extra={
                        "run_id": context.run_id,
                        "stage": stage,
                        "valid": result.valid,
                        "score": result.score,
                    },
                )
            except Exception as exc:
                self._logger.exception(
                    f"Validation {validator.validation_type} failed",
                    extra={"run_id": context.run_id, "stage": stage},
                )
                # Create a degraded validation result
                results.append(ValidationResult(
                    valid=True,  # Don't block pipeline on validator failure
                    score=0.5,
                    issues=[],
                    validation_type=validator.validation_type,
                    validated_count=0,
                    passed_count=0,
                ))

        return results

    def has_critical_issues(self, results: list[ValidationResult]) -> bool:
        """Check if any validation result has critical issues.

        Args:
            results: List of validation results

        Returns:
            True if any result recommends backtracking
        """
        return any(r.should_backtrack() for r in results)

    def get_backtrack_recommendation(
        self,
        results: list[ValidationResult],
    ) -> BacktrackRecommendation | None:
        """Get the most important backtrack recommendation.

        Args:
            results: List of validation results

        Returns:
            The highest priority backtrack recommendation, or None
        """
        recommendations = [
            r.backtrack_recommendation
            for r in results
            if r.backtrack_recommendation is not None
        ]

        if not recommendations:
            return None

        # Sort by priority and estimated impact
        recommendations.sort(
            key=lambda r: (SEVERITY_PRIORITY.get(r.priority, 3), -r.estimated_impact)
        )

        return recommendations[0]
