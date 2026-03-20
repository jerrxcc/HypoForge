'use client';

import { use } from 'react';
import Link from 'next/link';
import { useTrace } from '@/hooks/use-trace';
import { usePollRun } from '@/hooks/use-poll-run';
import { TraceShell } from '@/components/trace/trace-shell';
import { Skeleton } from '@/components/ui/skeleton';
import type { RunStatus } from '@/types';

const ACTIVE_STATUSES = new Set<RunStatus>([
  'queued',
  'retrieving',
  'reviewing',
  'criticizing',
  'planning',
  'reflecting',
]);

export default function TracePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { data: run } = usePollRun(id);
  const isActive = run ? ACTIVE_STATUSES.has(run.status) : false;
  const { data: traces, isLoading } = useTrace(id, isActive);

  const topic = run?.topic ?? id;

  return (
    <div className="flex flex-col gap-4">
      {/* Breadcrumb */}
      <p className="text-sm text-muted-foreground">
        <Link href="/dashboard/runs" className="hover:text-foreground transition-colors">
          Runs
        </Link>
        {' / '}
        <Link href={`/dashboard/runs/${id}`} className="hover:text-foreground transition-colors">
          {topic}
        </Link>
        {' / '}
        Trace
      </p>

      {/* Header */}
      <h1 className="text-xl font-semibold">Tool Call Trace</h1>

      {/* Content */}
      {isLoading ? (
        <TraceSkeleton />
      ) : traces && traces.length > 0 ? (
        <TraceShell traces={traces} />
      ) : (
        <div className="flex items-center justify-center py-24 text-center">
          <p className="text-muted-foreground">No trace data yet.</p>
        </div>
      )}
    </div>
  );
}

function TraceSkeleton() {
  return (
    <div className="flex gap-4">
      <div className="w-80 shrink-0 flex flex-col gap-2">
        {Array.from({ length: 8 }, (_, i) => (
          <Skeleton key={i} className="h-10 w-full" />
        ))}
      </div>
      <div className="flex-1">
        <Skeleton className="h-[400px] w-full" />
      </div>
    </div>
  );
}
