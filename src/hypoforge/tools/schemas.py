from __future__ import annotations

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

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


class GetAlphaXivPaperContentArgs(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    url: str
    full_text: bool = Field(
        default=False,
        validation_alias=AliasChoices("fullText", "full_text"),
        serialization_alias="fullText",
    )


class AnswerAlphaXivPdfQueriesArgs(BaseModel):
    url: str
    query: str


class ReadAlphaXivGithubRepositoryArgs(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    github_url: str = Field(
        validation_alias=AliasChoices("githubUrl", "github_url"),
        serialization_alias="githubUrl",
    )
    path: str


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
    paper_ids: list[str] = Field(default_factory=list)


class LoadEvidenceCardsArgs(BaseModel):
    note: str | None = None


class LoadConflictClustersArgs(BaseModel):
    note: str | None = None


TOOL_ARG_MODELS = {
    "search_openalex_works": SearchPapersArgs,
    "search_semantic_scholar_papers": SearchPapersArgs,
    "recommend_semantic_scholar_papers": RecommendPapersArgs,
    "search_alphaxiv_embedding_similarity": SearchPapersArgs,
    "search_alphaxiv_full_text_papers": SearchPapersArgs,
    "search_alphaxiv_agentic_paper_retrieval": SearchPapersArgs,
    "get_paper_details": GetPaperDetailsArgs,
    "get_alphaxiv_paper_content": GetAlphaXivPaperContentArgs,
    "answer_alphaxiv_pdf_queries": AnswerAlphaXivPdfQueriesArgs,
    "read_alphaxiv_github_repository": ReadAlphaXivGithubRepositoryArgs,
    "save_selected_papers": SaveSelectedPapersArgs,
    "load_selected_papers": LoadSelectedPapersArgs,
    "save_evidence_cards": SaveEvidenceCardsArgs,
    "load_evidence_cards": LoadEvidenceCardsArgs,
    "save_conflict_clusters": SaveConflictClustersArgs,
    "load_conflict_clusters": LoadConflictClustersArgs,
    "save_hypotheses": SaveHypothesesArgs,
    "render_markdown_report": RenderReportArgs,
}
