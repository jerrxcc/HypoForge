import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api-client';
import type { ToolTrace } from '@/types';

/**
 * Fetches the tool call trace for a run.
 * Polls every 3 seconds while `active` is true (i.e. run is still in progress).
 */
export function useTrace(runId: string | undefined, active = false) {
  return useQuery<ToolTrace[]>({
    queryKey: ['trace', runId],
    queryFn: () => api.getTrace(runId!),
    enabled: !!runId,
    refetchInterval: active ? 3000 : false,
  });
}
