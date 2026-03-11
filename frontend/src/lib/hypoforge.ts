export type RunStatus =
  | 'queued'
  | 'retrieving'
  | 'reviewing'
  | 'criticizing'
  | 'planning'
  | 'done'
  | 'failed';

export type StageStatus = 'started' | 'completed' | 'degraded' | 'failed';
export type StageName = 'retrieval' | 'review' | 'critic' | 'planner';

export type RunConstraints = {
  year_from: number;
  year_to: number;
  open_access_only: boolean;
  max_selected_papers: number;
  novelty_weight: number;
  feasibility_weight: number;
  lab_mode: 'wet' | 'dry' | 'either';
};

export type StageSummary = {
  stage_name: StageName;
  status: StageStatus;
  summary: Record<string, unknown>;
  error_message: string | null;
  started_at: string | null;
  completed_at: string | null;
};

export type RunSummary = {
  run_id: string;
  topic: string;
  status: RunStatus;
  created_at: string;
  updated_at: string;
  selected_paper_count: number;
  evidence_card_count: number;
  conflict_cluster_count: number;
  hypothesis_count: number;
  error_message: string | null;
};

export type RunLaunch = {
  run_id: string;
  topic: string;
  status: RunStatus;
  trace_path: string | null;
};

export type PaperDetail = {
  paper_id: string;
  title: string;
  abstract: string | null;
  year: number | null;
  authors: string[];
  venue: string | null;
  source: string | null;
  provenance: string[];
};

export type EvidenceCard = {
  evidence_id: string;
  paper_id: string;
  title: string;
  claim_text: string;
  system_or_material: string;
  intervention: string;
  outcome: string;
  direction: string;
  confidence: number;
  evidence_kind: string;
  conditions: string[];
  limitations: string[];
};

export type ConflictCluster = {
  cluster_id: string;
  topic_axis: string;
  supporting_evidence_ids: string[];
  conflicting_evidence_ids: string[];
  conflict_type: string;
  critic_summary: string;
  confidence: number;
};

export type Hypothesis = {
  rank: number;
  title: string;
  hypothesis_statement: string;
  why_plausible: string;
  why_not_obvious: string;
  supporting_evidence_ids: string[];
  counterevidence_ids: string[];
  prediction: string;
  limitations: string[];
  uncertainty_notes: string[];
  risks: string[];
  novelty_score: number;
  feasibility_score: number;
  overall_score: number;
};

export type RunResult = {
  run_id: string;
  topic: string;
  status: RunStatus;
  selected_papers: PaperDetail[];
  evidence_cards: EvidenceCard[];
  conflict_clusters: ConflictCluster[];
  hypotheses: Hypothesis[];
  report_markdown: string | null;
  trace_url: string | null;
  stage_summaries: StageSummary[];
};

export type ToolTrace = {
  id: string;
  agent_name: string;
  tool_name: string;
  args: Record<string, unknown>;
  result_summary: Record<string, unknown>;
  latency_ms: number;
  model_name: string;
  input_tokens: number | null;
  output_tokens: number | null;
  request_id: string | null;
  success: boolean;
  error_message: string | null;
};

export const defaultConstraints: RunConstraints = {
  year_from: 2018,
  year_to: 2026,
  open_access_only: false,
  max_selected_papers: 36,
  novelty_weight: 0.5,
  feasibility_weight: 0.5,
  lab_mode: 'either'
};

export const goldenTopics = [
  'solid-state battery electrolyte',
  'CO2 reduction catalyst selectivity',
  'graph neural network drug-target interaction',
  'perovskite solar cell stability additives',
  'protein binder design with diffusion models'
];

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, '') ??
  'http://127.0.0.1:8000';

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers ?? {})
    },
    cache: 'no-store'
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `request failed: ${response.status}`);
  }
  return (await response.json()) as T;
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
    cache: 'no-store'
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `request failed: ${response.status}`);
  }
  return response.text();
}

export async function createRun(payload: {
  topic: string;
  constraints: RunConstraints;
}): Promise<RunResult> {
  return request<RunResult>('/v1/runs', {
    method: 'POST',
    body: JSON.stringify(payload)
  });
}

export async function launchRun(payload: {
  topic: string;
  constraints: RunConstraints;
}): Promise<RunLaunch> {
  return request<RunLaunch>('/v1/runs/launch', {
    method: 'POST',
    body: JSON.stringify(payload)
  });
}

export async function rerunPlanner(runId: string): Promise<RunResult> {
  return request<RunResult>(`/v1/runs/${runId}/planner/rerun`, {
    method: 'POST'
  });
}
