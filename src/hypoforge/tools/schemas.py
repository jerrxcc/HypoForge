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

