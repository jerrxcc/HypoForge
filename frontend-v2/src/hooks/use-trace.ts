'use client';

import { useQuery } from '@tanstack/react-query';
import { getTrace } from '@/lib/api-client';
import type { RunStatus } from '@/types';

export function useTrace(runId: string, status?: RunStatus) {
  const isActive = status && !['done', 'failed'].includes(status);

  return useQuery({
    queryKey: ['trace', runId],
    queryFn: () => getTrace(runId),
    enabled: !!runId,
    refetchInterval: isActive ? 3000 : false,
    refetchIntervalInBackground: true,
  });
}
