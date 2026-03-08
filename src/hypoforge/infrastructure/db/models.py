from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import JSON


class Base(DeclarativeBase):
    pass


def default_id() -> str:
    return uuid4().hex


def utcnow() -> datetime:
    return datetime.now(UTC)


class RunRow(Base):
    __tablename__ = "runs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=default_id)
    topic: Mapped[str] = mapped_column(Text, nullable=False)
    constraints_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="queued")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    final_report_md: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
    )


class CacheEntryRow(Base):
    __tablename__ = "cache_entries"
    __table_args__ = (UniqueConstraint("namespace", "cache_key", name="uq_cache_namespace_key"),)

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=default_id)
    namespace: Mapped[str] = mapped_column(String(64), nullable=False)
    cache_key: Mapped[str] = mapped_column(String(255), nullable=False)
    payload_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
    )


class PaperRow(Base):
    __tablename__ = "papers"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    doi: Mapped[str | None] = mapped_column(String(256), nullable=True)
    normalized_title: Mapped[str] = mapped_column(Text, nullable=False)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    payload_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    source_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class RunPaperRow(Base):
    __tablename__ = "run_papers"
    __table_args__ = (UniqueConstraint("run_id", "paper_id", name="uq_run_paper"),)

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=default_id)
    run_id: Mapped[str] = mapped_column(ForeignKey("runs.id"), nullable=False)
    paper_id: Mapped[str] = mapped_column(ForeignKey("papers.id"), nullable=False)
    selected_rank: Mapped[int] = mapped_column(Integer, nullable=False)
    selection_reason: Mapped[str] = mapped_column(Text, nullable=False)
    source_list_json: Mapped[list] = mapped_column(JSON, nullable=False, default=list)


class EvidenceCardRow(Base):
    __tablename__ = "evidence_cards"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    run_id: Mapped[str] = mapped_column(ForeignKey("runs.id"), nullable=False)
    paper_id: Mapped[str] = mapped_column(ForeignKey("papers.id"), nullable=False)
    payload_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    confidence: Mapped[float] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ConflictClusterRow(Base):
    __tablename__ = "conflict_clusters"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    run_id: Mapped[str] = mapped_column(ForeignKey("runs.id"), nullable=False)
    payload_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class HypothesisRow(Base):
    __tablename__ = "hypotheses"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    run_id: Mapped[str] = mapped_column(ForeignKey("runs.id"), nullable=False)
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    payload_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class StageSummaryRow(Base):
    __tablename__ = "stage_summaries"
    __table_args__ = (UniqueConstraint("run_id", "stage_name", name="uq_stage_summary_run_stage"),)

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=default_id)
    run_id: Mapped[str] = mapped_column(ForeignKey("runs.id"), nullable=False)
    stage_name: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    summary_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
    )


class ToolTraceRow(Base):
    __tablename__ = "tool_traces"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=default_id)
    run_id: Mapped[str] = mapped_column(ForeignKey("runs.id"), nullable=False)
    agent_name: Mapped[str] = mapped_column(String(64), nullable=False)
    tool_name: Mapped[str] = mapped_column(String(128), nullable=False)
    args_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    result_summary_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    model_name: Mapped[str] = mapped_column(String(128), nullable=False)
    input_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    output_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
