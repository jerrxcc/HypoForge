from __future__ import annotations

from pydantic import BaseModel, Field

from hypoforge.domain.schemas import ConflictCluster, EvidenceCard, Hypothesis, PaperDetail


class SearchPapersArgs(BaseModel):
    query: str
    year_from: int
    year_to: int
    limit: int = Field(default=15, ge=1, le=50)


class RecommendPapersArgs(BaseModel):
    positive_paper_ids: list[str]
    limit: int = Field(default=20, ge=1, le=50)


class GetPaperDetailsArgs(BaseModel):
    paper_ids: list[str]


class SaveSelectedPapersArgs(BaseModel):
    paper_ids: list[str] = Field(default_factory=list)
    papers: list[PaperDetail] = Field(default_factory=list)
    selection_reason: str


class SaveEvidenceCardsArgs(BaseModel):
    evidence_cards: list[EvidenceCard]


class SaveConflictClustersArgs(BaseModel):
    conflict_clusters: list[ConflictCluster]


class SaveHypothesesArgs(BaseModel):
    hypotheses: list[Hypothesis]


class RenderReportArgs(BaseModel):
    include_appendix: bool = True


class LoadSelectedPapersArgs(BaseModel):
    note: str | None = None


class LoadEvidenceCardsArgs(BaseModel):
    note: str | None = None


class LoadConflictClustersArgs(BaseModel):
    note: str | None = None


TOOL_ARG_MODELS = {
    "search_openalex_works": SearchPapersArgs,
    "search_semantic_scholar_papers": SearchPapersArgs,
    "recommend_semantic_scholar_papers": RecommendPapersArgs,
    "get_paper_details": GetPaperDetailsArgs,
    "save_selected_papers": SaveSelectedPapersArgs,
    "load_selected_papers": LoadSelectedPapersArgs,
    "save_evidence_cards": SaveEvidenceCardsArgs,
    "load_evidence_cards": LoadEvidenceCardsArgs,
    "save_conflict_clusters": SaveConflictClustersArgs,
    "load_conflict_clusters": LoadConflictClustersArgs,
    "save_hypotheses": SaveHypothesesArgs,
    "render_markdown_report": RenderReportArgs,
}
