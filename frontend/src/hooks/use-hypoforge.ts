'use client';

import { useEffect, useState } from 'react';

import {
  getReport,
  getRun,
  getTrace,
  listRuns,
  type RunResult,
  type RunSummary,
  type ToolTrace
} from '@/lib/hypoforge';

function usePolling<T>(
  loader: () => Promise<T>,
  intervalMs: number,
  enabled = true
) {
  const [data, setData] = useState<T | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!enabled) {
      return;
    }
    let cancelled = false;

    async function load() {
      try {
        const result = await loader();
        if (cancelled) {
          return;
        }
        setData(result);
        setError(null);
      } catch (caughtError) {
        if (cancelled) {
          return;
        }
        const message =
          caughtError instanceof Error ? caughtError.message : 'request failed';
        setError(message);
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    }

    void load();
    const handle = window.setInterval(() => {
      void load();
    }, intervalMs);

    return () => {
      cancelled = true;
      window.clearInterval(handle);
    };
  }, [enabled, intervalMs, loader]);

  return { data, isLoading, error };
}

export function useRuns() {
  return usePolling<RunSummary[]>(() => listRuns(), 10000);
}

export function useRun(runId: string) {
  return usePolling<RunResult>(() => getRun(runId), 3000, Boolean(runId));
}

export function useRunTrace(runId: string) {
  return usePolling<ToolTrace[]>(() => getTrace(runId), 3000, Boolean(runId));
}

export function useRunReport(runId: string) {
  return usePolling<string>(() => getReport(runId), 5000, Boolean(runId));
}
