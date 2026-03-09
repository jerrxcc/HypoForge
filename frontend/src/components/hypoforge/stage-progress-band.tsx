'use client';

import type { RunStatus, StageSummary } from '@/lib/hypoforge';
import { cn } from '@/lib/utils';

const STAGES = ['retrieval', 'review', 'critic', 'planner'] as const;

type StageName = (typeof STAGES)[number];

function inferCurrentStage(runStatus?: RunStatus): StageName {
  switch (runStatus) {
    case 'reviewing':
      return 'review';
    case 'criticizing':
      return 'critic';
    case 'planning':
    case 'done':
    case 'failed':
      return 'planner';
    case 'queued':
    case 'retrieving':
    default:
      return 'retrieval';
  }
}

export function StageProgressBand({
  currentStage,
  runStatus,
  stageSummaries,
  className
}: {
  currentStage?: StageName;
  runStatus?: RunStatus;
  stageSummaries?: StageSummary[];
  className?: string;
}) {
  const resolvedStage = currentStage ?? inferCurrentStage(runStatus);
  const currentIndex = STAGES.indexOf(resolvedStage);

  return (
    <div
      className={cn(
        'grid gap-3 rounded-[1.5rem] border bg-card/85 p-4 shadow-sm md:grid-cols-4',
        className
      )}
    >
      {STAGES.map((stage, index) => {
        const summary = stageSummaries?.find((item) => item.stage_name === stage);
        const state =
          summary?.status ??
          (index < currentIndex ? 'completed' : index === currentIndex ? 'started' : 'pending');

        return (
          <div
            key={stage}
            className={cn(
              'rounded-[1.25rem] border px-4 py-3 transition-colors',
              state === 'completed' && 'border-primary/20 bg-primary/10 text-primary',
              state === 'started' && 'border-accent/40 bg-accent/20',
              state === 'degraded' && 'border-amber-300/50 bg-amber-100/70 text-amber-900 dark:bg-amber-950/40 dark:text-amber-100',
              state === 'failed' && 'border-destructive/35 bg-destructive/10 text-destructive',
              state === 'pending' && 'bg-background/70 text-muted-foreground'
            )}
          >
            <div className='flex items-center justify-between gap-2'>
              <p className='text-[11px] font-medium tracking-[0.18em] uppercase'>
                Stage {index + 1}
              </p>
              <span className='text-[10px] uppercase tracking-[0.18em]'>
                {state}
              </span>
            </div>
            <p className='font-serif mt-2 text-lg capitalize'>{stage}</p>
          </div>
        );
      })}
    </div>
  );
}
