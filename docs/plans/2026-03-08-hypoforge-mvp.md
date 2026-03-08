# HypoForge MVP Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build the HypoForge V1 backend from `SPEC.md`, including FastAPI API endpoints, bounded four-stage agent orchestration, SQLite persistence, deterministic report rendering, tests, and Git/GitHub initialization.

**Architecture:** Use a layered Python service under `src/hypoforge/` with a coordinator controlling fixed stage order and provider-backed agent runners controlling bounded tool loops. Keep OpenAI/OpenAlex/Semantic Scholar integration behind adapters so the system is testable offline while still supporting real services through configuration.

**Tech Stack:** Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2, httpx, pytest, GitHub CLI

---

### Task 1: Bootstrap packaging, settings, and app shell

**Files:**
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `.env.example`
- Create: `README.md`
- Create: `src/hypoforge/__init__.py`
- Create: `src/hypoforge/config.py`
- Create: `src/hypoforge/api/__init__.py`
- Create: `src/hypoforge/api/app.py`
- Create: `src/hypoforge/api/routes/__init__.py`
- Create: `src/hypoforge/api/routes/health.py`
- Test: `tests/unit/test_config.py`
- Test: `tests/integration/test_health_api.py`

**Step 1: Write the failing tests**

```python
from hypoforge.config import Settings


def test_settings_defaults():
    settings = Settings()
    assert settings.app_env == "dev"
    assert settings.max_selected_papers == 36
```

```python
from fastapi.testclient import TestClient

from hypoforge.api.app import create_app


def test_healthz_returns_ok():
    client = TestClient(create_app())
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_config.py tests/integration/test_health_api.py -v`
Expected: FAIL because the package and app do not exist yet.

**Step 3: Write minimal implementation**

Create a minimal package, settings object with SPEC-aligned defaults, FastAPI app factory, and `/healthz` route.

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_config.py tests/integration/test_health_api.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add pyproject.toml .gitignore .env.example README.md src/hypoforge tests
git commit -m "feat: bootstrap HypoForge service shell"
```

### Task 2: Define domain schemas and API contracts

**Files:**
- Create: `src/hypoforge/domain/__init__.py`
- Create: `src/hypoforge/domain/models.py`
- Create: `src/hypoforge/domain/schemas.py`
- Create: `src/hypoforge/api/schemas.py`
- Test: `tests/unit/test_domain_models.py`
- Test: `tests/unit/test_api_schemas.py`

**Step 1: Write the failing tests**

```python
from hypoforge.domain.schemas import RunConstraints


def test_run_constraints_default_weights_sum_to_one():
    constraints = RunConstraints()
    assert constraints.novelty_weight == 0.5
    assert constraints.feasibility_weight == 0.5
```

```python
import pytest

from hypoforge.domain.schemas import PlannerSummary


def test_planner_summary_requires_three_hypotheses():
    with pytest.raises(ValueError):
        PlannerSummary(hypotheses_created=2, report_rendered=True, top_axes=[], planner_notes=[])
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_domain_models.py tests/unit/test_api_schemas.py -v`
Expected: FAIL because schemas are not implemented.

**Step 3: Write minimal implementation**

Implement Pydantic models for run input, run result, paper detail, evidence card, conflict cluster, hypothesis, and summary payloads with SPEC-aligned validation rules.

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_domain_models.py tests/unit/test_api_schemas.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/hypoforge/domain src/hypoforge/api/schemas.py tests/unit
git commit -m "feat: add core domain schemas"
```

### Task 3: Implement persistence and repository operations

**Files:**
- Create: `src/hypoforge/infrastructure/__init__.py`
- Create: `src/hypoforge/infrastructure/db/__init__.py`
- Create: `src/hypoforge/infrastructure/db/models.py`
- Create: `src/hypoforge/infrastructure/db/session.py`
- Create: `src/hypoforge/infrastructure/db/repository.py`
- Test: `tests/unit/test_repository.py`

**Step 1: Write the failing tests**

```python
from hypoforge.domain.schemas import RunRequest
from hypoforge.infrastructure.db.repository import RunRepository


def test_repository_creates_and_loads_run(tmp_path):
    repo = RunRepository.from_sqlite_path(tmp_path / "app.db")
    run = repo.create_run(RunRequest(topic="protein binder design"))
    loaded = repo.get_run(run.run_id)
    assert loaded.run_id == run.run_id
    assert loaded.status == "queued"
```

