'use client';

import { useQuery } from '@tanstack/react-query';
import { listRuns } from '@/lib/api-client';

export function useRuns() {
  return useQuery({
    queryKey: ['runs'],
    queryFn: listRuns,
  });
}
