from __future__ import annotations

import json
import logging
from hashlib import sha256
from typing import Any, Callable

from hypoforge.domain.schemas import PaperDetail
from hypoforge.infrastructure.connectors.alphaxiv import AlphaXivConnector
from hypoforge.infrastructure.connectors.openalex import OpenAlexConnector
from hypoforge.infrastructure.connectors.semantic_scholar import SemanticScholarConnector
from hypoforge.infrastructure.db.cache_repository import CacheRepository

logger = logging.getLogger(__name__)


def _args_key(source: str, payload: dict) -> str:
    normalized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return sha256(f"{source}:{normalized}".encode("utf-8")).hexdigest()


def _paper_cache_keys(paper: PaperDetail) -> list[str]:
    keys = [paper.paper_id]
    if paper.doi:
        keys.append(f"doi:{paper.doi.lower()}")
    first_author = paper.authors[0].lower() if paper.authors else ""
    if paper.year:
        keys.append(f"title:{' '.join(paper.title.lower().split())}:{paper.year}:{first_author}")
    return keys


class CachedOpenAlexConnector:
    """Caching wrapper for OpenAlexConnector.

    Caches raw API responses to avoid redundant network requests
    across agent tool calls within a single run.
    """

    def __init__(
        self,
        connector: OpenAlexConnector,
        cache: CacheRepository,
        *,
        ttl_seconds: int,
        on_external_call: Callable[[], None] | None = None,
    ) -> None:
        self._connector = connector
        self._cache = cache
        self._ttl_seconds = ttl_seconds
        self._on_external_call = on_external_call
        self.last_cache_hit = False

    def search_works(self, query: str, year_from: int, year_to: int, limit: int) -> list[PaperDetail]:
        cache_key = _args_key(
            "openalex_search",
            {"query": query, "year_from": year_from, "year_to": year_to, "limit": limit},
        )
        cached = self._cache.get("raw_response", cache_key)
        if cached is not None and "papers" in cached:
            self.last_cache_hit = True
            return [PaperDetail.model_validate(paper) for paper in cached["papers"]]
        self.last_cache_hit = False
        if self._on_external_call is not None:
            self._on_external_call()
        papers = self._connector.search_works(query, year_from, year_to, limit)
        payload = {"papers": [paper.model_dump() for paper in papers]}
        self._cache.set("raw_response", cache_key, payload, ttl_seconds=self._ttl_seconds)
        return papers


class CachedSemanticScholarConnector:
    """Caching wrapper for SemanticScholarConnector.

    Caches raw API responses and individual normalized papers to avoid
    redundant network requests across agent tool calls.
    """

    def __init__(
        self,
        connector: SemanticScholarConnector,
        cache: CacheRepository,
        *,
        ttl_seconds: int,
        normalized_ttl_seconds: int,
        on_external_call: Callable[[], None] | None = None,
    ) -> None:
        self._connector = connector
        self._cache = cache
        self._ttl_seconds = ttl_seconds
        self._normalized_ttl_seconds = normalized_ttl_seconds
        self._on_external_call = on_external_call
        self.last_cache_hit = False

    def search_papers(self, query: str, year_from: int, year_to: int, limit: int) -> list[PaperDetail]:
        return self._cached_search(
            cache_source="semantic_scholar_search",
            cache_payload={"query": query, "year_from": year_from, "year_to": year_to, "limit": limit},
            fetch=lambda: self._connector.search_papers(query, year_from, year_to, limit),
            cache_normalized=True,
        )

    def recommend_papers(self, positive_paper_ids: list[str], limit: int) -> list[PaperDetail]:
        return self._cached_search(
            cache_source="semantic_scholar_recommend",
            cache_payload={"positive_paper_ids": positive_paper_ids, "limit": limit},
            fetch=lambda: self._connector.recommend_papers(positive_paper_ids, limit),
            cache_normalized=True,
        )

    def get_paper_details(self, paper_ids: list[str]) -> list[PaperDetail]:
        cached_papers: list[PaperDetail] = []
        missing_ids: list[str] = []
        for paper_id in paper_ids:
            payload = self._cache.get("normalized_paper", paper_id)
            if payload is None or "paper" not in payload:
                missing_ids.append(paper_id)
                continue
            cached_papers.append(PaperDetail.model_validate(payload["paper"]))
        fetched: list[PaperDetail] = []
        if missing_ids:
            self.last_cache_hit = False
            if self._on_external_call is not None:
                self._on_external_call()
            fetched = self._connector.get_paper_details(missing_ids)
            self._cache_papers(fetched)
        else:
            self.last_cache_hit = True
        papers_by_id = {paper.paper_id: paper for paper in [*cached_papers, *fetched]}
        return [papers_by_id[paper_id] for paper_id in paper_ids if paper_id in papers_by_id]

    def _cache_papers(self, papers: list[PaperDetail]) -> None:
        for paper in papers:
            payload = {"paper": paper.model_dump()}
            for cache_key in _paper_cache_keys(paper):
                self._cache.set(
                    "normalized_paper",
                    cache_key,
                    payload,
                    ttl_seconds=self._normalized_ttl_seconds,
                )

    def _cached_search(
        self,
        *,
        cache_source: str,
        cache_payload: dict,
        fetch: Callable[[], list[PaperDetail]],
        cache_normalized: bool = False,
    ) -> list[PaperDetail]:
        """Look up a raw-response cache entry; on miss, call *fetch* and store."""
        cache_key = _args_key(cache_source, cache_payload)
        cached = self._cache.get("raw_response", cache_key)
        if cached is not None and "papers" in cached:
            self.last_cache_hit = True
            return [PaperDetail.model_validate(paper) for paper in cached["papers"]]
        self.last_cache_hit = False
        if self._on_external_call is not None:
            self._on_external_call()
        papers = fetch()
        self._cache.set(
            "raw_response",
            cache_key,
            {"papers": [paper.model_dump() for paper in papers]},
            ttl_seconds=self._ttl_seconds,
        )
        if cache_normalized:
            self._cache_papers(papers)
        return papers


