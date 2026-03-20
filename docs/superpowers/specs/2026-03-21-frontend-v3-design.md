# HypoForge Frontend v3 — Design Spec

## Context

HypoForge is a multi-agent scientific hypothesis generator with a 4-stage pipeline (retrieval → review → critic → planner). The current frontend (v2) works but lacks personality and polish. This redesign rebuilds the frontend from scratch with Claude.ai's warm, humanistic design language — creating a distinctive, elegant research tool.

## Design Decisions

| Decision | Choice |
|----------|--------|
| Aesthetic | Claude.ai's design language — warm, humanistic, elegant |
| Layout | Top navigation bar, no sidebar |
| Core View | Master-Detail split (left: pipeline items, right: detail) |
| Color | Claude warm palette: terracotta #D97756, cream #FAF6F1, warm dark #2A2520 |
| Theme | Light + Dark, default follows OS `prefers-color-scheme` |
| Progress | Live streaming — results appear progressively via polling |
| New Run | Chat-style centered input with golden topic suggestions |
| Fonts | DM Sans (UI) + JetBrains Mono (code) |

## Tech Stack

- **Next.js 16** + **React 19** (App Router, RSC)
- **shadcn/ui** (Radix + Tailwind, themed to Claude palette)
- **Tailwind CSS v4** (CSS variables, `@theme` directive)
- **TanStack Query v5** (server state, polling)
- **Zustand** (client state: dossier selection, theme)
- **Motion** (Framer Motion — streaming animations, page transitions)
- **react-hook-form + Zod** (form validation)
- **next-themes** (dark/light mode with OS preference)
- **Lucide React** (icons)
- **react-markdown + rehype** (report rendering)

## Pages

### 1. Dashboard Home (`/dashboard`)

Chat-style centered input: "What do you want to research?" with a terracotta submit button. Below: golden topic chips (5 pre-set topics). Bottom: horizontal stats bar (total runs, papers, hypotheses). Below stats: recent runs strip (3-5 cards).

### 2. Runs List (`/dashboard/runs`)

Card grid of all runs. Each card shows: topic, status badge (colored), paper/evidence/hypothesis counts, relative timestamp. Search bar at top. Grid: 3 cols desktop, 2 tablet, 1 mobile. "+ New Run" button in header.

### 3. Run Detail (`/dashboard/runs/[id]`)

**Header**: Topic title, status badge, action buttons (report, trace, rerun planner).

**Stage Progress**: Horizontal 4-step indicator (Retrieval → Review → Critic → Planner) with check marks for completed stages, pulse animation for active stage.

**Dossier Shell (Master-Detail Split)**:
- **Master Panel** (left, 380px desktop / 300px tablet): Grouped item list — Hypotheses (3), Conflicts (N), Evidence (N), Papers (N). Each group is collapsible. Items are rows with title and key metadata. Search/filter bar at top.
- **Detail Panel** (right, fills remaining): Shows full detail of selected item. Content varies by type:
  - **Hypothesis**: title, statement, scores (novelty/feasibility/overall as badges), why plausible, why not obvious, supporting evidence IDs (clickable → cross-reference), counter evidence IDs, prediction, minimal experiment (system/design/control/readouts/success/failure), limitations, uncertainty notes, risks.
  - **Conflict**: topic axis, conflict type badge, supporting vs conflicting evidence (two columns), likely explanations, missing controls, critic summary.
  - **Evidence**: claim text, paper link (clickable → cross-reference), direction badge, evidence kind, PICO fields (system, intervention, comparator, outcome), conditions, limitations, confidence, grounding notes.
  - **Paper**: title, authors, year, venue, abstract, citation count, fields of study, DOI/URL links, provenance, source badges.

**Mobile**: Master and detail stack vertically. Selecting an item replaces the list with detail + back button.

**Cross-referencing**: Evidence IDs in hypothesis detail are clickable badges. Clicking one updates the Zustand dossier store, which causes the master panel to expand the Evidence group, scroll to the item, and show its detail. Same for paper_id links in evidence detail.

**Live Streaming**: `usePollRun` polls every 2s for active runs. As data arrives, new items animate in with Motion fade-in. Groups appear only when they have items. When the first hypothesis arrives, it's auto-selected.

### 4. Report View (`/dashboard/runs/[id]/report`)

Full-width markdown renderer with prose styling (warm palette). Download button for .md file. Breadcrumb back to run detail.

### 5. Trace View (`/dashboard/runs/[id]/trace`)

Split layout: left list of tool calls (agent name, tool name, success/error icon), right panel shows selected call detail (args JSON, result summary, latency, tokens). Auto-refreshes during active runs.

