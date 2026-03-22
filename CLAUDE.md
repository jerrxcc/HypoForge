# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

HypoForge is a multi-agent scientific hypothesis generator. It takes a research topic, runs it through a four-stage pipeline (retrieval → review → critic → planner), and returns an auditable dossier with selected papers, evidence cards, conflict clusters, three ranked hypotheses, and a final Markdown report.

**Stack:**
- Backend: FastAPI + OpenAI Responses API + SQLAlchemy + SQLite
- Frontend: Next.js 16 + React 19 + TypeScript + Radix UI + Tailwind CSS v4 + TanStack Query + Zustand

## Commands

### Backend

```bash
# Install dependencies
python3.12 -m venv .venv
./.venv/bin/pip install -e '.[dev]'

# Run the API server
./.venv/bin/uvicorn hypoforge.api.app:create_app --factory --reload

# Run tests
./.venv/bin/pytest -q

# Run a single test file
./.venv/bin/pytest tests/unit/test_config.py -v

# Run live API tests (requires OPENAI_API_KEY)
RUN_REAL_API_TESTS=1 ./.venv/bin/pytest tests/live/test_real_runs_api.py -v

# Run golden topic regressions
RUN_REAL_API_TESTS=1 RUN_GOLDEN_TOPIC_TESTS=1 ./.venv/bin/pytest tests/live/test_golden_topics_api.py -v

# CLI entry point for running a topic
./.venv/bin/python scripts/run_topic.py "solid-state battery electrolyte"
./.venv/bin/python scripts/run_topic.py "topic" --fake  # Fake mode
```

### Frontend

```bash
cd frontend
npm install
npm run dev      # Development server at http://localhost:3000
npm run lint     # ESLint
npm run build    # Production build
```

## Architecture

### Backend Structure (`src/hypoforge/`)

```
src/hypoforge/
├── api/                 # FastAPI routes and schemas
│   ├── app.py          # FastAPI app factory
│   ├── routes/         # health, runs endpoints
│   └── schemas.py      # API request/response models
├── application/         # Core orchestration
│   ├── coordinator.py  # Pipeline orchestration (retrieval → review → critic → planner)
│   ├── services.py     # Service container and dependency injection
│   ├── report_renderer.py  # Markdown report generation
│   ├── correction_loop.py  # Reflection-correction loop controller
│   └── stage_graph.py      # Stage navigation for backtracking
├── agents/              # Stage-specific agents
│   ├── retrieval.py    # Paper discovery from OpenAlex/Semantic Scholar
│   ├── review.py       # Evidence card extraction
│   ├── critic.py       # Conflict cluster identification
│   ├── planner.py      # Hypothesis generation (exactly 3)
│   ├── reflection.py   # Quality evaluation for reflection-correction loop
│   ├── runner.py       # Agent execution runtime (tool loop)
│   ├── prompts.py      # System prompts for each agent
│   └── providers.py    # OpenAI client configuration
├── domain/              # Domain models and validation
│   ├── models.py       # Core domain objects
│   ├── schemas.py      # Pydantic models for all stages
│   ├── quality.py      # Quality thresholds and evaluation
│   └── perspectives.py # Multi-perspective critique definitions
├── infrastructure/      # External integrations
│   ├── connectors/     # OpenAlex, Semantic Scholar, dedupe, ranking, normalizers
│   ├── db/             # SQLAlchemy models, session, repository
│   └── ...
└── tools/               # Tool implementations for agents
    ├── scholarly_tools.py   # search_openalex_works, search_semantic_scholar_papers
    ├── workspace_tools.py   # save/load papers, evidence, conflicts, hypotheses
    ├── render_tools.py      # render_markdown_report
    └── schemas.py           # Tool input/output schemas
```

### Pipeline Flow

```
Research Topic
    │
    ▼
┌─────────────┐
│  Retrieval  │ → Searches OpenAlex + Semantic Scholar → Selected Papers (24-36)
└─────────────┘
    │
    ▼
┌─────────────┐
│   Review    │ → Extracts Evidence Cards from papers
└─────────────┘
    │
    ▼
┌─────────────┐
│   Critic    │ → Builds Conflict Clusters from evidence
└─────────────┘
    │
    ▼
┌─────────────┐
│   Planner   │ → Generates exactly 3 hypotheses + Markdown report
└─────────────┘
```

### Key Design Principles

