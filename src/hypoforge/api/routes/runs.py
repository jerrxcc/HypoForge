from __future__ import annotations

import asyncio
import json
import time

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, status
from fastapi.responses import PlainTextResponse
from starlette.responses import StreamingResponse

from hypoforge.api.schemas import (
    RunLaunchResponseBody,
    RunRequestBody,
    RunResponseBody,
    RunSummaryBody,
)


router = APIRouter(prefix="/v1/runs", tags=["runs"])


@router.get("", response_model=list[RunSummaryBody])
def list_runs(request: Request) -> list[RunSummaryBody]:
    coordinator = request.app.state.services.coordinator
    return [RunSummaryBody(**item.model_dump()) for item in coordinator.list_runs()]


@router.post("", response_model=RunResponseBody)
def create_run(request_body: RunRequestBody, request: Request) -> RunResponseBody:
    coordinator = request.app.state.services.coordinator
    try:
        result = coordinator.run_topic(request_body.topic, request_body.constraints)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return RunResponseBody(**result.model_dump())


@router.post(
    "/launch",
    response_model=RunLaunchResponseBody,
    status_code=status.HTTP_202_ACCEPTED,
)
def launch_run(
    request_body: RunRequestBody,
    request: Request,
    background_tasks: BackgroundTasks,
) -> RunLaunchResponseBody:
    coordinator = request.app.state.services.coordinator
    run = coordinator.launch_run(request_body.topic, request_body.constraints)
    background_tasks.add_task(coordinator.execute_run, run.run_id)
    return RunLaunchResponseBody(**run.model_dump())


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


@router.get("/{run_id}/events")
async def stream_events(run_id: str, request: Request) -> StreamingResponse:
    """SSE endpoint for real-time run activity.

    Returns a Server-Sent Events stream with named events:
    - snapshot: initial state on connect
    - stage_start / stage_complete
    - tool_start / tool_complete
    - run_complete / run_error
    - keepalive (comment-only, every 15s)
    """
    event_bus = request.app.state.services.event_bus
    if event_bus is None:
        raise HTTPException(status_code=501, detail="SSE not available (event bus not configured)")

    # Verify run exists
    coordinator = request.app.state.services.coordinator
    try:
        coordinator.get_run_result(run_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    queue = event_bus.subscribe(run_id)

    async def event_generator():
        try:
            while True:
                # Check if client disconnected
                if await request.is_disconnected():
                    break
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=15.0)
                except asyncio.TimeoutError:
                    # Send keepalive comment
                    yield ": keepalive\n\n"
                    continue

                event_type = event.get("type", "message")
                data = json.dumps(event, default=str)
                yield f"event: {event_type}\ndata: {data}\n\n"

                # Terminal events — close stream
                if event_type in ("run_complete", "run_error"):
                    break
        finally:
            event_bus.unsubscribe(run_id, queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
