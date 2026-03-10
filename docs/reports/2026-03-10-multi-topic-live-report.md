# Multi-Topic Live Test Report

Date: 2026-03-10 13:33 +0800

## Scope
- Objective: verify that the current HypoForge stack is operational end-to-end from frontend to backend using multiple real research topics.
- Flow exercised for each topic:
  - `POST /v1/runs/launch`
  - poll `GET /v1/runs/{run_id}` until terminal state
  - fetch `GET /v1/runs/{run_id}/trace`
  - fetch `GET /v1/runs/{run_id}/report.md`
  - fetch `GET /v1/runs`
  - fetch frontend routes:
    - `/dashboard/runs/{run_id}`
    - `/dashboard/runs/{run_id}/trace`
    - `/dashboard/runs/{run_id}/report`
- Constraints used:
  - `year_from=2018`
  - `year_to=2026`
  - `open_access_only=false`
  - `max_selected_papers=18`
  - `novelty_weight=0.5`
  - `feasibility_weight=0.5`
  - `lab_mode=either`

## Fresh Verification
- `./.venv/bin/pytest -q` -> `66 passed, 6 skipped`
- `cd /Users/ccy/Documents/KEY/HypoForge/frontend && npm run lint` -> pass
- `cd /Users/ccy/Documents/KEY/HypoForge/frontend && npm run build` -> pass

## Topic Results
| Topic | Run ID | Final Status | Status Path | Papers | Evidence | Clusters | Hypotheses | Trace | Frontend Routes |
|---|---|---|---|---:|---:|---:|---:|---:|---|
| solid-state battery electrolyte | `run_dcee052e4e1e4172bd8b3143fc48150a` | done | retrieving -> reviewing -> criticizing -> planning -> done | 16 | 16 | 5 | 3 | 23 | overview/trace/report all 200 |
| protein binder design | `run_2e10888f4e1d4d708df1c0ec99630385` | done | queued -> retrieving -> reviewing -> criticizing -> planning -> done | 15 | 15 | 4 | 3 | 21 | overview/trace/report all 200 |
| CRISPR delivery lipid nanoparticles | `run_4094f52080a041f58267c242674ab854` | done | queued -> retrieving -> reviewing -> criticizing -> planning -> done | 14 | 14 | 4 | 3 | 19 | overview/trace/report all 200 |
| CO2 reduction catalyst selectivity | `run_1677ac41824142e38e7ad39cbb0100de` | done | queued -> retrieving -> reviewing -> criticizing -> planning -> done | 17 | 17 | 4 | 3 | 19 | overview/trace/report all 200 |
| diffusion model preference optimization | `run_217b6d7096524418a8cfed2b89cb2a58` | failed | queued -> retrieving -> reviewing -> criticizing -> planning -> failed | 13 | 7 | 4 | 0 | 19 | overview/trace/report all 200 |

## Aggregate Summary
- Topics tested: `5`
- Successful end-to-end runs: `4/5`
- Failed runs: `1/5`
- Success rate for this batch: `80%`
- Successful runs average duration: `266.4s`
- Successful runs paper count range: `14-17`
- Successful runs evidence count range: `14-17`
- Successful runs trace count range: `19-23`

## Failure Analysis
Failed topic:
- `diffusion model preference optimization`
- Run ID: `run_217b6d7096524418a8cfed2b89cb2a58`

Observed behavior:
- Retrieval completed successfully with 13 selected papers.
- Review completed with only 7 evidence cards.
- Critic completed with 4 conflict clusters.
- Planner reached `planning` and then the run terminated as `failed`.
- Frontend routes still rendered successfully, so this is not a UI routing failure.

Recorded planner degradation:
- `1 validation error for SaveHypothesesArgs`
- `hypotheses.1`
- `Value error, each hypothesis requires at least 3 supporting evidence ids`

Interpretation:
- The current stack is operational end-to-end, but not yet fully reliable across multiple live topics.
- The remaining instability is concentrated in planner output quality for lower-evidence topics, not in API routing, persistence, trace capture, or frontend rendering.

## Conclusion
- It is accurate to say that the frontend-to-backend workflow is operational and demonstrably works on real topics.
- It is not yet accurate to say that the system is fully stable for arbitrary live topics.
- Current evidence supports:
  - frontend routing works
  - async launch works
  - live status progression works
  - trace/report/archive retrieval works
  - multi-topic real runs usually complete
- Current blocker to a stronger claim:
  - planner/hypothesis validation can still fail on low-evidence live topics

## Recommended Next Step
- Harden planner fallback so that when a candidate hypothesis lacks 3 supporting evidence IDs, the host either:
  - repairs the hypothesis using nearby evidence in the same run, or
  - degrades to a valid partial planner result instead of marking the whole run as failed.

## Remediation Retest
Applied fix:
- `WorkspaceTools.save_hypotheses()` now pads sparse supporting evidence after host-side repair so planner output does not fail solely because a live topic produced fewer than 3 distinct supporting evidence IDs.
- The fix also adds a limitation note when this padding path is used.

Targeted live retest:
- Topic: `diffusion model preference optimization`
- Run ID: `run_039a9802068c409898c963b574b53fc8`
- Status path: `queued -> retrieving -> reviewing -> criticizing -> planning -> done`
- Final counts:
  - `selected_papers=18`
  - `evidence_cards=18`
  - `conflict_clusters=6`
  - `hypotheses=3`
  - `trace_count=34`
- Frontend route check:
  - `/dashboard/runs/{run_id}` returned `200`
- Planner stage:
  - `status=completed`
  - `report_rendered=true`

Updated interpretation after retest:
- The specific live failure observed in the first 5-topic batch is now resolved on a fresh rerun of the same topic.
- I have not rerun the full 5-topic batch after the fix, so the strongest verified claim is:
  - the previously failing live topic now completes end-to-end
  - backend regressions and frontend build checks remain green after the fix

## Strict-SPEC Addendum
Date: 2026-03-10

After reviewing the change against the original SPEC, the permissive fallback above was judged too weak semantically:
- it satisfied schema shape,
- but it did so by padding repeated supporting evidence IDs,
- which is not a faithful interpretation of "3 supporting evidence ids" in the spec.

Strict alignment changes:
- `Hypothesis` grounding now requires at least `3 distinct supporting evidence ids`.
- Host-side duplicate padding was removed.
- If planner cannot produce hypotheses with enough distinct support, the system falls back to the existing planner partial-result path instead of pretending success.

Fresh verification after strict pass:
- `./.venv/bin/pytest -q` -> `67 passed, 6 skipped`
- `RUN_REAL_API_TESTS=1 ./.venv/bin/pytest tests/live/test_real_runs_api.py -v` -> `1 passed in 221.69s`

Current interpretation:
- The system is now more faithful to the original grounding and hypothesis-quality intent of the SPEC.
- This may reduce apparent success rate on difficult low-evidence topics, but it is a more honest behavior.
- The permissive remediation section above should be treated as historical context, not the current policy.
