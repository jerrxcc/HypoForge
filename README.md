# HypoForge

HypoForge is a backend service for generating evidence-grounded scientific hypotheses from a research topic.

## Setup

```bash
python3.12 -m venv .venv
./.venv/bin/pip install -e '.[dev]'
```

## Tests

```bash
./.venv/bin/pytest -v
```

## Live API Test

```bash
RUN_REAL_API_TESTS=1 ./.venv/bin/pytest tests/live/test_real_runs_api.py -v
```

## Golden Topics Regression

```bash
RUN_REAL_API_TESTS=1 RUN_GOLDEN_TOPIC_TESTS=1 ./.venv/bin/pytest tests/live/test_golden_topics_api.py -v
```

`GET /v1/runs/{run_id}` now returns `stage_summaries`, which expose per-stage status, structured summary payloads, and timing metadata for `retrieval`, `review`, `critic`, and `planner`.

If a run fails in the planner stage but already has selected papers, evidence cards, and conflict clusters, you can rerun just the planner with `POST /v1/runs/{run_id}/planner/rerun`.

## Local Fake Run

```bash
./.venv/bin/python scripts/run_topic.py "solid-state battery electrolyte" --fake
```

## API

```bash
./.venv/bin/uvicorn hypoforge.api.app:create_app --factory --reload
```

## Status

The repository is being built from `SPEC.md` with a TDD-first workflow.
