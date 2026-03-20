'use client';

import { useQuery } from '@tanstack/react-query';
import { getRun } from '@/lib/api-client';
import { POLLING_INTERVAL } from '@/lib/constants';

export function usePollRun(runId: string) {
  return useQuery({
    queryKey: ['run', runId],
    queryFn: () => getRun(runId),
    enabled: !!runId,
    refetchInterval: (query) => {
      const data = query.state.data;
      // Stop polling if run is done or failed
      if (data?.status === 'done' || data?.status === 'failed') {
        return false;
      }
      return POLLING_INTERVAL;
    },
  });
}
