from __future__ import annotations

import logging

from hypoforge.domain.schemas import (
    CriticSummary,
    PlannerSummary,
    RetrievalSummary,
    ReviewSummary,
    RunConstraints,
    RunRequest,
    RunResult,
    RunSummary,
    StageStatus,
)
from hypoforge.application.report_renderer import ReportRenderer
from hypoforge.infrastructure.db.repository import RunRepository


class RunCoordinator:
    def __init__(
        self,
        *,
        repository: RunRepository,
        retrieval_agent,
        review_agent,
        critic_agent,
        planner_agent,
        report_renderer: ReportRenderer | None = None,
    ) -> None:
        self._repository = repository
        self._retrieval_agent = retrieval_agent
        self._review_agent = review_agent
        self._critic_agent = critic_agent
        self._planner_agent = planner_agent
        self._report_renderer = report_renderer or ReportRenderer()
        self._logger = logging.getLogger(__name__)

    def run_topic(self, topic: str, constraints: RunConstraints | None = None) -> RunResult:
        request = RunRequest(topic=topic, constraints=constraints or RunConstraints())
        run = self._repository.create_run(request)
        try:
            self._repository.update_run_status(run.run_id, "retrieving")
            self._repository.start_stage(run.run_id, "retrieval")
            self._logger.info("retrieval stage started", extra={"run_id": run.run_id})
            retrieval_summary = self._retrieval_agent(run.run_id, topic, request.constraints)
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
        return run.final_report_md or ""

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
            if summary.coverage_assessment == "low" or summary.needs_broader_search:
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
