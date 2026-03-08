# HypoForge V1 Design

## Background
HypoForge V1 is a backend-only scientific hypothesis generation system. It accepts a research topic, retrieves relevant literature, compresses metadata-grounded evidence, identifies conflicts or evidence gaps, and returns exactly three falsifiable hypotheses with minimal experiments and a deterministic Markdown report.

The project starts from an empty repository. The implementation must follow the SPEC's MVP scope: Python 3.12, FastAPI, SQLite, OpenAI model-driven tool calling, OpenAlex, Semantic Scholar, strict schemas, and full tool traceability.

## Goals
- Build a runnable API-first backend from the SPEC.
- Preserve the fixed stage order: retrieval -> review -> critic -> planner.
- Make the stage internals testable without requiring live third-party APIs.
- Initialize a Git repository and sync to a private GitHub remote.

## Non-Goals
- No frontend, browser automation, PDF parsing, vector database, or arbitrary code execution.
- No multi-tenant auth or collaboration model.
- No claim of scientific truth or guaranteed novelty.

## Recommended Approach
Use a layered Python service with a small application core and replaceable infrastructure adapters.

The coordinator owns only the stage transitions and failure policy. Each stage delegates to an agent runner that exposes a tool whitelist and drives a bounded tool loop through a provider abstraction. Tools encapsulate all external calls, schema validation, normalization, persistence, and trace recording. This keeps the architecture close to the SPEC while preserving local testability.

## Alternatives Considered
### Alternative A: Fully stubbed MVP
Implement only fake connectors and a synthetic agent loop.

Pros:
- Fastest path to a demo.
- Lowest integration risk.

Cons:
- Misses the SPEC's requirement for real OpenAlex and Semantic Scholar support.
- Pushes real complexity into a second rewrite.

### Alternative B: SDK-heavy agent orchestration
Use OpenAI Agents SDK as the primary runtime and keep the app layer very thin.

Pros:
- Closest to a hosted agent experience.
- Potentially less handwritten orchestration code.

Cons:
- Harder to test deterministically.
- Higher integration churn for an empty repo.

### Chosen Direction
Implement a real backend with adapter boundaries: real HTTP connectors for OpenAlex and Semantic Scholar, a provider interface for the model loop, and deterministic fakes for tests. This is the closest fit to the SPEC without making tests brittle.

## Architecture
### Repository Layout
Use a modern `src/` package layout.

```text
repo/
  pyproject.toml
  .env.example
  README.md
  SPEC.md
  docs/plans/
  src/hypoforge/
    api/
    application/
    agents/
    domain/
    infrastructure/
    tools/
  tests/
  scripts/
```

### Layer Responsibilities
- `api/`: FastAPI app, routes, request/response schemas.
- `application/`: coordinator, service orchestration, budget rules.
- `agents/`: prompts, stage runners, provider integration, tool-loop control.
- `domain/`: Pydantic models, enums, constraints, report/result schemas.
- `infrastructure/`: settings, logging, SQLite repository, SQLAlchemy models, HTTP connectors, trace persistence.
- `tools/`: typed tool specs and handlers for scholarly search, workspace state, and report rendering.

### Execution Flow
1. `POST /v1/runs` validates input and creates a run record.
2. The coordinator updates run status and executes four stages in order.
3. Each agent runner receives stage context, prompt, allowed tools, and budget limits.
4. The provider returns tool calls or a final structured response.
5. The tool dispatcher validates args, executes logic, stores results, and records traces.
6. On completion, the renderer builds deterministic Markdown from stored structures.
7. The API returns the aggregated run result and exposes trace/report endpoints.

## Data Model
Persist the SPEC's core entities in SQLite:
- `runs`
- `papers`
- `run_papers`
- `evidence_cards`
- `conflict_clusters`
- `hypotheses`
- `tool_traces`

Domain models mirror the SPEC schemas exactly where possible. The storage schema may include operational fields such as timestamps, normalized titles, hashes, and error messages, but the API response shape should stay aligned with the SPEC.

## Model and Tool Strategy
### Provider Boundary
Create a `ModelProvider` protocol that can:
- start a stage run with system prompt, context, and tool schemas
- return tool requests
- accept tool outputs
- return a final structured payload

`OpenAIResponsesProvider` implements the real path. Tests use a deterministic fake provider that scripts tool calls and final outputs.

### Tools
Tools are strictly typed and agent-scoped:
- scholarly tools: OpenAlex, Semantic Scholar search, recommendation, paper detail hydration
- workspace tools: load/save selected papers, evidence cards, conflict clusters, hypotheses
- render tool: deterministic Markdown report generation

Every tool call records latency, summarized output, success state, and model metadata in `tool_traces`.

## Error Handling
- Retrieval degrades to single-source mode and low-evidence mode when necessary.
- Review retries per batch and stores partial evidence.
- Critic failure does not block planner; planner must then surface uncertainty explicitly.
- Planner failure still returns partial run state.
- Structured output failures get one automatic retry, then one repair parse attempt.

## Testing Strategy
Use TDD throughout implementation.

### Unit tests
- domain schema validation
- normalizer, dedupe, ranking
- renderer
- connector request/response normalization
- repository persistence and trace storage

### Integration tests
- stage runner tool-loop behavior with fake provider
- coordinator happy path and degradation path
- API endpoints with in-memory or temp SQLite

### End-to-end tests
- fixed topic through fake provider and fake scholarly connectors
- assert run completes, selected papers >= threshold, hypotheses == 3, report non-empty, trace non-empty

## Git and Delivery
Initialize Git after the first runnable project skeleton exists so the initial commit contains meaningful project history. Use GitHub CLI to create a private remote repository named `HypoForge` and push `main`.

## Risks
- OpenAI Responses API integration details may differ from the SPEC's idealized loop; keep the provider layer isolated.
- Semantic Scholar and OpenAlex payload quality varies; normalization and dedupe logic need strong tests.
- Full real-agent autonomy is intentionally constrained in V1 to protect determinism and budget control.

## Approval Record
Approved by user on 2026-03-08 to proceed with the recommended approach and default GitHub private remote setup.
