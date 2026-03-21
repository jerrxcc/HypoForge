'use client';

import { useMemo } from 'react';
import Link from 'next/link';
import { useRuns } from '@/hooks/use-runs';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { formatDate, truncate } from '@/lib/utils';
import type { RunStatus } from '@/types';

function statusVariant(status: RunStatus) {
  switch (status) {
    case 'done':
      return 'success' as const;
    case 'failed':
      return 'error' as const;
    case 'queued':
      return 'secondary' as const;
    default:
      return 'warning' as const;
  }
}

function RunCardSkeleton() {
  return (
    <Card className="min-w-[200px] shrink-0">
      <CardContent className="flex flex-col gap-2 py-3">
        <Skeleton className="h-4 w-32" />
        <Skeleton className="h-5 w-16" />
        <Skeleton className="h-3 w-20" />
      </CardContent>
    </Card>
  );
}

export function RecentRunsStrip() {
  const { data: runs, isLoading } = useRuns();

  const recentRuns = useMemo(() => {
    if (!runs) return [];
    return [...runs]
      .sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime())
      .slice(0, 5);
  }, [runs]);

  if (isLoading) {
    return (
      <div className="flex gap-3 overflow-x-auto pb-2">
        <RunCardSkeleton />
        <RunCardSkeleton />
        <RunCardSkeleton />
      </div>
    );
  }

  if (recentRuns.length === 0) return null;

  return (
    <div className="space-y-3">
      <h2 className="text-sm font-medium text-muted-foreground">Recent runs</h2>
      <div className="relative flex gap-3 overflow-x-auto pb-2 snap-x snap-mandatory [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none] [mask-image:linear-gradient(to_right,black_calc(100%-2rem),transparent)] hover:[mask-image:none] focus-within:[mask-image:none]">
        {recentRuns.map((run) => (
          <Link
            key={run.run_id}
            href={`/dashboard/runs/${run.run_id}`}
            className="block min-w-[200px] shrink-0 snap-start"
          >
            <Card className="transition-colors hover:border-primary/30 dark:hover:border-primary/40">
              <CardContent className="flex flex-col gap-2 py-3">
                <span className="text-sm font-medium">{truncate(run.topic, 30)}</span>
                <Badge variant={statusVariant(run.status)}>{run.status}</Badge>
                <span className="text-xs text-muted-foreground">
                  {formatDate(run.updated_at)}
                </span>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}
