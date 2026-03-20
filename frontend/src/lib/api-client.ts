import type {
  RunSummary,
  RunLaunch,
  RunResult,
  RunConstraints,
  ToolTrace,
} from '@/types';
import { API_BASE_URL } from '@/lib/constants';

/** Typed error thrown for non-2xx responses from the API. */
export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

/** Generic fetch wrapper that parses JSON and throws ApiError on failure. */
async function request<T>(
  path: string,
  options?: RequestInit,
): Promise<T> {
  const url = `${API_BASE_URL}${path}`;
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  });

  if (!res.ok) {
    let message = `HTTP ${res.status} ${res.statusText}`;
    try {
      const body = await res.json();
      if (body?.detail) {
        message = typeof body.detail === 'string'
          ? body.detail
          : JSON.stringify(body.detail);
      }
    } catch {
      // ignore parse error — use default message
    }
    throw new ApiError(res.status, message);
  }

  return res.json() as Promise<T>;
}

/** Text variant of request for plain-text endpoints (e.g. report.md). */
async function requestText(path: string): Promise<string> {
  const url = `${API_BASE_URL}${path}`;
  const res = await fetch(url);

  if (!res.ok) {
    throw new ApiError(res.status, `HTTP ${res.status} ${res.statusText}`);
  }

  return res.text();
}

export interface LaunchRunPayload {
  topic: string;
  constraints?: Partial<RunConstraints>;
  fake?: boolean;
}

/** API client — all methods typed against backend schemas. */
export const api = {
  /** GET /healthz */
  healthz(): Promise<{ status: string }> {
    return request<{ status: string }>('/healthz');
  },

  /** GET /v1/runs */
  listRuns(): Promise<RunSummary[]> {
    return request<RunSummary[]>('/v1/runs');
  },

  /** GET /v1/runs/:id */
  getRun(runId: string): Promise<RunResult> {
    return request<RunResult>(`/v1/runs/${runId}`);
  },

  /** GET /v1/runs/:id/trace */
  getTrace(runId: string): Promise<ToolTrace[]> {
    return request<ToolTrace[]>(`/v1/runs/${runId}/trace`);
  },

  /** GET /v1/runs/:id/report.md — returns raw Markdown text */
  getReport(runId: string): Promise<string> {
    return requestText(`/v1/runs/${runId}/report.md`);
  },

  /** POST /v1/runs/launch — async, returns 202 with run metadata */
  launchRun(payload: LaunchRunPayload): Promise<RunLaunch> {
    return request<RunLaunch>('/v1/runs/launch', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  /** POST /v1/runs — synchronous, returns full result (long-running) */
  createRun(payload: LaunchRunPayload): Promise<RunResult> {
    return request<RunResult>('/v1/runs', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  /** POST /v1/runs/:id/planner/rerun */
  rerunPlanner(runId: string): Promise<RunResult> {
    return request<RunResult>(`/v1/runs/${runId}/planner/rerun`, {
      method: 'POST',
    });
  },
};
