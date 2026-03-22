<!-- Generated: 2026-03-22 | Files scanned: 58 | Token estimate: ~950 -->

# Backend Codemap

## Entry Point

`api/app.py` (27 lines) → `create_app()` → mounts health + runs routers, injects ServiceContainer

## API Routes

```
GET  /healthz                      → health.healthz()
GET  /v1/runs                      → runs.list_runs()       → coordinator.list_runs()
POST /v1/runs                      → runs.create_run()      → coordinator.run_topic()
POST /v1/runs/launch               → runs.launch_run() 202  → coordinator.launch_run() + background execute_run()
GET  /v1/runs/{id}                 → runs.get_run()         → coordinator.get_run_result()
GET  /v1/runs/{id}/trace           → runs.get_trace()       → coordinator.get_trace()
GET  /v1/runs/{id}/report.md       → runs.get_report()      → coordinator.get_report_markdown()
POST /v1/runs/{id}/planner/rerun   → runs.rerun_planner()   → coordinator.rerun_planner()
```

## Orchestration Chain

```
coordinator.run_topic(topic)
  ├── repository.create_run()
  ├── _execute_linear() | _execute_with_reflection() | _execute_with_validation()
  │     ├── retrieval_agent(topic, constraints) → RetrievalSummary
  │     ├── review_agent(papers)               → ReviewSummary
  │     ├── critic_agent(evidence)             → CriticSummary
  │     └── planner_agent(conflicts)           → PlannerSummary (3 hypotheses)
  ├── report_renderer.render(result)
  └── repository.build_final_result()
```

## Key Files by Size

| File | Lines | Role |
|------|-------|------|
| `application/services.py` | 1155 | DI wiring, batch review, recovery, repair functions |
| `application/coordinator.py` | 804 | Pipeline orchestration, 3 execution paths |
| `agents/quality_assessor.py` | 779 | Hypothesis quality validation agent |
| `agents/reflection.py` | 773 | Quality evaluation, multi-perspective critique |
| `agents/conflict_detector.py` | 638 | Conflict validation agent |
| `agents/evidence_validator.py` | 605 | Evidence card validation agent |
| `agents/feedback_synthesizer.py` | 597 | Feedback aggregation validation agent |
| `infrastructure/db/repository.py` | 585 | All DB CRUD operations |
| `domain/perspectives.py` | 546 | 3 critique perspectives (method/stats/domain) |
| `infrastructure/connectors/alphaxiv.py` | 471 | AlphaXiv MCP client + connector |
| `application/correction_loop.py` | 394 | Reflection iteration controller |
| `domain/schemas.py` | 365 | All domain Pydantic models |
| `application/stage_graph.py` | 362 | Backtrack rules, stage navigation |

## Agent → Tool Mapping

| Agent | Tools Available |
|-------|----------------|
| Retrieval | search_openalex_works, search_semantic_scholar_papers, recommend_semantic_scholar_papers, search_alphaxiv_*, save_selected_papers, get_paper_details |
| Review | load_selected_papers, save_evidence_cards |
| Critic | load_evidence_cards, save_conflict_clusters |
| Planner | load_evidence_cards, load_conflict_clusters, save_hypotheses, render_markdown_report |

## Dependency Graph (simplified)

```
domain/schemas (leaf)
  ↑
infrastructure/{db,connectors} → domain/schemas
  ↑
tools/* → infrastructure/*, domain/schemas
  ↑
agents/* → tools/schemas, domain/*
  ↑
application/* → agents/*, tools/*, infrastructure/*, domain/*
  ↑
api/* → application/services, domain/schemas
```
