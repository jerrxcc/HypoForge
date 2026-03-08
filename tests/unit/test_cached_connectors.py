from hypoforge.domain.schemas import PaperDetail
from hypoforge.infrastructure.connectors.cached import CachedOpenAlexConnector, CachedSemanticScholarConnector
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
