# Strict 8-Topic Live Report

Date: 2026-03-10 15:26 +0800

## Scope
- Mode: `strict-spec-grounding`
- Objective: validate frontend-to-backend live behavior on a broader topic set after switching to strict planner grounding.
- Execution flow per topic:
  - `POST /v1/runs/launch`
  - poll `GET /v1/runs/{run_id}` until terminal state
  - fetch `GET /v1/runs/{run_id}/trace`
  - fetch `GET /v1/runs/{run_id}/report.md`
  - fetch `GET /v1/runs`
  - fetch frontend routes:
    - `/dashboard/runs/{run_id}`
    - `/dashboard/runs/{run_id}/trace`
    - `/dashboard/runs/{run_id}/report`

## Constraints
- `year_from=2018`
- `year_to=2026`
- `open_access_only=false`
- `max_selected_papers=18`
- `novelty_weight=0.5`
- `feasibility_weight=0.5`
- `lab_mode=either`

## Results
| Topic | Run ID | Final Status | Papers | Evidence | Clusters | Hypotheses | Trace | Frontend Routes |
|---|---|---|---:|---:|---:|---:|---:|---|
| solid-state battery electrolyte | `run_8950f7b50a1e4d6880373cf445f3f253` | done | 18 | 18 | 4 | 3 | 19 | overview/trace/report all 200 |
| protein binder design | `run_c76036b09f2941dbb006dcfbb474bd8e` | done | 16 | 16 | 5 | 3 | 20 | overview/trace/report all 200 |
| CRISPR delivery lipid nanoparticles | `run_765958f20f5e418888f48c5e4a169af3` | done | 16 | 16 | 4 | 3 | 18 | overview/trace/report all 200 |
| CO2 reduction catalyst selectivity | `run_9ec2a98abdc947408ea6ca95aecba573` | done | 16 | 16 | 4 | 3 | 19 | overview/trace/report all 200 |
| diffusion model preference optimization | `run_997eac4637be4aa0b0124d40dc5d578a` | done | 15 | 10 | 3 | 3 | 21 | overview/trace/report all 200 |
| perovskite solar cell stability additives | `run_6781a0175c2e4ecca2924e1246607f86` | done | 18 | 18 | 2 | 3 | 19 | overview/trace/report all 200 |
| graph neural network drug-target interaction | `run_75d8fc79027d4b5bbb0d46c64da79526` | done | 14 | 14 | 4 | 3 | 19 | overview/trace/report all 200 |
| mRNA vaccine lipid nanoparticle formulation | `run_83348402821742c7a893aea85b741970` | done | 13 | 18 | 3 | 3 | 19 | overview/trace/report all 200 |

## Aggregate Summary
- Topics tested: `8`
- Successful runs: `8/8`
- Failed runs: `0/8`
- Success rate: `100%`
- Successful runs average duration: `230.2s`
- Paper count range: `13-18`
- Evidence count range: `10-18`
- Conflict cluster range: `2-5`
- Trace count range: `18-21`
- All frontend overview/trace/report routes returned `200`
- All topics produced non-zero token traces

## Interpretation
- Under strict planner grounding, the expanded sample of 8 real topics completed end-to-end without failure.
- This is materially stronger evidence than the earlier 5-topic batch because it includes:
  - the previously sensitive topic `diffusion model preference optimization`
  - 3 additional topics beyond the original batch
- The current system behavior is now both:
  - grounded more honestly against the original SPEC
  - operationally stable across a broader live sample

## Caution
- This is still an empirical batch result, not a mathematical guarantee.
- The right wording remains:
  - “the strict version currently runs end-to-end successfully on an 8-topic live batch”
  - not “all possible research topics are guaranteed to pass”
