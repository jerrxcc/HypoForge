from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
from pathlib import Path

from fastapi.testclient import TestClient

from hypoforge.api.app import create_app
from hypoforge.application.services import build_default_services
from hypoforge.config import Settings
from hypoforge.domain.schemas import ReflectionFeedback, RunIterationState


GOLDEN_TOPICS = (
    "solid-state battery electrolyte",
    "protein binder design",
    "perovskite solar cell stability degradation",
    "CO2 reduction catalyst selectivity",
    "diffusion model preference optimization",
)

_BASE_CONSTRAINTS: dict[str, object] = {
    "year_from": 2018,
    "year_to": 2026,
    "open_access_only": False,
    "max_selected_papers": 12,
    "novelty_weight": 0.5,
    "feasibility_weight": 0.5,
    "lab_mode": "either",
}


@dataclass(frozen=True, slots=True)
class LiveScenario:
    profile_name: str
    topic: str
    constraints: dict[str, object]
    min_selected_papers: int
    expect_retry: bool = False
    expect_reflection_feedback: bool = False
    expect_validation_rerun: bool = False


@dataclass(frozen=True, slots=True)
class LiveScenarioArtifacts:
    run_body: dict
    traces: list[dict]
    report_markdown: str
    reflection_history: list[ReflectionFeedback]
    iteration_state: RunIterationState | None


REFLECTION_RETRY_LIVE = LiveScenario(
    profile_name="reflection_retry_live",
    topic="solid-state battery electrolyte",
    constraints={**_BASE_CONSTRAINTS, "max_selected_papers": 5},
    min_selected_papers=5,
    expect_retry=True,
    expect_reflection_feedback=True,
)

VALIDATION_ONLY_LIVE = LiveScenario(
    profile_name="validation_only_live",
    topic="solid-state battery electrolyte",
    constraints={**_BASE_CONSTRAINTS, "max_selected_papers": 5},
    min_selected_papers=5,
    expect_retry=True,
    expect_validation_rerun=True,
)

COMBINED_LIVE = LiveScenario(
    profile_name="combined_live",
    topic="solid-state battery electrolyte",
    constraints={**_BASE_CONSTRAINTS, "max_selected_papers": 5},
    min_selected_papers=5,
    expect_retry=True,
    expect_reflection_feedback=True,
    expect_validation_rerun=True,
)


def run_live_topic_round_trip(
    tmp_path: Path,
    topic: str,
    *,
    max_selected_papers: int = 12,
) -> tuple[dict, list[dict], str]:
    scenario = LiveScenario(
        profile_name="baseline_golden_matrix",
        topic=topic,
        constraints={**_BASE_CONSTRAINTS, "max_selected_papers": max_selected_papers},
        min_selected_papers=max_selected_papers,
    )
    artifacts = run_live_scenario_round_trip(tmp_path, scenario)
    return artifacts.run_body, artifacts.traces, artifacts.report_markdown


def run_live_scenario_round_trip(
    tmp_path: Path,
    scenario: LiveScenario,
) -> LiveScenarioArtifacts:
    database_path = tmp_path / f"{scenario.profile_name}-{_topic_cache_key(scenario.topic)}.db"
    settings = build_live_settings(scenario.profile_name, database_path)
    services = build_default_services(settings)
    client = TestClient(create_app(services=services))

    response = client.post(
        "/v1/runs",
        json={
            "topic": scenario.topic,
            "constraints": scenario.constraints,
        },
    )

    assert response.status_code == 200, f"POST /v1/runs returned {response.status_code}: {response.text[:500]}"
    body = response.json()
    run_id = body["run_id"]

    get_run = client.get(f"/v1/runs/{run_id}")
    get_trace = client.get(f"/v1/runs/{run_id}/trace")
    get_report = client.get(f"/v1/runs/{run_id}/report.md")

    assert get_run.status_code == 200
    assert get_trace.status_code == 200
    assert get_report.status_code == 200

    return LiveScenarioArtifacts(
        run_body=get_run.json(),
        traces=get_trace.json(),
        report_markdown=get_report.text,
        reflection_history=services.coordinator.get_reflection_history(run_id),
        iteration_state=services.coordinator.get_iteration_state(run_id),
    )


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
        reflection_history=[],
        iteration_state=None,
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


def assert_live_scenario_meets_spec(
    *,
    scenario: LiveScenario,
    artifacts: LiveScenarioArtifacts,
) -> None:
    diagnostics = _build_live_failure_diagnostics(
        run_body=artifacts.run_body,
        traces=artifacts.traces,
        report_markdown=artifacts.report_markdown,
        reflection_history=artifacts.reflection_history,
        iteration_state=artifacts.iteration_state,
    )
    try:
        run_body = artifacts.run_body
        traces = artifacts.traces
        report_markdown = artifacts.report_markdown

        assert run_body["status"] == "done"
        assert len(run_body["selected_papers"]) >= scenario.min_selected_papers
        assert len(run_body["hypotheses"]) == 3
        assert report_markdown
        assert "# HypoForge Briefing:" in report_markdown
        assert "## Executive Summary" in report_markdown
        assert "## Evidence Appendix" in report_markdown
        assert "## Paper Appendix" in report_markdown
        assert traces
        assert any((item.get("input_tokens") or 0) > 0 for item in traces)

        if scenario.expect_retry:
            assert any(
                int(stage.get("attempt", 0)) >= 2
                for stage in (run_body.get("stage_summaries") or [])
            )

        if scenario.expect_reflection_feedback:
            assert len(artifacts.reflection_history) > 0

        if scenario.expect_validation_rerun and scenario.profile_name == "validation_only_live":
            assert len(artifacts.reflection_history) == 0
            assert any(
                int(stage.get("attempt", 0)) >= 2
                for stage in (run_body.get("stage_summaries") or [])
            )

        for hypothesis in run_body["hypotheses"]:
            assert len(hypothesis["supporting_evidence_ids"]) >= 3
            assert hypothesis["counterevidence_ids"] or hypothesis["limitations"]
            assert hypothesis["minimal_experiment"]["readouts"]
    except AssertionError as exc:
        message = str(exc) or "live scenario did not meet spec"
        raise AssertionError(f"{message}\n\nLive diagnostics:\n{diagnostics}") from exc


