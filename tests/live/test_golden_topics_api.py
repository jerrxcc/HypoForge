import pytest

from hypoforge.testing.live_regressions import (
    GOLDEN_TOPICS,
    assert_live_run_meets_spec,
    run_live_topic_round_trip,
)


@pytest.mark.parametrize("topic", GOLDEN_TOPICS, ids=lambda topic: topic.replace(" ", "-"))
def test_golden_topic_round_trip(tmp_path, topic: str) -> None:
    run_body, traces, report_markdown = run_live_topic_round_trip(tmp_path, topic)
    assert_live_run_meets_spec(
        run_body=run_body,
        traces=traces,
        report_markdown=report_markdown,
    )
