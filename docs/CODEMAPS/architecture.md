<!-- Generated: 2026-04-07 | Files scanned: 190 | Token estimate: ~900 -->

# Architecture

## System Overview

Multi-agent scientific hypothesis generator. Research topic in, auditable dossier out.

```
                    +-------------+
                    |  Next.js 16 |  :3000
                    |  React 19   |
                    +------+------+
                           | REST (JSON) + SSE
                    +------v------+
                    |  FastAPI    |  :8000
                    |  Uvicorn    |
                    +------+------+
                           |
          +----------------+----------------+
          |                |                |
    +-----v-----+   +-----v-----+   +------v-----+
    |  OpenAI   |   | OpenAlex  |   | Semantic   |
    | Responses |   |   API     |   | Scholar    |
    |   API     |   +-----------+   +------------+
    +-----------+         |                |
          |          +----v----------------v--+
          |          | AlphaXiv MCP (optional)|
          |          +------------------------+
          |
    +-----v-----+
    |  SQLite   |  hypoforge.db
    +-----------+
```

## Pipeline Flow

```
Topic -> Retrieval -> Review -> Critic -> Planner -> Dossier
            |           |        |         |
            |     (optional reflection/validation loop)
            |           |        |         |
         Papers    Evidence  Conflicts  3 Hypotheses
        (24-36)     Cards    Clusters   + MD Report
```

Each stage: agent gets system prompt + tools -> model decides tool calls -> bounded steps -> structured output.

SSE stream (`GET /v1/runs/{id}/events`) pushes real-time stage/tool events to the frontend via `RunEventBus`.

## Service Boundaries

| Layer | Directory | Responsibility |
|-------|-----------|---------------|
| API | `api/` | HTTP routes, request/response schemas, CORS, SSE |
| Application | `application/` | Coordinator, DI, reflection loop, stage graph, budget, event bus |
| Agents | `agents/` | Stage runners, prompts, providers, validation agents |
| Domain | `domain/` | Pydantic models, quality metrics, perspectives, validation models |
| Infrastructure | `infrastructure/` | DB repository, connectors (OA/S2/AX), caching |
| Tools | `tools/` | Tool implementations agents can invoke |
| Testing | `testing/` | Golden topic regressions, live test helpers |

## Key Constraints

- Always exactly 3 hypotheses per run
- Max 36 selected papers (configurable)
- Tool steps bounded per stage: retrieval=12, review=6, critic=4, planner=4
- All hypotheses must reference evidence IDs
- No PDF parsing -- title/abstract/metadata only
