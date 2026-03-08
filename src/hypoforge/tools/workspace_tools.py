from __future__ import annotations

from hypoforge.infrastructure.db.repository import RunRepository
from hypoforge.domain.schemas import ConflictCluster
from hypoforge.tools.schemas import SaveConflictClustersArgs, SaveEvidenceCardsArgs, SaveHypothesesArgs


class WorkspaceTools:
    def __init__(
        self,
        repository: RunRepository,
        *,
        selected_paper_ids: list[str] | None = None,
        append_evidence_cards: bool = False,
    ) -> None:
        self._repository = repository
        self._selected_paper_ids = selected_paper_ids
        self._append_evidence_cards = append_evidence_cards

    def load_selected_papers(self, run_id: str, payload: dict | None = None) -> dict:
        requested_ids = None
        if payload:
            requested_ids = payload.get("paper_ids")
        papers = self._repository.load_selected_papers(run_id)
        if self._selected_paper_ids is not None:
            allowed = set(self._selected_paper_ids)
            papers = [paper for paper in papers if paper.paper_id in allowed]
        if requested_ids:
            requested = set(requested_ids)
            papers = [paper for paper in papers if paper.paper_id in requested]
        return {"papers": [paper.model_dump() for paper in papers]}

    def save_evidence_cards(self, run_id: str, payload: dict) -> dict:
        args = SaveEvidenceCardsArgs.model_validate(payload)
        if self._append_evidence_cards:
            self._repository.append_evidence_cards(run_id, args.evidence_cards)
        else:
            self._repository.save_evidence_cards(run_id, args.evidence_cards)
        return {"evidence_ids": [card.evidence_id for card in args.evidence_cards]}

    def load_evidence_cards(self, run_id: str, payload: dict | None = None) -> dict:
        del payload
        cards = self._repository.load_evidence_cards(run_id)
        return {"evidence_cards": [card.model_dump() for card in cards]}

    def save_conflict_clusters(self, run_id: str, payload: dict) -> dict:
        args = SaveConflictClustersArgs.model_validate(payload)
        self._repository.save_conflict_clusters(run_id, args.conflict_clusters)
        return {"cluster_ids": [cluster.cluster_id for cluster in args.conflict_clusters]}

    def load_conflict_clusters(self, run_id: str, payload: dict | None = None) -> dict:
        del payload
        clusters = self._repository.load_conflict_clusters(run_id)
        return {"conflict_clusters": [cluster.model_dump() for cluster in clusters]}

    def save_hypotheses(self, run_id: str, payload: dict) -> dict:
        args = SaveHypothesesArgs.model_validate(
            self._repair_hypothesis_payload(run_id, payload)
        )
        self._repository.save_hypotheses(run_id, args.hypotheses)
        return {"hypothesis_ranks": [hypothesis.rank for hypothesis in args.hypotheses]}

    def load_hypotheses(self, run_id: str, payload: dict | None = None) -> dict:
        del payload
        hypotheses = self._repository.load_hypotheses(run_id)
        return {"hypotheses": [hypothesis.model_dump() for hypothesis in hypotheses]}

    def _repair_hypothesis_payload(self, run_id: str, payload: dict) -> dict:
        repaired = dict(payload)
        hypotheses = [dict(item) for item in repaired.get("hypotheses", [])]
        if not hypotheses:
            return repaired

        clusters = self._repository.load_conflict_clusters(run_id)
        evidence_cards = self._repository.load_evidence_cards(run_id)
        all_conflicting_ids = self._collect_conflicting_ids(clusters)
        all_evidence_ids = [card.evidence_id for card in evidence_cards]

        for hypothesis in hypotheses:
            if hypothesis.get("counterevidence_ids"):
                continue
            supporting_ids = hypothesis.get("supporting_evidence_ids", [])
            candidate_ids = self._infer_counterevidence_ids(
                supporting_ids=supporting_ids,
                clusters=clusters,
                all_conflicting_ids=all_conflicting_ids,
                all_evidence_ids=all_evidence_ids,
            )
            if candidate_ids:
                hypothesis["counterevidence_ids"] = candidate_ids[:3]
        repaired["hypotheses"] = hypotheses
        return repaired

    def _infer_counterevidence_ids(
        self,
        *,
        supporting_ids: list[str],
        clusters: list[ConflictCluster],
        all_conflicting_ids: list[str],
        all_evidence_ids: list[str],
    ) -> list[str]:
        related_conflicts: list[str] = []
        supporting_set = set(supporting_ids)
        for cluster in clusters:
            if supporting_set.intersection(cluster.supporting_evidence_ids):
                related_conflicts.extend(cluster.conflicting_evidence_ids)
        if related_conflicts:
            return list(dict.fromkeys(related_conflicts))
        fallback_conflicts = [
            evidence_id for evidence_id in all_conflicting_ids if evidence_id not in supporting_set
        ]
        if fallback_conflicts:
            return list(dict.fromkeys(fallback_conflicts))
        return [
            evidence_id for evidence_id in all_evidence_ids if evidence_id not in supporting_set
        ]

    def _collect_conflicting_ids(self, clusters: list[ConflictCluster]) -> list[str]:
        conflicting_ids: list[str] = []
        for cluster in clusters:
            conflicting_ids.extend(cluster.conflicting_evidence_ids)
        return list(dict.fromkeys(conflicting_ids))
