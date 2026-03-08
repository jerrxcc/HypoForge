from hypoforge.application.services import _summarize_tool_result


def test_summarize_tool_result_includes_result_count_and_cache_hit() -> None:
    summary = _summarize_tool_result(
        {
            "papers": [{"paper_id": "p1"}, {"paper_id": "p2"}],
            "cache_hit": True,
        }
    )

    assert summary["paper_count"] == 2
    assert summary["result_count"] == 2
    assert summary["cache_hit"] is True
