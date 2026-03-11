from __future__ import annotations

from collections import Counter

from hypoforge.domain.schemas import RunResult


class ReportRenderer:
    def render(self, result: RunResult) -> str:
        retrieval = _stage_summary(result, "retrieval")
        review = _stage_summary(result, "review")
        critic = _stage_summary(result, "critic")

        selected_count = len(result.selected_papers)
        evidence_count = len(result.evidence_cards)
        cluster_count = len(result.conflict_clusters)
        hypothesis_count = len(result.hypotheses)
        top_hypotheses = ", ".join(hypothesis.title for hypothesis in result.hypotheses[:3]) or "None"
        dominant_axes = review.get("dominant_axes") or []
        top_axes = critic.get("top_axes") or [cluster.topic_axis for cluster in result.conflict_clusters]

        lines = [
            f"# HypoForge Briefing: {result.topic}",
            "",
            f"- Run ID: `{result.run_id}`",
            f"- Final status: `{result.status}`",
            "",
            "## Executive Summary",
            f"- The dossier retained {selected_count} selected papers, {evidence_count} evidence cards, {cluster_count} conflict clusters, and {hypothesis_count} ranked hypotheses.",
            f"- Retrieval coverage was `{retrieval.get('coverage_assessment', 'not reported')}` with {len(retrieval.get('query_variants_used', [])) or 1} query variant(s).",
            f"- The strongest current themes are: {_join_list(top_axes) or _join_list(dominant_axes) or 'not yet distilled'}.",
            f"- Ranked hypotheses in this run: {top_hypotheses}.",
            "",
            "## Retrieval Coverage",
            f"- Coverage assessment: {retrieval.get('coverage_assessment', 'not reported')}",
            f"- Needs broader search: {'yes' if retrieval.get('needs_broader_search') else 'no'}",
            f"- Query variants used: {_join_list(retrieval.get('query_variants_used', [])) or 'not reported'}",
            f"- Selected papers: {selected_count}",
            f"- Search notes: {_join_list(retrieval.get('search_notes', []), sep=' | ') or 'None recorded'}",
            "",
            "## Evidence Footing",
            f"- Evidence cards created: {evidence_count}",
            f"- Papers processed in review: {review.get('papers_processed', 'not reported')}",
            f"- Dominant axes: {_join_list(dominant_axes) or 'not reported'}",
            f"- Low-confidence papers: {_join_list(review.get('low_confidence_paper_ids', [])) or 'None recorded'}",
            "",
            "### Evidence snapshots",
            *_render_evidence_snapshots(result),
            "",
            "## Conflict Map Snapshot",
            f"- Conflict clusters: {cluster_count}",
            f"- Top axes: {_join_list(top_axes) or 'not reported'}",
            *_render_conflict_clusters(result),
            "",
        ]
        for hypothesis in result.hypotheses:
            lines.extend(
                [
                    f"## Hypothesis {hypothesis.rank}: {hypothesis.title}",
                    hypothesis.hypothesis_statement,
                    "",
                    f"- Why plausible: {hypothesis.why_plausible}",
                    f"- Why not obvious: {hypothesis.why_not_obvious}",
                    f"- Prediction: {hypothesis.prediction}",
                    f"- Scores: novelty {hypothesis.novelty_score:.2f} • feasibility {hypothesis.feasibility_score:.2f} • overall {hypothesis.overall_score:.2f}",
                    f"- Supporting evidence: {', '.join(hypothesis.supporting_evidence_ids)}",
                    f"- Counterevidence: {', '.join(hypothesis.counterevidence_ids)}",
                    f"- Minimal experiment: {hypothesis.minimal_experiment.design}",
                    f"- Experiment system: {hypothesis.minimal_experiment.system}",
                    f"- Experiment control: {hypothesis.minimal_experiment.control}",
                    f"- Readouts: {', '.join(hypothesis.minimal_experiment.readouts)}",
                    f"- Success criteria: {hypothesis.minimal_experiment.success_criteria}",
                    f"- Failure interpretation: {hypothesis.minimal_experiment.failure_interpretation}",
                    f"- Limitations: {', '.join(hypothesis.limitations) or 'None recorded'}",
                    f"- Uncertainty: {', '.join(hypothesis.uncertainty_notes) or 'None recorded'}",
                    f"- Risks: {', '.join(hypothesis.risks) or 'None recorded'}",
                    "",
                ]
            )
        lines.extend(
            [
                "## Experiment Slate",
                *_render_experiment_slate(result),
                "",
                "## Evidence Appendix",
                *_render_evidence_appendix(result),
                "",
                "## Paper Appendix",
                *_render_paper_appendix(result),
                "",
            ]
        )
        return "\n".join(lines).strip() + "\n"


