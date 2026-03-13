# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

HypoForge is a multi-agent scientific hypothesis generator. It takes a research topic, runs it through a four-stage pipeline (retrieval → review → critic → planner), and returns an auditable dossier with selected papers, evidence cards, conflict clusters, three ranked hypotheses, and a final Markdown report.

**Stack:**
- Backend: FastAPI + OpenAI Responses API + SQLAlchemy + SQLite
- Frontend: Next.js 16 + React 19 + TypeScript + Shadcn UI + Tailwind CSS v4

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

Feature-based organization:
- `app/` - Next.js App Router (auth routes, dashboard routes, API routes)
- `components/` - Shared UI components (Shadcn-based)
- `features/` - Feature-specific components and actions
- `lib/` - Utilities and configurations
- `hooks/` - Custom React hooks
- `stores/` - Zustand state management
- `types/` - TypeScript types

## Environment Variables

### Backend (`.env`)

```env
OPENAI_API_KEY=required
DATABASE_URL=sqlite:///./hypoforge.db
FRONTEND_ALLOWED_ORIGINS=["http://127.0.0.1:3000","http://localhost:3000"]

# Optional
OPENAI_BASE_URL=
OPENAI_MODEL_RETRIEVAL=gpt-5.4
OPENAI_MODEL_REVIEW=gpt-5-mini
OPENAI_MODEL_CRITIC=gpt-5.4
OPENAI_MODEL_PLANNER=gpt-5.4
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
