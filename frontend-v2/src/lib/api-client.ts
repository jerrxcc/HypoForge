import { API_BASE_URL } from './constants';

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

export async function listRuns() {
  return request<{
    run_id: string;
    topic: string;
    status: string;
    created_at: string;
    updated_at: string;
    selected_paper_count: number;
    evidence_card_count: number;
    conflict_cluster_count: number;
    hypothesis_count: number;
    error_message: string | null;
  }[]>('/v1/runs');
}

export async function getRun(runId: string) {
  return request<{
    run_id: string;
    topic: string;
    status: string;
    selected_papers: Array<{
      paper_id: string;
      external_ids: Record<string, string | number | null>;
      doi: string | null;
      title: string;
      abstract: string | null;
      year: number | null;
      authors: string[];
      venue: string | null;
      citation_count: number | null;
      publication_type: string | null;
      fields_of_study: string[];
      topic_labels: string[];
      source: string | null;
      url: string | null;
      source_urls: Record<string, string>;
      provenance: string[];
    }>;
    evidence_cards: Array<{
      evidence_id: string;
      paper_id: string;
      title: string;
      claim_text: string;
      system_or_material: string;
      intervention: string;
      comparator: string;
      outcome: string;
      direction: string;
      evidence_kind: string;
      conditions: string[];
      limitations: string[];
      confidence: number;
      grounding_notes: string[];
    }>;
    conflict_clusters: Array<{
      cluster_id: string;
      topic_axis: string;
      supporting_evidence_ids: string[];
      conflicting_evidence_ids: string[];
      conflict_type: string;
      likely_explanations: string[];
      missing_controls: string[];
      critic_summary: string;
      confidence: number;
    }>;
    hypotheses: Array<{
      rank: number;
      title: string;
      hypothesis_statement: string;
      why_plausible: string;
      why_not_obvious: string;
      supporting_evidence_ids: string[];
      counterevidence_ids: string[];
      prediction: string;
      minimal_experiment: {
        system: string;
        design: string;
        control: string;
        readouts: string[];
        success_criteria: string;
        failure_interpretation: string;
      };
      limitations: string[];
      uncertainty_notes: string[];
      risks: string[];
      novelty_score: number;
      feasibility_score: number;
      overall_score: number;
    }>;
    report_markdown: string | null;
    trace_url: string | null;
    stage_summaries: Array<{
      stage_name: string;
      status: string;
      summary: Record<string, unknown>;
      error_message: string | null;
      started_at: string | null;
      completed_at: string | null;
    }>;
  }>(`/v1/runs/${runId}`);
}

export async function getTrace(runId: string) {
  return request<Array<{
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
  }>>(`/v1/runs/${runId}/trace`);
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