## Constraints & New Run Flow

The chat-style input on the dashboard home is the primary entry point. Below the topic input, a "Show advanced options" toggle reveals the **constraint drawer** containing:

| Field | Control | Default | Validation |
|-------|---------|---------|------------|
| Year range | Two number inputs (from/to) | 2018–2026 | from ≤ to |
| Open access only | Switch toggle | false | — |
| Max papers | Number input | 36 | > 0 |
| Novelty weight | Slider (0–1, step 0.05) | 0.5 | novelty + feasibility = 1.0 |
| Feasibility weight | Slider (linked inverse) | 0.5 | auto-adjusts with novelty |
| Lab mode | Select dropdown | "either" | wet / dry / either |

The novelty and feasibility sliders are linked — moving one adjusts the other to maintain sum = 1.0. Zod schema validates all constraints client-side before submission.

On submit: `POST /v1/runs/launch` with `{ topic, constraints }` → returns `RunLaunchResponse` (extends `RunState`: `run_id`, `topic`, `constraints`, `status`, `error_message`, `selected_paper_ids`, `evidence_ids`, `conflict_cluster_ids`, `hypothesis_ids`, `final_report_md`, `trace_path`). Frontend only uses `run_id` from this response, then navigates to `/dashboard/runs/{run_id}` where polling begins.

The `RunLaunch` type in `types/api.ts` must be updated to match the full backend `RunState` shape, or we use only the `run_id` field and type the response minimally as `{ run_id: string }`.

## Error States & Edge Cases

### Run Failures
- **`failed` status**: Show error banner at top of run detail page with `error_message`. Stage progress shows the failed stage in red. Master panel shows whatever data was collected before failure. Detail panel shows an error empty state if no items exist.
- **`degraded` stage**: Stage progress shows a warning icon (amber) instead of a green check. Tooltip shows "Stage completed with partial results". Data is still shown normally.

### Reflecting Status
- **`reflecting` status**: The stage progress shows the current stage with a "reflecting" sub-indicator (pulsing icon or label). This is a transient state between stages. The UI treats it like an active stage — polling continues, data may update.

### Network & API Errors
- **Polling failure**: If a poll request fails, retry on next interval. After 3 consecutive failures, show a "Connection lost" toast with a manual retry button. Do not stop polling.
- **404 on run detail**: Show a not-found page with a link back to the runs list.
- **409 on rerun planner**: Show a toast: "Cannot rerun — run is still in progress."

### Rerun Planner UX
The "Rerun Planner" button is only enabled when `status === 'done'`. Clicking it:
1. Shows a confirmation dialog ("This will regenerate hypotheses using the existing evidence and conflicts.")
2. On confirm: button shows a spinner, disabled. Calls `POST /v1/runs/{id}/planner/rerun` (synchronous — blocks until complete).
3. On success: `RunResult` response replaces the cached query data. Hypotheses update in place.
4. On error: toast with error message, button re-enables.

### Loading & Empty States
- **Run detail (loading)**: Skeleton placeholders for stage progress, master panel (3 skeleton rows per group), and detail panel (skeleton text blocks).
- **Master panel (no data yet)**: Show skeleton rows with pulse animation. Groups appear as data arrives.
- **Detail panel (nothing selected)**: Center text: "Select an item from the left panel to view details."
- **Runs list (empty)**: Illustration + "No runs yet. Start your first research above."
- **Report not ready**: "Report will be available when the run completes."

### Search/Filter in Master Panel
Client-side filtering. Searches across: item title/topic, claim text (evidence), hypothesis statement. Case-insensitive substring match. Results update instantly as the user types. Filtered items show within their groups — empty groups are hidden during search.

## Theming System

### CSS Variables (globals.css)

