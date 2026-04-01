"""Correction Loop Controller for managed stage execution.

This module provides the CorrectionLoopController that owns single-stage
execution with feedback injection and optional reflection-driven retries.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Callable

from hypoforge.config import ReflectionSettings
from hypoforge.domain.schemas import (
    CriticSummary,
    IterationState,
    PlannerSummary,
    ReflectionFeedback,
    RetrievalSummary,
    ReviewSummary,
    RunIterationState,
    StageName,
)
from hypoforge.domain.validation import SynthesizedFeedback

if TYPE_CHECKING:
    from hypoforge.agents.reflection import ReflectionAgent
    from hypoforge.infrastructure.db.repository import RunRepository


logger = logging.getLogger(__name__)

StageSummary = RetrievalSummary | ReviewSummary | CriticSummary | PlannerSummary
StageAttemptExecutor = Callable[[dict[str, Any]], StageSummary]

_STAGE_THRESHOLDS: dict[StageName, str] = {
    "retrieval": "retrieval_quality_threshold",
    "review": "review_quality_threshold",
    "critic": "critic_quality_threshold",
    "planner": "planner_quality_threshold",
}


@dataclass(slots=True)
class StageExecutionResult:
    summary: StageSummary
    iteration_state: IterationState
    reflection_feedbacks: list[ReflectionFeedback] = field(default_factory=list)
    backtrack_to: StageName | None = None


class CorrectionLoopController:
    """Controls managed stage execution and reflection retries."""

    def __init__(
        self,
        *,
        repository: RunRepository,
        reflection_agent: ReflectionAgent | None,
        settings: ReflectionSettings,
    ) -> None:
        self._repository = repository
        self._reflection_agent = reflection_agent
        self._settings = settings
        self._logger = logging.getLogger(__name__)

    def execute_stage(
        self,
        *,
        run_id: str,
        stage_name: StageName,
        run_iteration_state: RunIterationState,
        attempt_executor: StageAttemptExecutor,
        validation_feedback: SynthesizedFeedback | None = None,
        enable_reflection: bool,
    ) -> StageExecutionResult:
        """Execute a stage with optional reflection retries."""
        iteration_state = run_iteration_state.get_stage_state(stage_name)
        iteration_state.max_iterations = self._settings.max_stage_iterations
        iteration_state.quality_threshold = self._get_quality_threshold(stage_name)
        iteration_state.prepare_for_execution()

        reflection_feedbacks: list[ReflectionFeedback] = []

        while True:
            context = self._build_execution_context(
                iteration_state=iteration_state,
                validation_feedback=validation_feedback,
            )
            iteration_state.status = "in_progress"
            summary = attempt_executor(context)

            if not enable_reflection or self._reflection_agent is None:
                iteration_state.status = "completed"
                return StageExecutionResult(
                    summary=summary,
                    iteration_state=iteration_state,
                )

            reflection_summary = self._reflection_agent.evaluate_stage(
                run_id=run_id,
                stage_name=stage_name,
                iteration_state=iteration_state,
                stage_output=summary.model_dump(),
            )
            iteration_state.current_quality_score = reflection_summary.quality_score

            feedback = self._reflection_agent.create_feedback(
                summary=reflection_summary,
                iteration_number=iteration_state.iteration_number,
            )
            iteration_state.add_feedback(feedback)
            reflection_feedbacks.append(feedback)

            if feedback.should_backtrack():
                iteration_state.status = "backtracked"
                return StageExecutionResult(
                    summary=summary,
                    iteration_state=iteration_state,
                    reflection_feedbacks=reflection_feedbacks,
                    backtrack_to=feedback.recommended_backtrack_stage,
                )

            if reflection_summary.meets_threshold:
                iteration_state.status = "quality_threshold_met"
                return StageExecutionResult(
                    summary=summary,
                    iteration_state=iteration_state,
                    reflection_feedbacks=reflection_feedbacks,
                )

            if not iteration_state.can_iterate():
                iteration_state.status = "max_iterations_reached"
                return StageExecutionResult(
                    summary=summary,
                    iteration_state=iteration_state,
                    reflection_feedbacks=reflection_feedbacks,
                )

            self._logger.info(
                "quality below threshold, retrying stage",
                extra={
                    "run_id": run_id,
                    "stage": stage_name,
                    "iteration": iteration_state.iteration_number,
                    "score": reflection_summary.quality_score,
                },
            )
            iteration_state.iteration_number += 1

    def _build_execution_context(
        self,
        *,
        iteration_state: IterationState,
        validation_feedback: SynthesizedFeedback | None,
    ) -> dict[str, Any]:
        is_retry = (
            iteration_state.iteration_number > 1
            or bool(iteration_state.feedback_history)
            or validation_feedback is not None
        )
        context: dict[str, Any] = {
            "iteration_number": iteration_state.iteration_number,
            "is_retry": is_retry,
        }

        if iteration_state.feedback_history:
            latest_feedback = iteration_state.feedback_history[-1]
            context["previous_iteration_feedback"] = {
                "issues_found": latest_feedback.issues_found,
                "suggested_actions": latest_feedback.suggested_actions,
                "quality_scores": latest_feedback.quality_scores,
                "iteration_number": latest_feedback.iteration_number,
            }

        if iteration_state.learnings:
            context["accumulated_learnings"] = list(dict.fromkeys(iteration_state.learnings))

        if validation_feedback is not None:
            context["validation_feedback"] = validation_feedback.model_dump(mode="json")

        return context

    def _get_quality_threshold(self, stage_name: StageName) -> float:
        threshold_field = _STAGE_THRESHOLDS[stage_name]
        return float(getattr(self._settings, threshold_field))


def create_run_iteration_state(
    run_id: str,
    *,
    settings: ReflectionSettings,
    reflection_enabled: bool,
) -> RunIterationState:
    """Create a new run iteration state for managed execution."""
    return RunIterationState(
        run_id=run_id,
        max_cross_stage_iterations=settings.max_cross_stage_iterations,
        reflection_enabled=reflection_enabled,
    )
