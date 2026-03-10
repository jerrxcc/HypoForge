from __future__ import annotations

from dataclasses import dataclass


class BudgetExceededError(RuntimeError):
    """Raised when a per-run external API call budget is exhausted."""

    def __init__(self, *, source: str, message: str) -> None:
        super().__init__(message)
        self.source = source


class ToolStepBudgetExceededError(RuntimeError):
    """Raised when an agent exceeds its maximum allowed tool-call steps."""

    def __init__(self, *, agent_name: str, max_steps: int) -> None:
        super().__init__(f"{agent_name} exceeded tool step budget ({max_steps})")
        self.agent_name = agent_name
        self.max_steps = max_steps


@dataclass
class RunBudgetTracker:
    """Tracks and enforces per-run limits for external API calls.

    Keeps separate counters for OpenAlex and Semantic Scholar calls and
    raises :class:`BudgetExceededError` when either limit is reached.
    """

    max_openalex_calls: int
    max_semantic_scholar_calls: int
    openalex_calls: int = 0
    semantic_scholar_calls: int = 0

    def register_openalex_call(self) -> None:
        if self.openalex_calls >= self.max_openalex_calls:
            raise BudgetExceededError(
                source="openalex",
                message="budget exceeded for openalex calls",
            )
        self.openalex_calls += 1

    def register_semantic_scholar_call(self) -> None:
        if self.semantic_scholar_calls >= self.max_semantic_scholar_calls:
            raise BudgetExceededError(
                source="semantic_scholar",
                message="budget exceeded for semantic scholar calls",
            )
        self.semantic_scholar_calls += 1
