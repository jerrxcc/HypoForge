'use client';

import { use, useEffect } from 'react';
import { notFound } from 'next/navigation';
import { usePollRun } from '@/hooks/use-poll-run';
import { useDossierStore } from '@/stores/dossier-store';
import { StageProgress } from '@/components/run/stage-progress';
import { DossierShell } from '@/components/dossier/dossier-shell';
import { RunStatusBadge } from '@/components/run/run-status-badge';
import { RerunPlannerButton } from '@/components/run/rerun-planner-button';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import Link from 'next/link';

export default function RunDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { data: run, isLoading, error } = usePollRun(id);
  const reset = useDossierStore((s) => s.reset);

  // Reset dossier store when entering a new run
  useEffect(() => {
    reset();
  }, [id, reset]);

  if (isLoading) return <RunDetailSkeleton />;
  if (error || !run) return notFound();

  return (
    <div className="flex flex-col gap-4">
      {/* Breadcrumb */}
      <nav aria-label="Breadcrumb" className="text-sm text-muted-foreground">
        <ol className="flex items-center gap-1.5">
          <li><Link href="/dashboard/runs" className="hover:text-foreground transition-colors">Runs</Link></li>
          <li aria-hidden="true">/</li>
          <li aria-current="page" className="truncate max-w-xs">{run.topic}</li>
        </ol>
      </nav>

      {/* Header */}
      <div className="flex flex-wrap items-center gap-3">
        <h1 className="text-xl font-semibold">{run.topic}</h1>
        <RunStatusBadge status={run.status} />
      </div>

      {/* Error banner */}
      {run.status === 'failed' && (
        <div className="rounded-lg border border-destructive/30 bg-destructive/10 p-4 text-sm text-destructive">
          Run failed. Check the trace for details.
        </div>
      )}

      {/* Actions */}
      <div className="flex gap-2">
        <Button variant="outline" size="sm" asChild>
          <Link href={`/dashboard/runs/${id}/report`}>Report</Link>
        </Button>
        <Button variant="outline" size="sm" asChild>
          <Link href={`/dashboard/runs/${id}/trace`}>Trace</Link>
        </Button>
        <RerunPlannerButton runId={id} status={run.status} />
      </div>

      {/* Stage progress */}
      <StageProgress status={run.status} stageSummaries={run.stage_summaries} />

      {/* Dossier */}
      <DossierShell run={run} />
    </div>
  );
}

function RunDetailSkeleton() {
  return (
    <div className="flex flex-col gap-4">
      <Skeleton className="h-4 w-48" />
      <Skeleton className="h-7 w-full max-w-sm" />
      <div className="flex gap-2">
        <Skeleton className="h-9 w-20" />
        <Skeleton className="h-9 w-20" />
        <Skeleton className="h-9 w-32" />
      </div>
      <Skeleton className="h-12 w-full" />
      <div className="hidden gap-4 md:flex">
        <Skeleton className="h-[400px] w-[320px]" />
        <Skeleton className="h-[400px] flex-1" />
      </div>
      <Skeleton className="h-[300px] w-full md:hidden" />
    </div>
  );
}
