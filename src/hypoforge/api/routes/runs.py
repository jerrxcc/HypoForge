from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import PlainTextResponse

from hypoforge.api.schemas import RunRequestBody, RunResponseBody, RunSummaryBody


router = APIRouter(prefix="/v1/runs", tags=["runs"])


@router.get("", response_model=list[RunSummaryBody])
def list_runs(request: Request) -> list[RunSummaryBody]:
    coordinator = request.app.state.services.coordinator
    return [RunSummaryBody(**item.model_dump()) for item in coordinator.list_runs()]


@router.post("", response_model=RunResponseBody)
def create_run(request_body: RunRequestBody, request: Request) -> RunResponseBody:
    coordinator = request.app.state.services.coordinator
    result = coordinator.run_topic(request_body.topic, request_body.constraints)
    return RunResponseBody(**result.model_dump())


@router.get("/{run_id}", response_model=RunResponseBody)
def get_run(run_id: str, request: Request) -> RunResponseBody:
    coordinator = request.app.state.services.coordinator
    try:
        result = coordinator.get_run_result(run_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return RunResponseBody(**result.model_dump())


@router.get("/{run_id}/trace")
def get_trace(run_id: str, request: Request) -> list[dict]:
    coordinator = request.app.state.services.coordinator
    return coordinator.get_trace(run_id)


@router.get("/{run_id}/report.md", response_class=PlainTextResponse)
def get_report(run_id: str, request: Request) -> str:
    coordinator = request.app.state.services.coordinator
    return coordinator.get_report_markdown(run_id)


@router.post("/{run_id}/planner/rerun", response_model=RunResponseBody)
def rerun_planner(run_id: str, request: Request) -> RunResponseBody:
    coordinator = request.app.state.services.coordinator
    try:
        result = coordinator.rerun_planner(run_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return RunResponseBody(**result.model_dump())
