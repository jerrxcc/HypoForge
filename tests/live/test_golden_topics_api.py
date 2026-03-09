import pytest

from hypoforge.testing.live_regressions import (
    GOLDEN_TOPICS,
    assert_live_run_meets_spec,
    golden_topics_enabled,
    run_live_topic_round_trip,
)


@pytest.mark.skipif(
    not golden_topics_enabled(),
    reason="Set RUN_REAL_API_TESTS=1 RUN_GOLDEN_TOPIC_TESTS=1 and OPENAI_API_KEY to run golden topic regressions.",
)
@pytest.mark.parametrize("topic", GOLDEN_TOPICS, ids=lambda topic: topic.replace(" ", "-"))
def test_golden_topic_round_trip(tmp_path, topic: str) -> None:
    run_body, traces, report_markdown = run_live_topic_round_trip(tmp_path, topic)
    assert_live_run_meets_spec(
        run_body=run_body,
        traces=traces,
        report_markdown=report_markdown,
    )
