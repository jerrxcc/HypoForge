from hypoforge.testing.live_regressions import (
    GOLDEN_TOPICS,
    _build_live_failure_diagnostics,
    _build_live_settings,
)


def test_golden_topics_match_spec_regression_set() -> None:
    assert GOLDEN_TOPICS == (
        "solid-state battery electrolyte",
        "protein binder design",
        "CRISPR delivery lipid nanoparticles",
        "CO2 reduction catalyst selectivity",
        "diffusion model preference optimization",
    )


def test_live_failure_diagnostics_surfaces_run_and_trace_context() -> None:
    diagnostics = _build_live_failure_diagnostics(
        run_body={
            "run_id": "run_123",
            "status": "planning",
            "selected_papers": [{"paper_id": "p1"}],
            "hypotheses": [],
            "stage_summaries": [
                {"stage_name": "retrieval", "status": "completed"},
                {"stage_name": "review", "status": "completed"},
                {"stage_name": "planner", "status": "started"},
            ],
        },
        traces=[
            {"agent_name": "retrieval", "tool_name": "search_openalex_works", "success": True},
            {"agent_name": "review", "tool_name": "load_selected_papers", "success": True},
            {
                "agent_name": "planner",
                "tool_name": "load_conflict_clusters",
                "success": False,
                "error_message": "missing conflicts",
            },
        ],
        report_markdown="# Partial Report",
    )

    assert "run_id=run_123" in diagnostics
    assert "status=planning" in diagnostics
    assert "stage_statuses=retrieval:completed, review:completed, planner:started" in diagnostics
    assert "trace_counts=planner:1, retrieval:1, review:1" in diagnostics
    assert "planner.load_conflict_clusters success=False error=missing conflicts" in diagnostics
    assert "report_chars=16" in diagnostics


def test_live_settings_raise_request_timeout_floor_for_real_runs(tmp_path) -> None:
    settings = _build_live_settings(tmp_path / "live.db")

    assert settings.database_url.endswith("/live.db")
    assert settings.request_timeout_seconds >= 120
