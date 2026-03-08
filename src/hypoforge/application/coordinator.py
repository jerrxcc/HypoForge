from __future__ import annotations

from hypoforge.domain.schemas import RunConstraints, RunRequest, RunResult
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
    ) -> None:
        self._repository = repository
        self._retrieval_agent = retrieval_agent
        self._review_agent = review_agent
        self._critic_agent = critic_agent
        self._planner_agent = planner_agent

    def run_topic(self, topic: str, constraints: RunConstraints | None = None) -> RunResult:
        request = RunRequest(topic=topic, constraints=constraints or RunConstraints())
        run = self._repository.create_run(request)
        try:
            self._repository.update_run_status(run.run_id, "retrieving")
            self._retrieval_agent(run.run_id, topic, request.constraints)

            self._repository.update_run_status(run.run_id, "reviewing")
            self._review_agent(run.run_id)

            self._repository.update_run_status(run.run_id, "criticizing")
            self._critic_agent(run.run_id)

            self._repository.update_run_status(run.run_id, "planning")
            self._planner_agent(run.run_id)

            self._repository.update_run_status(run.run_id, "done")
        except Exception as exc:
            self._repository.update_run_status(run.run_id, "failed")
            raise RuntimeError(f"run failed: {run.run_id}") from exc
        return self._repository.build_final_result(run.run_id)

    def get_run_result(self, run_id: str) -> RunResult:
        return self._repository.build_final_result(run_id)

    def get_trace(self, run_id: str) -> list[dict]:
        return self._repository.list_tool_traces(run_id)

    def get_report_markdown(self, run_id: str) -> str:
        run = self._repository.get_run(run_id)
        return run.final_report_md or ""