Light mode: cream (#FAF6F1) background, warm dark (#2A2520) text, white (#FFFFFF) cards, warm gray (#E0D8CF) borders. Terracotta (#D97756) primary accent.

Dark mode: warm dark (#2A2520) background, cream text, warm brown (#372F2A) cards, dark gray (#50483E) borders. Same terracotta primary.

All colors mapped to shadcn/ui semantic variables (--background, --foreground, --primary, --card, --muted, --border, etc.).

### Dark Mode

`next-themes` with `attribute="class"` and `defaultTheme="system"`. Toggle in top nav header (sun/moon icon).

## Component Architecture

### Dossier Store (Zustand)

```
selectedType: 'hypothesis' | 'conflict' | 'evidence' | 'paper' | null
selectedId: string | null
searchQuery: string
expandedGroups: Record<string, boolean>
```

Actions: `select(type, id)`, `clearSelection()`, `setSearchQuery(q)`, `toggleGroup(group)`, `reset()`.

### Data Flow

1. User enters topic → `useLaunchRun` mutation → POST `/v1/runs/launch` → 202 with run_id
2. Navigate to `/dashboard/runs/{run_id}`
3. `usePollRun(runId)` polls GET `/v1/runs/{id}` every 2s
4. RunResult progressively fills: papers → evidence → conflicts → hypotheses
5. Master panel renders available items with entrance animations
6. At status=done, polling stops, dossier is complete

### API Client

Typed `api` object with methods: `listRuns`, `getRun`, `getTrace`, `getReport`, `createRun`, `launchRun`, `rerunPlanner`, `healthz`.

### Polling Strategy

- Interval: 2 seconds while run status is active (not `done` or `failed`)
- On error: retry on next interval, track consecutive failures
- After 3 consecutive failures: show "Connection lost" toast, continue polling silently
- On recovery: dismiss toast automatically
- No exponential backoff — runs are short-lived (1-3 minutes)

### ToolTrace Type

The backend `GET /v1/runs/{id}/trace` returns `list[dict]`. The frontend `ToolTrace` interface matches the shape produced by `coordinator.get_trace()`. If the backend shape ever changes, the frontend type must be updated to match. The type is treated as a best-effort contract.

## File Structure

```
frontend/src/
├── app/
│   ├── globals.css
│   ├── layout.tsx
│   ├── page.tsx
│   ├── not-found.tsx
│   └── dashboard/
│       ├── layout.tsx
│       ├── page.tsx
│       ├── new/
│       │   └── page.tsx
│       └── runs/
│           ├── page.tsx
│           └── [id]/
│               ├── page.tsx
│               ├── not-found.tsx
│               ├── report/page.tsx
│               └── trace/page.tsx
├── components/
│   ├── providers/   (query-provider, theme-provider)
│   ├── layout/      (top-nav, nav-link, logo, theme-toggle, mobile-nav)
│   ├── ui/          (shadcn/ui primitives: button, card, badge, input, dialog, etc.)
│   ├── dashboard/   (research-input, golden-topics, stats-bar, recent-runs-strip)
│   ├── run/         (run-card, run-status-badge, stage-progress, constraint-drawer, rerun-planner-button)
│   ├── dossier/     (dossier-shell, master-panel, detail-panel, item-group, evidence-link, search-filter)
│   │   ├── master-items/  (hypothesis-row, conflict-row, evidence-row, paper-row)
│   │   └── detail-views/  (hypothesis-detail, conflict-detail, evidence-detail, paper-detail)
│   ├── report/      (markdown-renderer, download-button)
│   └── trace/       (trace-list, trace-detail, trace-shell)
├── hooks/           (use-runs, use-run, use-poll-run, use-report, use-trace, use-launch-run, use-rerun-planner, use-media-query)
├── lib/             (api-client, constants, utils, schemas)
├── stores/          (dossier-store)
└── types/           (api, index)
```

~67 files total.

## Build Order

1. **Foundation**: package.json updates, globals.css (Claude palette), root layout (fonts, providers), utils, constants
2. **UI Primitives**: shadcn/ui components generation + theming customization
3. **Layout Shell**: top-nav, nav-link, logo, theme-toggle, mobile-nav, dashboard layout
4. **Data Layer**: types, api-client, all hooks, dossier store
5. **Dashboard Home**: research-input, golden-topics, stats-bar, recent-runs-strip, dashboard page
6. **Runs List**: run-card, run-status-badge, runs page
7. **Run Detail (Core)**: stage-progress, master panel components, detail view components, dossier-shell, evidence-link, run detail page
8. **Report & Trace**: markdown-renderer, trace components, report/trace pages
9. **New Run Page**: constraint-drawer, new run page
10. **Polish**: Motion animations, loading skeletons, empty states, dark mode QA, keyboard nav

## Verification

1. `npm install` succeeds
2. `npm run build` compiles without errors
3. `npm run lint` passes
4. Dark/light mode toggle works, OS preference respected
5. Dashboard home renders with input, golden topics, stats
6. Creating a run navigates to detail page with live progress
7. Master-detail split shows all data types correctly
8. Cross-referencing (clicking evidence ID in hypothesis) navigates correctly
9. Report page renders markdown with warm prose styling
10. Trace page shows tool calls with detail inspection
11. Responsive: mobile layout stacks master/detail, hamburger nav works
12. All API endpoints called correctly (check Network tab)
