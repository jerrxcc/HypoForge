from hypoforge.application.report_renderer import ReportRenderer
from hypoforge.domain.schemas import (
    Hypothesis,
    MinimalExperiment,
    RunResult,
)


def _hypothesis(rank: int) -> Hypothesis:
    return Hypothesis(
        rank=rank,
        title=f"Hypothesis {rank}",
        hypothesis_statement="Statement",
        why_plausible="Plausible",
        why_not_obvious="Not obvious",
        supporting_evidence_ids=["e1", "e2", "e3"],
        counterevidence_ids=["e4"],
        prediction="Prediction",
        minimal_experiment=MinimalExperiment(
            system="System",
            design="Design",
            control="Control",
            readouts=["Readout"],
            success_criteria="Success",
            failure_interpretation="Failure",
        ),
        limitations=["Low-evidence literature set"],
        uncertainty_notes=["Critic stage degraded"],
        risks=["Coverage may be incomplete"],
        novelty_score=0.7,
        feasibility_score=0.8,
        overall_score=0.75,
    )


def test_report_renderer_contains_three_hypotheses() -> None:
    renderer = ReportRenderer()
    markdown = renderer.render(
        RunResult(
            run_id="run_1",
            status="done",
            hypotheses=[_hypothesis(1), _hypothesis(2), _hypothesis(3)],
        )
    )

    assert markdown.count("## Hypothesis") == 3
    assert "- Limitations: Low-evidence literature set" in markdown
    assert "- Uncertainty: Critic stage degraded" in markdown
