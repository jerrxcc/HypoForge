from __future__ import annotations

from hypoforge.domain.schemas import PaperDetail
from hypoforge.infrastructure.connectors.normalizers import normalize_title


def _paper_key(paper: PaperDetail) -> tuple[str, ...]:
    if paper.doi:
        return ("doi", paper.doi.lower())
    return ("title-year", normalize_title(paper.title), str(paper.year or ""))


def _paper_score(paper: PaperDetail) -> tuple[int, int, int]:
    has_abstract = 1 if paper.abstract else 0
    citation_count = paper.citation_count or 0
    provenance_count = len(paper.provenance)
    return (has_abstract, citation_count, provenance_count)


def dedupe_papers(papers: list[PaperDetail]) -> list[PaperDetail]:
    winners: dict[tuple[str, ...], PaperDetail] = {}
    for paper in papers:
        key = _paper_key(paper)
        current = winners.get(key)
        if current is None or _paper_score(paper) > _paper_score(current):
            winners[key] = paper
    return list(winners.values())

