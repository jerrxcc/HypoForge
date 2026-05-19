from __future__ import annotations


class RecoverableToolInputError(ValueError):
    """Raised when a tool call can be retried with corrected model input."""

    def __init__(self, message: str, *, instruction: str) -> None:
        super().__init__(message)
        self.instruction = instruction
