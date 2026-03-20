"""Cache infrastructure for validation results and intermediate data.

This module provides caching utilities for the validation agents system,
enabling efficient reuse of computed results within a run.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any, Generic, TypeVar
from uuid import uuid4


logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass
class CacheEntry(Generic[T]):
    """A single cache entry with metadata."""

    key: str
    value: T
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    ttl_seconds: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def is_expired(self) -> bool:
        """Check if this entry has expired."""
        if self.ttl_seconds is None:
            return False
        expiry = self.created_at + timedelta(seconds=self.ttl_seconds)
        return datetime.now(UTC) > expiry


class ValidationCache:
    """In-memory cache for validation results.

    This cache stores validation results and intermediate computations
    within a run, avoiding redundant calculations.

    Cache Categories:
    - evidence_embeddings: Evidence embedding vectors
    - conflict_patterns: Detected conflict patterns
    - quality_assessments: Quality assessment results
    - validation_results: Full validation results
    """

    def __init__(self, run_id: str, default_ttl: int | None = None) -> None:
        """Initialize the validation cache.

        Args:
            run_id: The run identifier
            default_ttl: Default TTL in seconds (None = no expiry)
        """
        self._run_id = run_id
        self._default_ttl = default_ttl
        self._entries: dict[str, CacheEntry[Any]] = {}
        self._logger = logging.getLogger(f"{__name__}.{run_id[:8]}")

    def get(self, category: str, key: str) -> Any | None:
        """Get a cached value.

        Args:
            category: Cache category (e.g., 'evidence_embeddings')
            key: Cache key within category

        Returns:
            Cached value or None if not found/expired
        """
        full_key = f"{category}:{key}"
        entry = self._entries.get(full_key)

        if entry is None:
            return None

        if entry.is_expired():
            del self._entries[full_key]
            return None

        return entry.value

    def set(
        self,
        category: str,
        key: str,
        value: Any,
        ttl_seconds: int | None = None,
    ) -> None:
        """Set a cached value.

        Args:
            category: Cache category
            key: Cache key within category
            value: Value to cache
            ttl_seconds: TTL in seconds (uses default if None)
        """
        full_key = f"{category}:{key}"
        ttl = ttl_seconds if ttl_seconds is not None else self._default_ttl

        self._entries[full_key] = CacheEntry(
            key=full_key,
            value=value,
            ttl_seconds=ttl,
        )

    def delete(self, category: str, key: str) -> bool:
        """Delete a cached value.

        Args:
            category: Cache category
            key: Cache key within category

        Returns:
            True if entry was deleted, False if not found
        """
        full_key = f"{category}:{key}"
        if full_key in self._entries:
            del self._entries[full_key]
            return True
        return False

    def clear_category(self, category: str) -> int:
        """Clear all entries in a category.

        Args:
            category: Cache category to clear

        Returns:
            Number of entries cleared
        """
        keys_to_delete = [
            k for k in self._entries.keys()
            if k.startswith(f"{category}:")
        ]
        for key in keys_to_delete:
            del self._entries[key]
        return len(keys_to_delete)

    def clear(self) -> None:
        """Clear all cached entries."""
        self._entries.clear()

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dict with cache statistics
        """
        categories: dict[str, int] = {}
        expired = 0

        for key, entry in self._entries.items():
            category = key.split(":")[0]
            categories[category] = categories.get(category, 0) + 1
            if entry.is_expired():
                expired += 1

        return {
            "run_id": self._run_id,
            "total_entries": len(self._entries),
            "categories": categories,
            "expired_entries": expired,
        }

    def cleanup_expired(self) -> int:
        """Remove all expired entries.

        Returns:
            Number of entries removed
        """
        keys_to_delete = [
            k for k, v in self._entries.items()
            if v.is_expired()
        ]
        for key in keys_to_delete:
            del self._entries[key]
        return len(keys_to_delete)


class CacheManager:
    """Manager for validation caches across runs.

    Provides a centralized interface for managing caches for multiple runs.
    """

    def __init__(self) -> None:
        """Initialize the cache manager."""
        self._caches: dict[str, ValidationCache] = {}
        self._logger = logging.getLogger(__name__)

    def get_cache(self, run_id: str) -> ValidationCache:
        """Get or create a cache for a run.

        Args:
            run_id: The run identifier

        Returns:
            ValidationCache for the run
        """
        if run_id not in self._caches:
            self._caches[run_id] = ValidationCache(run_id)
        return self._caches[run_id]

    def clear_cache(self, run_id: str) -> None:
        """Clear and remove a run's cache.

        Args:
            run_id: The run identifier
        """
        if run_id in self._caches:
            self._caches[run_id].clear()
            del self._caches[run_id]

    def get_all_stats(self) -> dict[str, dict[str, Any]]:
        """Get statistics for all caches.

        Returns:
            Dict mapping run_id to cache stats
        """
        return {
            run_id: cache.get_stats()
            for run_id, cache in self._caches.items()
        }

    def cleanup_all_expired(self) -> int:
        """Clean up expired entries in all caches.

        Returns:
            Total number of entries removed
        """
        total = 0
        for cache in self._caches.values():
            total += cache.cleanup_expired()
        return total


# Global cache manager instance
_cache_manager: CacheManager | None = None


def get_cache_manager() -> CacheManager:
    """Get the global cache manager instance."""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager


def get_validation_cache(run_id: str) -> ValidationCache:
    """Get a validation cache for a run.

    Args:
        run_id: The run identifier

    Returns:
        ValidationCache for the run
    """
    return get_cache_manager().get_cache(run_id)


def clear_validation_cache(run_id: str) -> None:
    """Clear the validation cache for a run.

    Args:
        run_id: The run identifier
    """
    get_cache_manager().clear_cache(run_id)
