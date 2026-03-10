import pytest

from hypoforge.domain.schemas import ConflictCluster, EvidenceCard, PaperDetail, RunRequest
from hypoforge.infrastructure.db.repository import RunRepository
from hypoforge.tools.workspace_tools import WorkspaceTools


def test_save_hypotheses_repairs_missing_counterevidence_ids(tmp_path) -> None:
    repo = RunRepository.from_sqlite_path(tmp_path / "app.db")
    run = repo.create_run(RunRequest(topic="solid-state battery electrolyte"))
    repo.save_selected_papers(
        run.run_id,
        papers=[PaperDetail(paper_id="p1", title="Paper 1")],
        selection_reason="seed",
    )
    repo.save_evidence_cards(
        run.run_id,
        [
            EvidenceCard(
                evidence_id="e1",
                paper_id="p1",
                title="Paper 1",
                claim_text="Support",
                system_or_material="System",
                intervention="Intervention",
                outcome="Outcome",
                direction="positive",
                confidence=0.9,
            ),
            EvidenceCard(
                evidence_id="e2",
                paper_id="p1",
                title="Paper 1",
                claim_text="Conflict",
                system_or_material="System",
                intervention="Intervention",
                outcome="Outcome",
                direction="negative",
                confidence=0.7,
            ),
            EvidenceCard(
                evidence_id="e3",
                paper_id="p1",
                title="Paper 1",
                claim_text="Support 2",
                system_or_material="System",
                intervention="Intervention",
                outcome="Outcome",
                direction="positive",
                confidence=0.8,
            ),
            EvidenceCard(
                evidence_id="e4",
                paper_id="p1",
                title="Paper 1",
                claim_text="Support 3",
                system_or_material="System",
                intervention="Intervention",
                outcome="Outcome",
                direction="positive",
                confidence=0.75,
            ),
        ],
    )
    repo.save_conflict_clusters(
        run.run_id,
        [
            ConflictCluster(
                cluster_id="cluster_1",
                topic_axis="axis",
                supporting_evidence_ids=["e1", "e3", "e4"],
                conflicting_evidence_ids=["e2"],
                conflict_type="direct_conflict",
                critic_summary="conflict",
                confidence=0.8,
            )
        ],
    )

    tools = WorkspaceTools(repository=repo)
    result = tools.save_hypotheses(
        run.run_id,
        {
            "hypotheses": [
                {
                    "rank": 1,
                    "title": "Hypothesis 1",
                    "hypothesis_statement": "Statement",
                    "why_plausible": "Plausible",
                    "why_not_obvious": "Not obvious",
                    "supporting_evidence_ids": ["e1", "e3", "e4"],
                    "counterevidence_ids": [],
                    "prediction": "Prediction",
                    "minimal_experiment": {
                        "system": "System",
                        "design": "Design",
                        "control": "Control",
                        "readouts": ["Readout"],
                        "success_criteria": "Success",
                        "failure_interpretation": "Failure",
                    },
                    "risks": ["risk"],
                    "novelty_score": 0.7,
                    "feasibility_score": 0.8,
                    "overall_score": 0.75,
                },
                {
                    "rank": 2,
                    "title": "Hypothesis 2",
                    "hypothesis_statement": "Statement",
                    "why_plausible": "Plausible",
                    "why_not_obvious": "Not obvious",
                    "supporting_evidence_ids": ["e1", "e3", "e4"],
                    "counterevidence_ids": ["e2"],
                    "prediction": "Prediction",
                    "minimal_experiment": {
                        "system": "System",
                        "design": "Design",
                        "control": "Control",
                        "readouts": ["Readout"],
                        "success_criteria": "Success",
                        "failure_interpretation": "Failure",
                    },
                    "risks": ["risk"],
                    "novelty_score": 0.7,
                    "feasibility_score": 0.8,
                    "overall_score": 0.75,
                },
                {
                    "rank": 3,
                    "title": "Hypothesis 3",
                    "hypothesis_statement": "Statement",
                    "why_plausible": "Plausible",
                    "why_not_obvious": "Not obvious",
                    "supporting_evidence_ids": ["e1", "e3", "e4"],
                    "counterevidence_ids": ["e2"],
                    "prediction": "Prediction",
                    "minimal_experiment": {
                        "system": "System",
                        "design": "Design",
                        "control": "Control",
                        "readouts": ["Readout"],
                        "success_criteria": "Success",
                        "failure_interpretation": "Failure",
                    },
                    "risks": ["risk"],
                    "novelty_score": 0.7,
                    "feasibility_score": 0.8,
                    "overall_score": 0.75,
                },
            ]
        },
    )

    assert result["hypothesis_ranks"] == [1, 2, 3]
    hypotheses = repo.load_hypotheses(run.run_id)
    assert hypotheses[0].counterevidence_ids == ["e2"]


