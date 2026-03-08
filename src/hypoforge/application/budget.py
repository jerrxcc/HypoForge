from __future__ import annotations

from dataclasses import dataclass


class BudgetExceededError(RuntimeError):
    def __init__(self, *, source: str, message: str) -> None:
        super().__init__(message)
        self.source = source


@dataclass
class RunBudgetTracker:
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
