import os

import pytest
from fastapi.testclient import TestClient

from hypoforge.api.app import create_app
from hypoforge.application.services import build_default_services
from hypoforge.config import Settings


def _live_api_enabled() -> bool:
    return bool(os.getenv("RUN_REAL_API_TESTS")) and bool(Settings().openai_api_key)


@pytest.mark.skipif(not _live_api_enabled(), reason="Set RUN_REAL_API_TESTS=1 and OPENAI_API_KEY to run live API tests.")
def test_real_api_run_round_trip(tmp_path) -> None:
    settings = Settings(database_url=f"sqlite:///{tmp_path / 'live-api.db'}")
    services = build_default_services(settings)
    client = TestClient(create_app(services=services))

    response = client.post(
        "/v1/runs",
        json={
            "topic": "solid-state battery electrolyte",
            "constraints": {
                "year_from": 2020,
                "year_to": 2026,
                "open_access_only": False,
                "max_selected_papers": 12,
                "novelty_weight": 0.5,
                "feasibility_weight": 0.5,
                "lab_mode": "either",
            },
        },
    )

    assert response.status_code == 200
    body = response.json()
    run_id = body["run_id"]

    assert body["status"] == "done"
    assert len(body["hypotheses"]) == 3
    assert body["report_markdown"]
    assert body["trace_url"] == f"/v1/runs/{run_id}/trace"

    get_run = client.get(f"/v1/runs/{run_id}")
    get_trace = client.get(f"/v1/runs/{run_id}/trace")
    get_report = client.get(f"/v1/runs/{run_id}/report.md")

    assert get_run.status_code == 200
    assert get_trace.status_code == 200
    assert get_report.status_code == 200
    assert get_run.json()["status"] == "done"
    assert len(get_trace.json()) > 0
    assert any(item["agent_name"] == "retrieval" for item in get_trace.json())
    assert any((item.get("input_tokens") or 0) > 0 for item in get_trace.json())
    assert "# HypoForge Report:" in get_report.text
