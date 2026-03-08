from datetime import UTC, datetime, timedelta

from hypoforge.infrastructure.db.cache_repository import CacheRepository
from hypoforge.infrastructure.db.session import create_session_factory


def test_cache_repository_round_trip(tmp_path) -> None:
    cache = CacheRepository(create_session_factory(f"sqlite:///{tmp_path / 'app.db'}"))

    cache.set("raw_response", "openalex:query", {"papers": [{"paper_id": "p1"}]}, ttl_seconds=3600)

    assert cache.get("raw_response", "openalex:query") == {"papers": [{"paper_id": "p1"}]}


def test_cache_repository_expires_entries(tmp_path) -> None:
    now = datetime(2026, 3, 9, tzinfo=UTC)
    cache = CacheRepository(
        create_session_factory(f"sqlite:///{tmp_path / 'app.db'}"),
        now_provider=lambda: now,
    )

    cache.set("raw_response", "openalex:query", {"papers": []}, ttl_seconds=1)

    later = CacheRepository(
        create_session_factory(f"sqlite:///{tmp_path / 'app.db'}"),
        now_provider=lambda: now + timedelta(seconds=2),
    )

    assert later.get("raw_response", "openalex:query") is None
