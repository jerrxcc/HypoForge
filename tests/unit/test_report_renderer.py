from hypoforge.application.report_renderer import ReportRenderer
from hypoforge.domain.schemas import (
    ConflictCluster,
    EvidenceCard,
    Hypothesis,
    MinimalExperiment,
    PaperDetail,
    RunResult,
    StageSummary,
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
            topic="solid-state battery electrolyte",
            status="done",
            hypotheses=[_hypothesis(1), _hypothesis(2), _hypothesis(3)],
        )
    )

    assert markdown.count("## Hypothesis") == 3
    assert "- Limitations: Low-evidence literature set" in markdown
    assert "- Uncertainty: Critic stage degraded" in markdown


def test_report_renderer_outputs_briefing_sections() -> None:
    renderer = ReportRenderer()
    markdown = renderer.render(
        RunResult(
            run_id="run_2",
            topic="CRISPR delivery lipid nanoparticles",
            status="done",
            selected_papers=[
                PaperDetail(
                    paper_id="p1",
                    title="LNP delivery of CRISPR cargo",
                    year=2024,
                    venue="Nature Biotechnology",
                    source="openalex",
                    authors=["Author A", "Author B"],
                ),
                PaperDetail(
                    paper_id="p2",
                    title="Targeted extrahepatic CRISPR delivery",
                    year=2023,
                    venue="Science Translational Medicine",
                    source="openalex",
                    authors=["Author C"],
                ),
            ],
            evidence_cards=[
                EvidenceCard(
                    evidence_id="e1",
                    paper_id="p1",
                    title="LNP delivery of CRISPR cargo",
                    claim_text="Cas9 mRNA and sgRNA delivered by LNPs edited hepatocytes efficiently.",
                    system_or_material="ionizable LNP",
                    intervention="Cas9 mRNA + sgRNA delivery",
                    outcome="editing efficiency",
                    direction="positive",
                    confidence=0.91,
                    evidence_kind="experiment",
                ),
                EvidenceCard(
                    evidence_id="e2",
                    paper_id="p2",
                    title="Targeted extrahepatic CRISPR delivery",
                    claim_text="Targeting ligands shifted distribution beyond liver but reduced total editing yield.",
                    system_or_material="targeted LNP",
                    intervention="ligand-directed delivery",
                    outcome="extrahepatic tropism",
                    direction="mixed",
                    confidence=0.72,
                    evidence_kind="experiment",
                    limitations=["targeting effect varied by ligand density"],
                ),
            ],
            conflict_clusters=[
                ConflictCluster(
                    cluster_id="cluster_1",
                    topic_axis="Organ targeting tradeoff",
                    supporting_evidence_ids=["e1"],
                    conflicting_evidence_ids=["e2"],
                    conflict_type="conditional_divergence",
                    likely_explanations=["ligand density shifts biodistribution"],
                    missing_controls=["head-to-head dose matching"],
                    critic_summary="Liver efficiency and extrahepatic targeting remain in tension.",
                    confidence=0.74,
                )
            ],
            hypotheses=[_hypothesis(1), _hypothesis(2), _hypothesis(3)],
            stage_summaries=[
                StageSummary(
                    stage_name="retrieval",
                    status="completed",
                    summary={
                        "coverage_assessment": "medium",
                        "needs_broader_search": True,
                        "query_variants_used": ["CRISPR delivery lipid nanoparticles"],
                        "search_notes": [
                            "Semantic Scholar rate-limited; OpenAlex carried most of the retrieval load."
                        ],
                        "selected_paper_ids": ["p1", "p2"],
                    },
                ),
                StageSummary(
                    stage_name="review",
                    status="completed",
                    summary={
                        "papers_processed": 2,
                        "evidence_cards_created": 2,
                        "dominant_axes": ["cargo format", "organ targeting"],
                    },
                ),
                StageSummary(
                    stage_name="critic",
                    status="completed",
                    summary={
                        "clusters_created": 1,
                        "top_axes": ["Organ targeting tradeoff"],
                    },
                ),
            ],
        )
    )

    assert "## Executive Summary" in markdown
    assert "## Retrieval Coverage" in markdown
    assert "## Evidence Footing" in markdown
    assert "## Conflict Map Snapshot" in markdown
    assert "## Experiment Slate" in markdown
    assert "## Evidence Appendix" in markdown
    assert "## Paper Appendix" in markdown
    assert "Semantic Scholar rate-limited" in markdown
    assert "Organ targeting tradeoff" in markdown
