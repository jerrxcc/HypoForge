'use client';

import { useQuery } from '@tanstack/react-query';
import { getReport } from '@/lib/api-client';

export function useReport(runId: string) {
  return useQuery({
    queryKey: ['report', runId],
    queryFn: () => getReport(runId),
    enabled: !!runId,
  });
}
