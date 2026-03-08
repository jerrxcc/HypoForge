from __future__ import annotations

from hypoforge.domain.schemas import RunResult


class ReportRenderer:
    def render(self, result: RunResult) -> str:
        lines = [
            f"# HypoForge Report: {result.run_id}",
            "",
            "## Selected Papers",
            f"- Count: {len(result.selected_papers)}",
            "",
            "## Evidence Cards",
            f"- Count: {len(result.evidence_cards)}",
            "",
            "## Conflict Clusters",
            f"- Count: {len(result.conflict_clusters)}",
            "",
        ]
        for hypothesis in result.hypotheses:
            lines.extend(
                [
                    f"## Hypothesis {hypothesis.rank}: {hypothesis.title}",
                    hypothesis.hypothesis_statement,
                    "",
                    f"- Prediction: {hypothesis.prediction}",
                    f"- Supporting evidence: {', '.join(hypothesis.supporting_evidence_ids)}",
                    f"- Counterevidence: {', '.join(hypothesis.counterevidence_ids)}",
                    f"- Minimal experiment: {hypothesis.minimal_experiment.design}",
                    f"- Limitations: {', '.join(hypothesis.limitations) or 'None recorded'}",
                    f"- Uncertainty: {', '.join(hypothesis.uncertainty_notes) or 'None recorded'}",
                    f"- Risks: {', '.join(hypothesis.risks) or 'None recorded'}",
                    "",
                ]
            )
        return "\n".join(lines).strip() + "\n"
