<!-- Generated: 2026-04-07 | Files scanned: 59 | Token estimate: ~950 -->

# Backend Codemap

## Entry Point

`api/app.py` (33 lines) -> `create_app()` -> mounts health + runs routers, injects ServiceContainer

## API Routes

```
GET  /healthz                      -> health.healthz()
GET  /v1/runs                      -> runs.list_runs()       -> coordinator.list_runs()
POST /v1/runs                      -> runs.create_run()      -> coordinator.run_topic()
POST /v1/runs/launch               -> runs.launch_run() 202  -> coordinator.launch_run() + background execute_run()
GET  /v1/runs/{id}                 -> runs.get_run()         -> coordinator.get_run_result()
GET  /v1/runs/{id}/trace           -> runs.get_trace()       -> coordinator.get_trace()
GET  /v1/runs/{id}/report.md       -> runs.get_report()      -> coordinator.get_report_markdown()
POST /v1/runs/{id}/planner/rerun   -> runs.rerun_planner()   -> coordinator.rerun_planner()
GET  /v1/runs/{id}/events          -> runs.stream_events()   -> SSE via RunEventBus (real-time activity)
```

## Orchestration Chain

```
coordinator.run_topic(topic)
  +-- repository.create_run()
  +-- _execute_linear() | _execute_with_reflection() | _execute_with_validation()
  |     +-- retrieval_agent(topic, constraints) -> RetrievalSummary
  |     +-- review_agent(papers)               -> ReviewSummary
  |     +-- critic_agent(evidence)             -> CriticSummary
  |     +-- planner_agent(conflicts)           -> PlannerSummary (3 hypotheses)
  +-- report_renderer.render(result)
  +-- repository.build_final_result()
```

Events emitted via `_emit()` -> `RunEventBus.publish()` at stage_start, stage_complete, tool_start, tool_complete, run_complete, run_error.

## Key Files by Size

| File | Lines | Role |
|------|-------|------|
| `application/services.py` | 776 | DI wiring, batch review, connector/tool orchestration |
| `agents/quality_assessor.py` | 778 | Hypothesis quality validation agent |
| `agents/reflection.py` | 772 | Quality evaluation, multi-perspective critique |
| `infrastructure/db/repository.py` | 650 | All DB CRUD operations |
| `application/coordinator.py` | 729 | Pipeline orchestration, 3 execution paths, SSE events |
| `agents/conflict_detector.py` | 637 | Conflict validation agent |
| `agents/evidence_validator.py` | 604 | Evidence card validation agent |
| `agents/feedback_synthesizer.py` | 596 | Feedback aggregation validation agent |
| `domain/perspectives.py` | 545 | 3 critique perspectives (method/stats/domain) |
| `infrastructure/connectors/alphaxiv.py` | 470 | AlphaXiv MCP client + connector |
| `domain/schemas.py` | 378 | All domain Pydantic models |
| `application/stage_graph.py` | 361 | Backtrack rules, stage navigation |
| `testing/live_regressions.py` | 354 | Golden topic regression framework |
| `infrastructure/connectors/cached.py` | 282 | Cached connector wrappers |
| `infrastructure/cache.py` | 271 | In-memory validation cache |
| `agents/validation_base.py` | 269 | Abstract base for validation agents |
| `domain/validation.py` | 247 | Validation domain models (issues, backtrack, feedback) |
| `application/event_bus.py` | 155 | Thread-safe in-process SSE event bus |
| `application/budget.py` | ~80 | RunBudgetTracker, BudgetExceededError |

## Agent -> Tool Mapping

| Agent | Tools Available |
|-------|----------------|
| Retrieval | search_openalex_works, search_semantic_scholar_papers, recommend_semantic_scholar_papers, search_alphaxiv_*, save_selected_papers, get_paper_details |
| Review | load_selected_papers, save_evidence_cards |
| Critic | load_evidence_cards, save_conflict_clusters |
| Planner | load_evidence_cards, load_conflict_clusters, save_hypotheses, render_markdown_report |

## Dependency Graph (simplified)

```
domain/{schemas,validation} (leaf)
  ^
infrastructure/{db,connectors,cache} -> domain/schemas
  ^
tools/* -> infrastructure/*, domain/schemas
  ^
agents/* -> tools/schemas, domain/*, agents/validation_base
  ^
application/* -> agents/*, tools/*, infrastructure/*, domain/*
  ^
api/* -> application/services, domain/schemas
```
