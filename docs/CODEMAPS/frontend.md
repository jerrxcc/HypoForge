<!-- Generated: 2026-03-22 | Files scanned: 80 | Token estimate: ~800 -->

# Frontend Codemap

## Tech Stack

Next.js 16 + React 19 + TypeScript + Tailwind CSS v4 + Radix UI + TanStack Query + Zustand

## Page Tree

```
/ → redirect → /dashboard
/dashboard                    → DashboardPage (research input, stats, recent runs, golden topics)
/dashboard/new?topic=         → NewRunPage (form + constraints + launch)
/dashboard/runs               → RunsPage (list all runs)
/dashboard/runs/[id]          → RunDetailPage (stage progress + dossier master-detail)
/dashboard/runs/[id]/report   → ReportPage (markdown render + download)
/dashboard/runs/[id]/trace    → TracePage (tool call trace list + detail)
```

## Data Flow

```
api-client.ts (fetch wrapper)
  ↑
hooks/ (TanStack Query)
  ├── useRuns()          → GET /v1/runs
  ├── usePollRun(id)     → GET /v1/runs/{id} (polls 2s until terminal)
  ├── useLaunchRun()     → POST /v1/runs/launch (mutation)
  ├── useRerunPlanner()  → POST /v1/runs/{id}/planner/rerun
  ├── useReport(id)      → GET /v1/runs/{id}/report.md
  └── useTrace(id)       → GET /v1/runs/{id}/trace (polls 3s when active)
  ↑
components/ (consume hooks)
```

## State Management

- **Server state**: TanStack Query (staleTime: 30s, retry: 1)
- **UI state**: Zustand `dossierStore` — selectedType, selectedId, searchQuery, expandedGroups
- **Form state**: react-hook-form + zod validation

## Component Hierarchy

```
RootLayout (theme-provider, query-provider, tooltip-provider, sonner)
  └── DashboardLayout (top-nav)
        ├── DashboardPage
        │     ├── ResearchInput → ConstraintDrawer → ConstraintFields
        │     ├── StatsBar
        │     ├── RecentRunsStrip
        │     └── GoldenTopics
        ├── NewRunPage → ConstraintFields
        ├── RunsPage → RunCard → RunStatusBadge
        ├── RunDetailPage
        │     ├── StageProgress
        │     ├── RerunPlannerButton
        │     └── DossierShell
        │           ├── MasterPanel → SearchFilter + ItemGroup + {Paper,Evidence,Conflict,Hypothesis}Row
        │           └── DetailPanel → {Paper,Evidence,Conflict,Hypothesis}Detail
        ├── ReportPage → MarkdownRenderer + DownloadButton
        └── TracePage → TraceShell → TraceList + TraceDetail
```

## UI Primitives (shadcn/Radix)

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
