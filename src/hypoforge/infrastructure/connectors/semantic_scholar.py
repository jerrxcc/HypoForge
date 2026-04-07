from __future__ import annotations

import httpx

from hypoforge.domain.schemas import PaperDetail
from hypoforge.infrastructure.connectors.normalizers import normalize_semantic_scholar_query


class SemanticScholarConnector:
    BASE_URL = "https://api.semanticscholar.org/graph/v1"
    RECOMMENDATIONS_URL = "https://api.semanticscholar.org/recommendations/v1/papers"
    PAPER_FIELDS = ",".join(
        [
            "paperId",
            "externalIds",
            "title",
            "abstract",
            "year",
            "citationCount",
            "venue",
            "authors",
            "fieldsOfStudy",
            "publicationTypes",
            "url",
        ]
    )

    def __init__(
        self,
        client: httpx.Client | None = None,
        api_key: str | None = None,
    ) -> None:
        self._client = client or httpx.Client(timeout=30.0)
        self._api_key = api_key or None

    def search_papers(
        self,
        query: str,
        year_from: int,
        year_to: int,
        limit: int,
    ) -> list[PaperDetail]:
        normalized_query = normalize_semantic_scholar_query(query)
        response = self._client.get(
            f"{self.BASE_URL}/paper/search",
            params={
                "query": normalized_query,
                "year": f"{year_from}-{year_to}",
                "limit": limit,
                "fields": self.PAPER_FIELDS,
            },
            headers=self._headers(),
        )
        response.raise_for_status()
        payload = response.json()
        return [self._normalize_paper(item, provenance="semantic_scholar.search") for item in payload.get("data", [])]

    def recommend_papers(self, positive_paper_ids: list[str], limit: int) -> list[PaperDetail]:
        paper_ids = [paper_id.removeprefix("S2:") for paper_id in positive_paper_ids]
        response = self._client.post(
            self.RECOMMENDATIONS_URL,
            json={"positivePaperIds": paper_ids},
            params={"fields": self.PAPER_FIELDS, "limit": limit},
            headers=self._headers(),
        )
        response.raise_for_status()
        payload = response.json()
        return [
            self._normalize_paper(item, provenance="semantic_scholar.recommend")
            for item in payload.get("recommendedPapers", [])
        ]

    def get_paper_details(self, paper_ids: list[str]) -> list[PaperDetail]:
        normalized_ids = [paper_id.removeprefix("S2:") for paper_id in paper_ids]
        response = self._client.post(
            f"{self.BASE_URL}/paper/batch",
            params={"fields": self.PAPER_FIELDS},
            json={"ids": normalized_ids},
            headers=self._headers(),
        )
        response.raise_for_status()
        payload = response.json()
        return [self._normalize_paper(item, provenance="semantic_scholar.detail") for item in payload]

    def _headers(self) -> dict[str, str] | None:
        if not self._api_key:
            return None
        return {"x-api-key": self._api_key}

    def _normalize_paper(self, paper: dict, *, provenance: str) -> PaperDetail:
        external_ids = paper.get("externalIds") or {}
        doi = external_ids.get("DOI")
        publication_types = paper.get("publicationTypes") or []
        source_urls = {"semantic_scholar": paper.get("url", "")}
        arxiv_id = external_ids.get("ArXiv") or external_ids.get("ARXIV")
        if arxiv_id:
            source_urls["arxiv"] = f"https://arxiv.org/abs/{arxiv_id}"
        return PaperDetail(
            paper_id=f"S2:{paper.get('paperId', '')}",
            doi=doi,
            external_ids=external_ids,
            title=paper.get("title", ""),
            abstract=paper.get("abstract"),
            year=paper.get("year"),
            authors=[
                author.get("name", "")
                for author in paper.get("authors", [])
                if author.get("name")
            ],
            venue=paper.get("venue"),
            citation_count=paper.get("citationCount"),
            publication_type=publication_types[0] if publication_types else None,
            fields_of_study=paper.get("fieldsOfStudy") or [],
            source="semantic_scholar",
            url=paper.get("url"),
            source_urls=source_urls,
            provenance=[provenance],
        )
