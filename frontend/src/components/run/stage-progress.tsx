'use client';

import { CheckCircle2, Circle, XCircle, AlertTriangle, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { STAGES } from '@/lib/constants';
import type { RunStatus, StageSummary, StageName, StageStatus } from '@/types';

/** Maps a RunStatus to the stage that is currently active. */
const STATUS_TO_ACTIVE_STAGE: Partial<Record<RunStatus, StageName>> = {
  retrieving: 'retrieval',
  reviewing: 'review',
  criticizing: 'critic',
  planning: 'planner',
};

type VisualState = 'completed' | 'active' | 'pending' | 'failed' | 'degraded' | 'reflecting';

function deriveVisualState(
  stageId: StageName,
  runStatus: RunStatus,
  stageSummaries: readonly StageSummary[],
): VisualState {
  const summary = stageSummaries.find((s) => s.stage_name === stageId);

  if (summary) {
    const map: Record<StageStatus, VisualState> = {
      completed: 'completed',
      degraded: 'degraded',
      failed: 'failed',
      started: 'active',
    };
    return map[summary.status];
  }

  // No summary for this stage — check if it's the active one
  const activeStage = STATUS_TO_ACTIVE_STAGE[runStatus];
  if (activeStage === stageId) {
    return 'active';
  }

  // If reflecting, find the last active stage (latest summary that is 'started' or check run status context)
  if (runStatus === 'reflecting') {
    // The reflecting stage is the one most recently started or the one after the last completed
    const completedIndices = stageSummaries
      .filter((s) => s.status === 'completed' || s.status === 'degraded')
      .map((s) => STAGES.findIndex((st) => st.id === s.stage_name));
    const maxCompleted = completedIndices.length > 0 ? Math.max(...completedIndices) : -1;
    const stageIndex = STAGES.findIndex((st) => st.id === stageId);

    if (stageIndex === maxCompleted + 1) {
      return 'reflecting';
    }
  }

  return 'pending';
}

function StageIcon({ state }: { readonly state: VisualState }) {
  switch (state) {
    case 'completed':
      return <CheckCircle2 className="size-6 text-[var(--color-success)]" />;
    case 'active':
      return <Circle className="size-6 animate-pulse text-primary" />;
    case 'reflecting':
      return <Loader2 className="size-6 animate-spin text-primary" />;
    case 'failed':
      return <XCircle className="size-6 text-destructive" />;
    case 'degraded':
      return <AlertTriangle className="size-6 text-[var(--color-warning)]" />;
    case 'pending':
    default:
      return <Circle className="size-6 text-muted-foreground/40" />;
  }
}

interface StageProgressProps {
  readonly status: RunStatus;
  readonly stageSummaries: StageSummary[];
}

export function StageProgress({ status, stageSummaries }: StageProgressProps) {
  return (
    <div className="flex items-start justify-between gap-0">
      {STAGES.map((stage, index) => {
        const visualState = deriveVisualState(stage.id, status, stageSummaries);
        const isLast = index === STAGES.length - 1;
        const lineCompleted =
          visualState === 'completed' || visualState === 'degraded';

        return (
          <div key={stage.id} className="flex flex-1 items-start">
            {/* Stage node */}
            <div className="flex flex-col items-center gap-1.5">
              <StageIcon state={visualState} />
              <span
                className={cn(
                  'text-xs font-medium',
                  visualState === 'pending'
                    ? 'text-muted-foreground/60'
                    : 'text-foreground',
                )}
              >
                {stage.label}
              </span>
              {visualState === 'reflecting' && (
                <span className="animate-pulse text-[10px] text-primary">
                  reflecting...
                </span>
              )}
            </div>

            {/* Connecting line */}
            {!isLast && (
              <div className="mt-3 flex flex-1 items-center px-2">
                <div
                  className={cn(
                    'h-px w-full transition-colors duration-300',
                    lineCompleted ? 'bg-[var(--color-success)]' : 'bg-border',
                  )}
                />
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
