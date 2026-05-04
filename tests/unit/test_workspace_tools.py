import pytest

from hypoforge.domain.schemas import (
    ConflictCluster,
    EvidenceCard,
    PaperDetail,
    RunRequest,
)
from hypoforge.infrastructure.db.repository import RunRepository
from hypoforge.tools.workspace_tools import WorkspaceTools


def test_save_hypotheses_persists_valid_grounded_payload(tmp_path) -> None:
    repo, run_id = _seed_grounded_run(tmp_path)
    tools = WorkspaceTools(repository=repo)

    result = tools.save_hypotheses(
        run_id,
        {"hypotheses": [_hypothesis_payload(rank) for rank in (1, 2, 3)]},
    )

    hypotheses = repo.load_hypotheses(run_id)
    assert result["hypothesis_ranks"] == [1, 2, 3]
    assert hypotheses[0].supporting_evidence_ids == ["e1", "e2", "e3"]
    assert hypotheses[0].counterevidence_ids == ["e4"]
    assert hypotheses[0].risks == [
        "Grounding is limited to the retrieved abstracts and evidence cards rather than full-text review."
    ]


def test_save_hypotheses_rejects_missing_counterevidence_ids(tmp_path) -> None:
    repo, run_id = _seed_grounded_run(tmp_path)
    tools = WorkspaceTools(repository=repo)
    payloads = [_hypothesis_payload(rank) for rank in (1, 2, 3)]
    payloads[0]["counterevidence_ids"] = []

    with pytest.raises(ValueError, match="at least 1 counterevidence id"):
        tools.save_hypotheses(run_id, {"hypotheses": payloads})


def test_save_hypotheses_rejects_missing_supporting_evidence_ids(tmp_path) -> None:
    repo, run_id = _seed_grounded_run(tmp_path)
    tools = WorkspaceTools(repository=repo)
    payloads = [_hypothesis_payload(rank) for rank in (1, 2, 3)]
    payloads[0]["supporting_evidence_ids"] = ["e1"]

    with pytest.raises(ValueError, match="3 distinct supporting evidence ids"):
        tools.save_hypotheses(run_id, {"hypotheses": payloads})


def test_save_hypotheses_rejects_unknown_evidence_ids(tmp_path) -> None:
    repo, run_id = _seed_grounded_run(tmp_path)
    tools = WorkspaceTools(repository=repo)
    payloads = [_hypothesis_payload(rank) for rank in (1, 2, 3)]
    payloads[0]["supporting_evidence_ids"] = ["e1", "e2", "phantom_evidence"]

    with pytest.raises(ValueError, match="must reference saved evidence cards"):
        tools.save_hypotheses(run_id, {"hypotheses": payloads})


def test_save_conflict_clusters_rejects_unknown_evidence_ids(tmp_path) -> None:
    repo = RunRepository.from_sqlite_path(tmp_path / "app.db")
    run = repo.create_run(RunRequest(topic="solid-state battery electrolyte"))
    repo.save_evidence_cards(
        run.run_id,
        [
            _evidence_card("e1", "positive", "Support"),
            _evidence_card("e2", "negative", "Conflict"),
        ],
    )
    tools = WorkspaceTools(repository=repo)

    with pytest.raises(ValueError, match="conflict cluster evidence ids"):
        tools.save_conflict_clusters(
            run.run_id,
            {
                "conflict_clusters": [
                    {
                        "cluster_id": "cluster_1",
                        "topic_axis": "axis",
                        "supporting_evidence_ids": ["e1", "phantom_evidence"],
                        "conflicting_evidence_ids": ["e2"],
                        "conflict_type": "direct_conflict",
                        "critic_summary": "conflict",
                        "confidence": 0.8,
                    }
                ]
            },
        )

    assert repo.load_conflict_clusters(run.run_id) == []


def _seed_grounded_run(tmp_path) -> tuple[RunRepository, str]:
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
            _evidence_card("e1", "positive", "Support 1"),
            _evidence_card("e2", "positive", "Support 2"),
            _evidence_card("e3", "positive", "Support 3"),
            _evidence_card("e4", "negative", "Conflict"),
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
    return repo, run.run_id


def _evidence_card(evidence_id: str, direction: str, claim_text: str) -> EvidenceCard:
    return EvidenceCard(
        evidence_id=evidence_id,
        paper_id="p1",
        title="Paper 1",
        claim_text=claim_text,
        system_or_material="System",
        intervention="Intervention",
        outcome="Outcome",
        direction=direction,
        confidence=0.8,
    )


def _hypothesis_payload(rank: int) -> dict:
    return {
        "rank": rank,
        "title": f"Hypothesis {rank}",
        "hypothesis_statement": "Statement",
        "why_plausible": "Plausible",
        "why_not_obvious": "Not obvious",
        "supporting_evidence_ids": ["e1", "e2", "e3"],
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
        "novelty_score": 0.7,
        "feasibility_score": 0.8,
        "overall_score": 0.75,
    }
