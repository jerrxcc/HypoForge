# HypoForge Frontend Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build the agreed HypoForge frontend console on top of `Kiranism/next-shadcn-dashboard-starter`, and add the smallest backend extensions needed to support it.

**Architecture:** Keep the existing FastAPI backend as the system of record. Add a separate `frontend/` Next.js app that reuses the starter shell, strips unrelated features, and consumes typed backend APIs for run creation, run listing, detail, trace, and report views.

**Tech Stack:** Next.js 16, React 19, TypeScript, shadcn/ui, TanStack Query, TanStack Table, react-markdown, FastAPI, pytest.

---

### Task 1: Add `GET /v1/runs`

**Files:**
- Modify: `src/hypoforge/domain/schemas.py`
- Modify: `src/hypoforge/api/schemas.py`
- Modify: `src/hypoforge/api/routes/runs.py`
- Modify: `src/hypoforge/infrastructure/db/repository.py`
- Test: `tests/integration/test_runs_api.py`

**Step 1: Write the failing test**

Add a test that calls `GET /v1/runs` and asserts the response returns newest-first summaries with counts.

**Step 2: Run test to verify it fails**

Run: `./.venv/bin/pytest tests/integration/test_runs_api.py -k list_runs -v`

Expected: FAIL because the route does not exist yet.

**Step 3: Write minimal implementation**

Add a repository list method, a lightweight run summary schema, and the new route.

**Step 4: Run test to verify it passes**

Run: `./.venv/bin/pytest tests/integration/test_runs_api.py -k list_runs -v`

Expected: PASS

**Step 5: Commit**

```bash
git add tests/integration/test_runs_api.py src/hypoforge/domain/schemas.py src/hypoforge/api/schemas.py src/hypoforge/api/routes/runs.py src/hypoforge/infrastructure/db/repository.py
git commit -m "feat: add run list api"
```

### Task 2: Add frontend CORS support if needed

**Files:**
- Modify: `src/hypoforge/config.py`
- Modify: `src/hypoforge/api/app.py`
- Test: `tests/integration/test_health_api.py`

**Step 1: Write the failing test**

Add a preflight or origin header test for allowed frontend origins.

**Step 2: Run test to verify it fails**

Run: `./.venv/bin/pytest tests/integration/test_health_api.py -k cors -v`

Expected: FAIL because CORS middleware is not configured.

**Step 3: Write minimal implementation**

Add configurable allowed origins and wire `CORSMiddleware`.

**Step 4: Run test to verify it passes**

Run: `./.venv/bin/pytest tests/integration/test_health_api.py -k cors -v`

Expected: PASS

**Step 5: Commit**

```bash
git add tests/integration/test_health_api.py src/hypoforge/config.py src/hypoforge/api/app.py
git commit -m "feat: enable frontend cors"
```

### Task 3: Scaffold `frontend/` from the starter

**Files:**
- Create: `frontend/...`
- Modify: `.gitignore`

**Step 1: Copy the starter into `frontend/`**

Keep the layout shell and UI primitives.

**Step 2: Remove unrelated template features**

Strip Clerk auth and unused example modules.

**Step 3: Rename app metadata**

Replace titles, descriptions, default redirects, and demo copy with HypoForge equivalents.

**Step 4: Install dependencies and verify the shell boots**

Run: `cd frontend && npm install && npm run lint`

Expected: PASS

**Step 5: Commit**

```bash
git add .gitignore frontend
git commit -m "feat: scaffold frontend shell"
```

### Task 4: Add typed API client

**Files:**
- Create: `frontend/src/lib/api.ts`
- Create: `frontend/src/lib/types.ts`
- Create: `frontend/src/lib/query-client.ts`
- Create: `frontend/src/hooks/use-runs.ts`
- Create: `frontend/src/hooks/use-run-detail.ts`

**Step 1: Write the failing test**

Add a mocked client test for list-run and run-detail fetches.

**Step 2: Run test to verify it fails**

Run: `cd frontend && npm test -- api`

Expected: FAIL

**Step 3: Write minimal implementation**

Add typed fetch helpers for:
- create run
- list runs
- get run
- get trace
- get report
- rerun planner

**Step 4: Run test to verify it passes**

Run: `cd frontend && npm test -- api`

Expected: PASS

**Step 5: Commit**

```bash
git add frontend/src/lib frontend/src/hooks
git commit -m "feat: add frontend api client"
```

### Task 5: Replace navigation and theme

**Files:**
- Modify: `frontend/src/config/nav-config.ts`
- Modify: `frontend/src/app/layout.tsx`
- Modify: `frontend/src/app/dashboard/layout.tsx`
- Modify: `frontend/src/styles/theme.css`
- Modify: `frontend/src/styles/globals.css`
- Create: `frontend/src/components/hypoforge/stage-progress-band.tsx`

**Step 1: Write the failing test**

Add a component test that asserts nav items are `New Run` and `Runs`, and that the stage band renders all four stages.

**Step 2: Run test to verify it fails**

Run: `cd frontend && npm test -- nav`

Expected: FAIL

**Step 3: Write minimal implementation**

Replace template nav and add the light editorial theme and stage progress component.

**Step 4: Run test to verify it passes**

Run: `cd frontend && npm test -- nav`

Expected: PASS

**Step 5: Commit**

```bash
git add frontend/src/config/nav-config.ts frontend/src/app/layout.tsx frontend/src/app/dashboard/layout.tsx frontend/src/styles/theme.css frontend/src/styles/globals.css frontend/src/components/hypoforge/stage-progress-band.tsx
git commit -m "feat: add hypoforge theme and nav"
```

### Task 6: Build `New Run`

