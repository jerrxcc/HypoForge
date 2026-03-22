<!-- Generated: 2026-03-22 | Files scanned: 184 | Token estimate: ~700 -->

# Data Codemap

## Database: SQLite (SQLAlchemy ORM)

### Entity Relationship Diagram

```
runs (1) ──< run_papers >── papers (1)
runs (1) ──< evidence_cards >── papers (1)
runs (1) ──< conflict_clusters
runs (1) ──< hypotheses
runs (1) ──< stage_summaries     [unique per stage]
runs (1) ──< tool_traces
runs (1) ──< reflection_feedback
           cache_entries          [standalone]
```

### Tables

**runs** — core entity, tracks pipeline execution
- `id` PK (uuid4 hex), `topic`, `constraints_json`, `status` (queued→done/failed)
- `final_report_md`, `error_message`, `iteration_state_json`, `reflection_enabled`
- `created_at`, `updated_at`

**papers** — deduplicated paper store (shared across runs)
- `id` PK (external ID), `doi`, `normalized_title`, `year`, `payload_json`, `source_hash`

**run_papers** — join table, FK(runs, papers)
- `selected_rank`, `selection_reason`, `source_list_json`
- Unique: (run_id, paper_id)

**evidence_cards** — FK(runs, papers)
- `id` PK, `payload_json`, `confidence` float

**conflict_clusters** — FK(runs)
- `id` PK, `payload_json`

**hypotheses** — FK(runs)
- `id` PK, `rank` (1-3), `payload_json`

**stage_summaries** — FK(runs), unique(run_id, stage_name)
- `stage_name`, `status`, `summary_json`, `error_message`, `started_at`, `completed_at`

**tool_traces** — FK(runs)
- `agent_name`, `tool_name`, `args_json`, `result_summary_json`
- `latency_ms`, `model_name`, `input_tokens`, `output_tokens`, `success`

**reflection_feedback** — FK(runs)
- `feedback_id`, `target_stage`, `severity`, `issues_json`, `suggested_actions_json`
- `backtrack_stage`, `quality_scores_json`, `iteration_number`

**cache_entries** — standalone cache
- `namespace`, `cache_key` (unique together), `payload_json`, `expires_at`

### Migrations

Manual ALTER TABLE via `run_all_migrations()` at startup:
1. Add `iteration_state_json` + `reflection_enabled` to `runs`
2. Create `reflection_feedback` table if not exists

## Domain Models (Pydantic)

### Pipeline Data

| Model | Key Fields |
|-------|-----------|
| PaperDetail | paper_id, doi, title, abstract, year, authors, citation_count, provenance |
| EvidenceCard | evidence_id, paper_id, claim_text, direction, evidence_kind, confidence |
| ConflictCluster | cluster_id, topic_axis, conflict_type, supporting/conflicting_evidence_ids |
| Hypothesis | rank(1-3), title, statement, supporting_evidence_ids(min 3), novelty/feasibility/overall_score |
| MinimalExperiment | system, design, control, readouts, success_criteria |

### Stage Summaries

RetrievalSummary, ReviewSummary, CriticSummary, PlannerSummary (validates hypotheses_created==3)

### Type Enums

| Type | Values |
|------|--------|
| RunStatus | queued, retrieving, reviewing, criticizing, planning, reflecting, done, failed |
| StageName | retrieval, review, critic, planner |
| Direction | positive, negative, mixed, null, unclear |
| EvidenceKind | review, meta_analysis, experiment, simulation, benchmark, theory, unknown |
| ConflictType | direct_conflict, conditional_divergence, weak_evidence_gap |
