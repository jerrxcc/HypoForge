'use client';

import { useEffect, useRef } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { api } from '@/lib/api-client';
import type { RunResult, RunStatus } from '@/types';

const TERMINAL_STATUSES = new Set<RunStatus>(['done', 'failed']);
const MAX_CONSECUTIVE_FAILURES = 3;
const POLL_INTERVAL_MS = 2000;

export function usePollRun(runId: string | undefined) {
  const queryClient = useQueryClient();
  const failureCountRef = useRef(0);
  const toastIdRef = useRef<string | number | undefined>(undefined);

  const query = useQuery<RunResult>({
    queryKey: ['run', runId],
    queryFn: () => api.getRun(runId!),
    enabled: !!runId,
    refetchInterval: (query) => {
      const data = query.state.data;
      if (data && TERMINAL_STATUSES.has(data.status)) {
        return false;
      }
      return POLL_INTERVAL_MS;
    },
  });

  useEffect(() => {
    if (query.isError) {
      failureCountRef.current += 1;
      if (failureCountRef.current >= MAX_CONSECUTIVE_FAILURES && toastIdRef.current === undefined) {
        toastIdRef.current = toast.error('Connection lost', {
          description: 'Unable to reach the server. Retrying...',
          duration: Infinity,
        });
      }
    } else if (query.isSuccess) {
      if (failureCountRef.current > 0) {
        failureCountRef.current = 0;
        if (toastIdRef.current !== undefined) {
          toast.dismiss(toastIdRef.current);
          toastIdRef.current = undefined;
        }
      }
    }
  }, [query.isError, query.isSuccess]);

  // Invalidate runs list whenever this run reaches a terminal state
  useEffect(() => {
    const data = query.data;
    if (data && TERMINAL_STATUSES.has(data.status)) {
      queryClient.invalidateQueries({ queryKey: ['runs'] });
    }
  }, [query.data, queryClient]);

  return query;
}
