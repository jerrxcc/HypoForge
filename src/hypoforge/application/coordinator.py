from __future__ import annotations

import logging
from copy import deepcopy
from typing import TYPE_CHECKING, Callable

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
from hypoforge.application.report_renderer import ReportRenderer
from hypoforge.config import ReflectionSettings
from hypoforge.infrastructure.db.repository import RunRepository

if TYPE_CHECKING:
    from hypoforge.agents.reflection import ReflectionAgent
    from hypoforge.application.correction_loop import CorrectionLoopController
    from hypoforge.application.stage_graph import StageNavigator


class RunCoordinator:
    """Orchestrates the four-stage hypothesis generation pipeline.

    Stages: retrieval → review → critic → planner. Each stage can
    degrade gracefully when the agent encounters an error, preserving
    partial results so that downstream stages still have data to work with.

    With reflection enabled, the coordinator supports:
    - Quality evaluation after each stage
    - Iterative re-execution when quality is below threshold
    - Cross-stage backtracking for upstream improvements
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
        self._logger = logging.getLogger(__name__)

        # Agent mapping for dynamic dispatch
        self._agents: dict[StageName, Callable] = {
            "retrieval": retrieval_agent,
            "review": review_agent,
            "critic": critic_agent,
            "planner": planner_agent,
        }

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

        if reflection_enabled:
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

        stage_order: list[StageName] = ["retrieval", "review", "critic", "planner"]
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

        except Exception as exc:
            self._repository.update_run_status(run_id, "failed", error_message=str(exc))
            self._render_partial_report(run_id)
            self._logger.exception("run failed", extra={"run_id": run_id})
            if raise_on_failure:
                raise RuntimeError(f"run failed: {run_id}") from exc

        return self._repository.build_final_result(run_id)

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
        self._repository.update_run_status(run_id, status_map[stage_name])
        self._repository.start_stage(run_id, stage_name)

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
            degraded_summary = self._create_degraded_summary(stage_name, str(exc))
            self._repository.finish_stage(
                run_id, stage_name, summary=degraded_summary, status="degraded", error_message=str(exc)
            )
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
        self._finish_stage(run_id, stage_name, summary)

        return summary, stage_iter_state

    def _execute_linear(
        self,
        run_id: str,
        request: RunRequest,
        raise_on_failure: bool,
    ) -> RunResult:
        """Execute pipeline without reflection (original linear flow)."""
        run = self._repository.get_run(run_id)
        try:
            self._repository.update_run_status(run.run_id, "retrieving")
            self._repository.start_stage(run.run_id, "retrieval")
            self._logger.info("retrieval stage started", extra={"run_id": run.run_id})
            retrieval_summary = self._retrieval_agent(run.run_id, request.topic, request.constraints)
            self._finish_stage(run.run_id, "retrieval", retrieval_summary)

            self._repository.update_run_status(run.run_id, "reviewing")
            self._repository.start_stage(run.run_id, "review")
            self._logger.info("review stage started", extra={"run_id": run.run_id})
            try:
                review_summary = self._review_agent(run.run_id)
                self._finish_stage(run.run_id, "review", review_summary)
            except Exception as exc:
                if not self._repository.load_evidence_cards(run.run_id):
                    self._repository.finish_stage(
                        run.run_id,
                        "review",
                        summary={},
                        status="failed",
                        error_message=str(exc),
                    )
                    raise
                degraded_summary = {
                    "evidence_cards_created": len(self._repository.load_evidence_cards(run.run_id)),
                    "coverage_summary": "partial review results retained after stage degradation",
                }
                self._repository.finish_stage(
                    run.run_id,
                    "review",
                    summary=degraded_summary,
                    status="degraded",
                    error_message=str(exc),
                )
                self._logger.warning("review stage degraded", extra={"run_id": run.run_id})

            self._repository.update_run_status(run.run_id, "criticizing")
            self._repository.start_stage(run.run_id, "critic")
            self._logger.info("critic stage started", extra={"run_id": run.run_id})
            try:
                critic_summary = self._critic_agent(run.run_id)
                self._finish_stage(run.run_id, "critic", critic_summary)
            except Exception as exc:
                self._repository.finish_stage(
                    run.run_id,
                    "critic",
                    summary={},
                    status="degraded",
                    error_message=str(exc),
                )
                self._logger.warning("critic stage degraded", extra={"run_id": run.run_id})

            self._repository.update_run_status(run.run_id, "planning")
            self._repository.start_stage(run.run_id, "planner")
            self._logger.info("planner stage started", extra={"run_id": run.run_id})
            try:
                planner_summary = self._planner_agent(run.run_id)
                self._finish_stage(run.run_id, "planner", planner_summary)
            except Exception as exc:
                self._repository.finish_stage(
                    run.run_id,
                    "planner",
                    summary={},
                    status="degraded",
                    error_message=str(exc),
                )
                self._logger.warning("planner stage degraded", extra={"run_id": run.run_id})
                self._render_partial_report(run.run_id)
                self._repository.update_run_status(
                    run.run_id,
                    "failed",
                    error_message="planner unavailable",
                )
                return self._repository.build_final_result(run.run_id)

            self._repository.update_run_status(run.run_id, "done", error_message=None)
        except Exception as exc:
            self._repository.update_run_status(
                run.run_id,
                "failed",
                error_message=str(exc),
            )
            self._render_partial_report(run.run_id)
            self._logger.exception("run failed", extra={"run_id": run.run_id})
            if raise_on_failure:
                raise RuntimeError(f"run failed: {run.run_id}") from exc
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

        self._repository.update_run_status(run_id, "planning", error_message=None)
        self._repository.start_stage(run_id, "planner")
        self._logger.info("planner rerun started", extra={"run_id": run_id})
        try:
            planner_summary = self._planner_agent(run_id)
            self._finish_stage(run_id, "planner", planner_summary)
            self._repository.update_run_status(run_id, "done", error_message=None)
        except Exception as exc:
            self._repository.finish_stage(
                run_id,
                "planner",
                summary={},
                status="degraded",
                error_message=str(exc),
            )
            self._repository.update_run_status(
                run_id,
                "failed",
                error_message="planner unavailable",
            )
            self._render_partial_report(run_id)
            self._logger.warning("planner rerun degraded", extra={"run_id": run_id})
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
    ) -> None:
        payload = summary.model_dump()
        self._repository.finish_stage(
            run_id,
            stage_name,
            summary=payload,
            status=self._stage_status(summary),
        )
        self._logger.info(
            "%s stage completed",
            stage_name,
            extra={"run_id": run_id, "summary": payload},
        )

    def _stage_status(
        self,
        summary: RetrievalSummary | ReviewSummary | CriticSummary | PlannerSummary,
    ) -> StageStatus:
        if isinstance(summary, RetrievalSummary):
            if summary.coverage_assessment == "low":
                return "degraded"
        if isinstance(summary, ReviewSummary):
            if summary.failed_paper_ids:
                return "degraded"
        if isinstance(summary, CriticSummary):
            if any("budget exceeded" in note for note in summary.critic_notes):
                return "degraded"
        if isinstance(summary, PlannerSummary):
            if any("budget exceeded" in note for note in summary.planner_notes):
                return "degraded"
        return "completed"

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

    def _create_degraded_summary(
        self,
        stage_name: StageName,
        error_message: str,
    ) -> dict:
        """Create a degraded summary for a failed stage."""
        if stage_name == "retrieval":
            return {
                "canonical_topic": "",
                "query_variants_used": [],
                "search_notes": [f"Stage degraded: {error_message}"],
                "selected_paper_ids": [],
                "excluded_paper_ids": [],
                "coverage_assessment": "low",
                "needs_broader_search": True,
            }
        elif stage_name == "review":
            return {
                "papers_processed": 0,
                "evidence_cards_created": 0,
                "coverage_summary": f"Stage degraded: {error_message}",
                "dominant_axes": [],
                "low_confidence_paper_ids": [],
                "failed_paper_ids": [],
            }
        elif stage_name == "critic":
            return {
                "clusters_created": 0,
                "top_axes": [],
                "critic_notes": [f"Stage degraded: {error_message}"],
            }
        elif stage_name == "planner":
            return {
                "hypotheses_created": 0,
                "report_rendered": False,
                "top_axes": [],
                "planner_notes": [f"Stage degraded: {error_message}"],
            }
        return {}