def build_live_settings(profile_name: str, database_path: Path) -> Settings:
    base_settings = _require_live_base_settings()
    reflection_updates: dict[str, object] = {}
    validation_updates: dict[str, object] = {}

    if profile_name == "reflection_retry_live":
        reflection_updates = {
            "enable_reflection": True,
            "max_stage_iterations": 2,
            "retrieval_quality_threshold": 0.85,
            "review_quality_threshold": 0.8,
            "critic_quality_threshold": 0.8,
            "planner_quality_threshold": 0.85,
        }
        validation_updates = {
            "enable_validation_agents": False,
        }
    elif profile_name == "validation_only_live":
        reflection_updates = {
            "enable_reflection": False,
        }
        validation_updates = {
            "enable_validation_agents": True,
            "max_total_backtrack": 1,
            "min_valid_evidence": 10,
            "min_conflict_coverage": 0.8,
            "min_quality_score": 0.85,
            "evidence_completeness_threshold": 0.75,
        }
    elif profile_name == "combined_live":
        reflection_updates = {
            "enable_reflection": True,
            "max_stage_iterations": 2,
            "retrieval_quality_threshold": 0.85,
            "review_quality_threshold": 0.8,
            "critic_quality_threshold": 0.8,
            "planner_quality_threshold": 0.85,
        }
        validation_updates = {
            "enable_validation_agents": True,
            "max_total_backtrack": 1,
            "min_valid_evidence": 10,
            "min_conflict_coverage": 0.8,
            "min_quality_score": 0.85,
        }
    elif profile_name != "baseline_golden_matrix":
        raise ValueError(f"unsupported live profile: {profile_name}")

    reflection_settings = base_settings.reflection_settings.model_copy(update=reflection_updates)
    validation_settings = base_settings.validation_settings.model_copy(update=validation_updates)
    return base_settings.model_copy(
        update={
            "database_url": f"sqlite:///{database_path}",
            "request_timeout_seconds": max(base_settings.request_timeout_seconds, 120),
            "reflection_settings": reflection_settings,
            "validation_settings": validation_settings,
        }
    )


def _build_live_failure_diagnostics(
    *,
    run_body: dict,
    traces: list[dict],
    report_markdown: str,
    reflection_history: list[ReflectionFeedback] | None = None,
    iteration_state: RunIterationState | None = None,
) -> str:
    reflection_history = reflection_history or []
    stage_summaries = run_body.get("stage_summaries") or []
    stage_statuses = ", ".join(
        (
            f"{stage.get('stage_name', '?')}:{stage.get('status', '?')}#{stage.get('attempt')}"
            if stage.get("attempt") is not None
            else f"{stage.get('stage_name', '?')}:{stage.get('status', '?')}"
        )
        for stage in stage_summaries
    ) or "none"
    trace_counts = ", ".join(
        f"{agent}:{count}"
        for agent, count in sorted(
            Counter((trace.get("agent_name") or "unknown") for trace in traces).items()
        )
    ) or "none"
    recent_trace_lines = [
        (
            f"{trace.get('agent_name', '?')}.{trace.get('tool_name', '?')} "
            f"success={trace.get('success')} "
            f"error={trace.get('error_message') or '-'}"
        )
        for trace in traces[-5:]
    ] or ["none"]
    iteration_snapshot = (
        iteration_state.model_dump(mode="json")
        if iteration_state is not None
        else None
    )

    return "\n".join(
        [
            f"run_id={run_body.get('run_id', '?')}",
            f"status={run_body.get('status', '?')}",
            f"selected_papers={len(run_body.get('selected_papers') or [])}",
            f"hypotheses={len(run_body.get('hypotheses') or [])}",
            f"stage_statuses={stage_statuses}",
            f"trace_count={len(traces)}",
            f"trace_counts={trace_counts}",
            f"reflection_feedback_count={len(reflection_history)}",
            f"iteration_state={iteration_snapshot}",
            f"report_chars={len(report_markdown or '')}",
            "recent_traces=",
            *recent_trace_lines,
        ]
    )


def _require_live_base_settings() -> Settings:
    settings = Settings()
    assert settings.openai_api_key.strip(), "OPENAI_API_KEY is required for live tests"
    return settings


def _build_live_settings(database_path: Path) -> Settings:
    return build_live_settings("baseline_golden_matrix", database_path)


def _topic_cache_key(topic: str) -> str:
    return hashlib.sha1(topic.encode("utf-8")).hexdigest()[:12]
