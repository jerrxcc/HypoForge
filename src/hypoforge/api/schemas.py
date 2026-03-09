from hypoforge.domain.schemas import RunRequest, RunResult, RunSummary


class RunRequestBody(RunRequest):
    """Public request schema for creating a run."""


class RunResponseBody(RunResult):
    """Public response schema for run results."""


class RunSummaryBody(RunSummary):
    """Public response schema for run list rows."""