class CachedAlphaXivConnector:
    """Caching wrapper for AlphaXivConnector."""

    def __init__(
        self,
        connector: AlphaXivConnector,
        cache: CacheRepository,
        *,
        ttl_seconds: int,
        on_external_call: Callable[[], None] | None = None,
    ) -> None:
        self._connector = connector
        self._cache = cache
        self._ttl_seconds = ttl_seconds
        self._on_external_call = on_external_call
        self.last_cache_hit = False

    def search_embedding_similarity(
        self,
        query: str,
        year_from: int,
        year_to: int,
        limit: int,
    ) -> list[PaperDetail]:
        return self._cached_papers(
            "alphaxiv_embedding_similarity",
            {"query": query, "year_from": year_from, "year_to": year_to, "limit": limit},
            lambda: self._connector.search_embedding_similarity(query, year_from, year_to, limit),
        )

    def search_full_text_papers(
        self,
        query: str,
        year_from: int,
        year_to: int,
        limit: int,
    ) -> list[PaperDetail]:
        return self._cached_papers(
            "alphaxiv_full_text_papers",
            {"query": query, "year_from": year_from, "year_to": year_to, "limit": limit},
            lambda: self._connector.search_full_text_papers(query, year_from, year_to, limit),
        )

    def search_agentic_paper_retrieval(
        self,
        query: str,
        year_from: int,
        year_to: int,
        limit: int,
    ) -> list[PaperDetail]:
        return self._cached_papers(
            "alphaxiv_agentic_paper_retrieval",
            {"query": query, "year_from": year_from, "year_to": year_to, "limit": limit},
            lambda: self._connector.search_agentic_paper_retrieval(query, year_from, year_to, limit),
        )

    def get_paper_content(self, url: str, full_text: bool = False) -> str:
        return self._cached_payload(
            "alphaxiv_get_paper_content",
            {"url": url, "full_text": full_text},
            lambda: self._connector.get_paper_content(url, full_text),
        )

    def answer_pdf_queries(self, url: str, query: str) -> str:
        return self._cached_payload(
            "alphaxiv_answer_pdf_queries",
            {"url": url, "query": query},
            lambda: self._connector.answer_pdf_queries(url, query),
        )

    def read_files_from_github_repository(self, github_url: str, path: str) -> dict[str, Any] | str:
        return self._cached_payload(
            "alphaxiv_read_files_from_github_repository",
            {"github_url": github_url, "path": path},
            lambda: self._connector.read_files_from_github_repository(github_url, path),
        )

    def _cached_papers(
        self,
        cache_source: str,
        cache_payload: dict[str, Any],
        fetch: Callable[[], list[PaperDetail]],
    ) -> list[PaperDetail]:
        payload = self._cached_payload(
            cache_source,
            cache_payload,
            lambda: [paper.model_dump() for paper in fetch()],
        )
        return [PaperDetail.model_validate(paper) for paper in payload]

    def _cached_payload(
        self,
        cache_source: str,
        cache_payload: dict[str, Any],
        fetch: Callable[[], Any],
    ) -> Any:
        cache_key = _args_key(cache_source, cache_payload)
        cached = self._cache.get("raw_response", cache_key)
        if cached is not None and "result" in cached:
            self.last_cache_hit = True
            return cached["result"]
        self.last_cache_hit = False
        if self._on_external_call is not None:
            self._on_external_call()
        result = fetch()
        self._cache.set(
            "raw_response",
            cache_key,
            {"result": result},
            ttl_seconds=self._ttl_seconds,
        )
        return result
