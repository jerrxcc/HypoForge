# HypoForge Dashboard

This is the current Next.js dashboard for the HypoForge course-project prototype.
It is a demo UI for launching runs, monitoring stage progress, inspecting the
dossier, reading reports, and checking tool traces against the FastAPI backend.

## Local Use

Start the backend from the repository root:

```bash
rtk ./.venv/bin/uvicorn hypoforge.api.app:create_app --factory --reload
```

Start the dashboard:

```bash
rtk npm install
rtk npm run dev
```

Set the backend URL when it differs from the default:

```env
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

Open `http://127.0.0.1:3000/dashboard`.

## Demo Flow

- `/dashboard`: research input, golden topics, summary stats, and recent runs
- `/dashboard/new`: constrained new-run form
- `/dashboard/runs`: run history
- `/dashboard/runs/[id]`: stage progress and dossier inspection
- `/dashboard/runs/[id]/report`: Markdown briefing
- `/dashboard/runs/[id]/trace`: tool-call trace

## Checks

```bash
rtk npm run lint
rtk npm run build
```
