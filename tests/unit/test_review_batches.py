import pytest

from hypoforge.application.services import _review_papers_in_batches
from hypoforge.domain.schemas import PaperDetail, ReviewSummary


def test_review_batches_aggregate_all_successful() -> None:
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
        return ReviewSummary(
            papers_processed=len(batch),
            evidence_cards_created=len(batch) + 1,
            coverage_summary=f"batch ok ({len(batch)})",
            dominant_axes=["conductivity"],
            low_confidence_paper_ids=[],
        )

    summary = _review_papers_in_batches(
        selected_papers=papers,
        batch_size=2,
        review_batch=review_batch,
    )

    assert calls == [["p1", "p2"], ["p3", "p4"], ["p5"]]
    assert summary.papers_processed == 5
    assert summary.evidence_cards_created == 8
    assert summary.dominant_axes == ["conductivity"]
    assert summary.failed_paper_ids == []
    assert "5/5" in summary.coverage_summary


def test_review_batches_raise_when_batch_fails() -> None:
    papers = [
        PaperDetail(paper_id="p1", title="Paper 1"),
        PaperDetail(paper_id="p2", title="Paper 2"),
        PaperDetail(paper_id="p3", title="Paper 3"),
    ]

    def review_batch(batch: list[PaperDetail]) -> ReviewSummary:
        batch_ids = [paper.paper_id for paper in batch]
        if "p3" in batch_ids:
            raise RuntimeError("batch failed")
        return ReviewSummary(
            papers_processed=len(batch),
            evidence_cards_created=len(batch),
            coverage_summary="ok",
            dominant_axes=[],
            low_confidence_paper_ids=[],
        )

    with pytest.raises(RuntimeError, match="batch failed"):
        _review_papers_in_batches(
            selected_papers=papers,
            batch_size=2,
            review_batch=review_batch,
        )


def test_review_batches_empty_papers() -> None:
    summary = _review_papers_in_batches(
        selected_papers=[],
        batch_size=2,
        review_batch=lambda batch: (_ for _ in ()).throw(RuntimeError("should not be called")),
    )

    assert summary.papers_processed == 0
    assert summary.evidence_cards_created == 0
