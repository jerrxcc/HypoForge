import { useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api-client';
import type { RunResult } from '@/types';

export function useRerunPlanner(runId: string) {
  const queryClient = useQueryClient();

  return useMutation<RunResult, Error, void>({
    mutationFn: () => api.rerunPlanner(runId),
    onSuccess: (updatedRun) => {
      queryClient.setQueryData(['run', runId], updatedRun);
    },
  });
}
