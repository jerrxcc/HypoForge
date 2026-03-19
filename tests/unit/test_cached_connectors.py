from hypoforge.domain.schemas import PaperDetail
from hypoforge.infrastructure.connectors.cached import (
    CachedAlphaXivConnector,
    CachedOpenAlexConnector,
    CachedSemanticScholarConnector,
)
from hypoforge.infrastructure.db.cache_repository import CacheRepository
from hypoforge.infrastructure.db.session import create_session_factory


class CountingOpenAlexConnector:
    def __init__(self) -> None:
        self.calls = 0

    def search_works(self, query: str, year_from: int, year_to: int, limit: int):
        self.calls += 1
        return [
            PaperDetail(
                paper_id="oa:W1",
                title=query,
                abstract="Abstract",
                year=2024,
                authors=["A"],
            )
        ]


class CountingSemanticScholarConnector:
    def __init__(self) -> None:
        self.search_calls = 0
        self.detail_calls = 0

    def search_papers(self, query: str, year_from: int, year_to: int, limit: int):
        self.search_calls += 1
        return [
            PaperDetail(
                paper_id="S2:p1",
                doi="10.1/example",
                title=query,
                abstract="Abstract",
                year=2024,
                authors=["A"],
            )
        ]

    def recommend_papers(self, positive_paper_ids: list[str], limit: int):
        return []

    def get_paper_details(self, paper_ids: list[str]):
        self.detail_calls += 1
        return [
            PaperDetail(
                paper_id=paper_id,
                doi=f"10.1/{paper_id.lower()}",
                title=paper_id,
                abstract="Abstract",
                year=2024,
                authors=["A"],
            )
            for paper_id in paper_ids
        ]


class CountingAlphaXivConnector:
    def __init__(self) -> None:
        self.search_calls = 0
        self.content_calls = 0

    def search_embedding_similarity(self, query: str, year_from: int, year_to: int, limit: int):
        del year_from, year_to, limit
        self.search_calls += 1
        return [
            PaperDetail(
                paper_id="ax:2401.12345",
                title=query,
                abstract="Abstract",
                year=2024,
                authors=["A"],
            )
        ]

    def search_full_text_papers(self, query: str, year_from: int, year_to: int, limit: int):
        return self.search_embedding_similarity(query, year_from, year_to, limit)

    def search_agentic_paper_retrieval(self, query: str, year_from: int, year_to: int, limit: int):
        return self.search_embedding_similarity(query, year_from, year_to, limit)

    def get_paper_content(self, url: str, full_text: bool = False):
        del full_text
        self.content_calls += 1
        return f"content:{url}"

    def answer_pdf_queries(self, url: str, query: str):
        self.content_calls += 1
        return f"answer:{url}:{query}"

    def read_files_from_github_repository(self, github_url: str, path: str):
        self.content_calls += 1
        return {"github_url": github_url, "path": path}


def test_cached_openalex_connector_reuses_raw_response_cache(tmp_path) -> None:
    cache = CacheRepository(create_session_factory(f"sqlite:///{tmp_path / 'app.db'}"))
    base = CountingOpenAlexConnector()
    connector = CachedOpenAlexConnector(base, cache, ttl_seconds=3600)

    first = connector.search_works("battery", 2018, 2026, 5)
    second = connector.search_works("battery", 2018, 2026, 5)

    assert [paper.paper_id for paper in first] == ["oa:W1"]
    assert [paper.paper_id for paper in second] == ["oa:W1"]
    assert base.calls == 1


def test_cached_semantic_scholar_connector_reuses_normalized_paper_cache(tmp_path) -> None:
    cache = CacheRepository(create_session_factory(f"sqlite:///{tmp_path / 'app.db'}"))
    base = CountingSemanticScholarConnector()
    connector = CachedSemanticScholarConnector(base, cache, ttl_seconds=3600, normalized_ttl_seconds=3600)

    connector.search_papers("battery", 2018, 2026, 5)
    papers = connector.get_paper_details(["S2:p1"])

    assert [paper.paper_id for paper in papers] == ["S2:p1"]
    assert base.search_calls == 1
    assert base.detail_calls == 0


def test_cached_connectors_only_charge_budget_on_cache_miss(tmp_path) -> None:
    cache = CacheRepository(create_session_factory(f"sqlite:///{tmp_path / 'app.db'}"))
    openalex_base = CountingOpenAlexConnector()
    semantic_base = CountingSemanticScholarConnector()
    openalex_budget_calls = 0
    semantic_budget_calls = 0

    def on_openalex_call() -> None:
        nonlocal openalex_budget_calls
        openalex_budget_calls += 1

    def on_semantic_call() -> None:
        nonlocal semantic_budget_calls
        semantic_budget_calls += 1

    openalex = CachedOpenAlexConnector(
        openalex_base,
        cache,
        ttl_seconds=3600,
        on_external_call=on_openalex_call,
    )
    semantic = CachedSemanticScholarConnector(
        semantic_base,
        cache,
        ttl_seconds=3600,
        normalized_ttl_seconds=3600,
        on_external_call=on_semantic_call,
    )

    openalex.search_works("battery", 2018, 2026, 5)
    openalex.search_works("battery", 2018, 2026, 5)
    semantic.search_papers("battery", 2018, 2026, 5)
    semantic.get_paper_details(["S2:p1"])

    assert openalex_budget_calls == 1
    assert semantic_budget_calls == 1


def test_cached_alphaxiv_connector_reuses_search_and_content_cache(tmp_path) -> None:
    cache = CacheRepository(create_session_factory(f"sqlite:///{tmp_path / 'app.db'}"))
    base = CountingAlphaXivConnector()
    connector = CachedAlphaXivConnector(base, cache, ttl_seconds=3600)

    first = connector.search_embedding_similarity("battery", 2018, 2026, 5)
    second = connector.search_embedding_similarity("battery", 2018, 2026, 5)
    content_one = connector.get_paper_content("https://arxiv.org/abs/2401.12345")
    content_two = connector.get_paper_content("https://arxiv.org/abs/2401.12345")

    assert [paper.paper_id for paper in first] == ["ax:2401.12345"]
    assert [paper.paper_id for paper in second] == ["ax:2401.12345"]
    assert content_one == content_two == "content:https://arxiv.org/abs/2401.12345"
    assert base.search_calls == 1
    assert base.content_calls == 1
