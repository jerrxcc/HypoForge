import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api-client';
import type { RunResult } from '@/types';

export function useRun(runId: string | undefined) {
  return useQuery<RunResult>({
    queryKey: ['run', runId],
    queryFn: () => api.getRun(runId!),
    enabled: !!runId,
  });
}
