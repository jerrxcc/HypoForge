from hypoforge.domain.schemas import PaperDetail
from hypoforge.infrastructure.connectors.dedupe import dedupe_papers


def test_dedupe_prefers_record_with_abstract() -> None:
    winners = dedupe_papers(
        [
            PaperDetail(
                paper_id="p1",
                title="Solid State Battery",
                abstract=None,
                year=2024,
                authors=["A"],
                doi="10.1/example",
            ),
            PaperDetail(
                paper_id="p2",
                title="Solid State Battery",
                abstract="useful abstract",
                year=2024,
                authors=["A"],
                doi="10.1/example",
            ),
        ]
    )

    assert len(winners) == 1
    assert winners[0].abstract == "useful abstract"


def test_dedupe_merges_provenance_and_source_urls_for_duplicate_papers() -> None:
    winners = dedupe_papers(
        [
            PaperDetail(
                paper_id="oa:W1",
                title="Solid State Battery",
                abstract="short",
                year=2024,
                doi="10.1/example",
                provenance=["openalex.search"],
                source_urls={"openalex": "https://openalex.org/W1"},
            ),
            PaperDetail(
                paper_id="ax:2401.12345",
                title="Solid State Battery",
                abstract="much better abstract",
                year=2024,
                doi="10.1/example",
                provenance=["alphaxiv.embedding_similarity_search"],
                source_urls={
                    "alphaxiv": "https://alphaxiv.org/overview/2401.12345",
                    "arxiv": "https://arxiv.org/abs/2401.12345",
                },
            ),
        ]
    )

    assert len(winners) == 1
    assert winners[0].abstract == "much better abstract"
    assert winners[0].provenance == [
        "alphaxiv.embedding_similarity_search",
        "openalex.search",
    ]
    assert winners[0].source_urls["openalex"] == "https://openalex.org/W1"
    assert winners[0].source_urls["alphaxiv"] == "https://alphaxiv.org/overview/2401.12345"
