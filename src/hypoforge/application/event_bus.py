"""In-process event bus for SSE streaming of run activity.

WARNING: This is a process-local bus. Multi-worker deployments will
lose events for subscribers connected to a different worker. Run with
``--workers 1`` (the uvicorn default).
"""

from __future__ import annotations

import asyncio
import logging
import threading
import time
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class _Subscriber:
    queue: asyncio.Queue
    loop: asyncio.AbstractEventLoop


class RunEventBus:
    """Thread-safe in-process event bus with per-run pub/sub."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._subscribers: dict[str, list[_Subscriber]] = {}
        self._seq: dict[str, int] = {}
        self._current_activity: dict[str, dict | None] = {}
        self._stage_attempts: dict[str, dict[str, int]] = {}

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------

    def init_run(self, run_id: str, seed_attempts: dict[str, int] | None = None) -> None:
        """Initialize tracking for a new run.

        Args:
            run_id: The run to track.
            seed_attempts: Pre-existing stage attempt counts from DB (for restart safety).
        """
        with self._lock:
            self._subscribers.setdefault(run_id, [])
            self._seq[run_id] = 0
            self._current_activity[run_id] = None
            self._stage_attempts[run_id] = dict(seed_attempts or {})

    def init_rerun_planner(self, run_id: str, seed_attempts: dict[str, int] | None = None) -> None:
        """Initialize for a planner rerun — keep existing stage attempts, reset planner."""
        with self._lock:
            self._subscribers.setdefault(run_id, [])
            self._seq.setdefault(run_id, 0)
            self._current_activity[run_id] = None
            if seed_attempts:
                self._stage_attempts[run_id] = dict(seed_attempts)

    # ------------------------------------------------------------------
    # Attempt tracking
    # ------------------------------------------------------------------

    def record_stage_attempt(self, run_id: str, stage_name: str) -> int:
        """Increment and return the new attempt number for a stage."""
        with self._lock:
            attempts = self._stage_attempts.setdefault(run_id, {})
            current = attempts.get(stage_name, 0)
            new_attempt = current + 1
            attempts[stage_name] = new_attempt
            return new_attempt

    def get_attempt(self, run_id: str, stage_name: str) -> int:
        """Get current attempt for a stage (defaults to 1)."""
        with self._lock:
            return self._stage_attempts.get(run_id, {}).get(stage_name, 1)

    # ------------------------------------------------------------------
    # Pub/Sub
    # ------------------------------------------------------------------

    def subscribe(self, run_id: str) -> asyncio.Queue:
        """Subscribe to events for a run. Returns a queue that receives events.

        Immediately pushes a snapshot event with current state.
        Must be called from an async context (needs running event loop).
        """
        loop = asyncio.get_running_loop()
        queue: asyncio.Queue = asyncio.Queue()
        sub = _Subscriber(queue=queue, loop=loop)

        with self._lock:
            self._subscribers.setdefault(run_id, []).append(sub)
            # Build snapshot
            snapshot = {
                "type": "snapshot",
                "seq": 0,
                "timestamp": time.time(),
                "current_activity": self._current_activity.get(run_id),
                "stage_attempts": dict(self._stage_attempts.get(run_id, {})),
            }

        # Push snapshot directly (already in async context)
        queue.put_nowait(snapshot)
        return queue

    def unsubscribe(self, run_id: str, queue: asyncio.Queue) -> None:
        """Remove a subscriber."""
        with self._lock:
            subs = self._subscribers.get(run_id, [])
            self._subscribers[run_id] = [s for s in subs if s.queue is not queue]

    def publish(self, run_id: str, event: dict) -> None:
        """Publish an event to all subscribers of a run.

        Injects seq + timestamp. Safe to call from any thread.
        """
        with self._lock:
            seq = self._seq.get(run_id, 0) + 1
            self._seq[run_id] = seq

            event = {**event, "seq": seq, "timestamp": time.time()}

            # Track current activity
            event_type = event.get("type")
            if event_type == "tool_start":
                self._current_activity[run_id] = event
            elif event_type in ("tool_complete", "stage_complete", "run_complete", "run_error"):
                self._current_activity[run_id] = None

            subs = list(self._subscribers.get(run_id, []))

        # Deliver outside lock
        dead: list[_Subscriber] = []
        for sub in subs:
            try:
                sub.loop.call_soon_threadsafe(sub.queue.put_nowait, event)
            except RuntimeError:
                dead.append(sub)

        if dead:
            with self._lock:
                for d in dead:
                    subs_list = self._subscribers.get(run_id, [])
                    self._subscribers[run_id] = [s for s in subs_list if s.queue is not d.queue]

    def cleanup_run(self, run_id: str) -> None:
        """Remove all tracking data for a run."""
        with self._lock:
            self._subscribers.pop(run_id, None)
            self._seq.pop(run_id, None)
            self._current_activity.pop(run_id, None)
            self._stage_attempts.pop(run_id, None)
