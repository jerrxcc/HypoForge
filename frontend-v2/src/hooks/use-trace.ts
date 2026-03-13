'use client';

import { useQuery } from '@tanstack/react-query';
import { getTrace } from '@/lib/api-client';

export function useTrace(runId: string) {
  return useQuery({
    queryKey: ['trace', runId],
    queryFn: () => getTrace(runId),
    enabled: !!runId,
  });
}
