import pytest

from hypoforge.application.budget import BudgetExceededError, RunBudgetTracker


def test_budget_tracker_counts_calls_per_source() -> None:
    tracker = RunBudgetTracker(max_openalex_calls=2, max_semantic_scholar_calls=1)

    tracker.register_openalex_call()
    tracker.register_openalex_call()
    tracker.register_semantic_scholar_call()

    assert tracker.openalex_calls == 2
    assert tracker.semantic_scholar_calls == 1


def test_budget_tracker_raises_when_source_limit_exceeded() -> None:
    tracker = RunBudgetTracker(max_openalex_calls=1, max_semantic_scholar_calls=1)

    tracker.register_openalex_call()

    with pytest.raises(BudgetExceededError) as exc:
        tracker.register_openalex_call()

    assert exc.value.source == "openalex"