1. **Fixed stage sequence**: retrieval → review → critic → planner (cannot be reordered)
2. **Model-driven tool calling**: Each agent autonomously decides which tools to call within its stage
3. **Tool whitelist per agent**: Each agent only has access to specific tools
4. **Graceful degradation**: Stages can finish in "degraded" state, preserving partial results
5. **Reflection-correction loop**: Optional quality evaluation after each stage with backtracking support

### Reflection System

When `REFLECTION_ENABLE_REFLECTION=true`, the coordinator:
- Evaluates quality after each stage via `ReflectionAgent`
- Allows iterative re-execution when quality is below threshold
- Supports cross-stage backtracking for upstream improvements
- Records feedback history for debugging

### Frontend Structure (`frontend/src/`)

```
frontend/src/
├── app/                    # Next.js App Router
│   ├── layout.tsx          # Root layout
│   ├── page.tsx            # Landing (redirects to dashboard)
│   └── dashboard/          # Dashboard routes
│       ├── layout.tsx      # Dashboard shell
│       ├── page.tsx        # Dashboard home (stats, recent runs, golden topics)
│       ├── new/            # New run form
│       └── runs/           # Run list and detail views
│           ├── page.tsx    # All runs list
│           └── [id]/       # Single run detail
│               ├── page.tsx       # Run overview (papers, evidence, conflicts, hypotheses)
│               ├── report/        # Markdown report view
│               └── trace/         # Tool call trace view
├── components/
│   ├── dashboard/          # Dashboard-specific (hero, stats, recent runs, golden topics)
│   ├── dossier/            # Run result tabs (papers, evidence, conflicts, hypotheses)
│   ├── layout/             # App shell, header, sidebar, nav
│   ├── primitives/         # Base UI components (button, card, badge, dialog, etc.)
│   ├── report/             # Markdown renderer
│   ├── run/                # Run form, run card, stage progress
│   ├── trace/              # Trace panel
│   └── query-provider.tsx  # TanStack Query provider
├── hooks/                  # Custom hooks (use-runs, use-run, use-poll-run, use-report, use-trace)
├── lib/                    # API client, constants, utilities
├── stores/                 # Zustand state management
└── types/                  # TypeScript types (API response types)
```

## Environment Variables

### Backend (`.env`)

```env
OPENAI_API_KEY=required
DATABASE_URL=sqlite:///./hypoforge.db
FRONTEND_ALLOWED_ORIGINS=["http://127.0.0.1:3000","http://localhost:3000"]

# Optional
OPENAI_BASE_URL=
OPENAI_MODEL_RETRIEVAL=gpt-5.4-mini
OPENAI_MODEL_REVIEW=gpt-5.4-mini
OPENAI_MODEL_CRITIC=gpt-5.4-mini
OPENAI_MODEL_PLANNER=gpt-5.4-mini
OPENAI_REASONING_EFFORT=high
OPENALEX_API_KEY=
SEMANTIC_SCHOLAR_API_KEY=

# Reflection system
REFLECTION_ENABLE_REFLECTION=true
REFLECTION_MAX_STAGE_ITERATIONS=3
REFLECTION_MAX_CROSS_STAGE_ITERATIONS=2
```

### Frontend (`frontend/.env.local`)

```env
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

## API Endpoints

- `POST /v1/runs` - Synchronous run (returns full result)
- `POST /v1/runs/launch` - Async run (returns 202 Accepted)
- `GET /v1/runs` - List all runs
- `GET /v1/runs/{run_id}` - Get run result
- `GET /v1/runs/{run_id}/trace` - Get tool call trace
- `GET /v1/runs/{run_id}/report.md` - Get Markdown report
- `POST /v1/runs/{run_id}/planner/rerun` - Rerun planner only
- `GET /healthz` - Health check

## Testing Conventions

- Unit tests: `tests/unit/`
- Integration tests: `tests/integration/`
- E2E tests: `tests/e2e/`
- Live tests: `tests/live/` (require `RUN_REAL_API_TESTS=1`)
- Shared fixtures in `tests/conftest.py` and `tests/helpers/`

## Important Constraints

- **Hypotheses**: Always exactly 3 per run
- **Papers**: Default max 36 selected papers per run
- **Tool steps**: Bounded per stage (retrieval: 12, review: 6, critic: 4, planner: 4)
- **Grounding**: All hypotheses must reference evidence IDs from the pool
- **No PDF parsing**: V1 operates on title/abstract/metadata only

<!-- rtk-instructions v2 -->
# RTK (Rust Token Killer) - Token-Optimized Commands

## Golden Rule

**Always prefix commands with `rtk`**. If RTK has a dedicated filter, it uses it. If not, it passes through unchanged. This means RTK is always safe to use.

**Important**: Even in command chains with `&&`, use `rtk`:
```bash
# ❌ Wrong
git add . && git commit -m "msg" && git push

