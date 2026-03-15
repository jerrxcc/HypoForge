export const STAGES = ['retrieval', 'review', 'critic', 'planner'] as const;
export const STAGE_LABELS: Record<string, string> = {
  retrieval: 'Retrieval',
  review: 'Review',
  critic: 'Critic',
  planner: 'Planner',
};

export const POLLING_INTERVAL = 2000; // 2 seconds
export const MAX_POLLING_ATTEMPTS = 300; // 10 minutes max

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, '') ??
  'http://127.0.0.1:8000';
