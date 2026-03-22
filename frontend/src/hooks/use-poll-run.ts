'use client';

import { useEffect } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api-client';
import type { RunResult, RunStatus } from '@/types';

const TERMINAL_STATUSES = new Set<RunStatus>(['done', 'failed']);
const POLL_INTERVAL_MS = 2000;

export function usePollRun(runId: string | undefined) {
  const queryClient = useQueryClient();

  const query = useQuery<RunResult>({
    queryKey: ['run', runId],
    queryFn: () => api.getRun(runId!),
    enabled: !!runId,
    retry: 2,
    staleTime: (query) => {
      const data = query.state.data;
      return data && TERMINAL_STATUSES.has(data.status) ? Infinity : 0;
    },
    refetchInterval: (query) => {
      const data = query.state.data;
      if (data && TERMINAL_STATUSES.has(data.status)) {
        return false;
      }
      return POLL_INTERVAL_MS;
    },
  });

  // Invalidate runs list whenever this run reaches a terminal state
  useEffect(() => {
    const data = query.data;
    if (data && TERMINAL_STATUSES.has(data.status)) {
      queryClient.invalidateQueries({ queryKey: ['runs'] });
    }
  }, [query.data, queryClient]);

  return query;
}
