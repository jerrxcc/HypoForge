from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, sessionmaker

from hypoforge.infrastructure.db.models import CacheEntryRow


class CacheRepository:
    def __init__(
        self,
        session_factory: sessionmaker[Session],
        *,
        now_provider=None,
    ) -> None:
        self._session_factory = session_factory
        self._now_provider = now_provider or (lambda: datetime.now(UTC))

    def get(self, namespace: str, cache_key: str) -> dict | None:
        with self._session_factory() as session:
            row = session.execute(
                select(CacheEntryRow).where(
                    CacheEntryRow.namespace == namespace,
                    CacheEntryRow.cache_key == cache_key,
                )
            ).scalar_one_or_none()
            if row is None:
                return None
            if _ensure_utc(row.expires_at) <= _ensure_utc(self._now_provider()):
                session.delete(row)
                session.commit()
                return None
            return row.payload_json

    def set(self, namespace: str, cache_key: str, payload: dict, *, ttl_seconds: int) -> None:
        expires_at = self._now_provider() + timedelta(seconds=ttl_seconds)
        with self._session_factory() as session:
            row = session.execute(
                select(CacheEntryRow).where(
                    CacheEntryRow.namespace == namespace,
                    CacheEntryRow.cache_key == cache_key,
                )
            ).scalar_one_or_none()
            if row is None:
                row = CacheEntryRow(
                    namespace=namespace,
                    cache_key=cache_key,
                    payload_json=payload,
                    expires_at=expires_at,
                )
                session.add(row)
            else:
                row.payload_json = payload
                row.expires_at = expires_at
            session.commit()

    def clear_namespace(self, namespace: str) -> None:
        with self._session_factory() as session:
            session.execute(delete(CacheEntryRow).where(CacheEntryRow.namespace == namespace))
            session.commit()


def _ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)
