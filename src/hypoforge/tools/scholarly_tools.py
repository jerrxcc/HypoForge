from __future__ import annotations

from hypoforge.domain.schemas import PaperDetail
from hypoforge.infrastructure.connectors.dedupe import dedupe_papers
from hypoforge.infrastructure.connectors.ranking import rank_papers
from hypoforge.infrastructure.db.repository import RunRepository
from hypoforge.tools.schemas import GetPaperDetailsArgs, RecommendPapersArgs, SaveSelectedPapersArgs, SearchPapersArgs


class ScholarlyTools:
    def __init__(self, openalex, semantic_scholar, repository: RunRepository) -> None:
        self._openalex = openalex
        self._semantic_scholar = semantic_scholar
        self._repository = repository

    def search_openalex_works(self, payload: dict) -> dict:
        args = SearchPapersArgs.model_validate(payload)
        papers = self._openalex.search_works(args.query, args.year_from, args.year_to, args.limit)
        return {"papers": [paper.model_dump() for paper in papers]}

    def search_semantic_scholar_papers(self, payload: dict) -> dict:
        args = SearchPapersArgs.model_validate(payload)
        papers = self._semantic_scholar.search_papers(
            args.query,
            args.year_from,
            args.year_to,
            args.limit,
        )
        return {"papers": [paper.model_dump() for paper in papers]}

    def recommend_semantic_scholar_papers(self, payload: dict) -> dict:
        args = RecommendPapersArgs.model_validate(payload)
        papers = self._semantic_scholar.recommend_papers(args.positive_paper_ids, args.limit)
        return {"papers": [paper.model_dump() for paper in papers]}

    def get_paper_details(self, payload: dict) -> dict:
        args = GetPaperDetailsArgs.model_validate(payload)
        semantic_ids = [paper_id for paper_id in args.paper_ids if paper_id.startswith("S2:")]
        papers = self._semantic_scholar.get_paper_details(semantic_ids) if semantic_ids else []
        return {"papers": [paper.model_dump() for paper in papers]}

    def merge_candidates(self, papers: list[PaperDetail]) -> list[PaperDetail]:
        return rank_papers(dedupe_papers(papers))

    def save_selected_papers(self, run_id: str, payload: dict) -> dict:
        args = SaveSelectedPapersArgs.model_validate(payload)
        papers = args.papers
        if not papers and args.paper_ids:
            raise ValueError("save_selected_papers currently requires full paper payloads")
        self._repository.save_selected_papers(run_id, papers, args.selection_reason)
        return {"paper_ids": [paper.paper_id for paper in papers], "selection_reason": args.selection_reason}