def test_save_hypotheses_adds_limitations_and_uncertainty_for_degraded_context(tmp_path) -> None:
    repo = RunRepository.from_sqlite_path(tmp_path / "app.db")
    run = repo.create_run(RunRequest(topic="solid-state battery electrolyte"))
    repo.save_selected_papers(
        run.run_id,
        papers=[PaperDetail(paper_id="p1", title="Paper 1")],
        selection_reason="seed",
    )
    repo.save_evidence_cards(
        run.run_id,
        [
            EvidenceCard(
                evidence_id="e1",
                paper_id="p1",
                title="Paper 1",
                claim_text="Support 1",
                system_or_material="System",
                intervention="Intervention",
                outcome="Outcome",
                direction="positive",
                confidence=0.9,
            ),
            EvidenceCard(
                evidence_id="e2",
                paper_id="p1",
                title="Paper 1",
                claim_text="Support 2",
                system_or_material="System",
                intervention="Intervention",
                outcome="Outcome",
                direction="positive",
                confidence=0.8,
            ),
            EvidenceCard(
                evidence_id="e3",
                paper_id="p1",
                title="Paper 1",
                claim_text="Support 3",
                system_or_material="System",
                intervention="Intervention",
                outcome="Outcome",
                direction="positive",
                confidence=0.75,
            ),
            EvidenceCard(
                evidence_id="e4",
                paper_id="p1",
                title="Paper 1",
                claim_text="Potential counterevidence",
                system_or_material="System",
                intervention="Intervention",
                outcome="Outcome",
                direction="negative",
                confidence=0.6,
            ),
        ],
    )
    repo.finish_stage(
        run.run_id,
        "retrieval",
        summary={"coverage_assessment": "low", "needs_broader_search": True},
        status="degraded",
    )
    repo.finish_stage(
        run.run_id,
        "review",
        summary={"coverage_summary": "partial", "failed_paper_ids": ["p2"]},
        status="degraded",
    )
    repo.finish_stage(
        run.run_id,
        "critic",
        summary={},
        status="degraded",
        error_message="critic unavailable",
    )

    tools = WorkspaceTools(repository=repo)
    tools.save_hypotheses(
        run.run_id,
        {
            "hypotheses": [
                {
                    "rank": 1,
                    "title": "Hypothesis 1",
                    "hypothesis_statement": "Statement",
                    "why_plausible": "Plausible",
                    "why_not_obvious": "Not obvious",
                    "supporting_evidence_ids": ["e1", "e2", "e3"],
                    "counterevidence_ids": [],
                    "prediction": "Prediction",
                    "minimal_experiment": {
                        "system": "System",
                        "design": "Design",
                        "control": "Control",
                        "readouts": ["Readout"],
                        "success_criteria": "Success",
                        "failure_interpretation": "Failure",
                    },
                    "risks": [],
                    "novelty_score": 0.7,
                    "feasibility_score": 0.8,
                    "overall_score": 0.75,
                },
                {
                    "rank": 2,
                    "title": "Hypothesis 2",
                    "hypothesis_statement": "Statement",
                    "why_plausible": "Plausible",
                    "why_not_obvious": "Not obvious",
                    "supporting_evidence_ids": ["e1", "e2", "e3"],
                    "counterevidence_ids": [],
                    "prediction": "Prediction",
                    "minimal_experiment": {
                        "system": "System",
                        "design": "Design",
                        "control": "Control",
                        "readouts": ["Readout"],
                        "success_criteria": "Success",
                        "failure_interpretation": "Failure",
                    },
                    "risks": [],
                    "novelty_score": 0.7,
                    "feasibility_score": 0.8,
                    "overall_score": 0.75,
                },
                {
                    "rank": 3,
                    "title": "Hypothesis 3",
                    "hypothesis_statement": "Statement",
                    "why_plausible": "Plausible",
                    "why_not_obvious": "Not obvious",
                    "supporting_evidence_ids": ["e1", "e2", "e3"],
                    "counterevidence_ids": [],
                    "prediction": "Prediction",
                    "minimal_experiment": {
                        "system": "System",
                        "design": "Design",
                        "control": "Control",
                        "readouts": ["Readout"],
                        "success_criteria": "Success",
                        "failure_interpretation": "Failure",
                    },
                    "risks": [],
                    "novelty_score": 0.7,
                    "feasibility_score": 0.8,
                    "overall_score": 0.75,
                },
            ]
        },
    )

    hypotheses = repo.load_hypotheses(run.run_id)
    assert hypotheses[0].counterevidence_ids == ["e4"]
    assert any("low-evidence" in item for item in hypotheses[0].limitations)
    assert any("partial" in item for item in hypotheses[0].limitations)
    assert any("critic" in item for item in hypotheses[0].uncertainty_notes)


