from hypoforge.application.services import _review_papers_in_batches
from hypoforge.domain.schemas import PaperDetail, ReviewSummary


def test_review_batches_aggregate_partial_failures() -> None:
    papers = [
        PaperDetail(paper_id="p1", title="Paper 1"),
        PaperDetail(paper_id="p2", title="Paper 2"),
        PaperDetail(paper_id="p3", title="Paper 3"),
        PaperDetail(paper_id="p4", title="Paper 4"),
        PaperDetail(paper_id="p5", title="Paper 5"),
    ]
    calls: list[list[str]] = []

    def review_batch(batch: list[PaperDetail]) -> ReviewSummary:
        batch_ids = [paper.paper_id for paper in batch]
        calls.append(batch_ids)
        if batch_ids == ["p3", "p4"]:
            raise RuntimeError("batch failed")
        if batch_ids == ["p1", "p2"]:
            return ReviewSummary(
                papers_processed=2,
                evidence_cards_created=3,
                coverage_summary="batch 1 ok",
                dominant_axes=["conductivity"],
                low_confidence_paper_ids=["p2"],
            )
        return ReviewSummary(
            papers_processed=1,
            evidence_cards_created=1,
            coverage_summary="batch 3 ok",
            dominant_axes=["stability"],
            low_confidence_paper_ids=[],
        )

    summary = _review_papers_in_batches(
        selected_papers=papers,
        batch_size=2,
        review_batch=review_batch,
    )

    assert calls == [["p1", "p2"], ["p3", "p4"], ["p5"]]
    assert summary.papers_processed == 3
    assert summary.evidence_cards_created == 4
    assert summary.dominant_axes == ["conductivity", "stability"]
    assert summary.low_confidence_paper_ids == ["p2"]
    assert summary.failed_paper_ids == ["p3", "p4"]
    assert "3/5" in summary.coverage_summary


def test_review_batches_raise_when_all_batches_fail() -> None:
    papers = [
        PaperDetail(paper_id="p1", title="Paper 1"),
        PaperDetail(paper_id="p2", title="Paper 2"),
    ]

    def review_batch(batch: list[PaperDetail]) -> ReviewSummary:
        del batch
        raise RuntimeError("all failed")

    try:
        _review_papers_in_batches(
            selected_papers=papers,
            batch_size=1,
            review_batch=review_batch,
        )
    except RuntimeError as exc:
        assert str(exc) == "all failed"
    else:
        raise AssertionError("expected batch failure to be raised")
