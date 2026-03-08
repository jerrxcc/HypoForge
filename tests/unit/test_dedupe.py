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

