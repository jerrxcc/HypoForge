from __future__ import annotations

from hypoforge.domain.schemas import ConflictCluster, Hypothesis, StageSummary
from hypoforge.infrastructure.db.repository import RunRepository
from hypoforge.tools.schemas import (
    SaveConflictClustersArgs,
    SaveEvidenceCardsArgs,
    SaveHypothesesArgs,
)
from hypoforge.tools.errors import RecoverableToolInputError


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
        valid_ids = {
            card.evidence_id for card in self._repository.load_evidence_cards(run_id)
        }
        invalid_refs: list[str] = []
        for cluster in args.conflict_clusters:
            invalid_supporting = [
                eid for eid in cluster.supporting_evidence_ids if eid not in valid_ids
            ]
            invalid_conflicting = [
                eid for eid in cluster.conflicting_evidence_ids if eid not in valid_ids
            ]
            if invalid_supporting:
                invalid_refs.append(
                    f"{cluster.cluster_id} supporting_evidence_ids={invalid_supporting}"
                )
            if invalid_conflicting:
                invalid_refs.append(
                    f"{cluster.cluster_id} conflicting_evidence_ids={invalid_conflicting}"
                )
        if invalid_refs:
            raise RecoverableToolInputError(
                "conflict cluster evidence ids must reference saved evidence cards: "
                + "; ".join(invalid_refs),
                instruction=(
                    "Call load_evidence_cards again if needed, then re-call "
                    "save_conflict_clusters using only exact EvidenceCard.evidence_id "
                    "values from the loaded evidence cards."
                ),
            )
        self._repository.save_conflict_clusters(run_id, args.conflict_clusters)
        return {
            "cluster_ids": [cluster.cluster_id for cluster in args.conflict_clusters]
        }

    def load_conflict_clusters(self, run_id: str, payload: dict | None = None) -> dict:
        del payload
        clusters = self._repository.load_conflict_clusters(run_id)
        return {"conflict_clusters": [cluster.model_dump() for cluster in clusters]}

    def save_hypotheses(self, run_id: str, payload: dict) -> dict:
        args = SaveHypothesesArgs.model_validate(payload)
        self._validate_hypothesis_grounding(run_id, args.hypotheses)
        self._annotate_hypothesis_credibility(run_id, args.hypotheses)
        self._repository.save_hypotheses(run_id, args.hypotheses)
        return {"hypothesis_ranks": [hypothesis.rank for hypothesis in args.hypotheses]}

    def load_hypotheses(self, run_id: str, payload: dict | None = None) -> dict:
        del payload
        hypotheses = self._repository.load_hypotheses(run_id)
        return {"hypotheses": [hypothesis.model_dump() for hypothesis in hypotheses]}

    def _validate_hypothesis_grounding(
        self,
        run_id: str,
        hypotheses: list[Hypothesis],
    ) -> None:
        valid_ids = {
            card.evidence_id for card in self._repository.load_evidence_cards(run_id)
        }
        invalid_refs: list[str] = []
        for hypothesis in hypotheses:
            invalid_supporting = [
                evidence_id
                for evidence_id in hypothesis.supporting_evidence_ids
                if evidence_id not in valid_ids
            ]
            invalid_counter = [
                evidence_id
                for evidence_id in hypothesis.counterevidence_ids
                if evidence_id not in valid_ids
            ]
            if invalid_supporting:
                invalid_refs.append(
                    f"rank {hypothesis.rank} supporting_evidence_ids={invalid_supporting}"
                )
            if invalid_counter:
                invalid_refs.append(
                    f"rank {hypothesis.rank} counterevidence_ids={invalid_counter}"
                )
        if invalid_refs:
            raise RecoverableToolInputError(
                "hypothesis evidence ids must reference saved evidence cards: "
                + "; ".join(invalid_refs),
                instruction=(
                    "Call load_evidence_cards and load_conflict_clusters again if needed, "
                    "then re-call save_hypotheses using only exact EvidenceCard.evidence_id "
                    "values from the loaded evidence cards."
                ),
            )

    def _annotate_hypothesis_credibility(
        self,
        run_id: str,
        hypotheses: list[Hypothesis],
    ) -> None:
        if not hypotheses:
            return

        clusters = self._repository.load_conflict_clusters(run_id)
        stage_summaries = {
            summary.stage_name: summary
            for summary in self._repository.list_stage_summaries(run_id)
        }
        retrieval_low_evidence = self._is_retrieval_low_evidence(
            stage_summaries.get("retrieval")
        )
        review_partial = self._is_review_partial(stage_summaries.get("review"))
        critic_unavailable = self._is_critic_unavailable(
            stage_summaries.get("critic"), clusters
        )

        for hypothesis in hypotheses:
            self._apply_credibility_annotations(
                hypothesis,
                retrieval_low_evidence=retrieval_low_evidence,
                review_partial=review_partial,
                critic_unavailable=critic_unavailable,
            )

    def _apply_credibility_annotations(
        self,
        hypothesis: Hypothesis,
        *,
        retrieval_low_evidence: bool,
        review_partial: bool,
        critic_unavailable: bool,
    ) -> None:
        limitations = list(hypothesis.limitations)
        uncertainty_notes = list(hypothesis.uncertainty_notes)
        risks = list(hypothesis.risks)

        if retrieval_low_evidence:
            limitations.append(
                "Built from a low-evidence retrieval set, so literature coverage may be incomplete."
            )
            uncertainty_notes.append(
                "Confidence is provisional because retrieval entered low-evidence mode."
            )
        if review_partial:
            limitations.append(
                "Evidence extraction was partial, so some selected papers may not be represented in the evidence cards."
            )
        if critic_unavailable:
            limitations.append(
                "Conflict analysis was unavailable or empty, so counterevidence coverage may be incomplete."
            )
            uncertainty_notes.append(
                "The critic stage did not produce a usable conflict map, so this hypothesis should be treated as provisional."
            )
        if not risks:
            risks.append(
                "Grounding is limited to the retrieved abstracts and evidence cards rather than full-text review."
            )

        hypothesis.limitations = list(dict.fromkeys(limitations))
        hypothesis.uncertainty_notes = list(dict.fromkeys(uncertainty_notes))
        hypothesis.risks = list(dict.fromkeys(risks))

    def _is_retrieval_low_evidence(self, summary: StageSummary | None) -> bool:
        if summary is None:
            return False
        coverage = summary.summary.get("coverage_assessment")
        return coverage == "low" or bool(summary.summary.get("needs_broader_search"))

    def _is_review_partial(self, summary: StageSummary | None) -> bool:
        if summary is None:
            return False
        return bool(summary.summary.get("failed_paper_ids"))

    def _is_critic_unavailable(
        self,
        summary: StageSummary | None,
        clusters: list[ConflictCluster],
    ) -> bool:
        if not clusters:
            return True
        if summary is None:
            return False
        return summary.status == "failed"
