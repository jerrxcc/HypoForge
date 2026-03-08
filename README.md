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
