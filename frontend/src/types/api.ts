// API types - matches backend schemas

export type RunStatus =
  | 'queued'
  | 'retrieving'
  | 'reviewing'
  | 'criticizing'
  | 'planning'
  | 'reflecting'
  | 'done'
  | 'failed';

export type StageStatus = 'started' | 'completed' | 'degraded' | 'failed';
export type StageName = 'retrieval' | 'review' | 'critic' | 'planner';

export type Direction = 'positive' | 'negative' | 'mixed' | 'null' | 'unclear';
export type EvidenceKind =
  | 'review'
  | 'meta_analysis'
  | 'experiment'
  | 'simulation'
  | 'benchmark'
  | 'theory'
  | 'unknown';

export type ConflictType =
  | 'direct_conflict'
  | 'conditional_divergence'
  | 'weak_evidence_gap';

export interface RunConstraints {
  year_from: number;
  year_to: number;
  open_access_only: boolean;
  max_selected_papers: number;
  novelty_weight: number;
  feasibility_weight: number;
  lab_mode: 'wet' | 'dry' | 'either';
}

export interface StageSummary {
  stage_name: StageName;
  status: StageStatus;
  summary: Record<string, unknown>;
  error_message: string | null;
  started_at: string | null;
  completed_at: string | null;
}

export interface RunSummary {
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
}

export interface RunLaunch {
  run_id: string;
  topic: string;
  status: RunStatus;
  trace_path: string | null;
}

export interface PaperDetail {
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
}

export interface EvidenceCard {
  evidence_id: string;
  paper_id: string;
  title: string;
  claim_text: string;
  system_or_material: string;
  intervention: string;
  comparator: string;
  outcome: string;
  direction: Direction;
  evidence_kind: EvidenceKind;
  conditions: string[];
  limitations: string[];
  confidence: number;
  grounding_notes: string[];
}

export interface ConflictCluster {
  cluster_id: string;
  topic_axis: string;
  supporting_evidence_ids: string[];
  conflicting_evidence_ids: string[];
  conflict_type: ConflictType;
  likely_explanations: string[];
  missing_controls: string[];
  critic_summary: string;
  confidence: number;
}

export interface MinimalExperiment {
  system: string;
  design: string;
  control: string;
  readouts: string[];
  success_criteria: string;
  failure_interpretation: string;
}

export interface Hypothesis {
  rank: number;
  title: string;
  hypothesis_statement: string;
  why_plausible: string;
  why_not_obvious: string;
  supporting_evidence_ids: string[];
  counterevidence_ids: string[];
  prediction: string;
  minimal_experiment: MinimalExperiment;
  limitations: string[];
  uncertainty_notes: string[];
  risks: string[];
  novelty_score: number;
  feasibility_score: number;
  overall_score: number;
}

export interface RunResult {
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
}

export interface ToolTrace {
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
}

// Defaults
export const defaultConstraints: RunConstraints = {
  year_from: 2018,
  year_to: 2026,
  open_access_only: false,
  max_selected_papers: 36,
  novelty_weight: 0.5,
  feasibility_weight: 0.5,
  lab_mode: 'either',
};

export const goldenTopics = [
  'solid-state battery electrolyte',
  'CO2 reduction catalyst selectivity',
  'graph neural network drug-target interaction',
  'perovskite solar cell stability additives',
  'protein binder design with diffusion models',
];
