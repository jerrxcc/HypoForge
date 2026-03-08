from __future__ import annotations

import httpx

from hypoforge.domain.schemas import PaperDetail
from hypoforge.infrastructure.connectors.normalizers import normalize_semantic_scholar_query


class SemanticScholarConnector:
    BASE_URL = "https://api.semanticscholar.org/graph/v1"
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

    def __init__(self, client: httpx.Client | None = None) -> None:
        self._client = client or httpx.Client(timeout=30.0)

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
        )
        response.raise_for_status()
        payload = response.json()
        return [self._normalize_paper(item) for item in payload.get("data", [])]

    def recommend_papers(self, positive_paper_ids: list[str], limit: int) -> list[PaperDetail]:
        paper_ids = [paper_id.removeprefix("S2:") for paper_id in positive_paper_ids]
        response = self._client.post(
            f"{self.BASE_URL}/paper/recommendations",
            json={"positivePaperIds": paper_ids, "limit": limit},
            params={"fields": self.PAPER_FIELDS},
        )
        response.raise_for_status()
        payload = response.json()
        return [self._normalize_paper(item) for item in payload.get("recommendedPapers", [])]

    def get_paper_details(self, paper_ids: list[str]) -> list[PaperDetail]:
        normalized_ids = [paper_id.removeprefix("S2:") for paper_id in paper_ids]
        response = self._client.post(
            f"{self.BASE_URL}/paper/batch",
            params={"fields": self.PAPER_FIELDS},
            json={"ids": normalized_ids},
        )
        response.raise_for_status()
        payload = response.json()
        return [self._normalize_paper(item) for item in payload]

    def _normalize_paper(self, paper: dict) -> PaperDetail:
        external_ids = paper.get("externalIds") or {}
        doi = external_ids.get("DOI")
        publication_types = paper.get("publicationTypes") or []
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
            source_urls={"semantic_scholar": paper.get("url", "")},
            provenance=["semantic_scholar"],
        )

