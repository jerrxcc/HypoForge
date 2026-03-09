from datetime import UTC, datetime

from fastapi.testclient import TestClient

from hypoforge.api.app import create_app
from hypoforge.application.services import ServiceContainer
from hypoforge.domain.schemas import RunConstraints, RunResult, RunSummary


class FakeCoordinator:
    def __init__(self) -> None:
        timestamp = datetime.now(UTC)
        self._result = RunResult(
            run_id="run_123",
            topic="solid-state battery electrolyte",
            status="done",
            report_markdown="# Report",
            trace_url="/v1/runs/run_123/trace",
        )
        self._runs = [
            RunSummary(
                run_id="run_124",
                topic="perovskite stability",
                status="reviewing",
                created_at=timestamp,
                updated_at=timestamp,
                selected_paper_count=9,
                evidence_card_count=14,
                conflict_cluster_count=2,
                hypothesis_count=0,
            ),
            RunSummary(
                run_id="run_123",
                topic="solid-state battery electrolyte",
                status="done",
                created_at=timestamp,
                updated_at=timestamp,
                selected_paper_count=20,
                evidence_card_count=12,
                conflict_cluster_count=5,
                hypothesis_count=3,
            )
        ]

    def run_topic(self, topic: str, constraints: RunConstraints | None = None) -> RunResult:
        del topic, constraints
        return self._result

    def get_run_result(self, run_id: str) -> RunResult:
        del run_id
        return self._result

    def get_trace(self, run_id: str) -> list[dict]:
        del run_id
        return [{"tool_name": "search_openalex_works"}]

    def list_runs(self) -> list[RunSummary]:
        return self._runs

    def rerun_planner(self, run_id: str) -> RunResult:
        del run_id
        return self._result


def test_post_runs_returns_final_result() -> None:
    services = ServiceContainer(coordinator=FakeCoordinator())
    client = TestClient(create_app(services=services))

    response = client.post("/v1/runs", json={"topic": "solid-state battery electrolyte"})

    assert response.status_code == 200
    assert response.json()["topic"] == "solid-state battery electrolyte"
    assert response.json()["status"] == "done"


def test_get_trace_returns_trace_entries() -> None:
    services = ServiceContainer(coordinator=FakeCoordinator())
    client = TestClient(create_app(services=services))

    response = client.get("/v1/runs/run_123/trace")

    assert response.status_code == 200
    assert response.json()[0]["tool_name"] == "search_openalex_works"


def test_get_runs_returns_run_summaries() -> None:
    services = ServiceContainer(coordinator=FakeCoordinator())
    client = TestClient(create_app(services=services))

    response = client.get("/v1/runs")

    assert response.status_code == 200
    payload = response.json()
    assert [item["run_id"] for item in payload] == ["run_124", "run_123"]
    assert payload[0]["selected_paper_count"] == 9
    assert payload[1]["hypothesis_count"] == 3


def test_post_rerun_planner_returns_final_result() -> None:
    services = ServiceContainer(coordinator=FakeCoordinator())
    client = TestClient(create_app(services=services))

    response = client.post("/v1/runs/run_123/planner/rerun")

    assert response.status_code == 200
    assert response.json()["run_id"] == "run_123"
