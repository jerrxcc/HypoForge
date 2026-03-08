from hypoforge.application.services import _run_retrieval_with_recovery
from hypoforge.domain.schemas import RetrievalSummary, RunConstraints


def test_retrieval_recovery_retries_once_and_broadens_year_range() -> None:
    attempts: list[tuple[int, bool]] = []

    def execute_attempt(constraints: RunConstraints, broadened: bool) -> tuple[RetrievalSummary, int]:
        attempts.append((constraints.year_from, broadened))
        if not broadened:
            return (
                RetrievalSummary(
                    canonical_topic="solid-state battery electrolyte",
                    query_variants_used=["solid-state battery electrolyte"],
                    search_notes=["initial search"],
                    selected_paper_ids=["p1", "p2", "p3", "p4", "p5"],
                    excluded_paper_ids=[],
                    coverage_assessment="medium",
                    needs_broader_search=False,
                ),
                5,
            )
        return (
            RetrievalSummary(
                canonical_topic="solid-state battery electrolyte",
                query_variants_used=["solid-state battery electrolyte", "solid electrolyte interface"],
                search_notes=["broadened search"],
                selected_paper_ids=[f"p{i}" for i in range(1, 13)],
                excluded_paper_ids=[],
                coverage_assessment="good",
                needs_broader_search=False,
            ),
            12,
        )

    summary = _run_retrieval_with_recovery(
        topic="solid-state battery electrolyte",
        constraints=RunConstraints(year_from=2020, year_to=2026, max_selected_papers=12),
        execute_attempt=execute_attempt,
    )

    assert attempts == [(2020, False), (2015, True)]
    assert len(summary.selected_paper_ids) == 12
    assert "broadened retrieval window after low recall" in summary.search_notes


def test_retrieval_recovery_marks_low_evidence_mode_after_broadened_retry() -> None:
    def execute_attempt(constraints: RunConstraints, broadened: bool) -> tuple[RetrievalSummary, int]:
        del constraints
        return (
            RetrievalSummary(
                canonical_topic="protein binder design",
                query_variants_used=["protein binder design"],
                search_notes=["search complete"],
                selected_paper_ids=["p1", "p2", "p3", "p4", "p5", "p6"],
                excluded_paper_ids=[],
                coverage_assessment="medium",
                needs_broader_search=False,
            ),
            6,
        )

    summary = _run_retrieval_with_recovery(
        topic="protein binder design",
        constraints=RunConstraints(year_from=2022, year_to=2026, max_selected_papers=12),
        execute_attempt=execute_attempt,
    )

    assert summary.coverage_assessment == "low"
    assert summary.needs_broader_search is True
    assert "low evidence mode" in summary.search_notes[-1]
