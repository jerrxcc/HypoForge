import pytest

from hypoforge.domain.schemas import PlannerSummary, RunConstraints


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