**Files:**
- Create: `frontend/src/app/dashboard/new-run/page.tsx`
- Create: `frontend/src/components/hypoforge/new-run-form.tsx`
- Create: `frontend/src/components/hypoforge/golden-topic-launcher.tsx`

**Step 1: Write the failing test**

Add a form test proving successful submit creates a run and navigates to its detail page.

**Step 2: Run test to verify it fails**

Run: `cd frontend && npm test -- new-run`

Expected: FAIL

**Step 3: Write minimal implementation**

Build the launch form and golden topic shortcuts.

**Step 4: Run test to verify it passes**

Run: `cd frontend && npm test -- new-run`

Expected: PASS

**Step 5: Commit**

```bash
git add frontend/src/app/dashboard/new-run/page.tsx frontend/src/components/hypoforge/new-run-form.tsx frontend/src/components/hypoforge/golden-topic-launcher.tsx
git commit -m "feat: add new run view"
```

### Task 7: Build `Runs`

**Files:**
- Create: `frontend/src/app/dashboard/runs/page.tsx`
- Create: `frontend/src/components/hypoforge/runs-table.tsx`
- Create: `frontend/src/components/hypoforge/run-status-badge.tsx`

**Step 1: Write the failing test**

Add a table test that asserts live run summaries render and link into detail pages.

**Step 2: Run test to verify it fails**

Run: `cd frontend && npm test -- runs`

Expected: FAIL

**Step 3: Write minimal implementation**

Render the real run list, summary metrics, and click-through to details.

**Step 4: Run test to verify it passes**

Run: `cd frontend && npm test -- runs`

Expected: PASS

**Step 5: Commit**

```bash
git add frontend/src/app/dashboard/runs/page.tsx frontend/src/components/hypoforge/runs-table.tsx frontend/src/components/hypoforge/run-status-badge.tsx
git commit -m "feat: add runs view"
```

### Task 8: Build `Run Detail / Overview`

**Files:**
- Create: `frontend/src/app/dashboard/runs/[runId]/page.tsx`
- Create: `frontend/src/components/hypoforge/run-overview.tsx`
- Create: `frontend/src/components/hypoforge/stage-summary-cards.tsx`
- Create: `frontend/src/components/hypoforge/result-panels.tsx`

**Step 1: Write the failing test**

Add a component test that asserts stage summaries and result counts render from run detail data.

**Step 2: Run test to verify it fails**

Run: `cd frontend && npm test -- overview`

Expected: FAIL

**Step 3: Write minimal implementation**

Build the overview hero, stage summaries, result panels, and degraded/failure notes.

**Step 4: Run test to verify it passes**

Run: `cd frontend && npm test -- overview`

Expected: PASS

**Step 5: Commit**

```bash
git add frontend/src/app/dashboard/runs/[runId]/page.tsx frontend/src/components/hypoforge/run-overview.tsx frontend/src/components/hypoforge/stage-summary-cards.tsx frontend/src/components/hypoforge/result-panels.tsx
git commit -m "feat: add run overview"
```

### Task 9: Build `Trace`

**Files:**
- Create: `frontend/src/app/dashboard/runs/[runId]/trace/page.tsx`
- Create: `frontend/src/components/hypoforge/trace-timeline.tsx`
- Create: `frontend/src/components/hypoforge/trace-inspector.tsx`

**Step 1: Write the failing test**

Add a test proving selecting a trace row updates the inspector panel.

**Step 2: Run test to verify it fails**

Run: `cd frontend && npm test -- trace`

Expected: FAIL

**Step 3: Write minimal implementation**

Build the split trace timeline and inspector view.

**Step 4: Run test to verify it passes**

Run: `cd frontend && npm test -- trace`

Expected: PASS

**Step 5: Commit**

```bash
git add frontend/src/app/dashboard/runs/[runId]/trace/page.tsx frontend/src/components/hypoforge/trace-timeline.tsx frontend/src/components/hypoforge/trace-inspector.tsx
git commit -m "feat: add trace view"
```

### Task 10: Build `Report`

**Files:**
- Create: `frontend/src/app/dashboard/runs/[runId]/report/page.tsx`
- Create: `frontend/src/components/hypoforge/report-panel.tsx`
- Create: `frontend/src/components/hypoforge/hypothesis-outline.tsx`

**Step 1: Write the failing test**

Add a test proving markdown content and hypothesis outline render from the fetched report data.

**Step 2: Run test to verify it fails**

Run: `cd frontend && npm test -- report`

Expected: FAIL

**Step 3: Write minimal implementation**

Build the markdown report panel and outline sidebar.

**Step 4: Run test to verify it passes**

Run: `cd frontend && npm test -- report`

Expected: PASS

**Step 5: Commit**

```bash
git add frontend/src/app/dashboard/runs/[runId]/report/page.tsx frontend/src/components/hypoforge/report-panel.tsx frontend/src/components/hypoforge/hypothesis-outline.tsx
git commit -m "feat: add report view"
```

### Task 11: Verify and document

**Files:**
- Modify: `README.md`
- Modify: `.env.example`

**Step 1: Run backend verification**

Run: `./.venv/bin/pytest tests/integration/test_runs_api.py tests/integration/test_health_api.py -v`

Expected: PASS

**Step 2: Run frontend verification**

Run: `cd frontend && npm test && npm run lint`

Expected: PASS

**Step 3: Run manual smoke**

Start backend and frontend, create a real run, and verify overview, trace, and report pages load.

**Step 4: Update docs**

Document frontend setup and env vars.

**Step 5: Commit**

```bash
git add README.md .env.example frontend tests/integration/test_runs_api.py tests/integration/test_health_api.py src/hypoforge
git commit -m "feat: add hypoforge frontend console"
```
