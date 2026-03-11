"""Correction Loop Controller for the reflection-correction system.

This module provides the CorrectionLoopController that manages iterative
execution with quality evaluation and feedback injection.
"""

from __future__ import annotations

import logging
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

if TYPE_CHECKING:
    from hypoforge.agents.reflection import ReflectionAgent
    from hypoforge.infrastructure.db.repository import RunRepository


logger = logging.getLogger(__name__)


# Type aliases for agent functions
AgentFn = Callable[..., RetrievalSummary | ReviewSummary | CriticSummary | PlannerSummary]


class CorrectionLoopController:
    """Controls the reflection-correction loop for pipeline stages.

    This controller manages:
    - Iterative stage execution with quality checks
    - Feedback injection between iterations
    - Cross-stage backtracking
    - State persistence for iteration tracking
    """

    def __init__(
        self,
        *,
        repository: RunRepository,
        reflection_agent: ReflectionAgent,
        settings: ReflectionSettings,
    ) -> None:
        self._repository = repository
        self._reflection_agent = reflection_agent
        self._settings = settings
        self._logger = logging.getLogger(__name__)

    def should_iterate(
        self,
        iteration_state: IterationState,
        quality_score: float | None,
    ) -> bool:
        """Determine if another iteration is needed.

        Args:
            iteration_state: Current iteration state for the stage
            quality_score: Current quality score (None if not yet evaluated)

        Returns:
            True if another iteration should be performed
        """
        if not self._settings.enable_reflection:
            return False

        # Check iteration limit
        if iteration_state.iteration_number >= iteration_state.max_iterations:
            self._logger.info(
                "Max iterations reached",
                extra={
                    "stage": iteration_state.stage_name,
                    "iterations": iteration_state.iteration_number,
                },
            )
            return False

        # Check quality threshold
        if quality_score is not None and quality_score >= iteration_state.quality_threshold:
            self._logger.info(
                "Quality threshold met",
                extra={
                    "stage": iteration_state.stage_name,
                    "score": quality_score,
                    "threshold": iteration_state.quality_threshold,
                },
            )
            return False

        return True

    def execute_with_reflection(
        self,
        run_id: str,
        stage_name: StageName,
        agent_fn: AgentFn,
        run_iteration_state: RunIterationState,
        agent_kwargs: dict[str, Any] | None = None,
    ) -> tuple[RetrievalSummary | ReviewSummary | CriticSummary | PlannerSummary, IterationState]:
        """Execute a stage with reflection and potential re-execution.

        This method runs the agent, evaluates quality, and iterates if needed.

        Args:
            run_id: The run identifier
            stage_name: The stage being executed
            agent_fn: The agent function to execute
            run_iteration_state: The overall run iteration state
            agent_kwargs: Additional keyword arguments for the agent

        Returns:
            Tuple of (final_summary, final_iteration_state)
        """
        agent_kwargs = agent_kwargs or {}
        iteration_state = run_iteration_state.get_stage_state(stage_name)

        # Get quality threshold for this stage
        quality_threshold = self._get_quality_threshold(stage_name)
        iteration_state.quality_threshold = quality_threshold
        iteration_state.max_iterations = self._settings.max_stage_iterations

        # Build context with any previous feedback
        context = self._build_execution_context(
            run_id=run_id,
            stage_name=stage_name,
            iteration_state=iteration_state,
        )

        # Execute the agent
        iteration_state.status = "in_progress"
        summary = agent_fn(**{**agent_kwargs, **context})

        # Evaluate quality
        stage_output = summary.model_dump()
        reflection_summary = self._reflection_agent.evaluate_stage(
            run_id=run_id,
            stage_name=stage_name,
            iteration_state=iteration_state,
            stage_output=stage_output,
        )

        iteration_state.current_quality_score = reflection_summary.quality_score

        # Create and store feedback
        feedback = self._reflection_agent.create_feedback(
            summary=reflection_summary,
            iteration_number=iteration_state.iteration_number,
        )
        iteration_state.add_feedback(feedback)

        # Determine if iteration is needed
        if not reflection_summary.meets_threshold and iteration_state.can_iterate():
            self._logger.info(
                "Quality below threshold, will iterate",
                extra={
                    "run_id": run_id,
                    "stage": stage_name,
                    "score": reflection_summary.quality_score,
                    "iteration": iteration_state.iteration_number,
                },
            )
            # Note: actual re-execution is handled by the coordinator
            # This just records the state
            iteration_state.status = "in_progress"
        elif reflection_summary.meets_threshold:
            iteration_state.status = "quality_threshold_met"
        else:
            iteration_state.status = "max_iterations_reached"

        return summary, iteration_state

    def handle_cross_stage_backtrack(
        self,
        run_id: str,
        from_stage: StageName,
        to_stage: StageName,
        run_iteration_state: RunIterationState,
        reason: str,
    ) -> bool:
        """Handle cross-stage backtracking.

        Args:
            run_id: The run identifier
            from_stage: The current stage that triggered backtrack
            to_stage: The target stage to backtrack to
            run_iteration_state: The overall run iteration state
            reason: The reason for backtracking

        Returns:
            True if backtracking was successful, False if not allowed
        """
        if not run_iteration_state.can_backtrack():
            self._logger.warning(
                "Cross-stage backtracking limit reached",
                extra={
                    "run_id": run_id,
                    "from_stage": from_stage,
                    "to_stage": to_stage,
                },
            )
            return False

        # Record the backtrack
        run_iteration_state.record_backtrack(
            from_stage=from_stage,
            to_stage=to_stage,
            reason=reason,
        )

        # Mark downstream data as needing re-validation
        self._mark_downstream_for_validation(
            run_id=run_id,
            from_stage=from_stage,
            to_stage=to_stage,
        )

        self._logger.info(
            "Cross-stage backtrack recorded",
            extra={
                "run_id": run_id,
                "from_stage": from_stage,
                "to_stage": to_stage,
                "cross_iteration": run_iteration_state.cross_stage_iterations,
            },
        )

        return True

    def _inject_feedback(
        self,
        stage_name: StageName,
        iteration_state: IterationState,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """Inject feedback from previous iterations into context.

        Args:
            stage_name: The stage being executed
            iteration_state: Current iteration state
            context: The execution context to enhance

        Returns:
            Enhanced context with feedback incorporated
        """
        if not iteration_state.feedback_history:
            return context

        # Get the most recent feedback
        latest_feedback = iteration_state.feedback_history[-1]

        # Add feedback to context
        enhanced_context = dict(context)
        enhanced_context["previous_iteration_feedback"] = {
            "issues_found": latest_feedback.issues_found,
            "suggested_actions": latest_feedback.suggested_actions,
            "quality_scores": latest_feedback.quality_scores,
            "iteration_number": latest_feedback.iteration_number,
        }

        # Add accumulated learnings
        if iteration_state.learnings:
            enhanced_context["accumulated_learnings"] = iteration_state.learnings

        return enhanced_context

    def _build_execution_context(
        self,
        run_id: str,
        stage_name: StageName,
        iteration_state: IterationState,
    ) -> dict[str, Any]:
        """Build execution context for an agent.

        Args:
            run_id: The run identifier
            stage_name: The stage being executed
            iteration_state: Current iteration state

        Returns:
            Context dictionary for agent execution
        """
        context: dict[str, Any] = {
            "run_id": run_id,
            "iteration_number": iteration_state.iteration_number,
            "is_retry": iteration_state.iteration_number > 1,
        }

        # Inject feedback if this is a retry
        if iteration_state.iteration_number > 1:
            context = self._inject_feedback(
                stage_name=stage_name,
                iteration_state=iteration_state,
                context=context,
            )

        return context

    def _get_quality_threshold(self, stage_name: StageName) -> float:
        """Get the quality threshold for a stage."""
        thresholds = {
            "retrieval": self._settings.retrieval_quality_threshold,
            "review": self._settings.review_quality_threshold,
            "critic": self._settings.critic_quality_threshold,
            "planner": self._settings.planner_quality_threshold,
        }
        return thresholds.get(stage_name, 0.5)

    def _mark_downstream_for_validation(
        self,
        run_id: str,
        from_stage: StageName,
        to_stage: StageName,
    ) -> None:
        """Mark downstream data as needing validation after backtracking.

        This method doesn't actually delete data but records that
        certain data should be re-validated. The actual handling
        is done by the StageNavigator.
        """
        # Stages in order
        stage_order = ["retrieval", "review", "critic", "planner"]

        from_idx = stage_order.index(from_stage)
        to_idx = stage_order.index(to_stage)

        # Mark stages between to_stage and from_stage as needing re-execution
        stages_to_validate = stage_order[to_idx:from_idx]

        self._logger.info(
            "Marking stages for validation after backtrack",
            extra={
                "run_id": run_id,
                "stages": stages_to_validate,
            },
        )


def create_iteration_state(
    run_id: str,
    stage_name: StageName,
    settings: ReflectionSettings,
) -> IterationState:
    """Create a new iteration state for a stage.

    Args:
        run_id: The run identifier
        stage_name: The stage name
        settings: Reflection settings

    Returns:
        New IterationState instance
    """
    thresholds = {
        "retrieval": settings.retrieval_quality_threshold,
        "review": settings.review_quality_threshold,
        "critic": settings.critic_quality_threshold,
        "planner": settings.planner_quality_threshold,
    }

    return IterationState(
        run_id=run_id,
        stage_name=stage_name,
        max_iterations=settings.max_stage_iterations,
        quality_threshold=thresholds.get(stage_name, 0.5),
    )


def create_run_iteration_state(
    run_id: str,
    settings: ReflectionSettings,
) -> RunIterationState:
    """Create a new run iteration state.

    Args:
        run_id: The run identifier
        settings: Reflection settings

    Returns:
        New RunIterationState instance
    """
    return RunIterationState(
        run_id=run_id,
        max_cross_stage_iterations=settings.max_cross_stage_iterations,
        reflection_enabled=settings.enable_reflection,
    )