def test_save_hypotheses_repairs_missing_supporting_evidence_ids(tmp_path) -> None:
    repo = RunRepository.from_sqlite_path(tmp_path / "app.db")
    run = repo.create_run(RunRequest(topic="CO2 reduction catalyst selectivity"))
    repo.save_selected_papers(
        run.run_id,
        papers=[PaperDetail(paper_id="p1", title="Paper 1")],
        selection_reason="seed",
    )
    repo.save_evidence_cards(
        run.run_id,
        [
            EvidenceCard(
                evidence_id="e1",
                paper_id="p1",
                title="Paper 1",
                claim_text="Support 1",
                system_or_material="System",
                intervention="Intervention",
                outcome="Outcome",
                direction="positive",
                confidence=0.9,
            ),
            EvidenceCard(
                evidence_id="e2",
                paper_id="p1",
                title="Paper 1",
                claim_text="Support 2",
                system_or_material="System",
                intervention="Intervention",
                outcome="Outcome",
                direction="positive",
                confidence=0.8,
            ),
            EvidenceCard(
                evidence_id="e3",
                paper_id="p1",
                title="Paper 1",
                claim_text="Support 3",
                system_or_material="System",
                intervention="Intervention",
                outcome="Outcome",
                direction="positive",
                confidence=0.7,
            ),
            EvidenceCard(
                evidence_id="e4",
                paper_id="p1",
                title="Paper 1",
                claim_text="Conflict",
                system_or_material="System",
                intervention="Intervention",
                outcome="Outcome",
                direction="negative",
                confidence=0.6,
            ),
        ],
    )
    repo.save_conflict_clusters(
        run.run_id,
        [
            ConflictCluster(
                cluster_id="cluster_1",
                topic_axis="axis",
                supporting_evidence_ids=["e1", "e2", "e3"],
                conflicting_evidence_ids=["e4"],
                conflict_type="direct_conflict",
                critic_summary="conflict",
                confidence=0.8,
            )
        ],
    )

    tools = WorkspaceTools(repository=repo)
    tools.save_hypotheses(
        run.run_id,
        {
            "hypotheses": [
                {
                    "rank": 1,
                    "title": "Hypothesis 1",
                    "hypothesis_statement": "Statement",
                    "why_plausible": "Plausible",
                    "why_not_obvious": "Not obvious",
                    "supporting_evidence_ids": ["e1"],
                    "counterevidence_ids": ["e4"],
                    "prediction": "Prediction",
                    "minimal_experiment": {
                        "system": "System",
                        "design": "Design",
                        "control": "Control",
                        "readouts": ["Readout"],
                        "success_criteria": "Success",
                        "failure_interpretation": "Failure",
                    },
                    "risks": ["risk"],
                    "novelty_score": 0.7,
                    "feasibility_score": 0.8,
                    "overall_score": 0.75,
                },
                {
                    "rank": 2,
                    "title": "Hypothesis 2",
                    "hypothesis_statement": "Statement",
                    "why_plausible": "Plausible",
                    "why_not_obvious": "Not obvious",
                    "supporting_evidence_ids": ["e1"],
                    "counterevidence_ids": ["e4"],
                    "prediction": "Prediction",
                    "minimal_experiment": {
                        "system": "System",
                        "design": "Design",
                        "control": "Control",
                        "readouts": ["Readout"],
                        "success_criteria": "Success",
                        "failure_interpretation": "Failure",
                    },
                    "risks": ["risk"],
                    "novelty_score": 0.7,
                    "feasibility_score": 0.8,
                    "overall_score": 0.75,
                },
                {
                    "rank": 3,
                    "title": "Hypothesis 3",
                    "hypothesis_statement": "Statement",
                    "why_plausible": "Plausible",
                    "why_not_obvious": "Not obvious",
                    "supporting_evidence_ids": ["e1"],
                    "counterevidence_ids": ["e4"],
                    "prediction": "Prediction",
                    "minimal_experiment": {
                        "system": "System",
                        "design": "Design",
                        "control": "Control",
                        "readouts": ["Readout"],
                        "success_criteria": "Success",
                        "failure_interpretation": "Failure",
                    },
                    "risks": ["risk"],
                    "novelty_score": 0.7,
                    "feasibility_score": 0.8,
                    "overall_score": 0.75,
                },
            ]
        },
    )

    hypotheses = repo.load_hypotheses(run.run_id)
    assert hypotheses[0].supporting_evidence_ids == ["e1", "e2", "e3"]
    assert hypotheses[2].supporting_evidence_ids == ["e1", "e2", "e3"]


