from __future__ import annotations

from hypoforge.domain.schemas import PaperDetail
from hypoforge.infrastructure.connectors.normalizers import normalize_title


def paper_identity_key(paper: PaperDetail) -> tuple[str, ...]:
    if paper.doi:
        return ("doi", paper.doi.lower())
    return ("title-year", normalize_title(paper.title), str(paper.year or ""))


def merge_paper_details(primary: PaperDetail, secondary: PaperDetail) -> PaperDetail:
    """Merge duplicate papers while preserving multi-source provenance."""
    external_ids = dict(secondary.external_ids)
    external_ids.update({key: value for key, value in primary.external_ids.items() if value not in (None, "")})

    source_urls = dict(secondary.source_urls)
    source_urls.update({key: value for key, value in primary.source_urls.items() if value})

    authors = _merge_text_lists(primary.authors, secondary.authors)
    fields_of_study = _merge_text_lists(primary.fields_of_study, secondary.fields_of_study)
    topic_labels = _merge_text_lists(primary.topic_labels, secondary.topic_labels)
    provenance = _merge_text_lists(primary.provenance, secondary.provenance)

    return primary.model_copy(
        update={
            "doi": primary.doi or secondary.doi,
            "external_ids": external_ids,
            "title": primary.title or secondary.title,
            "abstract": _pick_better_text(primary.abstract, secondary.abstract),
            "year": primary.year or secondary.year,
            "authors": authors,
            "venue": _pick_better_text(primary.venue, secondary.venue),
            "citation_count": _pick_higher_int(primary.citation_count, secondary.citation_count),
            "publication_type": primary.publication_type or secondary.publication_type,
            "fields_of_study": fields_of_study,
            "topic_labels": topic_labels,
            "source": primary.source or secondary.source,
            "url": primary.url or secondary.url,
            "source_urls": source_urls,
            "provenance": provenance,
        }
    )


def dedupe_papers(papers: list[PaperDetail]) -> list[PaperDetail]:
    winners: dict[tuple[str, ...], PaperDetail] = {}
    for paper in papers:
        key = paper_identity_key(paper)
        current = winners.get(key)
        if current is None:
            winners[key] = paper
            continue

        preferred, secondary = _prefer_primary(current, paper)
        winners[key] = merge_paper_details(preferred, secondary)
    return list(winners.values())


def _paper_score(paper: PaperDetail) -> tuple[int, int, int, int]:
    has_abstract = 1 if paper.abstract else 0
    abstract_length = len((paper.abstract or "").strip())
    citation_count = paper.citation_count or 0
    provenance_count = len(paper.provenance)
    return (has_abstract, abstract_length, citation_count, provenance_count)


def _prefer_primary(first: PaperDetail, second: PaperDetail) -> tuple[PaperDetail, PaperDetail]:
    if _paper_score(second) > _paper_score(first):
        return second, first
    return first, second


def _merge_text_lists(primary: list[str], secondary: list[str]) -> list[str]:
    merged: list[str] = []
    for value in [*primary, *secondary]:
        normalized = value.strip()
        if not normalized or normalized in merged:
            continue
        merged.append(normalized)
    return merged


def _pick_better_text(primary: str | None, secondary: str | None) -> str | None:
    if primary and len(primary.strip()) >= len((secondary or "").strip()):
        return primary
    return secondary or primary


def _pick_higher_int(primary: int | None, secondary: int | None) -> int | None:
    if primary is None:
        return secondary
    if secondary is None:
        return primary
    return max(primary, secondary)
