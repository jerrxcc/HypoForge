"""Database migration utilities for HypoForge.

This module provides migration functions to add new columns
when the database schema changes.
"""

from __future__ import annotations

import logging
from sqlalchemy import text
from sqlalchemy.orm import Session


logger = logging.getLogger(__name__)


def migrate_add_reflection_columns(session: Session) -> None:
    """Add reflection-related columns to the runs table.

    This migration adds:
    - iteration_state_json: JSON column for iteration state
    - reflection_enabled: Boolean column for reflection toggle

    Args:
        session: SQLAlchemy session to use for migration
    """
    # Check if columns already exist
    result = session.execute(text("PRAGMA table_info(runs)"))
    columns = [row[1] for row in result.fetchall()]

    if "iteration_state_json" not in columns:
        logger.info("Adding iteration_state_json column to runs table")
        session.execute(text("ALTER TABLE runs ADD COLUMN iteration_state_json JSON"))
        session.commit()

    if "reflection_enabled" not in columns:
        logger.info("Adding reflection_enabled column to runs table")
        session.execute(text("ALTER TABLE runs ADD COLUMN reflection_enabled BOOLEAN DEFAULT 1"))
        session.commit()


def migrate_create_reflection_feedback_table(session: Session) -> None:
    """Create the reflection_feedback table if it doesn't exist.

    Args:
        session: SQLAlchemy session to use for migration
    """
    session.execute(text("""
        CREATE TABLE IF NOT EXISTS reflection_feedback (
            id VARCHAR(64) PRIMARY KEY,
            run_id VARCHAR(64) NOT NULL REFERENCES runs(id),
            feedback_id VARCHAR(64) NOT NULL,
            target_stage VARCHAR(32) NOT NULL,
            issues_json JSON NOT NULL DEFAULT '[]',
            severity VARCHAR(16) NOT NULL DEFAULT 'medium',
            suggested_actions_json JSON NOT NULL DEFAULT '[]',
            backtrack_stage VARCHAR(32),
            quality_scores_json JSON NOT NULL DEFAULT '{}',
            iteration_number INTEGER NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """))
    session.commit()
    logger.info("Created reflection_feedback table")


def run_all_migrations(session: Session) -> None:
    """Run all pending migrations.

    Args:
        session: SQLAlchemy session to use for migration
    """
    migrate_add_reflection_columns(session)
    migrate_create_reflection_feedback_table(session)
    logger.info("All migrations completed")


if __name__ == "__main__":
    # Run migrations from command line
    import sys
    from pathlib import Path

    # Add src to path
    src_path = Path(__file__).parent.parent
    sys.path.insert(0, str(src_path))

    from hypoforge.infrastructure.db.session import create_session_factory
    from hypoforge.config import Settings

    settings = Settings()
    session_factory = create_session_factory(settings.database_url)

    with session_factory() as session:
        run_all_migrations(session)

    print("Migrations completed successfully!")
