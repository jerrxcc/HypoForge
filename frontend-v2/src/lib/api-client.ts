import { API_BASE_URL } from './constants';
import type { RunSummary, RunResult, ToolTrace } from '@/types';

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers ?? {}),
    },
    cache: 'no-store',
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed: ${response.status}`);
  }

  return response.json() as T;
}

export async function listRuns(): Promise<RunSummary[]> {
  return request<RunSummary[]>('/v1/runs');
}

export async function getRun(runId: string): Promise<RunResult> {
  return request<RunResult>(`/v1/runs/${runId}`);
}

export async function getTrace(runId: string): Promise<ToolTrace[]> {
  return request<ToolTrace[]>(`/v1/runs/${runId}/trace`);
}

export async function getReport(runId: string): Promise<string> {
  const response = await fetch(`${API_BASE_URL}/v1/runs/${runId}/report.md`, {
    cache: 'no-store',
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed: ${response.status}`);
  }

  return response.text();
}

export async function createRun(payload: { topic: string; constraints: Record<string, unknown> }) {
  return request<{
    run_id: string;
    topic: string;
    status: string;
    selected_papers: unknown[];
    evidence_cards: unknown[];
    conflict_clusters: unknown[];
    hypotheses: unknown[];
    report_markdown: string | null;
    trace_url: string | null;
    stage_summaries: unknown[];
  }>('/v1/runs', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function launchRun(payload: { topic: string; constraints: Record<string, unknown> }) {
  return request<{
    run_id: string;
    topic: string;
    status: string;
    trace_path: string | null;
  }>('/v1/runs/launch', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function rerunPlanner(runId: string) {
  return request<{
    run_id: string;
    topic: string;
    status: string;
    selected_papers: unknown[];
    evidence_cards: unknown[];
    conflict_clusters: unknown[];
    hypotheses: unknown[];
    report_markdown: string | null;
    trace_url: string | null;
    stage_summaries: unknown[];
  }>(`/v1/runs/${runId}/planner/rerun`, {
    method: 'POST',
  });
}
