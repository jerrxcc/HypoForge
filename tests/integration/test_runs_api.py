from fastapi.testclient import TestClient

from hypoforge.api.app import create_app
from hypoforge.application.services import ServiceContainer
from hypoforge.domain.schemas import RunConstraints, RunResult


class FakeCoordinator:
    def __init__(self) -> None:
        self._result = RunResult(
            run_id="run_123",
            status="done",
            report_markdown="# Report",
            trace_url="/v1/runs/run_123/trace",
        )

    def run_topic(self, topic: str, constraints: RunConstraints | None = None) -> RunResult:
        del topic, constraints
        return self._result

    def get_run_result(self, run_id: str) -> RunResult:
        del run_id
        return self._result

    def get_trace(self, run_id: str) -> list[dict]:
        del run_id
        return [{"tool_name": "search_openalex_works"}]


def test_post_runs_returns_final_result() -> None:
    services = ServiceContainer(coordinator=FakeCoordinator())
    client = TestClient(create_app(services=services))

    response = client.post("/v1/runs", json={"topic": "solid-state battery electrolyte"})

    assert response.status_code == 200
    assert response.json()["status"] == "done"


def test_get_trace_returns_trace_entries() -> None:
    services = ServiceContainer(coordinator=FakeCoordinator())
    client = TestClient(create_app(services=services))

    response = client.get("/v1/runs/run_123/trace")

    assert response.status_code == 200
    assert response.json()[0]["tool_name"] == "search_openalex_works"
