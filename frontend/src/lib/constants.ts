/** Backend API base URL, injected via Next.js public env var. */
export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://127.0.0.1:8000';

/** Polling interval (ms) for in-progress runs. */
export const POLLING_INTERVAL_MS = 2000;

/** Pipeline stage definitions in execution order. */
export const STAGES = [
  { id: 'retrieval', label: 'Retrieval', description: 'Searching papers across OpenAlex & Semantic Scholar' },
  { id: 'review', label: 'Review', description: 'Extracting evidence cards from selected papers' },
  { id: 'critic', label: 'Critic', description: 'Identifying conflict clusters in evidence' },
  { id: 'planner', label: 'Planner', description: 'Generating hypotheses and final report' },
] as const;

export type StageId = (typeof STAGES)[number]['id'];

/** Curated golden topics for quick demo runs. */
export const GOLDEN_TOPICS = [
  'solid-state battery electrolyte interfaces',
  'CRISPR base editing off-target effects',
  'microbiome modulation of Alzheimer disease',
  'perovskite solar cell stability degradation',
  'mRNA vaccine adjuvant innate immune response',
] as const;

/** Default run constraints exposed in the new-run form. */
export const DEFAULT_CONSTRAINTS = {
  maxPapers: 36,
  minEvidenceCards: 10,
  minHypotheses: 3,
  maxHypotheses: 3,
  enableReflection: false,
} as const;
