'use client';

import { useQuery } from '@tanstack/react-query';
import { getRun } from '@/lib/api-client';

export function useRun(runId: string) {
  return useQuery({
    queryKey: ['run', runId],
    queryFn: () => getRun(runId),
    enabled: !!runId,
  });
}
