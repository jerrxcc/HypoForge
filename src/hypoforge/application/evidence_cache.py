"""Evidence-card caching helpers.

These functions let the review stage skip LLM extraction when the same
paper was already processed with the same model and prompt version.
"""

from __future__ import annotations

from collections import defaultdict

from hypoforge.domain.schemas import EvidenceCard, PaperDetail
from hypoforge.infrastructure.db.cache_repository import CacheRepository
from hypoforge.infrastructure.db.repository import RunRepository


def evidence_cache_key(paper_id: str, model_name: str, prompt_version: str) -> str:
    return f"{paper_id}:{model_name}:{prompt_version}"


def load_cached_evidence_cards_for_papers(
    *,
    papers: list[PaperDetail],
    cache_repository: CacheRepository,
    model_name: str,
    prompt_version: str,
) -> list[EvidenceCard] | None:
    if not papers:
        return None
    cards: list[EvidenceCard] = []
    for paper in papers:
        payload = cache_repository.get(
            "evidence_extraction",
            evidence_cache_key(paper.paper_id, model_name, prompt_version),
        )
        if payload is None:
            return None
        cards.extend(EvidenceCard.model_validate(card) for card in payload["evidence_cards"])
    return cards


def save_evidence_cards_to_cache(
    *,
    run_id: str,
    papers: list[PaperDetail],
    repository: RunRepository,
    cache_repository: CacheRepository,
    model_name: str,
    prompt_version: str,
    ttl_seconds: int,
) -> None:
    cards = repository.load_evidence_cards(run_id)
    allowed_paper_ids = {paper.paper_id for paper in papers}
    cards_by_paper: dict[str, list[EvidenceCard]] = defaultdict(list)
    for card in cards:
        if card.paper_id not in allowed_paper_ids:
            continue
        cards_by_paper[card.paper_id].append(card)
    for paper_id, paper_cards in cards_by_paper.items():
        cache_repository.set(
            "evidence_extraction",
            evidence_cache_key(paper_id, model_name, prompt_version),
            {"evidence_cards": [card.model_dump() for card in paper_cards]},
            ttl_seconds=ttl_seconds,
        )
