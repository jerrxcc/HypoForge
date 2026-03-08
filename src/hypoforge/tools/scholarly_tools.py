from __future__ import annotations

from typing import Callable

import httpx

from hypoforge.application.budget import BudgetExceededError
from hypoforge.domain.schemas import PaperDetail
from hypoforge.infrastructure.connectors.dedupe import dedupe_papers
from hypoforge.infrastructure.connectors.ranking import rank_papers
from hypoforge.infrastructure.db.repository import RunRepository
from hypoforge.tools.schemas import GetPaperDetailsArgs, RecommendPapersArgs, SaveSelectedPapersArgs, SearchPapersArgs


class ScholarlyTools:
    def __init__(self, openalex, semantic_scholar, repository: RunRepository, paper_lookup: Callable[[list[str]], list[dict | PaperDetail]] | None = None) -> None:
        self._openalex = openalex
        self._semantic_scholar = semantic_scholar
        self._repository = repository
        self._paper_lookup = paper_lookup

    def search_openalex_works(self, payload: dict) -> dict:
        args = SearchPapersArgs.model_validate(payload)
        return self._run_source_call(
            lambda: self._openalex.search_works(args.query, args.year_from, args.year_to, args.limit),
            source=self._openalex,
        )

    def search_semantic_scholar_papers(self, payload: dict) -> dict:
        args = SearchPapersArgs.model_validate(payload)
        return self._run_source_call(
            lambda: self._semantic_scholar.search_papers(
                args.query,
                args.year_from,
                args.year_to,
                args.limit,
            ),
            source=self._semantic_scholar,
        )

    def recommend_semantic_scholar_papers(self, payload: dict) -> dict:
        args = RecommendPapersArgs.model_validate(payload)
        return self._run_source_call(
            lambda: self._semantic_scholar.recommend_papers(args.positive_paper_ids, args.limit),
            source=self._semantic_scholar,
        )

    def get_paper_details(self, payload: dict) -> dict:
        args = GetPaperDetailsArgs.model_validate(payload)
        semantic_ids = [paper_id for paper_id in args.paper_ids if paper_id.startswith("S2:")]
        return self._run_source_call(
            lambda: self._semantic_scholar.get_paper_details(semantic_ids) if semantic_ids else [],
            source=self._semantic_scholar,
        )

    def merge_candidates(self, papers: list[PaperDetail]) -> list[PaperDetail]:
        return rank_papers(dedupe_papers(papers))

    def save_selected_papers(self, run_id: str, payload: dict) -> dict:
        args = SaveSelectedPapersArgs.model_validate(payload)
        papers = list(args.papers)
        if not papers and args.paper_ids:
            if self._paper_lookup is None:
                raise ValueError("save_selected_papers received paper_ids but no paper lookup is configured")
            papers = [
                paper if isinstance(paper, PaperDetail) else PaperDetail.model_validate(paper)
                for paper in self._paper_lookup(args.paper_ids)
            ]
            found_ids = {paper.paper_id for paper in papers}
            missing_ids = [paper_id for paper_id in args.paper_ids if paper_id not in found_ids]
            if missing_ids:
                raise ValueError(f"save_selected_papers could not resolve paper_ids: {missing_ids}")
        self._repository.save_selected_papers(run_id, papers, args.selection_reason)
        return {"paper_ids": [paper.paper_id for paper in papers], "selection_reason": args.selection_reason}

    def _run_source_call(self, fn: Callable[[], list[PaperDetail]], *, source=None) -> dict:
        try:
            papers = fn()
            return {
                "papers": [paper.model_dump() for paper in papers],
                "cache_hit": bool(getattr(source, "last_cache_hit", False)),
            }
        except httpx.HTTPStatusError as exc:
            return {
                "papers": [],
                "cache_hit": bool(getattr(source, "last_cache_hit", False)),
                "error": {
                    "type": "http_status_error",
                    "status_code": exc.response.status_code,
                    "message": str(exc),
                },
            }
        except BudgetExceededError as exc:
            return {
                "papers": [],
                "cache_hit": bool(getattr(source, "last_cache_hit", False)),
                "error": {
                    "type": "budget_exceeded",
                    "source": exc.source,
                    "message": str(exc),
                },
            }
        except httpx.HTTPError as exc:
            return {
                "papers": [],
                "cache_hit": bool(getattr(source, "last_cache_hit", False)),
                "error": {
                    "type": "http_error",
                    "message": str(exc),
                },
            }