def _stage_summary(result: RunResult, stage_name: str) -> dict:
    for summary in result.stage_summaries:
        if summary.stage_name == stage_name:
            return summary.summary
    return {}


def _join_list(values: object, *, sep: str = ", ") -> str:
    if not isinstance(values, list):
        return ""
    items = [str(value).strip() for value in values if str(value).strip()]
    return sep.join(items)


def _render_evidence_snapshots(result: RunResult) -> list[str]:
    if not result.evidence_cards:
        return ["- No evidence cards recorded."]
    top_cards = sorted(
        result.evidence_cards,
        key=lambda card: (card.confidence, len(card.claim_text)),
        reverse=True,
    )[:5]
    return [
        f"- `{card.evidence_id}` [{card.direction}, conf {card.confidence:.2f}] {card.claim_text} ({card.title})"
        for card in top_cards
    ]


def _render_conflict_clusters(result: RunResult) -> list[str]:
    if not result.conflict_clusters:
        return ["- No explicit conflict clusters recorded."]
    lines: list[str] = []
    for cluster in result.conflict_clusters[:5]:
        explanations = _join_list(cluster.likely_explanations) or "no explicit explanation recorded"
        controls = _join_list(cluster.missing_controls) or "no missing controls recorded"
        lines.append(
            f"- `{cluster.cluster_id}` {cluster.topic_axis} [{cluster.conflict_type}, conf {cluster.confidence:.2f}] — {cluster.critic_summary}; explanations: {explanations}; missing controls: {controls}"
        )
    return lines


def _render_experiment_slate(result: RunResult) -> list[str]:
    if not result.hypotheses:
        return ["- No experiment slate available."]
    return [
        f"- Rank {hypothesis.rank}: {hypothesis.minimal_experiment.system} — {hypothesis.minimal_experiment.design} | readouts: {', '.join(hypothesis.minimal_experiment.readouts)}"
        for hypothesis in result.hypotheses
    ]


def _render_evidence_appendix(result: RunResult) -> list[str]:
    if not result.evidence_cards:
        return ["- No evidence appendix available."]
    evidence_by_kind = Counter(card.evidence_kind for card in result.evidence_cards)
    lines = [
        f"- Evidence kind distribution: {', '.join(f'{kind}={count}' for kind, count in sorted(evidence_by_kind.items()))}"
    ]
    for card in result.evidence_cards:
        limitations = _join_list(card.limitations) or "None"
        conditions = _join_list(card.conditions) or "None"
        lines.append(
            f"- `{card.evidence_id}` [{card.direction}, conf {card.confidence:.2f}] paper `{card.paper_id}` — {card.claim_text} | system: {card.system_or_material} | intervention: {card.intervention} | outcome: {card.outcome} | conditions: {conditions} | limitations: {limitations}"
        )
    return lines


def _render_paper_appendix(result: RunResult) -> list[str]:
    if not result.selected_papers:
        return ["- No selected papers recorded."]
    return [
        f"- `{paper.paper_id}` {paper.year or 'n.d.'} — {paper.title} | venue: {paper.venue or 'Unknown'} | source: {paper.source or 'unknown'} | authors: {_join_list(paper.authors) or 'Unknown'}"
        for paper in result.selected_papers
    ]