# ✅ Correct
rtk git add . && rtk git commit -m "msg" && rtk git push
```

## RTK Commands by Workflow

### Build & Compile (80-90% savings)
```bash
rtk cargo build         # Cargo build output
rtk cargo check         # Cargo check output
rtk cargo clippy        # Clippy warnings grouped by file (80%)
rtk tsc                 # TypeScript errors grouped by file/code (83%)
rtk lint                # ESLint/Biome violations grouped (84%)
rtk prettier --check    # Files needing format only (70%)
rtk next build          # Next.js build with route metrics (87%)
```

### Test (90-99% savings)
```bash
rtk cargo test          # Cargo test failures only (90%)
rtk vitest run          # Vitest failures only (99.5%)
rtk playwright test     # Playwright failures only (94%)
rtk test <cmd>          # Generic test wrapper - failures only
```

### Git (59-80% savings)
```bash
rtk git status          # Compact status
rtk git log             # Compact log (works with all git flags)
rtk git diff            # Compact diff (80%)
rtk git show            # Compact show (80%)
rtk git add             # Ultra-compact confirmations (59%)
rtk git commit          # Ultra-compact confirmations (59%)
rtk git push            # Ultra-compact confirmations
rtk git pull            # Ultra-compact confirmations
rtk git branch          # Compact branch list
rtk git fetch           # Compact fetch
rtk git stash           # Compact stash
rtk git worktree        # Compact worktree
```

Note: Git passthrough works for ALL subcommands, even those not explicitly listed.

### GitHub (26-87% savings)
```bash
rtk gh pr view <num>    # Compact PR view (87%)
rtk gh pr checks        # Compact PR checks (79%)
rtk gh run list         # Compact workflow runs (82%)
rtk gh issue list       # Compact issue list (80%)
rtk gh api              # Compact API responses (26%)
```

### JavaScript/TypeScript Tooling (70-90% savings)
```bash
rtk pnpm list           # Compact dependency tree (70%)
rtk pnpm outdated       # Compact outdated packages (80%)
rtk pnpm install        # Compact install output (90%)
rtk npm run <script>    # Compact npm script output
rtk npx <cmd>           # Compact npx command output
rtk prisma              # Prisma without ASCII art (88%)
```

### Files & Search (60-75% savings)
```bash
rtk ls <path>           # Tree format, compact (65%)
rtk read <file>         # Code reading with filtering (60%)
rtk grep <pattern>      # Search grouped by file (75%)
rtk find <pattern>      # Find grouped by directory (70%)
```

### Analysis & Debug (70-90% savings)
```bash
rtk err <cmd>           # Filter errors only from any command
rtk log <file>          # Deduplicated logs with counts
rtk json <file>         # JSON structure without values
rtk deps                # Dependency overview
rtk env                 # Environment variables compact
rtk summary <cmd>       # Smart summary of command output
rtk diff                # Ultra-compact diffs
```

### Infrastructure (85% savings)
```bash
rtk docker ps           # Compact container list
rtk docker images       # Compact image list
rtk docker logs <c>     # Deduplicated logs
rtk kubectl get         # Compact resource list
rtk kubectl logs        # Deduplicated pod logs
```

### Network (65-70% savings)
```bash
rtk curl <url>          # Compact HTTP responses (70%)
rtk wget <url>          # Compact download output (65%)
```

### Meta Commands
```bash
rtk gain                # View token savings statistics
rtk gain --history      # View command history with savings
rtk discover            # Analyze Claude Code sessions for missed RTK usage
rtk proxy <cmd>         # Run command without filtering (for debugging)
rtk init                # Add RTK instructions to CLAUDE.md
rtk init --global       # Add RTK to ~/.claude/CLAUDE.md
```

## Token Savings Overview

| Category | Commands | Typical Savings |
|----------|----------|-----------------|
| Tests | vitest, playwright, cargo test | 90-99% |
| Build | next, tsc, lint, prettier | 70-87% |
| Git | status, log, diff, add, commit | 59-80% |
| GitHub | gh pr, gh run, gh issue | 26-87% |
| Package Managers | pnpm, npm, npx | 70-90% |
| Files | ls, read, grep, find | 60-75% |
| Infrastructure | docker, kubectl | 85% |
| Network | curl, wget | 65-70% |

Overall average: **60-90% token reduction** on common development operations.
<!-- /rtk-instructions -->