from __future__ import annotations

import hashlib
import os
from pathlib import Path

from fastapi.testclient import TestClient

from hypoforge.api.app import create_app
from hypoforge.application.services import build_default_services
from hypoforge.config import Settings


GOLDEN_TOPICS = (
    "solid-state battery electrolyte",
    "protein binder design",
    "CRISPR delivery lipid nanoparticles",
    "CO2 reduction catalyst selectivity",
    "diffusion model preference optimization",
)


def live_api_enabled() -> bool:
    return bool(os.getenv("RUN_REAL_API_TESTS")) and bool(Settings().openai_api_key)


def golden_topics_enabled() -> bool:
    return live_api_enabled() and bool(os.getenv("RUN_GOLDEN_TOPIC_TESTS"))


def run_live_topic_round_trip(
    tmp_path: Path,
    topic: str,
    *,
    max_selected_papers: int = 12,
) -> tuple[dict, list[dict], str]:
    database_path = tmp_path / f"{_topic_cache_key(topic)}.db"
    settings = Settings(database_url=f"sqlite:///{database_path}")
    services = build_default_services(settings)
    client = TestClient(create_app(services=services))

    response = client.post(
        "/v1/runs",
        json={
            "topic": topic,
            "constraints": {
                "year_from": 2018,
                "year_to": 2026,
                "open_access_only": False,
                "max_selected_papers": max_selected_papers,
                "novelty_weight": 0.5,
                "feasibility_weight": 0.5,
                "lab_mode": "either",
            },
        },
    )

    assert response.status_code == 200
    body = response.json()
    run_id = body["run_id"]

    get_run = client.get(f"/v1/runs/{run_id}")
    get_trace = client.get(f"/v1/runs/{run_id}/trace")
    get_report = client.get(f"/v1/runs/{run_id}/report.md")

    assert get_run.status_code == 200
    assert get_trace.status_code == 200
    assert get_report.status_code == 200

    return get_run.json(), get_trace.json(), get_report.text


def assert_live_run_meets_spec(
    *,
    run_body: dict,
    traces: list[dict],
    report_markdown: str,
) -> None:
    assert run_body["status"] == "done"
    assert len(run_body["selected_papers"]) >= 12
    assert len(run_body["hypotheses"]) == 3
    assert report_markdown
    assert "# HypoForge Briefing:" in report_markdown
    assert "## Executive Summary" in report_markdown
    assert "## Evidence Appendix" in report_markdown
    assert "## Paper Appendix" in report_markdown
    assert len(traces) > 0
    retrieval_traces = [item for item in traces if item["agent_name"] == "retrieval"]
    assert len(retrieval_traces) >= 2
    assert any((item.get("input_tokens") or 0) > 0 for item in traces)

    for hypothesis in run_body["hypotheses"]:
        assert len(hypothesis["supporting_evidence_ids"]) >= 3
        assert hypothesis["counterevidence_ids"] or hypothesis["limitations"]
        assert hypothesis["minimal_experiment"]["readouts"]


def _topic_cache_key(topic: str) -> str:
    return hashlib.sha1(topic.encode("utf-8")).hexdigest()[:12]
