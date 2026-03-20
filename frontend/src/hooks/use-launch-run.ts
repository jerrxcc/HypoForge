import { useMutation, useQueryClient } from '@tanstack/react-query';
import { api, type LaunchRunPayload } from '@/lib/api-client';
import type { RunLaunch } from '@/types';

export function useLaunchRun() {
  const queryClient = useQueryClient();

  return useMutation<RunLaunch, Error, LaunchRunPayload>({
    mutationFn: (payload) => api.launchRun(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['runs'] });
    },
  });
}
