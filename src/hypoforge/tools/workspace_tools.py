from __future__ import annotations

from hypoforge.infrastructure.db.repository import RunRepository
from hypoforge.tools.schemas import SaveConflictClustersArgs, SaveEvidenceCardsArgs, SaveHypothesesArgs


class WorkspaceTools:
    def __init__(self, repository: RunRepository) -> None:
        self._repository = repository

    def load_selected_papers(self, run_id: str, payload: dict | None = None) -> dict:
        del payload
        papers = self._repository.load_selected_papers(run_id)
        return {"papers": [paper.model_dump() for paper in papers]}

    def save_evidence_cards(self, run_id: str, payload: dict) -> dict:
        args = SaveEvidenceCardsArgs.model_validate(payload)
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
        args = SaveHypothesesArgs.model_validate(payload)
        self._repository.save_hypotheses(run_id, args.hypotheses)
        return {"hypothesis_ranks": [hypothesis.rank for hypothesis in args.hypotheses]}

    def load_hypotheses(self, run_id: str, payload: dict | None = None) -> dict:
        del payload
        hypotheses = self._repository.load_hypotheses(run_id)
        return {"hypotheses": [hypothesis.model_dump() for hypothesis in hypotheses]}

