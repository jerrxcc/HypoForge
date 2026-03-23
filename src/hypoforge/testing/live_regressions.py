from __future__ import annotations

from collections import Counter
import hashlib
from pathlib import Path

from fastapi.testclient import TestClient

from hypoforge.api.app import create_app
from hypoforge.application.services import build_default_services
from hypoforge.config import Settings


GOLDEN_TOPICS = (
    "solid-state battery electrolyte",
    "protein binder design",
    "mRNA vaccine thermostability",
    "CO2 reduction catalyst selectivity",
    "diffusion model preference optimization",
)


def run_live_topic_round_trip(
    tmp_path: Path,
    topic: str,
    *,
    max_selected_papers: int = 12,
) -> tuple[dict, list[dict], str]:
    database_path = tmp_path / f"{_topic_cache_key(topic)}.db"
    settings = _build_live_settings(database_path)
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
    diagnostics = _build_live_failure_diagnostics(
        run_body=run_body,
        traces=traces,
        report_markdown=report_markdown,
    )
    try:
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
    except AssertionError as exc:
        message = str(exc) or "live run did not meet spec"
        raise AssertionError(f"{message}\n\nLive diagnostics:\n{diagnostics}") from exc


def _build_live_failure_diagnostics(
    *,
    run_body: dict,
    traces: list[dict],
    report_markdown: str,
) -> str:
    stage_summaries = run_body.get("stage_summaries") or []
    stage_statuses = ", ".join(
        f"{stage.get('stage_name', '?')}:{stage.get('status', '?')}"
        for stage in stage_summaries
    ) or "none"
    trace_counts = ", ".join(
        f"{agent}:{count}"
        for agent, count in sorted(
            Counter((trace.get("agent_name") or "unknown") for trace in traces).items()
        )
    ) or "none"
    recent_traces = traces[-5:]
    recent_trace_lines = [
        (
            f"{trace.get('agent_name', '?')}.{trace.get('tool_name', '?')} "
            f"success={trace.get('success')} "
            f"error={trace.get('error_message') or '-'}"
        )
        for trace in recent_traces
    ] or ["none"]

    return "\n".join(
        [
            f"run_id={run_body.get('run_id', '?')}",
            f"status={run_body.get('status', '?')}",
            f"selected_papers={len(run_body.get('selected_papers') or [])}",
            f"hypotheses={len(run_body.get('hypotheses') or [])}",
            f"stage_statuses={stage_statuses}",
            f"trace_count={len(traces)}",
            f"trace_counts={trace_counts}",
            f"report_chars={len(report_markdown or '')}",
            "recent_traces=",
            *recent_trace_lines,
        ]
    )


def _topic_cache_key(topic: str) -> str:
    return hashlib.sha1(topic.encode("utf-8")).hexdigest()[:12]


def _build_live_settings(database_path: Path) -> Settings:
    base_settings = Settings()
    return base_settings.model_copy(
        update={
            "database_url": f"sqlite:///{database_path}",
            "request_timeout_seconds": max(base_settings.request_timeout_seconds, 120),
        }
    )
