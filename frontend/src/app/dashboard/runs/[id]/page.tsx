'use client';

import { use, useEffect, useState } from 'react';
import { notFound } from 'next/navigation';
import { usePollRun } from '@/hooks/use-poll-run';
import { useRunActivity } from '@/hooks/use-run-activity';
import { useDossierStore } from '@/stores/dossier-store';
import { StageProgress } from '@/components/run/stage-progress';
import { DossierShell } from '@/components/dossier/dossier-shell';
import { RunStatusBadge } from '@/components/run/run-status-badge';
import { RerunPlannerButton } from '@/components/run/rerun-planner-button';
import { ActivityDrawer } from '@/components/run/activity-drawer';
import { ActivityToggle } from '@/components/run/activity-toggle';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import Link from 'next/link';
import type { RunStatus } from '@/types';

const ACTIVE_STATUSES = new Set<RunStatus>(['queued', 'retrieving', 'reviewing', 'criticizing', 'planning', 'reflecting']);

export default function RunDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { data: run, isLoading, error } = usePollRun(id);
  const reset = useDossierStore((s) => s.reset);

  const isActive = run ? ACTIVE_STATUSES.has(run.status) : false;
  const activity = useRunActivity(id, isActive || !run);
  // User-controlled toggle; defaults to null meaning "auto" (open when active)
  const [userDrawerPref, setUserDrawerPref] = useState<boolean | null>(null);
  const drawerOpen = userDrawerPref ?? isActive;

  // Reset dossier store when entering a new run
  useEffect(() => {
    reset();
  }, [id, reset]);

  if (isLoading) return <RunDetailSkeleton />;

  // Network error with no cached data — show error panel, not 404
  if (error && !run) {
    return (
      <div className="flex flex-col items-center gap-4 py-16 text-center">
        <div role="alert" className="max-w-md rounded-lg border border-destructive/30 bg-destructive/10 p-6">
          <h2 className="text-lg font-semibold text-destructive">Failed to load run</h2>
          <p className="mt-2 text-sm text-muted-foreground">{error.message}</p>
          <Button
            variant="outline"
            size="sm"
            className="mt-4"
            onClick={() => window.location.reload()}
          >
            Retry
          </Button>
        </div>
      </div>
    );
  }

  if (!run) return notFound();

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
        <div role="alert" className="rounded-lg border border-destructive/30 bg-destructive/10 p-4 text-sm text-destructive">
          {run.error_message || 'Run failed. Check the trace for details.'}
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
        <ActivityToggle
          open={drawerOpen}
          onToggle={() => setUserDrawerPref((prev) => !(prev ?? isActive))}
          hasActivity={activity.activeToolName !== null}
        />
        <RerunPlannerButton runId={id} status={run.status} />
      </div>

      {/* Stage progress */}
      <div aria-live="polite">
        <StageProgress status={run.status} stageSummaries={run.stage_summaries} />
      </div>

      {/* Dossier */}
      <DossierShell run={run} />

      {/* Activity drawer */}
      <ActivityDrawer
        activity={activity}
        open={drawerOpen}
        onClose={() => setUserDrawerPref(false)}
        runCreatedAt={run.created_at}
        runUpdatedAt={run.updated_at}
        runActive={isActive}
      />
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
        <Skeleton className="h-[400px] md:w-[260px] lg:w-[320px] xl:w-[380px]" />
        <Skeleton className="h-[400px] flex-1" />
      </div>
      <Skeleton className="h-[300px] w-full md:hidden" />
    </div>
  );
}
