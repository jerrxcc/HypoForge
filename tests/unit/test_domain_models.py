import pytest

from hypoforge.domain.schemas import PlannerSummary, RunConstraints, RunRequest


def test_run_constraints_default_weights_sum_to_one() -> None:
    constraints = RunConstraints()

    assert constraints.novelty_weight == 0.5
    assert constraints.feasibility_weight == 0.5


def test_planner_summary_requires_three_hypotheses() -> None:
    with pytest.raises(ValueError):
        PlannerSummary(
            hypotheses_created=2,
            report_rendered=True,
            top_axes=[],
            planner_notes=[],
        )


def test_run_constraints_rejects_negative_weights() -> None:
    with pytest.raises(ValueError, match="novelty_weight must be between 0 and 1"):
        RunConstraints(novelty_weight=-0.5, feasibility_weight=1.5)


def test_run_constraints_rejects_weights_above_one() -> None:
    with pytest.raises(ValueError, match="feasibility_weight must be between 0 and 1"):
        RunConstraints(novelty_weight=0.5, feasibility_weight=1.5)


def test_run_request_rejects_whitespace_only_topic() -> None:
    with pytest.raises(ValueError, match="topic must contain non-whitespace characters"):
        RunRequest(topic="   ")

