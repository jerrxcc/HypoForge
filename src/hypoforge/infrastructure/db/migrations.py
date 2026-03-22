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
    """Add reflection-related columns to the runs table."""
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
    """Create the reflection_feedback table if it doesn't exist."""
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


def migrate_add_trace_and_stage_attempt_columns(session: Session) -> None:
    """Add stage_name + attempt to tool_traces, and rebuild stage_summaries with attempt."""
    # 1. tool_traces: add stage_name and attempt columns
    tt_cols = [row[1] for row in session.execute(text("PRAGMA table_info(tool_traces)")).fetchall()]
    if "stage_name" not in tt_cols:
        logger.info("Adding stage_name column to tool_traces table")
        session.execute(text("ALTER TABLE tool_traces ADD COLUMN stage_name VARCHAR(32) NOT NULL DEFAULT 'unknown'"))
    if "attempt" not in tt_cols:
        logger.info("Adding attempt column to tool_traces table")
        session.execute(text("ALTER TABLE tool_traces ADD COLUMN attempt INTEGER NOT NULL DEFAULT 1"))
    session.commit()

    # 2. stage_summaries: rebuild table with attempt column and new unique constraint
    _migrate_rebuild_stage_summaries_with_attempt(session)


def _migrate_rebuild_stage_summaries_with_attempt(session: Session) -> None:
    """Rebuild stage_summaries table to add attempt column and change unique constraint."""
    ss_cols = [row[1] for row in session.execute(text("PRAGMA table_info(stage_summaries)")).fetchall()]
    if "attempt" in ss_cols:
        return  # Already migrated
    logger.info("Rebuilding stage_summaries table with attempt column")
    session.execute(text("ALTER TABLE stage_summaries RENAME TO _stage_summaries_old"))
    session.execute(text("""
        CREATE TABLE stage_summaries (
            id VARCHAR(64) PRIMARY KEY,
            run_id VARCHAR(64) NOT NULL REFERENCES runs(id),
            stage_name VARCHAR(32) NOT NULL,
            attempt INTEGER NOT NULL DEFAULT 1,
            status VARCHAR(32) NOT NULL,
            summary_json JSON NOT NULL DEFAULT '{}',
            error_message TEXT,
            started_at DATETIME,
            completed_at DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(run_id, stage_name, attempt)
        )
    """))
    session.execute(text("""
        INSERT INTO stage_summaries (id, run_id, stage_name, attempt, status, summary_json,
            error_message, started_at, completed_at, created_at, updated_at)
        SELECT id, run_id, stage_name, 1,
            CASE WHEN status = 'degraded' THEN 'completed' ELSE status END,
            summary_json, error_message, started_at, completed_at, created_at, updated_at
        FROM _stage_summaries_old
    """))
    session.execute(text("DROP TABLE _stage_summaries_old"))
    session.commit()


def run_all_migrations(session: Session) -> None:
    """Run all pending migrations."""
    migrate_add_reflection_columns(session)
    migrate_create_reflection_feedback_table(session)
    migrate_add_trace_and_stage_attempt_columns(session)
    logger.info("All migrations completed")
