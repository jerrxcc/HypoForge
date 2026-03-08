from hypoforge.domain.schemas import RunRequest, RunResult


class RunRequestBody(RunRequest):
    """Public request schema for creating a run."""


class RunResponseBody(RunResult):
    """Public response schema for run results."""
