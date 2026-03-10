from __future__ import annotations

import httpx

from hypoforge.domain.schemas import PaperDetail
from hypoforge.infrastructure.connectors.normalizers import reconstruct_openalex_abstract


class OpenAlexConnector:
    BASE_URL = "https://api.openalex.org"

    def __init__(
        self,
        client: httpx.Client | None = None,
        api_key: str | None = None,
    ) -> None:
        self._client = client or httpx.Client(timeout=30.0)
        self._api_key = api_key or None

    def search_works(
        self,
        query: str,
        year_from: int,
        year_to: int,
        limit: int,
    ) -> list[PaperDetail]:
        params = {
            "search": query,
            "filter": f"from_publication_date:{year_from}-01-01,to_publication_date:{year_to}-12-31",
            "per-page": limit,
        }
        if self._api_key:
            params["api_key"] = self._api_key
        response = self._client.get(f"{self.BASE_URL}/works", params=params)
        response.raise_for_status()
        payload = response.json()
        return [self._normalize_work(work) for work in payload.get("results", [])]

    def _normalize_work(self, work: dict) -> PaperDetail:
        raw_id = work.get("id", "").rsplit("/", 1)[-1]
        doi = work.get("doi")
        if isinstance(doi, str) and doi.startswith("https://doi.org/"):
            doi = doi.removeprefix("https://doi.org/")
        primary_location = work.get("primary_location") or {}
        source = primary_location.get("source") or {}
        return PaperDetail(
            paper_id=f"oa:{raw_id}",
            doi=doi,
            external_ids={"openalex": raw_id, "doi": doi},
            title=work.get("title", ""),
            abstract=reconstruct_openalex_abstract(work.get("abstract_inverted_index")),
            year=work.get("publication_year"),
            authors=[
                authorship.get("author", {}).get("display_name", "")
                for authorship in work.get("authorships", [])
                if authorship.get("author", {}).get("display_name")
            ],
            venue=source.get("display_name"),
            citation_count=work.get("cited_by_count"),
            topic_labels=[
                concept.get("display_name", "")
                for concept in work.get("concepts", [])
                if concept.get("display_name")
            ],
            source="openalex",
            url=primary_location.get("landing_page_url"),
            source_urls={"openalex": work.get("id", "")},
            provenance=["openalex"],
        )
