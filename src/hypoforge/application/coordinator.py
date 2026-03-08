from __future__ import annotations

import logging

from hypoforge.domain.schemas import RunConstraints, RunRequest, RunResult
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
            self._logger.info("retrieval stage started", extra={"run_id": run.run_id})
            self._retrieval_agent(run.run_id, topic, request.constraints)

            self._repository.update_run_status(run.run_id, "reviewing")
            self._logger.info("review stage started", extra={"run_id": run.run_id})
            try:
                self._review_agent(run.run_id)
            except Exception:
                if not self._repository.load_evidence_cards(run.run_id):
                    raise
                self._logger.warning("review stage degraded", extra={"run_id": run.run_id})

            self._repository.update_run_status(run.run_id, "criticizing")
            self._logger.info("critic stage started", extra={"run_id": run.run_id})
            try:
                self._critic_agent(run.run_id)
            except Exception:
                self._logger.warning("critic stage degraded", extra={"run_id": run.run_id})

            self._repository.update_run_status(run.run_id, "planning")
            self._logger.info("planner stage started", extra={"run_id": run.run_id})
            try:
                self._planner_agent(run.run_id)
            except Exception:
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

    def get_trace(self, run_id: str) -> list[dict]:
        return self._repository.list_tool_traces(run_id)

    def get_report_markdown(self, run_id: str) -> str:
        run = self._repository.get_run(run_id)
        return run.final_report_md or ""

    def _render_partial_report(self, run_id: str) -> None:
        result = self._repository.build_final_result(run_id)
        if result.report_markdown:
            return
        self._repository.save_report_markdown(run_id, self._report_renderer.render(result))
