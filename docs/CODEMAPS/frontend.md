<!-- Generated: 2026-04-07 | Files scanned: 84 | Token estimate: ~850 -->

# Frontend Codemap

## Tech Stack

Next.js 16 + React 19 + TypeScript + Tailwind CSS v4 + Radix UI + TanStack Query + Zustand

## Page Tree

```
/ -> redirect -> /dashboard
/dashboard                    -> DashboardPage (research input, stats, recent runs, golden topics)
/dashboard/new?topic=         -> NewRunPage (form + constraints + launch)
/dashboard/runs               -> RunsPage (list all runs)
/dashboard/runs/[id]          -> RunDetailPage (stage progress + dossier master-detail + activity drawer)
/dashboard/runs/[id]/report   -> ReportPage (markdown render + download)
/dashboard/runs/[id]/trace    -> TracePage (tool call trace list + detail)
```

Not-found pages: `app/not-found.tsx` (global 404), `app/dashboard/runs/[id]/not-found.tsx` (run 404).

## Data Flow

```
api-client.ts (fetch wrapper + SSE URL builder)
  ^
hooks/ (TanStack Query + SSE)
  +-- useRuns()          -> GET /v1/runs
  +-- usePollRun(id)     -> GET /v1/runs/{id} (polls 2s until terminal)
  +-- useLaunchRun()     -> POST /v1/runs/launch (mutation)
  +-- useRerunPlanner()  -> POST /v1/runs/{id}/planner/rerun
  +-- useReport(id)      -> GET /v1/runs/{id}/report.md
  +-- useTrace(id)       -> GET /v1/runs/{id}/trace (polls 3s when active)
  +-- useRunActivity(id) -> SSE /v1/runs/{id}/events (real-time stage/tool events)
  +-- useMediaQuery(q)   -> CSS media query subscription
  ^
components/ (consume hooks)
```

## State Management

- **Server state**: TanStack Query (staleTime: 30s, retry: 1)
- **SSE state**: `useRunActivity` hook with `useReducer` (traces, activeAgent, metrics, connected)
- **UI state**: Zustand `dossierStore` -- selectedType, selectedId, searchQuery, expandedGroups
- **Form state**: react-hook-form + zod validation

## Component Hierarchy

```
RootLayout (theme-provider, query-provider, tooltip-provider, sonner)
  +-- DashboardLayout (top-nav + mobile-nav)
        +-- DashboardPage
        |     +-- ResearchInput -> ConstraintDrawer -> ConstraintFields
        |     +-- StatsBar
        |     +-- RecentRunsStrip
        |     +-- GoldenTopics
        +-- NewRunPage -> ConstraintFields
        +-- RunsPage -> RunCard -> RunStatusBadge
        +-- RunDetailPage
        |     +-- StageProgress
        |     +-- RerunPlannerButton
        |     +-- ActivityToggle + ActivityDrawer (SSE real-time feed)
        |     +-- DossierShell
        |           +-- MasterPanel -> SearchFilter + ItemGroup + {Paper,Evidence,Conflict,Hypothesis}Row
        |           +-- DetailPanel -> {Paper,Evidence,Conflict,Hypothesis}Detail + EvidenceLink + PaperLink
        +-- ReportPage -> MarkdownRenderer + DownloadButton
        +-- TracePage -> TraceShell -> TraceList + TraceDetail
```

## Providers (components/providers/)

- `QueryProvider` -- TanStack QueryClient with defaults
- `ThemeProvider` -- next-themes wrapper (system/light/dark)

## UI Primitives (components/ui/, shadcn/Radix)

accordion, badge, button, card, collapsible, dialog, dropdown-menu, input, progress, scroll-area, select, separator, skeleton, slider, sonner, switch, tabs, tooltip

## Key External Libraries

| Library | Purpose |
|---------|---------|
| @tanstack/react-query | Server state, polling |
| zustand | Client UI state |
| react-hook-form + zod | Form validation |
| react-markdown | Report rendering |
| lucide-react | Icons |
| next-themes | Dark/light mode |
| sonner | Toast notifications |
| clsx + tailwind-merge | Class merging (cn utility) |
