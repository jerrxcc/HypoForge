import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api-client';

export function useReport(runId: string | undefined) {
  return useQuery<string>({
    queryKey: ['report', runId],
    queryFn: () => api.getReport(runId!),
    enabled: !!runId,
    staleTime: Infinity,
  });
}
