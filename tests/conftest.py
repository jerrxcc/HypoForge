"""Shared pytest fixtures for HypoForge tests."""

from pathlib import Path

import pytest

from hypoforge.infrastructure.db.repository import RunRepository


@pytest.fixture
def repo(tmp_path: Path) -> RunRepository:
    """Create a test repository with a temporary database."""
    return RunRepository.from_sqlite_path(tmp_path / "app.db")
