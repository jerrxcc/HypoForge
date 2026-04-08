# Live Batch Report

Date: 2026-04-08 10:30 +0800

## Scope
- Mode: `strict-spec-grounding`
- Baseline: OpenAI + OpenAlex + Semantic Scholar (no alphaXiv — token expired)
- Execution: synchronous `POST /v1/runs` + GET run/trace/report per topic
- Run in two batches (topics 1-4 + topics 5-8) due to network interruption between batches

## Constraints
- `year_from=2018`
- `year_to=2026`
- `open_access_only=False`
- `max_selected_papers=18`
- `novelty_weight=0.5`
- `feasibility_weight=0.5`
- `lab_mode=either`

## Results
| Topic | Status | Papers | Evidence | Clusters | Hypo | Grounding | Duration |
|---|---|---:|---:|---:|---:|---|---:|
| solid-state battery electrolyte | done | 18 | 18 | 2 | 3 | pass | 303.6s |
| protein binder design | done | 18 | 18 | 4 | 3 | pass | 457.7s |
| mRNA vaccine lipid nanoparticle formulation | done | 18 | 18 | 4 | 3 | pass | 472.0s |
| CO2 reduction catalyst selectivity | done | 18 | 18 | 2 | 3 | pass | 337.8s |
| diffusion model preference optimization | done | 18 | 18 | 2 | 3 | pass | 365.8s |
| perovskite solar cell stability additives | done | 18 | 18 | 2 | 3 | pass | 433.3s |
| graph neural network drug-target interaction | done | 18 | 18 | 2 | 3 | pass | 473.6s |
| quantum error correction surface codes | done | 18 | 20 | 4 | 3 | pass | 935.3s |

## Aggregate Summary
- Topics tested: `8`
- Successful runs: `8/8`
- Failed runs: `0/8`
- Success rate: `100%`
- Average duration: `472.4s`
- Paper count: `18` (all topics)
- Evidence count range: `18-20`
- Conflict cluster range: `2-4`
- All hypotheses: exactly `3` per topic
- All grounding checks: `passed`
- All API routes: `200`

## Bugs Found and Fixed During This Batch

### 1. `CriticQualityMetrics.evidence_coverage` exceeding 1.0

**File:** `agents/reflection.py:428`

**Root cause:** Critic clusters can reference phantom evidence IDs (hallucinated by the LLM). The coverage calculation `len(covered_evidence) / len(evidence_cards)` counted phantom IDs in the numerator, producing ratios > 1.0, which violated the Pydantic `le=1.0` constraint.

**Fix:** Intersect `covered_evidence` with `valid_evidence_ids` before computing the ratio.

### 2. Phantom evidence ID references in clusters and hypotheses

**Files:** `tools/workspace_tools.py` (save_conflict_clusters, _repair_hypothesis_payload)

**Root cause:** The LLM (critic and planner agents) occasionally generates evidence IDs that do not exist in the evidence pool. `save_conflict_clusters` and `save_hypotheses` accepted these without validation, breaking downstream grounding checks.

**Fix:** Added input boundary validation at the tool layer — phantom IDs are stripped from `supporting_evidence_ids` and `conflicting_evidence_ids` before saving, with a warning log.

**Observation:** Phantom ID frequency varies by topic. `quantum error correction surface codes` had 18+ phantom IDs stripped across clusters and hypotheses; simpler topics like `solid-state battery electrolyte` had zero.

## Hypothesis Grounding Detail

### solid-state battery electrolyte
- H1: Sulfide interfacial protection has a finite operating window (support=6, counter=1, experiment=yes)
- H2: Oxide Li-metal stability requires mechanics as well as surface chemistry (support=6, counter=1, experiment=yes)
- H3: Halide electrolytes win when they are dense, dry, and compositionally tuned (support=4, counter=3, experiment=yes)

### protein binder design
- H1: RFdiffusion success is target-class and assay dependent (support=4, counter=1, experiment=yes)
- H2: Peptide-specialized design stacks outperform generic ProteinMPNN-centered pipelines (support=3, counter=2, experiment=yes)
- H3: Need for post-design maturation depends on target and scaffold class (support=4, counter=2, experiment=yes)

### mRNA vaccine lipid nanoparticle formulation
- H1: PEG-lipid benefits are conditional and can invert under anti-PEG exposure (support=3, counter=1, experiment=yes)
- H2: Apparent charge-driven liver off-targeting is actually a pH-transition effect (support=3, counter=3, experiment=yes)
- H3: Extra innate adjuvanting helps only on weaker LNP backbones (support=3, counter=1, experiment=yes)

### CO2 reduction catalyst selectivity
- H1: Steady-state C2+ selectivity on Cu is governed by a dynamic CO/oxide microenvironment (support=4, counter=4, experiment=yes)
- H2: Ethanol gains require single-atom or nanoscale Ag that creates adjacent asymmetric sites (support=4, counter=3, experiment=yes)
- H3: CO-desorption tuning dominates open molecular SACs; methanol requires confinement (support=4, counter=2, experiment=yes)

### diffusion model preference optimization
- H1: Cheap feedback is enough for text-to-image alignment (support=4, counter=4, experiment=yes)
- H2: Heuristics, not objectives, explain most DPO-style diffusion gains (support=8, counter=3, experiment=yes)
- H3: Video alignment needs video-native feedback (support=3, counter=3, experiment=yes)

### perovskite solar cell stability additives
- H1: Annealing window governs the volatile-AX efficiency–stability tradeoff (support=7, counter=2, experiment=yes)
- H2: Standardized aging will reorder the apparent stability hierarchy (support=8, counter=4, experiment=yes)
- H3: Multifunctional additives outperform single-function passivators by coupling passivation with morphology control (support=10, counter=2, experiment=yes)

### graph neural network drug-target interaction
- H1: 3D pose-aware graph representations should win on structure-dependent DTI tasks (support=3, counter=2, experiment=yes)
- H2: Pocket-focused meta-learning should give the biggest edge in cold-start DTI (support=4, counter=2, experiment=yes)
- H3: Multi-scale and contrastive regularization helps DTA only under rigorous split conditions (support=3, counter=3, experiment=yes)

### quantum error correction surface codes
- H1: Bias-dependent crossover between tailored and rectangular surface codes (support=3, counter=3, experiment=yes)
- H2: Active leakage suppression beats post-selection on net throughput (support=4, counter=1, experiment=yes)
- H3: Decoder choice will form a Pareto frontier, not a single winner (support=4, counter=3, experiment=yes)

## Comparison with 2026-03-10 Strict Report

| Metric | 2026-03-10 | 2026-04-08 |
|--------|-----------|-----------|
| Topics | 8/8 | 8/8 |
| Success rate | 100% | 100% |
| Avg duration | 230.2s | 472.4s |
| Paper range | 13-18 | 18-18 |
| Evidence range | 10-18 | 18-20 |
| Cluster range | 2-5 | 2-4 |
| Grounding checks | not performed | all passed |
| Phantom ID validation | not implemented | implemented and active |

Duration increase is expected: reflection-correction loop (added 2026-03-11) runs quality evaluation after each stage. Paper count is now consistently 18 across all topics (vs 13-18 previously).

## Caution
- Empirical batch result, not a mathematical guarantee.
- Right wording: "the current system runs end-to-end successfully on an 8-topic live batch."
- alphaXiv integration was disabled for this batch (token expired); results reflect OpenAlex + Semantic Scholar baseline only.
