from __future__ import annotations

from hypoforge.domain.schemas import PaperDetail


def rank_papers(papers: list[PaperDetail]) -> list[PaperDetail]:
    return sorted(
        papers,
        key=lambda paper: (
            1 if paper.abstract else 0,
            paper.citation_count or 0,
            paper.year or 0,
        ),
        reverse=True,
    )

