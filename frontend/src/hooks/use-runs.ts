import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api-client';
import type { RunSummary } from '@/types';

export function useRuns() {
  return useQuery<RunSummary[]>({
    queryKey: ['runs'],
    queryFn: () => api.listRuns(),
    staleTime: 30_000,
  });
}
