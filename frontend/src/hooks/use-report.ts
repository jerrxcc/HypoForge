import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api-client';
import type { RunStatus } from '@/types';

const TERMINAL_STATUSES = new Set<RunStatus>(['done', 'failed']);
const REPORT_POLL_INTERVAL_MS = 3000;

export function useReport(runId: string | undefined, status: RunStatus | undefined) {
  const isTerminal = status ? TERMINAL_STATUSES.has(status) : false;

  return useQuery<string>({
    queryKey: ['report', runId, status ?? 'unknown'],
    queryFn: () => api.getReport(runId!),
    enabled: !!runId,
    staleTime: isTerminal ? Infinity : 0,
    refetchInterval: isTerminal ? false : REPORT_POLL_INTERVAL_MS,
  });
}
