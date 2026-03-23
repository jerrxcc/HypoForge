from hypoforge.testing.live_regressions import (
    assert_live_run_meets_spec,
    run_live_topic_round_trip,
)


def test_real_api_run_round_trip(tmp_path) -> None:
    run_body, traces, report_markdown = run_live_topic_round_trip(
        tmp_path,
        "solid-state battery electrolyte",
    )
    assert_live_run_meets_spec(
        run_body=run_body,
        traces=traces,
        report_markdown=report_markdown,
    )
