from __future__ import annotations

import logging
from copy import deepcopy
from typing import TYPE_CHECKING, Any, Callable

from hypoforge.application.correction_loop import (
    CorrectionLoopController,
    StageExecutionResult,
    create_run_iteration_state,
)
from hypoforge.application.report_renderer import ReportRenderer
from hypoforge.config import ReflectionSettings, ValidationSettings
from hypoforge.domain.schemas import (
    CriticSummary,
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
)
from hypoforge.domain.validation import (
    FeedbackPool,
    ValidationContext,
    ValidationResult,
)
from hypoforge.infrastructure.db.repository import RunRepository

if TYPE_CHECKING:
    from hypoforge.agents.reflection import ReflectionAgent
    from hypoforge.agents.validation_base import ValidationAgentRegistry
    from hypoforge.application.stage_graph import StageNavigator


StageSummary = RetrievalSummary | ReviewSummary | CriticSummary | PlannerSummary


class RunCoordinator:
    """Orchestrates the four-stage hypothesis generation pipeline."""

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
        correction_loop_controller: CorrectionLoopController | None = None,
        run_cleanup: Callable[[str], None] | None = None,
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
        self._run_cleanup = run_cleanup
        self._logger = logging.getLogger(__name__)
        self._correction_loop_controller = (
            correction_loop_controller
            or CorrectionLoopController(
                repository=repository,
                reflection_agent=reflection_agent,
                settings=self._reflection_settings,
            )
        )
        self._agents: dict[StageName, Callable[..., StageSummary]] = {
            "retrieval": retrieval_agent,
            "review": review_agent,
            "critic": critic_agent,
            "planner": planner_agent,
        }
        self._feedback_pools: dict[str, FeedbackPool] = {}

    # ------------------------------------------------------------------
    # Event helpers
    # ------------------------------------------------------------------

    def _emit(self, run_id: str, event: dict) -> None:
        if self._event_bus is not None:
            self._event_bus.publish(run_id, event)

    def _emit_stage_start(self, run_id: str, stage_name: str, attempt: int) -> None:
        self._emit(
            run_id,
            {
                "type": "stage_start",
                "stage_name": stage_name,
                "attempt": attempt,
            },
        )

    def _emit_stage_complete(
        self, run_id: str, stage_name: str, attempt: int, status: str
    ) -> None:
        self._emit(
            run_id,
            {
                "type": "stage_complete",
                "stage_name": stage_name,
                "attempt": attempt,
                "status": status,
            },
        )

    def _emit_run_terminal(
        self, run_id: str, status: str, error: str | None = None
    ) -> None:
        event_type = "run_complete" if status == "done" else "run_error"
        self._emit(
            run_id,
            {
                "type": event_type,
                "status": status,
                "error": error,
            },
        )

    def _get_attempt(self, run_id: str, stage_name: str) -> int:
        if self._event_bus is not None:
            return self._event_bus.record_stage_attempt(run_id, stage_name)
        return self._repository.get_max_stage_attempts(run_id).get(stage_name, 0) + 1

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run_topic(
        self, topic: str, constraints: RunConstraints | None = None
    ) -> RunResult:
        run = self.launch_run(topic, constraints)
        self.execute_run(run.run_id, raise_on_failure=True)
        return self._repository.build_final_result(run.run_id)

    def launch_run(
        self, topic: str, constraints: RunConstraints | None = None
    ) -> RunState:
        request = RunRequest(topic=topic, constraints=constraints or RunConstraints())
        run_state = self._repository.create_run(request)

        reflection_globally_enabled = (
            self._reflection_settings.enable_reflection
            and self._reflection_agent is not None
        )
        validation_globally_enabled = (
            self._validation_settings.enable_validation_agents
            and self._validation_registry is not None
        )
        if reflection_globally_enabled or validation_globally_enabled:
            iteration_state = create_run_iteration_state(
                run_state.run_id,
                settings=self._reflection_settings,
                reflection_enabled=reflection_globally_enabled,
            )
            self._repository.save_iteration_state(run_state.run_id, iteration_state)

        if self._event_bus is not None:
            seed = self._repository.get_max_stage_attempts(run_state.run_id)
            self._event_bus.init_run(run_state.run_id, seed_attempts=seed)

        return run_state

    def execute_run(self, run_id: str, *, raise_on_failure: bool = False) -> RunResult:
        run = self._repository.get_run(run_id)
        request = RunRequest(topic=run.topic, constraints=deepcopy(run.constraints))
        reflection_enabled, validation_enabled = self._feature_flags(run_id)

        if reflection_enabled or validation_enabled:
            return self._execute_managed(
                run_id,
                request,
                raise_on_failure,
                reflection_enabled=reflection_enabled,
                validation_enabled=validation_enabled,
            )
        return self._execute_linear(run_id, request, raise_on_failure)

    def get_run_result(self, run_id: str) -> RunResult:
        result = self._repository.build_final_result(run_id)
        if result.report_markdown and self._report_needs_refresh(
            result.report_markdown,
            result.status,
        ):
            self._render_report(run_id)
            return self._repository.build_final_result(run_id)
        return result

    def list_runs(self) -> list[RunSummary]:
        return self._repository.list_runs()

    def get_trace(self, run_id: str) -> list[dict]:
        return self._repository.list_tool_traces(run_id)

    def get_report_markdown(self, run_id: str) -> str:
        run = self._repository.get_run(run_id)
        report_markdown = run.final_report_md or ""
        if not report_markdown or self._report_needs_refresh(
            report_markdown,
            run.status,
        ):
            return self._render_report(run_id)
        return report_markdown

    def get_reflection_history(
        self,
        run_id: str,
        stage_name: StageName | None = None,
    ) -> list[ReflectionFeedback]:
        return self._repository.load_reflection_history(run_id, stage_name)

    def get_iteration_state(self, run_id: str) -> RunIterationState | None:
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
            planner_summary = self._planner_agent(run_id, execution_context=None)
            self._finish_stage(run_id, "planner", planner_summary, attempt=attempt)
            self._emit_stage_complete(run_id, "planner", attempt, "completed")
            self._repository.update_run_status(run_id, "done", error_message=None)
            self._render_report(run_id)
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
            self._repository.update_run_status(run_id, "failed", error_message=str(exc))
            self._render_partial_report(run_id)
            self._emit_run_terminal(run_id, "failed", error=str(exc))
            self._logger.warning("planner rerun failed", extra={"run_id": run_id})
            raise
        return self._repository.build_final_result(run_id)

    # ------------------------------------------------------------------
    # Managed execution
    # ------------------------------------------------------------------

    def _feature_flags(self, run_id: str) -> tuple[bool, bool]:
        reflection_enabled = (
            self._reflection_settings.enable_reflection
            and self._reflection_agent is not None
            and self._repository.is_reflection_enabled(run_id)
        )
        validation_enabled = (
            self._validation_settings.enable_validation_agents
            and self._validation_registry is not None
        )
        return reflection_enabled, validation_enabled

    def _ensure_iteration_state(
        self,
        run_id: str,
        *,
        reflection_enabled: bool,
        validation_enabled: bool,
    ) -> RunIterationState:
        iteration_state = self._repository.load_iteration_state(run_id)
        if iteration_state is None:
            iteration_state = create_run_iteration_state(
                run_id,
                settings=self._reflection_settings,
                reflection_enabled=reflection_enabled,
            )
        elif reflection_enabled and not iteration_state.reflection_enabled:
            iteration_state.reflection_enabled = True
        if reflection_enabled or validation_enabled:
            self._repository.save_iteration_state(run_id, iteration_state)
        return iteration_state

    def _execute_managed(
        self,
        run_id: str,
        request: RunRequest,
        raise_on_failure: bool,
        *,
        reflection_enabled: bool,
        validation_enabled: bool,
    ) -> RunResult:
        iteration_state = self._ensure_iteration_state(
            run_id,
            reflection_enabled=reflection_enabled,
            validation_enabled=validation_enabled,
        )
        feedback_pool = None
        if validation_enabled:
            feedback_pool = self._feedback_pools.setdefault(
                run_id, FeedbackPool(run_id=run_id)
            )

        current_stage: StageName | None = "retrieval"
        total_validation_backtracks = 0

        try:
            while current_stage is not None:
                pending_validation_feedback = (
                    feedback_pool.get_latest_feedback(current_stage)
                    if feedback_pool is not None
                    else None
                )
                stage_result = self._correction_loop_controller.execute_stage(
                    run_id=run_id,
                    stage_name=current_stage,
                    run_iteration_state=iteration_state,
                    attempt_executor=lambda execution_context, stage_name=current_stage: (
                        self._run_managed_stage_attempt(
                            run_id,
                            stage_name,
                            request,
                            execution_context,
                        )
                    ),
                    validation_feedback=pending_validation_feedback,
                    enable_reflection=reflection_enabled,
                )

                for feedback in stage_result.reflection_feedbacks:
                    self._repository.save_reflection_feedback(run_id, feedback)

                if (
                    feedback_pool is not None
                    and pending_validation_feedback is not None
                ):
                    feedback_pool.consume_feedback(current_stage)

                self._repository.save_iteration_state(run_id, iteration_state)

                if stage_result.backtrack_to is not None:
                    reason = self._reflection_backtrack_reason(stage_result)
                    if self._prepare_backtrack(
                        run_id=run_id,
                        iteration_state=iteration_state,
                        current_stage=current_stage,
                        target_stage=stage_result.backtrack_to,
                        reason=reason,
                        feedback_pool=feedback_pool,
                        record_cross_stage=True,
                    ):
                        self._repository.save_iteration_state(run_id, iteration_state)
                        current_stage = stage_result.backtrack_to
                        continue
                    raise RuntimeError(
                        "reflection backtrack could not be applied: "
                        f"{current_stage} -> {stage_result.backtrack_to}; {reason}"
                    )

                if validation_enabled:
                    validation_results = self._run_validation_agents(
                        run_id=run_id,
                        stage_name=current_stage,
                        request=request,
                        summary=stage_result.summary,
                        iteration_state=iteration_state,
                        feedback_pool=feedback_pool,
                    )
                    backtrack_recommendation = self._get_backtrack_recommendation(
                        validation_results
                    )
                    if backtrack_recommendation is not None:
                        if (
                            feedback_pool is None
                            or total_validation_backtracks
                            >= self._validation_settings.max_total_backtrack
                        ):
                            raise RuntimeError(
                                "validation backtrack could not be applied: "
                                f"{current_stage} -> {backtrack_recommendation.target_stage}; "
                                f"{backtrack_recommendation.reason}"
                            )
                        from hypoforge.agents.feedback_synthesizer import (
                            FeedbackSynthesizer,
                        )

                        synthesizer = FeedbackSynthesizer(
                            repository=self._repository,
                            settings=self._validation_settings,
                        )
                        stage_feedback = synthesizer.create_feedback_for_stage(
                            target_stage=backtrack_recommendation.target_stage,
                            validation_results=validation_results,
                            context=self._build_validation_context(
                                run_id=run_id,
                                current_stage=current_stage,
                                request=request,
                                summary=stage_result.summary,
                                iteration_state=iteration_state,
                                feedback_pool=feedback_pool,
                            ),
                        )
                        feedback_pool.add_feedback(
                            backtrack_recommendation.target_stage, stage_feedback
                        )

                        if self._prepare_backtrack(
                            run_id=run_id,
                            iteration_state=iteration_state,
                            current_stage=current_stage,
                            target_stage=backtrack_recommendation.target_stage,
                            reason=backtrack_recommendation.reason,
                            feedback_pool=feedback_pool,
                            record_cross_stage=backtrack_recommendation.target_stage
                            != current_stage,
                        ):
                            total_validation_backtracks += 1
                            self._repository.save_iteration_state(
                                run_id, iteration_state
                            )
                            current_stage = backtrack_recommendation.target_stage
                            continue

                current_stage = self._get_next_stage(current_stage)

            self._repository.save_iteration_state(run_id, iteration_state)
            self._repository.update_run_status(run_id, "done", error_message=None)
            self._render_report(run_id)
            self._emit_run_terminal(run_id, "done")
        except Exception as exc:
            self._repository.update_run_status(run_id, "failed", error_message=str(exc))
            self._render_partial_report(run_id)
            self._logger.exception("run failed", extra={"run_id": run_id})
            self._emit_run_terminal(run_id, "failed", error=str(exc))
            if raise_on_failure:
                raise
        finally:
            self._feedback_pools.pop(run_id, None)
            if self._run_cleanup is not None:
                self._run_cleanup(run_id)

        return self._repository.build_final_result(run_id)

    def _reflection_backtrack_reason(self, stage_result: StageExecutionResult) -> str:
        if not stage_result.reflection_feedbacks:
            return "reflection requested backtrack"
        latest_feedback = stage_result.reflection_feedbacks[-1]
        return (
            "; ".join(latest_feedback.issues_found[:2])
            or "reflection requested backtrack"
        )

    def _prepare_backtrack(
        self,
        *,
        run_id: str,
        iteration_state: RunIterationState,
        current_stage: StageName,
        target_stage: StageName,
        reason: str,
        feedback_pool: FeedbackPool | None,
        record_cross_stage: bool,
    ) -> bool:
        if record_cross_stage:
            if not iteration_state.can_backtrack():
                return False
            if (
                self._stage_navigator is not None
                and not self._stage_navigator.can_backtrack_to(
                    current_stage, target_stage
                )
            ):
                return False
            iteration_state.record_backtrack(
                from_stage=current_stage,
                to_stage=target_stage,
                reason=reason,
            )

        self._repository.clear_downstream_data(run_id, target_stage)
        iteration_state.clear_downstream_stage_iterations(target_stage)
        if feedback_pool is not None:
            feedback_pool.clear_downstream_feedback(target_stage)
        return True

    def _run_managed_stage_attempt(
        self,
        run_id: str,
        stage_name: StageName,
        request: RunRequest,
        execution_context: dict[str, Any],
    ) -> StageSummary:
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

        try:
            if stage_name == "retrieval":
                summary = self._retrieval_agent(
                    run_id,
                    request.topic,
                    request.constraints,
                    execution_context=execution_context,
                )
            else:
                summary = self._agents[stage_name](
                    run_id, execution_context=execution_context
                )
        except Exception as exc:
            self._repository.finish_stage(
                run_id,
                stage_name,
                attempt=attempt,
                summary={},
                status="failed",
                error_message=str(exc),
            )
            self._emit_stage_complete(run_id, stage_name, attempt, "failed")
            raise

        self._finish_stage(run_id, stage_name, summary, attempt=attempt)
        self._emit_stage_complete(run_id, stage_name, attempt, "completed")
        return summary

    def _run_validation_agents(
        self,
        *,
        run_id: str,
        stage_name: StageName,
        request: RunRequest,
        summary: StageSummary,
        iteration_state: RunIterationState,
        feedback_pool: FeedbackPool | None,
    ) -> list[ValidationResult]:
        if self._validation_registry is None:
            return []

        context = self._build_validation_context(
            run_id=run_id,
            current_stage=stage_name,
            request=request,
            summary=summary,
            iteration_state=iteration_state,
            feedback_pool=feedback_pool,
        )
        validators = self._validation_registry.get_validators(stage_name)
        results: list[ValidationResult] = []
        for validator in validators:
            try:
                result = validator.validate(context)
                results.append(result)
                self._logger.info(
                    "Validation %s completed",
                    validator.validation_type,
                    extra={
                        "run_id": run_id,
                        "stage": stage_name,
                        "valid": result.valid,
                        "score": result.score,
                    },
                )
            except Exception as exc:
                self._logger.warning(
                    "Validation %s failed: %s",
                    validator.validation_type,
                    exc,
                    extra={"run_id": run_id, "stage": stage_name},
                )
                raise
        return results

    def _build_validation_context(
        self,
        *,
        run_id: str,
        current_stage: StageName,
        request: RunRequest,
        summary: StageSummary,
        iteration_state: RunIterationState,
        feedback_pool: FeedbackPool | None,
    ) -> ValidationContext:
        run = self._repository.get_run(run_id)
        stage_iteration = iteration_state.get_stage_state(current_stage)
        return ValidationContext(
            run_id=run_id,
            topic=request.topic,
            current_stage=current_stage,
            iteration_number=stage_iteration.iteration_number,
            previous_feedback=list(feedback_pool.feedback_history)
            if feedback_pool
            else [],
            stage_output=summary.model_dump(),
            selected_paper_ids=run.selected_paper_ids,
            evidence_ids=run.evidence_ids,
            conflict_cluster_ids=run.conflict_cluster_ids,
            hypothesis_ids=run.hypothesis_ids,
        )

    def _get_backtrack_recommendation(
        self,
        validation_results: list[ValidationResult],
    ) -> Any:
        if self._validation_registry is None:
            return None
        return self._validation_registry.get_backtrack_recommendation(
            validation_results
        )

    # ------------------------------------------------------------------
    # Linear execution
    # ------------------------------------------------------------------

    def _run_linear_stage(
        self,
        run_id: str,
        stage_name: StageName,
        request: RunRequest,
    ) -> None:
        summary = self._run_managed_stage_attempt(
            run_id,
            stage_name,
            request,
            execution_context={},
        )
        del summary

    def _execute_linear(
        self,
        run_id: str,
        request: RunRequest,
        raise_on_failure: bool,
    ) -> RunResult:
        try:
            self._run_linear_stage(run_id, "retrieval", request)
            self._run_linear_stage(run_id, "review", request)
            self._run_linear_stage(run_id, "critic", request)
            self._run_linear_stage(run_id, "planner", request)
            self._repository.update_run_status(run_id, "done", error_message=None)
            self._render_report(run_id)
            self._emit_run_terminal(run_id, "done")
        except Exception as exc:
            self._repository.update_run_status(run_id, "failed", error_message=str(exc))
            self._render_partial_report(run_id)
            self._logger.exception("run failed", extra={"run_id": run_id})
            self._emit_run_terminal(run_id, "failed", error=str(exc))
            if raise_on_failure:
                raise
        finally:
            if self._run_cleanup is not None:
                self._run_cleanup(run_id)
        return self._repository.build_final_result(run_id)

    def _render_partial_report(self, run_id: str) -> None:
        result = self._repository.build_final_result(run_id)
        if result.report_markdown and not self._report_needs_refresh(
            result.report_markdown,
            result.status,
        ):
            return
        self._repository.save_report_markdown(
            run_id, self._report_renderer.render(result)
        )

    def _render_report(self, run_id: str) -> str:
        result = self._repository.build_final_result(run_id)
        markdown = self._report_renderer.render(result)
        self._repository.save_report_markdown(run_id, markdown)
        return markdown

    def _report_needs_refresh(self, report_markdown: str, status: str) -> bool:
        expected_status_line = f"- Final status: `{status}`"
        return (
            report_markdown.startswith("# HypoForge Report:")
            or expected_status_line not in report_markdown
        )

    def _finish_stage(
        self,
        run_id: str,
        stage_name: str,
        summary: StageSummary,
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
        stage_order: list[StageName] = ["retrieval", "review", "critic", "planner"]
        try:
            current_idx = stage_order.index(current_stage)
            if current_idx < len(stage_order) - 1:
                return stage_order[current_idx + 1]
        except ValueError:
            pass
        return None
