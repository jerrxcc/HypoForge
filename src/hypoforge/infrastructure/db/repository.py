from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from uuid import uuid4

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session, sessionmaker

from hypoforge.domain.schemas import (
    ConflictCluster,
    EvidenceCard,
    Hypothesis,
    PaperDetail,
    RunConstraints,
    RunRequest,
    RunResult,
    RunSummary,
    StageName,
    StageStatus,
    StageSummary,
    RunState,
    RunStatus,
)
from hypoforge.infrastructure.db.models import (
    ConflictClusterRow,
    EvidenceCardRow,
    HypothesisRow,
    PaperRow,
    RunPaperRow,
    RunRow,
    StageSummaryRow,
    ToolTraceRow,
    utcnow,
)
from hypoforge.infrastructure.db.session import create_session_factory


def _normalize_title(value: str) -> str:
    return " ".join(value.lower().split())


class RunRepository:
    def __init__(self, session_factory: sessionmaker[Session]):
        self._session_factory = session_factory

    @classmethod
    def from_database_url(cls, database_url: str) -> "RunRepository":
        return cls(create_session_factory(database_url))

    @classmethod
    def from_sqlite_path(cls, path: Path) -> "RunRepository":
        return cls.from_database_url(f"sqlite:///{path}")

    def create_run(self, request: RunRequest) -> RunState:
        run_id = f"run_{uuid4().hex}"
        row = RunRow(
            id=run_id,
            topic=request.topic,
            constraints_json=request.constraints.model_dump(),
            status="queued",
        )
        with self._session_factory() as session:
            session.add(row)
            session.commit()
        return self.get_run(run_id)

    def get_run(self, run_id: str) -> RunState:
        with self._session_factory() as session:
            row = session.get(RunRow, run_id)
            if row is None:
                raise KeyError(f"run not found: {run_id}")
            return self._to_run_state(session, row)

    def list_runs(self) -> list[RunSummary]:
        with self._session_factory() as session:
            rows = session.execute(select(RunRow).order_by(RunRow.updated_at.desc())).scalars()
            return [self._to_run_summary(session, row) for row in rows]

    def update_run_status(
        self,
        run_id: str,
        status: RunStatus,
        *,
        error_message: str | None = None,
    ) -> None:
        with self._session_factory() as session:
            row = self._require_run(session, run_id)
            row.status = status
            row.error_message = error_message
            session.commit()

    def save_report_markdown(self, run_id: str, report_markdown: str) -> None:
        with self._session_factory() as session:
            row = self._require_run(session, run_id)
            row.final_report_md = report_markdown
            session.commit()

    def save_selected_papers(
        self,
        run_id: str,
        papers: list[PaperDetail],
        selection_reason: str,
    ) -> None:
        with self._session_factory() as session:
            self._require_run(session, run_id)
            session.execute(delete(RunPaperRow).where(RunPaperRow.run_id == run_id))
            for index, paper in enumerate(papers, start=1):
                payload = paper.model_dump()
                paper_row = session.get(PaperRow, paper.paper_id)
                if paper_row is None:
                    paper_row = PaperRow(
                        id=paper.paper_id,
                        doi=paper.doi,
                        normalized_title=_normalize_title(paper.title),
                        year=paper.year,
                        payload_json=payload,
                        source_hash=sha256(repr(sorted(payload.items())).encode("utf-8")).hexdigest(),
                    )
                    session.add(paper_row)
                else:
                    paper_row.payload_json = payload
                    paper_row.doi = paper.doi
                    paper_row.year = paper.year
                    paper_row.normalized_title = _normalize_title(paper.title)

                session.add(
                    RunPaperRow(
                        run_id=run_id,
                        paper_id=paper.paper_id,
                        selected_rank=index,
                        selection_reason=selection_reason,
                        source_list_json=paper.provenance,
                    )
                )
            session.commit()

    def load_selected_papers(self, run_id: str) -> list[PaperDetail]:
        with self._session_factory() as session:
            rows = session.execute(
                select(PaperRow.payload_json)
                .join(RunPaperRow, RunPaperRow.paper_id == PaperRow.id)
                .where(RunPaperRow.run_id == run_id)
                .order_by(RunPaperRow.selected_rank.asc())
            ).all()
            return [PaperDetail.model_validate(payload) for payload, in rows]

    def save_evidence_cards(self, run_id: str, cards: list[EvidenceCard]) -> None:
        with self._session_factory() as session:
            self._require_run(session, run_id)
            session.execute(delete(EvidenceCardRow).where(EvidenceCardRow.run_id == run_id))
            for card in cards:
                session.add(
                    EvidenceCardRow(
                        id=self._scoped_id(run_id, card.evidence_id),
                        run_id=run_id,
                        paper_id=card.paper_id,
                        payload_json=card.model_dump(),
                        confidence=card.confidence,
                    )
                )
            session.commit()

    def append_evidence_cards(self, run_id: str, cards: list[EvidenceCard]) -> None:
        with self._session_factory() as session:
            self._require_run(session, run_id)
            for card in cards:
                row_id = self._scoped_id(run_id, card.evidence_id)
                row = session.get(EvidenceCardRow, row_id)
                if row is None:
                    session.add(
                        EvidenceCardRow(
                            id=row_id,
                            run_id=run_id,
                            paper_id=card.paper_id,
                            payload_json=card.model_dump(),
                            confidence=card.confidence,
                        )
                    )
                    continue
                row.paper_id = card.paper_id
                row.payload_json = card.model_dump()
                row.confidence = card.confidence
            session.commit()

    def load_evidence_cards(self, run_id: str) -> list[EvidenceCard]:
        with self._session_factory() as session:
            rows = session.execute(
                select(EvidenceCardRow.payload_json).where(EvidenceCardRow.run_id == run_id)
            ).all()
            return [EvidenceCard.model_validate(payload) for payload, in rows]

    def save_conflict_clusters(self, run_id: str, clusters: list[ConflictCluster]) -> None:
        with self._session_factory() as session:
            self._require_run(session, run_id)
            session.execute(delete(ConflictClusterRow).where(ConflictClusterRow.run_id == run_id))
            for cluster in clusters:
                session.add(
                    ConflictClusterRow(
                        id=self._scoped_id(run_id, cluster.cluster_id),
                        run_id=run_id,
                        payload_json=cluster.model_dump(),
                    )
                )
            session.commit()

    def load_conflict_clusters(self, run_id: str) -> list[ConflictCluster]:
        with self._session_factory() as session:
            rows = session.execute(
                select(ConflictClusterRow.payload_json).where(ConflictClusterRow.run_id == run_id)
            ).all()
            return [ConflictCluster.model_validate(payload) for payload, in rows]

    def save_hypotheses(self, run_id: str, hypotheses: list[Hypothesis]) -> None:
        with self._session_factory() as session:
            self._require_run(session, run_id)
            session.execute(delete(HypothesisRow).where(HypothesisRow.run_id == run_id))
            for hypothesis in hypotheses:
                session.add(
                    HypothesisRow(
                        id=f"{run_id}_h{hypothesis.rank}",
                        run_id=run_id,
                        rank=hypothesis.rank,
                        payload_json=hypothesis.model_dump(),
                    )
                )
            session.commit()

    def load_hypotheses(self, run_id: str) -> list[Hypothesis]:
        with self._session_factory() as session:
            rows = session.execute(
                select(HypothesisRow.payload_json)
                .where(HypothesisRow.run_id == run_id)
                .order_by(HypothesisRow.rank.asc())
            ).all()
            return [Hypothesis.model_validate(payload) for payload, in rows]

    def record_tool_trace(
        self,
        *,
        run_id: str,
        agent_name: str,
        tool_name: str,
        args: dict,
        result_summary: dict,
        latency_ms: int,
        model_name: str,
        success: bool,
        input_tokens: int | None = None,
        output_tokens: int | None = None,
        error_message: str | None = None,
    ) -> None:
        with self._session_factory() as session:
            self._require_run(session, run_id)
            session.add(
                ToolTraceRow(
                    run_id=run_id,
                    agent_name=agent_name,
                    tool_name=tool_name,
                    args_json=args,
                    result_summary_json=result_summary,
                    latency_ms=latency_ms,
                    model_name=model_name,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    success=success,
                    error_message=error_message,
                )
            )
            session.commit()

    def start_stage(self, run_id: str, stage_name: StageName) -> None:
        with self._session_factory() as session:
            self._require_run(session, run_id)
            row = session.execute(
                select(StageSummaryRow).where(
                    StageSummaryRow.run_id == run_id,
                    StageSummaryRow.stage_name == stage_name,
                )
            ).scalar_one_or_none()
            if row is None:
                row = StageSummaryRow(
                    run_id=run_id,
                    stage_name=stage_name,
                    status="started",
                    summary_json={},
                    started_at=utcnow(),
                )
                session.add(row)
            else:
                row.status = "started"
                row.summary_json = {}
                row.error_message = None
                row.started_at = utcnow()
                row.completed_at = None
            session.commit()

    def finish_stage(
        self,
        run_id: str,
        stage_name: StageName,
        *,
        summary: dict,
        status: StageStatus = "completed",
        error_message: str | None = None,
    ) -> None:
        with self._session_factory() as session:
            self._require_run(session, run_id)
            row = session.execute(
                select(StageSummaryRow).where(
                    StageSummaryRow.run_id == run_id,
                    StageSummaryRow.stage_name == stage_name,
                )
            ).scalar_one_or_none()
            if row is None:
                row = StageSummaryRow(
                    run_id=run_id,
                    stage_name=stage_name,
                    status=status,
                    summary_json=summary,
                    error_message=error_message,
                    started_at=utcnow(),
                    completed_at=utcnow(),
                )
                session.add(row)
            else:
                row.status = status
                row.summary_json = summary
                row.error_message = error_message
                row.started_at = row.started_at or utcnow()
                row.completed_at = utcnow()
            session.commit()

    def list_stage_summaries(self, run_id: str) -> list[StageSummary]:
        with self._session_factory() as session:
            rows = session.execute(
                select(StageSummaryRow)
                .where(StageSummaryRow.run_id == run_id)
                .order_by(StageSummaryRow.created_at.asc())
            ).scalars()
            return [
                StageSummary(
                    stage_name=row.stage_name,
                    status=row.status,
                    summary=row.summary_json,
                    error_message=row.error_message,
                    started_at=row.started_at,
                    completed_at=row.completed_at,
                )
                for row in rows
            ]

    def list_tool_traces(self, run_id: str) -> list[dict]:
        with self._session_factory() as session:
            rows = session.execute(
                select(ToolTraceRow)
                .where(ToolTraceRow.run_id == run_id)
                .order_by(ToolTraceRow.created_at.asc())
            ).scalars()
            return [
                {
                    "id": row.id,
                    "agent_name": row.agent_name,
                    "tool_name": row.tool_name,
                    "args": row.args_json,
                    "result_summary": row.result_summary_json,
                    "latency_ms": row.latency_ms,
                    "model_name": row.model_name,
                    "input_tokens": row.input_tokens,
                    "output_tokens": row.output_tokens,
                    "request_id": (row.result_summary_json or {}).get("request_id"),
                    "success": row.success,
                    "error_message": row.error_message,
                }
                for row in rows
            ]

    def build_final_result(self, run_id: str) -> RunResult:
        run = self.get_run(run_id)
        return RunResult(
            run_id=run.run_id,
            status=run.status,
            selected_papers=self.load_selected_papers(run_id),
            evidence_cards=self.load_evidence_cards(run_id),
            conflict_clusters=self.load_conflict_clusters(run_id),
            hypotheses=self.load_hypotheses(run_id),
            report_markdown=run.final_report_md,
            trace_url=f"/v1/runs/{run_id}/trace",
            stage_summaries=self.list_stage_summaries(run_id),
        )

    def _require_run(self, session: Session, run_id: str) -> RunRow:
        row = session.get(RunRow, run_id)
        if row is None:
            raise KeyError(f"run not found: {run_id}")
        return row

    def _scoped_id(self, run_id: str, local_id: str) -> str:
        return f"{run_id}:{local_id}"

    def _to_run_state(self, session: Session, row: RunRow) -> RunState:
        selected_paper_ids = list(
            session.execute(
                select(RunPaperRow.paper_id)
                .where(RunPaperRow.run_id == row.id)
                .order_by(RunPaperRow.selected_rank.asc())
            ).scalars()
        )
        evidence_ids = list(
            session.execute(
                select(EvidenceCardRow.id).where(EvidenceCardRow.run_id == row.id)
            ).scalars()
        )
        conflict_cluster_ids = list(
            session.execute(
                select(ConflictClusterRow.id).where(ConflictClusterRow.run_id == row.id)
            ).scalars()
        )
        hypothesis_ids = list(
            session.execute(select(HypothesisRow.id).where(HypothesisRow.run_id == row.id)).scalars()
        )
        return RunState(
            run_id=row.id,
            topic=row.topic,
            constraints=RunConstraints.model_validate(row.constraints_json),
            status=row.status,
            error_message=row.error_message,
            selected_paper_ids=selected_paper_ids,
            evidence_ids=evidence_ids,
            conflict_cluster_ids=conflict_cluster_ids,
            hypothesis_ids=hypothesis_ids,
            final_report_md=row.final_report_md,
            trace_path=f"/v1/runs/{row.id}/trace",
        )

    def _to_run_summary(self, session: Session, row: RunRow) -> RunSummary:
        return RunSummary(
            run_id=row.id,
            topic=row.topic,
            status=row.status,
            created_at=row.created_at,
            updated_at=row.updated_at,
            selected_paper_count=self._count_rows(session, RunPaperRow, row.id),
            evidence_card_count=self._count_rows(session, EvidenceCardRow, row.id),
            conflict_cluster_count=self._count_rows(session, ConflictClusterRow, row.id),
            hypothesis_count=self._count_rows(session, HypothesisRow, row.id),
            error_message=row.error_message,
        )

    def _count_rows(self, session: Session, row_type, run_id: str) -> int:
        return int(
            session.execute(
                select(func.count()).select_from(row_type).where(row_type.run_id == run_id)
            ).scalar_one()
        )