```python
def test_repository_stores_tool_trace(tmp_path):
    repo = RunRepository.from_sqlite_path(tmp_path / "app.db")
    run = repo.create_run(...)
    repo.record_tool_trace(...)
    traces = repo.list_tool_traces(run.run_id)
    assert len(traces) == 1
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_repository.py -v`
Expected: FAIL because the database layer does not exist.

**Step 3: Write minimal implementation**

Create SQLAlchemy tables for the SPEC entities and repository methods for run lifecycle, stage outputs, trace logging, and final result aggregation.

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_repository.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/hypoforge/infrastructure/db tests/unit/test_repository.py
git commit -m "feat: add sqlite repository and trace persistence"
```

### Task 4: Build normalization, connectors, and scholarly tool handlers

**Files:**
- Create: `src/hypoforge/infrastructure/connectors/__init__.py`
- Create: `src/hypoforge/infrastructure/connectors/openalex.py`
- Create: `src/hypoforge/infrastructure/connectors/semantic_scholar.py`
- Create: `src/hypoforge/infrastructure/connectors/normalizers.py`
- Create: `src/hypoforge/infrastructure/connectors/dedupe.py`
- Create: `src/hypoforge/infrastructure/connectors/ranking.py`
- Create: `src/hypoforge/tools/__init__.py`
- Create: `src/hypoforge/tools/schemas.py`
- Create: `src/hypoforge/tools/scholarly_tools.py`
- Create: `src/hypoforge/tools/workspace_tools.py`
- Create: `src/hypoforge/tools/render_tools.py`
- Test: `tests/unit/test_normalizers.py`
- Test: `tests/unit/test_dedupe.py`
- Test: `tests/unit/test_openalex_connector.py`
- Test: `tests/unit/test_semantic_scholar_connector.py`
- Test: `tests/unit/test_scholarly_tools.py`

**Step 1: Write the failing tests**

```python
from hypoforge.infrastructure.connectors.normalizers import normalize_semantic_scholar_query


def test_semantic_scholar_query_replaces_hyphens():
    assert normalize_semantic_scholar_query("solid-state battery") == "solid state battery"
```

```python
def test_dedupe_prefers_record_with_abstract():
    winners = dedupe_papers([paper_without_abstract, paper_with_abstract])
    assert winners[0].abstract == "useful abstract"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_normalizers.py tests/unit/test_dedupe.py tests/unit/test_openalex_connector.py tests/unit/test_semantic_scholar_connector.py tests/unit/test_scholarly_tools.py -v`
Expected: FAIL because connectors and tool handlers are not implemented.

**Step 3: Write minimal implementation**

Implement query normalization, paper normalization, dedupe/ranking helpers, real HTTP connectors with `httpx`, and typed tool handlers that return compact JSON.

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_normalizers.py tests/unit/test_dedupe.py tests/unit/test_openalex_connector.py tests/unit/test_semantic_scholar_connector.py tests/unit/test_scholarly_tools.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/hypoforge/infrastructure/connectors src/hypoforge/tools tests/unit
git commit -m "feat: add scholarly connectors and tool handlers"
```

### Task 5: Implement renderer, prompts, and provider-backed agent runners

**Files:**
- Create: `src/hypoforge/agents/__init__.py`
- Create: `src/hypoforge/agents/prompts.py`
- Create: `src/hypoforge/agents/providers.py`
- Create: `src/hypoforge/agents/runner.py`
- Create: `src/hypoforge/agents/retrieval.py`
- Create: `src/hypoforge/agents/review.py`
- Create: `src/hypoforge/agents/critic.py`
- Create: `src/hypoforge/agents/planner.py`
- Create: `src/hypoforge/application/report_renderer.py`
- Test: `tests/unit/test_report_renderer.py`
- Test: `tests/integration/test_agent_runner.py`

**Step 1: Write the failing tests**

```python
def test_report_renderer_contains_three_hypotheses():
    markdown = render_report(run_result_with_three_hypotheses())
    assert markdown.count("## Hypothesis") == 3
```

```python
def test_agent_runner_executes_allowed_tool_calls(fake_provider, tool_dispatcher):
    summary = runner.execute_stage(...)
    assert summary.selected_paper_ids == ["p1", "p2"]
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_report_renderer.py tests/integration/test_agent_runner.py -v`
Expected: FAIL because renderer and stage runners are missing.

**Step 3: Write minimal implementation**