def test_save_hypotheses_rejects_insufficient_distinct_supporting_evidence_ids(tmp_path) -> None:
    repo = RunRepository.from_sqlite_path(tmp_path / "app.db")
    run = repo.create_run(RunRequest(topic="diffusion model preference optimization"))
    repo.save_selected_papers(
        run.run_id,
        papers=[PaperDetail(paper_id="p1", title="Paper 1")],
        selection_reason="seed",
    )
    repo.save_evidence_cards(
        run.run_id,
        [
            EvidenceCard(
                evidence_id="e1",
                paper_id="p1",
                title="Paper 1",
                claim_text="Support 1",
                system_or_material="System",
                intervention="Intervention",
                outcome="Outcome",
                direction="positive",
                confidence=0.9,
            ),
            EvidenceCard(
                evidence_id="e2",
                paper_id="p1",
                title="Paper 1",
                claim_text="Conflict 1",
                system_or_material="System",
                intervention="Intervention",
                outcome="Outcome",
                direction="negative",
                confidence=0.6,
            ),
        ],
    )
    repo.save_conflict_clusters(
        run.run_id,
        [
            ConflictCluster(
                cluster_id="cluster_1",
                topic_axis="axis",
                supporting_evidence_ids=["e1"],
                conflicting_evidence_ids=["e2"],
                conflict_type="direct_conflict",
                critic_summary="conflict",
                confidence=0.8,
            )
        ],
    )

    tools = WorkspaceTools(repository=repo)
    with pytest.raises(ValueError, match="3 distinct supporting evidence ids"):
        tools.save_hypotheses(
            run.run_id,
            {
                "hypotheses": [
                    {
                        "rank": 1,
                        "title": "Hypothesis 1",
                        "hypothesis_statement": "Statement",
                        "why_plausible": "Plausible",
                        "why_not_obvious": "Not obvious",
                        "supporting_evidence_ids": ["e1"],
                        "counterevidence_ids": ["e2"],
                        "prediction": "Prediction",
                        "minimal_experiment": {
                            "system": "System",
                            "design": "Design",
                            "control": "Control",
                            "readouts": ["Readout"],
                            "success_criteria": "Success",
                            "failure_interpretation": "Failure",
                        },
                        "risks": ["risk"],
                        "novelty_score": 0.7,
                        "feasibility_score": 0.8,
                        "overall_score": 0.75,
                    },
                    {
                        "rank": 2,
                        "title": "Hypothesis 2",
                        "hypothesis_statement": "Statement",
                        "why_plausible": "Plausible",
                        "why_not_obvious": "Not obvious",
                        "supporting_evidence_ids": ["e1"],
                        "counterevidence_ids": ["e2"],
                        "prediction": "Prediction",
                        "minimal_experiment": {
                            "system": "System",
                            "design": "Design",
                            "control": "Control",
                            "readouts": ["Readout"],
                            "success_criteria": "Success",
                            "failure_interpretation": "Failure",
                        },
                        "risks": ["risk"],
                        "novelty_score": 0.7,
                        "feasibility_score": 0.8,
                        "overall_score": 0.75,
                    },
                    {
                        "rank": 3,
                        "title": "Hypothesis 3",
                        "hypothesis_statement": "Statement",
                        "why_plausible": "Plausible",
                        "why_not_obvious": "Not obvious",
                        "supporting_evidence_ids": ["e1"],
                        "counterevidence_ids": ["e2"],
                        "prediction": "Prediction",
                        "minimal_experiment": {
                            "system": "System",
                            "design": "Design",
                            "control": "Control",
                            "readouts": ["Readout"],
                            "success_criteria": "Success",
                            "failure_interpretation": "Failure",
                        },
                        "risks": ["risk"],
                        "novelty_score": 0.7,
                        "feasibility_score": 0.8,
                        "overall_score": 0.75,
                    },
                ]
            },
        )
