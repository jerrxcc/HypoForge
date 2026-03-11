# HypoForge Briefing Depth Design

## Goal

Increase the perceived and actual information value of a completed run without adding a new agent stage or violating the current grounding rules.

## Problem

Completed runs currently feel thinner than the runtime cost suggests because:

1. `ReportRenderer` only outputs counts and three basic hypothesis sections.
2. The frontend mostly visualizes counts, status, and raw stage payloads instead of a substantive scientific dossier.
3. Retrieval is marked `degraded` whenever `needs_broader_search=true`, even when the run already has >=12 selected papers and the rest of the pipeline completes successfully.

## Decision

Use a backend-first approach:

- fix retrieval degradation semantics to better match `SPEC.md`
- expand the final report into a richer research briefing
- then reframe `Overview` and `Report` around that briefing

## Retrieval Semantics

Current behavior is more conservative than SPEC.

Target behavior:

- `needs_broader_search=true` remains visible as a warning/note
- retrieval becomes `degraded` only when `coverage_assessment == "low"`
- single-source fallback can still complete successfully without forcing a degraded badge

This aligns more closely with SPEC 18.1:

- single-source fallback is acceptable
- broaden once if needed
- low-evidence mode is the true degradation boundary

## Backend Briefing Expansion

The final report should be upgraded into a grounded briefing built from existing artifacts.

New sections:

1. Executive summary
2. Evidence footing
3. Retrieval coverage and source health
4. Conflict map snapshot
5. Ranked hypothesis briefs
6. Experiment slate
7. Evidence appendix
8. Paper appendix

No extra model pass is introduced. The report only reorganizes data already present in:

- selected papers
- evidence cards
- conflict clusters
- hypotheses
- stage summaries

## Frontend Upgrade

Keep the current route structure, but make `Overview` and `Report` feel like a research dossier.

Planned changes:

- `Overview`: add a briefing-style summary layer for retrieval coverage, evidence footing, top conflict axes, and dossier health
- `Report`: pair the richer Markdown with a structured side rail for ranking, evidence density, and reading sequence

## Testing

Use TDD:

1. add failing tests for retrieval stage status semantics
2. add failing tests for richer report sections
3. implement minimal backend changes
4. adjust frontend presentation to consume the richer report and summary structure
5. run backend tests, frontend lint/build, and targeted verification

## Non-Goals

- no new agent stage
- no extra report-only LLM call
- no change to strict grounding rules
- no major route or shell redesign
