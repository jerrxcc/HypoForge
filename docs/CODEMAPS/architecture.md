<!-- Generated: 2026-03-22 | Files scanned: 184 | Token estimate: ~900 -->

# Architecture

## System Overview

Multi-agent scientific hypothesis generator. Research topic in, auditable dossier out.

```
                    ┌─────────────┐
                    │  Next.js 16 │  :3000
                    │  React 19   │
                    └──────┬──────┘
                           │ REST (JSON)
                    ┌──────▼──────┐
                    │  FastAPI    │  :8000
                    │  Uvicorn    │
                    └──────┬──────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
    ┌─────▼─────┐   ┌─────▼─────┐   ┌─────▼─────┐
    │  OpenAI   │   │ OpenAlex  │   │ Semantic   │
    │ Responses │   │   API     │   │ Scholar    │
    │   API     │   └───────────┘   └────────────┘
    └───────────┘         │                │
          │          ┌────▼────────────────▼──┐
          │          │  AlphaXiv MCP (optional)│
          │          └────────────────────────┘
          │
    ┌─────▼─────┐
    │  SQLite   │  hypoforge.db
    └───────────┘
```

## Pipeline Flow

```
Topic → Retrieval → Review → Critic → Planner → Dossier
           │           │        │         │
           │     (optional reflection/validation loop)
           │           │        │         │
        Papers    Evidence  Conflicts  3 Hypotheses
       (24-36)     Cards    Clusters   + MD Report
```

Each stage: agent gets system prompt + tools → model decides tool calls → bounded steps → structured output.

## Service Boundaries

| Layer | Directory | Responsibility |
|-------|-----------|---------------|
| API | `api/` | HTTP routes, request/response schemas, CORS |
| Application | `application/` | Coordinator, DI, reflection loop, stage graph, budget |
| Agents | `agents/` | Stage runners, prompts, providers, validation agents |
| Domain | `domain/` | Pydantic models, quality metrics, perspectives |
| Infrastructure | `infrastructure/` | DB repository, connectors (OA/S2/AX), caching |
| Tools | `tools/` | Tool implementations agents can invoke |

## Key Constraints

- Always exactly 3 hypotheses per run
- Max 36 selected papers (configurable)
- Tool steps bounded per stage: retrieval=12, review=6, critic=4, planner=4
- All hypotheses must reference evidence IDs
- No PDF parsing — title/abstract/metadata only