Implement deterministic Markdown rendering, provider protocol, fake provider support, OpenAI provider skeleton, stage prompts, and agent runners with tool whitelist and step-budget enforcement.

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_report_renderer.py tests/integration/test_agent_runner.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/hypoforge/agents src/hypoforge/application/report_renderer.py tests
git commit -m "feat: add agent runners and report renderer"
```

### Task 6: Implement coordinator and run APIs

**Files:**
- Create: `src/hypoforge/application/__init__.py`
- Create: `src/hypoforge/application/coordinator.py`
- Create: `src/hypoforge/application/services.py`
- Create: `src/hypoforge/api/routes/runs.py`
- Modify: `src/hypoforge/api/app.py`
- Test: `tests/integration/test_coordinator.py`
- Test: `tests/integration/test_runs_api.py`

**Step 1: Write the failing tests**

```python
def test_coordinator_runs_all_stages_in_order(fake_environment):
    result = coordinator.run_topic("protein binder design")
    assert result.status == "done"
    assert result.hypotheses[0].rank == 1
```

```python
def test_post_runs_returns_final_result(test_client):
    response = test_client.post("/v1/runs", json={"topic": "solid-state battery electrolyte"})
    assert response.status_code == 200
    assert response.json()["status"] in {"done", "failed"}
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/integration/test_coordinator.py tests/integration/test_runs_api.py -v`
Expected: FAIL because coordinator and run routes do not exist.

**Step 3: Write minimal implementation**

Wire repository, connectors, tools, agents, and renderer into a coordinator and expose the SPEC endpoints for run creation, run retrieval, report markdown, and trace.

**Step 4: Run test to verify it passes**

Run: `pytest tests/integration/test_coordinator.py tests/integration/test_runs_api.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/hypoforge/application src/hypoforge/api/routes tests/integration
git commit -m "feat: add coordinator and run endpoints"
```

### Task 7: Add end-to-end coverage, CLI helper, and repository automation

**Files:**
- Create: `scripts/run_topic.py`
- Create: `tests/e2e/test_end_to_end.py`
- Modify: `README.md`
- Modify: `task_plan.md`
- Modify: `findings.md`
- Modify: `progress.md`

**Step 1: Write the failing tests**

```python
def test_end_to_end_run_returns_three_hypotheses(fake_stack):
    result = run_fake_topic("CRISPR delivery lipid nanoparticles")
    assert result.status == "done"
    assert len(result.hypotheses) == 3
    assert result.report_markdown
    assert result.trace_url
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/e2e/test_end_to_end.py -v`
Expected: FAIL because the end-to-end wiring and helper script are incomplete.

**Step 3: Write minimal implementation**

Add a small CLI helper for manual local runs, complete the README usage instructions, and ensure the fake end-to-end stack passes.

**Step 4: Run test to verify it passes**

Run: `pytest tests/e2e/test_end_to_end.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add scripts/run_topic.py tests/e2e README.md
git commit -m "feat: add end-to-end coverage and local runner"
```

### Task 8: Initialize Git and push the private remote

**Files:**
- Create or modify as needed: `.git/`

**Step 1: Verify GitHub CLI authentication**

Run: `gh auth status`
Expected: authenticated GitHub account details.

**Step 2: Initialize repository**

Run: `git init -b main`
Expected: local Git repository created on branch `main`.

**Step 3: Commit the current project state**

Run: `git add . && git commit -m "feat: initialize HypoForge MVP"`
Expected: working tree clean after commit.

**Step 4: Create and push remote**

Run: `gh repo create HypoForge --private --source=. --remote=origin --push`
Expected: GitHub private repository created, `origin` configured, branch pushed.

**Step 5: Verify remote**

Run: `git remote -v`
Expected: `origin` points at the new GitHub repository.

### Task 9: Final verification

**Files:**
- Modify: `task_plan.md`
- Modify: `progress.md`

**Step 1: Run the focused test suite**

Run: `pytest -v`
Expected: all tests pass.

**Step 2: Run a smoke check**

Run: `python scripts/run_topic.py "solid-state battery electrolyte" --fake`
Expected: a completed fake run with three hypotheses and a Markdown report summary.

**Step 3: Verify API boot**

Run: `uvicorn hypoforge.api.app:create_app --factory --host 127.0.0.1 --port 8000`
Expected: app starts without import or config errors.

**Step 4: Update planning files**

Record completed phases, test evidence, and any residual risks in `task_plan.md` and `progress.md`.

**Step 5: Commit**

```bash
git add task_plan.md progress.md
git commit -m "chore: record final verification"
```
