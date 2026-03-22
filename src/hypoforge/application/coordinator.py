from __future__ import annotations

import asyncio
import logging
from copy import deepcopy
from typing import TYPE_CHECKING, Any, Callable

from hypoforge.domain.schemas import (
    CriticSummary,
    IterationState,
    PlannerSummary,
    ReflectionFeedback,
    RetrievalSummary,
    ReviewSummary,
    RunConstraints,
    RunIterationState,
    RunRequest,
    RunResult,
    RunState,
    RunSummary,
    StageName,
    StageStatus,
)
from hypoforge.domain.validation import (
    FeedbackPool,
    SynthesizedFeedback,
    ValidationContext,
    ValidationResult,
)
from hypoforge.application.report_renderer import ReportRenderer
from hypoforge.config import ReflectionSettings, ValidationSettings
from hypoforge.infrastructure.db.repository import RunRepository

if TYPE_CHECKING:
    from hypoforge.agents.reflection import ReflectionAgent
    from hypoforge.agents.validation_base import ValidationAgentRegistry
    from hypoforge.application.correction_loop import CorrectionLoopController
    from hypoforge.application.stage_graph import StageNavigator


class RunCoordinator:
    """Orchestrates the four-stage hypothesis generation pipeline.

    Stages: retrieval → review → critic → planner. Each stage either
    completes successfully or fails — no degraded/partial fallback paths.

    With reflection enabled, the coordinator supports:
    - Quality evaluation after each stage
    - Iterative re-execution when quality is below threshold
    - Cross-stage backtracking for upstream improvements

    With validation agents enabled, the coordinator supports:
    - Evidence validation after review stage
    - Conflict detection enhancement after critic stage
    - Quality assessment after planner stage
    - Feedback synthesis for iterative improvement
    """

    def __init__(
        self,
        *,
        repository: RunRepository,
        retrieval_agent: Callable[..., RetrievalSummary],
        review_agent: Callable[..., ReviewSummary],
        critic_agent: Callable[..., CriticSummary],
        planner_agent: Callable[..., PlannerSummary],
        report_renderer: ReportRenderer | None = None,
        reflection_agent: ReflectionAgent | None = None,
        reflection_settings: ReflectionSettings | None = None,
        stage_navigator: StageNavigator | None = None,
        validation_registry: ValidationAgentRegistry | None = None,
        validation_settings: ValidationSettings | None = None,
        event_bus: Any | None = None,
    ) -> None:
        self._repository = repository
        self._retrieval_agent = retrieval_agent
        self._review_agent = review_agent
        self._critic_agent = critic_agent
        self._planner_agent = planner_agent
        self._report_renderer = report_renderer or ReportRenderer()
        self._reflection_agent = reflection_agent
        self._reflection_settings = reflection_settings or ReflectionSettings()
        self._stage_navigator = stage_navigator
        self._validation_registry = validation_registry
        self._validation_settings = validation_settings or ValidationSettings()
        self._event_bus = event_bus
        self._logger = logging.getLogger(__name__)

        # Agent mapping for dynamic dispatch
        self._agents: dict[StageName, Callable] = {
            "retrieval": retrieval_agent,
            "review": review_agent,
            "critic": critic_agent,
            "planner": planner_agent,
        }

        # Feedback pools per run
        self._feedback_pools: dict[str, FeedbackPool] = {}

    # ------------------------------------------------------------------
    # Event helpers
    # ------------------------------------------------------------------

    def _emit(self, run_id: str, event: dict) -> None:
        if self._event_bus is not None:
            self._event_bus.publish(run_id, event)

    def _emit_stage_start(self, run_id: str, stage_name: str, attempt: int) -> None:
        self._emit(run_id, {
            "type": "stage_start",
            "stage_name": stage_name,
            "attempt": attempt,
        })

    def _emit_stage_complete(self, run_id: str, stage_name: str, attempt: int, status: str) -> None:
        self._emit(run_id, {
            "type": "stage_complete",
            "stage_name": stage_name,
            "attempt": attempt,
            "status": status,
        })

    def _emit_run_terminal(self, run_id: str, status: str, error: str | None = None) -> None:
        event_type = "run_complete" if status == "done" else "run_error"
        self._emit(run_id, {
            "type": event_type,
            "status": status,
            "error": error,
        })

    def _get_attempt(self, run_id: str, stage_name: str) -> int:
        if self._event_bus is not None:
            return self._event_bus.record_stage_attempt(run_id, stage_name)
        return self._repository.get_max_stage_attempts(run_id).get(stage_name, 0) + 1

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run_topic(self, topic: str, constraints: RunConstraints | None = None) -> RunResult:
        run = self.launch_run(topic, constraints)
        self.execute_run(run.run_id, raise_on_failure=True)
        return self._repository.build_final_result(run.run_id)

    def launch_run(self, topic: str, constraints: RunConstraints | None = None) -> RunState:
        request = RunRequest(topic=topic, constraints=constraints or RunConstraints())
        run_state = self._repository.create_run(request)

        # Initialize reflection state if enabled
        if self._reflection_settings.enable_reflection:
            iteration_state = RunIterationState(
                run_id=run_state.run_id,
                max_cross_stage_iterations=self._reflection_settings.max_cross_stage_iterations,
                reflection_enabled=True,
            )
            self._repository.save_iteration_state(run_state.run_id, iteration_state)

        if self._event_bus is not None:
            seed = self._repository.get_max_stage_attempts(run_state.run_id)
            self._event_bus.init_run(run_state.run_id, seed_attempts=seed)

        return run_state

    def execute_run(self, run_id: str, *, raise_on_failure: bool = False) -> RunResult:
        run = self._repository.get_run(run_id)
        request = RunRequest(topic=run.topic, constraints=deepcopy(run.constraints))

        # Check if reflection is enabled
        reflection_enabled = (
            self._reflection_settings.enable_reflection
            and self._reflection_agent is not None
            and self._repository.is_reflection_enabled(run_id)
        )

        # Check if validation agents are enabled
        validation_enabled = (
            self._validation_settings.enable_validation_agents
            and self._validation_registry is not None
        )

        if reflection_enabled and validation_enabled:
            return self._execute_with_validation(run_id, request, raise_on_failure)
        elif reflection_enabled:
            return self._execute_with_reflection(run_id, request, raise_on_failure)
        else:
            return self._execute_linear(run_id, request, raise_on_failure)

    def _execute_with_reflection(
        self,
        run_id: str,
        request: RunRequest,
        raise_on_failure: bool,
    ) -> RunResult:
        """Execute pipeline with reflection-correction loop."""
        iteration_state = self._repository.load_iteration_state(run_id)
        if iteration_state is None:
            iteration_state = RunIterationState(
                run_id=run_id,
                max_cross_stage_iterations=self._reflection_settings.max_cross_stage_iterations,
                reflection_enabled=True,
            )

        current_stage: StageName | None = "retrieval"

        try:
            while current_stage is not None:
                # Execute stage with reflection
                summary, stage_iter_state = self._execute_stage_with_reflection(
                    run_id=run_id,
                    stage_name=current_stage,
                    request=request,
                    iteration_state=iteration_state,
                )

                # Check for backtracking
                if stage_iter_state.feedback_history:
                    latest_feedback = stage_iter_state.feedback_history[-1]
                    if latest_feedback.should_backtrack() and iteration_state.can_backtrack():
                        backtrack_to = latest_feedback.recommended_backtrack_stage
                        if backtrack_to and self._stage_navigator:
                            self._logger.info(
                                "Backtracking from %s to %s",
                                current_stage,
                                backtrack_to,
                                extra={"run_id": run_id, "reason": latest_feedback.issues_found[:3]},
                            )
                            iteration_state.record_backtrack(
                                from_stage=current_stage,
                                to_stage=backtrack_to,
                                reason="; ".join(latest_feedback.issues_found[:2]),
                            )
                            self._repository.save_reflection_feedback(run_id, latest_feedback)
                            self._repository.clear_downstream_data(run_id, backtrack_to)
                            current_stage = backtrack_to
                            continue

                # Save feedback
                if stage_iter_state.feedback_history:
                    self._repository.save_reflection_feedback(
                        run_id, stage_iter_state.feedback_history[-1]
                    )

                # Move to next stage
                current_stage = self._get_next_stage(current_stage)

            # Save final iteration state
            self._repository.save_iteration_state(run_id, iteration_state)
            self._repository.update_run_status(run_id, "done", error_message=None)
            self._emit_run_terminal(run_id, "done")

        except Exception as exc:
            self._repository.update_run_status(run_id, "failed", error_message=str(exc))
            self._render_partial_report(run_id)
            self._logger.exception("run failed", extra={"run_id": run_id})
            self._emit_run_terminal(run_id, "failed", error=str(exc))
            if raise_on_failure:
                raise

        return self._repository.build_final_result(run_id)

    def _execute_with_validation(
        self,
        run_id: str,
        request: RunRequest,
        raise_on_failure: bool,
    ) -> RunResult:
        """Execute pipeline with validation agents and feedback synthesis."""
        iteration_state = self._repository.load_iteration_state(run_id)
        if iteration_state is None:
            iteration_state = RunIterationState(
                run_id=run_id,
                max_cross_stage_iterations=self._reflection_settings.max_cross_stage_iterations,
                reflection_enabled=True,
            )

        # Initialize feedback pool
        if run_id not in self._feedback_pools:
            self._feedback_pools[run_id] = FeedbackPool(run_id=run_id)

        feedback_pool = self._feedback_pools[run_id]
        current_stage: StageName | None = "retrieval"
        total_backtracks = 0

        try:
            while current_stage is not None:
                # Execute stage
                summary = self._execute_stage_with_validation(
                    run_id=run_id,
                    stage_name=current_stage,
                    request=request,
                    feedback_pool=feedback_pool,
                )

                # Run validation agents for this stage
                validation_results = asyncio.run(self._run_validation_agents(
                    run_id=run_id,
                    stage_name=current_stage,
                    request=request,
                    feedback_pool=feedback_pool,
                ))

                # Check for backtracking from validation
                backtrack_recommendation = self._get_backtrack_recommendation(validation_results)

                if backtrack_recommendation and total_backtracks < self._validation_settings.max_total_backtrack:
                    target_stage = backtrack_recommendation.target_stage
                    self._logger.info(
                        "Validation-triggered backtrack from %s to %s",
                        current_stage,
                        target_stage,
                        extra={"run_id": run_id, "reason": backtrack_recommendation.reason},
                    )

                    # Synthesize feedback for target stage
                    if self._validation_registry:
                        from hypoforge.agents.feedback_synthesizer import FeedbackSynthesizer
                        synthesizer = FeedbackSynthesizer(
                            repository=self._repository,
                            settings=self._validation_settings,
                        )
                        stage_feedback = synthesizer.create_feedback_for_stage(
                            target_stage=target_stage,
                            validation_results=validation_results,
                            context=self._build_validation_context(run_id, current_stage, request),
                        )
                        feedback_pool.add_feedback(stage_feedback)

                    # Clear downstream data
                    self._repository.clear_downstream_data(run_id, target_stage)
                    total_backtracks += 1
                    current_stage = target_stage
                    continue

                # Move to next stage
                current_stage = self._get_next_stage(current_stage)

            # Save final state
            self._repository.save_iteration_state(run_id, iteration_state)
            self._repository.update_run_status(run_id, "done", error_message=None)
            self._emit_run_terminal(run_id, "done")

        except Exception as exc:
            self._repository.update_run_status(run_id, "failed", error_message=str(exc))
            self._render_partial_report(run_id)
            self._logger.exception("run failed with validation", extra={"run_id": run_id})
            self._emit_run_terminal(run_id, "failed", error=str(exc))
            if raise_on_failure:
                raise
        finally:
            # Clean up feedback pool to prevent memory leak
            if run_id in self._feedback_pools:
                del self._feedback_pools[run_id]

        return self._repository.build_final_result(run_id)

    def _execute_stage_with_validation(
        self,
        run_id: str,
        stage_name: StageName,
        request: RunRequest,
        feedback_pool: FeedbackPool,
    ) -> RetrievalSummary | ReviewSummary | CriticSummary | PlannerSummary:
        """Execute a single stage with validation-aware context."""
        # Map status to run status
        status_map = {
            "retrieval": "retrieving",
            "review": "reviewing",
            "critic": "criticizing",
            "planner": "planning",
        }
        attempt = self._get_attempt(run_id, stage_name)
        self._repository.update_run_status(run_id, status_map[stage_name])
        self._repository.start_stage(run_id, stage_name, attempt)
        self._emit_stage_start(run_id, stage_name, attempt)

        self._logger.info(
            f"{stage_name} stage started (with validation)",
            extra={"run_id": run_id},
        )

        # Build context with feedback
        context: dict = {"run_id": run_id}
        if stage_name == "retrieval":
            context["topic"] = request.topic
            context["constraints"] = request.constraints.model_dump()

        # Inject accumulated feedback
        latest_feedback = feedback_pool.get_latest_feedback()
        if latest_feedback:
            context["validation_feedback"] = {
                "avoid_patterns": latest_feedback.avoid_patterns,
                "focus_areas": latest_feedback.focus_areas,
                "priority_issues": [i.description for i in latest_feedback.priority_issues[:3]],
            }

        # Execute agent
        agent_fn = self._agents[stage_name]
        try:
            if stage_name == "retrieval":
                summary = agent_fn(run_id, request.topic, request.constraints)
            else:
                summary = agent_fn(run_id)
        except Exception as exc:
            self._repository.finish_stage(
                run_id, stage_name, attempt=attempt, summary={}, status="failed", error_message=str(exc)
            )
            self._emit_stage_complete(run_id, stage_name, attempt, "failed")
            raise

        self._finish_stage(run_id, stage_name, summary, attempt=attempt)
        self._emit_stage_complete(run_id, stage_name, attempt, "completed")
        return summary

    async def _run_validation_agents(
        self,
        run_id: str,
        stage_name: StageName,
        request: RunRequest,
        feedback_pool: FeedbackPool,
    ) -> list[ValidationResult]:
        """Run validation agents for a stage."""
        if not self._validation_registry:
            return []

        context = self._build_validation_context(run_id, stage_name, request)
        validators = self._validation_registry.get_validators(stage_name)

        results = []
        for validator in validators:
            try:
                result = await validator.validate(context)
                results.append(result)
                self._logger.info(
                    f"Validation {validator.validation_type} completed",
                    extra={
                        "run_id": run_id,
                        "stage": stage_name,
                        "valid": result.valid,
                        "score": result.score,
                    },
                )
            except Exception as exc:
                self._logger.warning(
                    f"Validation {validator.validation_type} failed: {exc}",
                    extra={"run_id": run_id, "stage": stage_name},
                )
                raise

        return results

    def _build_validation_context(
        self,
        run_id: str,
        current_stage: StageName,
        request: RunRequest,
    ) -> ValidationContext:
        """Build validation context for a stage."""
        run = self._repository.get_run(run_id)
        feedback_pool = self._feedback_pools.get(run_id)

        return ValidationContext(
            run_id=run_id,
            topic=request.topic,
            current_stage=current_stage,
            previous_feedback=feedback_pool.feedback_history if feedback_pool else [],
            selected_paper_ids=run.selected_paper_ids,
            evidence_ids=run.evidence_ids,
            conflict_cluster_ids=run.conflict_cluster_ids,
            hypothesis_ids=run.hypothesis_ids,
        )

    def _get_backtrack_recommendation(
        self,
        validation_results: list[ValidationResult],
    ) -> Any:
        """Get the highest priority backtrack recommendation from validation results."""
        if not self._validation_registry:
            return None
        return self._validation_registry.get_backtrack_recommendation(validation_results)

    def _execute_stage_with_reflection(
        self,
        run_id: str,
        stage_name: StageName,
        request: RunRequest,
        iteration_state: RunIterationState,
    ) -> tuple[RetrievalSummary | ReviewSummary | CriticSummary | PlannerSummary, IterationState]:
        """Execute a single stage with reflection evaluation."""
        stage_iter_state = iteration_state.get_stage_state(stage_name)
        stage_iter_state.max_iterations = self._reflection_settings.max_stage_iterations

        # Map status to run status
        status_map = {
            "retrieval": "retrieving",
            "review": "reviewing",
            "critic": "criticizing",
            "planner": "planning",
        }
        attempt = self._get_attempt(run_id, stage_name)
        self._repository.update_run_status(run_id, status_map[stage_name])
        self._repository.start_stage(run_id, stage_name, attempt)
        self._emit_stage_start(run_id, stage_name, attempt)

        self._logger.info(
            f"{stage_name} stage started",
            extra={"run_id": run_id, "iteration": stage_iter_state.iteration_number},
        )

        # Build context for agent
        context: dict = {"run_id": run_id}
        if stage_name == "retrieval":
            context["topic"] = request.topic
            context["constraints"] = request.constraints.model_dump()

        # Inject previous feedback if retrying
        if stage_iter_state.feedback_history:
            latest_feedback = stage_iter_state.feedback_history[-1]
            context["previous_iteration_feedback"] = {
                "issues_found": latest_feedback.issues_found,
                "suggested_actions": latest_feedback.suggested_actions,
                "iteration_number": latest_feedback.iteration_number,
            }

        # Execute agent
        agent_fn = self._agents[stage_name]
        try:
            if stage_name == "retrieval":
                summary = agent_fn(run_id, request.topic, request.constraints)
            else:
                summary = agent_fn(run_id)
        except Exception as exc:
            self._repository.finish_stage(
                run_id, stage_name, attempt=attempt, summary={}, status="failed", error_message=str(exc)
            )
            self._emit_stage_complete(run_id, stage_name, attempt, "failed")
            raise

        # Evaluate quality
        if self._reflection_agent:
            reflection_summary = self._reflection_agent.evaluate_stage(
                run_id=run_id,
                stage_name=stage_name,
                iteration_state=stage_iter_state,
                stage_output=summary.model_dump(),
            )

            stage_iter_state.current_quality_score = reflection_summary.quality_score

            # Create feedback
            feedback = self._reflection_agent.create_feedback(
                summary=reflection_summary,
                iteration_number=stage_iter_state.iteration_number,
            )
            stage_iter_state.add_feedback(feedback)

            # Update status
            if reflection_summary.meets_threshold:
                stage_iter_state.status = "quality_threshold_met"
            elif not stage_iter_state.can_iterate():
                stage_iter_state.status = "max_iterations_reached"

        # Finish stage
        self._finish_stage(run_id, stage_name, summary, attempt=attempt)
        self._emit_stage_complete(run_id, stage_name, attempt, "completed")

        return summary, stage_iter_state

    def _run_linear_stage(
        self,
        run_id: str,
        stage_name: StageName,
        agent_fn: Callable,
        *agent_args: object,
    ) -> None:
        """Execute a single stage in linear mode with proper fail-fast bookkeeping."""
        status_map = {
            "retrieval": "retrieving",
            "review": "reviewing",
            "critic": "criticizing",
            "planner": "planning",
        }
        attempt = self._get_attempt(run_id, stage_name)
        self._repository.update_run_status(run_id, status_map[stage_name])
        self._repository.start_stage(run_id, stage_name, attempt)
        self._emit_stage_start(run_id, stage_name, attempt)
        self._logger.info(f"{stage_name} stage started", extra={"run_id": run_id})
        try:
            summary = agent_fn(*agent_args)
        except Exception as exc:
            self._repository.finish_stage(
                run_id, stage_name, attempt=attempt,
                summary={}, status="failed", error_message=str(exc),
            )
            self._emit_stage_complete(run_id, stage_name, attempt, "failed")
            raise
        self._finish_stage(run_id, stage_name, summary, attempt=attempt)
        self._emit_stage_complete(run_id, stage_name, attempt, "completed")

    def _execute_linear(
        self,
        run_id: str,
        request: RunRequest,
        raise_on_failure: bool,
    ) -> RunResult:
        """Execute pipeline without reflection (original linear flow)."""
        run = self._repository.get_run(run_id)
        try:
            self._run_linear_stage(run.run_id, "retrieval", self._retrieval_agent, run.run_id, request.topic, request.constraints)
            self._run_linear_stage(run.run_id, "review", self._review_agent, run.run_id)
            self._run_linear_stage(run.run_id, "critic", self._critic_agent, run.run_id)
            self._run_linear_stage(run.run_id, "planner", self._planner_agent, run.run_id)
            self._repository.update_run_status(run.run_id, "done", error_message=None)
            self._emit_run_terminal(run.run_id, "done")
        except Exception as exc:
            self._repository.update_run_status(
                run.run_id,
                "failed",
                error_message=str(exc),
            )
            self._render_partial_report(run.run_id)
            self._logger.exception("run failed", extra={"run_id": run.run_id})
            self._emit_run_terminal(run.run_id, "failed", error=str(exc))
            if raise_on_failure:
                raise
        return self._repository.build_final_result(run.run_id)

    def get_run_result(self, run_id: str) -> RunResult:
        return self._repository.build_final_result(run_id)

    def list_runs(self) -> list[RunSummary]:
        return self._repository.list_runs()

    def get_trace(self, run_id: str) -> list[dict]:
        return self._repository.list_tool_traces(run_id)

    def get_report_markdown(self, run_id: str) -> str:
        run = self._repository.get_run(run_id)
        report_markdown = run.final_report_md or ""
        if not report_markdown or report_markdown.startswith("# HypoForge Report:"):
            refreshed = self._report_renderer.render(self._repository.build_final_result(run_id))
            self._repository.save_report_markdown(run_id, refreshed)
            return refreshed
        return report_markdown

    def get_reflection_history(
        self,
        run_id: str,
        stage_name: StageName | None = None,
    ) -> list[ReflectionFeedback]:
        """Get reflection feedback history for a run."""
        return self._repository.load_reflection_history(run_id, stage_name)

    def get_iteration_state(self, run_id: str) -> RunIterationState | None:
        """Get the iteration state for a run."""
        return self._repository.load_iteration_state(run_id)

    def rerun_planner(self, run_id: str) -> RunResult:
        self._repository.get_run(run_id)
        if not self._repository.load_evidence_cards(run_id):
            raise RuntimeError(f"planner rerun requires evidence cards: {run_id}")

        if self._event_bus is not None:
            seed = self._repository.get_max_stage_attempts(run_id)
            self._event_bus.init_rerun_planner(run_id, seed_attempts=seed)

        attempt = self._get_attempt(run_id, "planner")
        self._repository.update_run_status(run_id, "planning", error_message=None)
        self._repository.start_stage(run_id, "planner", attempt)
        self._emit_stage_start(run_id, "planner", attempt)
        self._logger.info("planner rerun started", extra={"run_id": run_id})
        try:
            planner_summary = self._planner_agent(run_id)
            self._finish_stage(run_id, "planner", planner_summary, attempt=attempt)
            self._emit_stage_complete(run_id, "planner", attempt, "completed")
            self._repository.update_run_status(run_id, "done", error_message=None)
            self._emit_run_terminal(run_id, "done")
        except Exception as exc:
            self._repository.finish_stage(
                run_id,
                "planner",
                attempt=attempt,
                summary={},
                status="failed",
                error_message=str(exc),
            )
            self._emit_stage_complete(run_id, "planner", attempt, "failed")
            self._repository.update_run_status(
                run_id,
                "failed",
                error_message=str(exc),
            )
            self._render_partial_report(run_id)
            self._emit_run_terminal(run_id, "failed", error=str(exc))
            self._logger.warning("planner rerun failed", extra={"run_id": run_id})
            raise
        return self._repository.build_final_result(run_id)

    def _render_partial_report(self, run_id: str) -> None:
        result = self._repository.build_final_result(run_id)
        if result.report_markdown:
            return
        self._repository.save_report_markdown(run_id, self._report_renderer.render(result))

    def _finish_stage(
        self,
        run_id: str,
        stage_name: str,
        summary: RetrievalSummary | ReviewSummary | CriticSummary | PlannerSummary,
        *,
        attempt: int = 1,
    ) -> None:
        payload = summary.model_dump()
        self._repository.finish_stage(
            run_id,
            stage_name,
            attempt=attempt,
            summary=payload,
            status="completed",
        )
        self._logger.info(
            "%s stage completed",
            stage_name,
            extra={"run_id": run_id, "summary": payload},
        )

    def _get_next_stage(self, current_stage: StageName) -> StageName | None:
        """Get the next stage in the pipeline."""
        stage_order: list[StageName] = ["retrieval", "review", "critic", "planner"]
        try:
            current_idx = stage_order.index(current_stage)
            if current_idx < len(stage_order) - 1:
                return stage_order[current_idx + 1]
        except ValueError:
            pass
        return None
