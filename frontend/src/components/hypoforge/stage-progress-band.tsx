'use client';

import type { RunStatus, StageSummary } from '@/lib/hypoforge';
import {
  getActiveStageName,
  getStageDescription,
  getStageStateLabel,
  getStageSummaryEntries
} from '@/lib/hypoforge-display';
import { cn } from '@/lib/utils';

const STAGES = ['retrieval', 'review', 'critic', 'planner'] as const;

type StageName = (typeof STAGES)[number];

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
  const resolvedStage = currentStage ?? getActiveStageName(runStatus ?? 'queued');
  const currentIndex = STAGES.indexOf(resolvedStage);

  return (
    <div
      className={cn(
        'grid gap-3 rounded-[1.5rem] border bg-card/85 p-4 shadow-sm md:grid-cols-2 2xl:grid-cols-4',
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
              'rounded-[1.35rem] border px-4 py-4 transition-colors',
              state === 'completed' && 'border-primary/20 bg-primary/10 text-primary',
              state === 'started' &&
                'border-accent/45 bg-accent/20 text-foreground shadow-[0_0_0_1px_color-mix(in_oklab,var(--accent)_22%,transparent)]',
              state === 'degraded' && 'border-amber-300/50 bg-amber-100/70 text-amber-900 dark:bg-amber-950/40 dark:text-amber-100',
              state === 'failed' && 'border-destructive/35 bg-destructive/10 text-destructive',
              state === 'pending' && 'bg-background/70 text-muted-foreground'
            )}
          >
            <div className='flex items-center justify-between gap-2'>
              <p className='flex items-center gap-2 text-[11px] font-medium tracking-[0.18em] uppercase'>
                {state === 'started' ? (
                  <span className='relative flex size-2.5'>
                    <span className='absolute inline-flex h-full w-full animate-ping rounded-full bg-current opacity-35' />
                    <span className='relative inline-flex size-2.5 rounded-full bg-current' />
                  </span>
                ) : null}
                Stage {index + 1}
              </p>
              <span className='text-[10px] uppercase tracking-[0.18em]'>
                {state === 'started' ? 'Live now' : getStageStateLabel(state)}
              </span>
            </div>
            <p className='mt-2 font-serif text-lg capitalize'>{stage}</p>
            <p
              className={cn(
                'mt-2 text-sm leading-6',
                state === 'pending' ? 'text-muted-foreground' : 'text-current/80'
              )}
            >
              {getStageDescription(stage)}
            </p>
            {summary ? (
              <div className='mt-4 grid gap-2 sm:grid-cols-2 xl:grid-cols-1'>
                {getStageSummaryEntries(summary)
                  .slice(0, 2)
                  .map((entry) => (
                    <div
                      key={`${stage}-${entry.label}`}
                      className={cn(
                        'rounded-2xl border px-3 py-2',
                        state === 'pending'
                          ? 'border-border/60 bg-background/70'
                          : 'border-current/12 bg-white/55 dark:bg-black/10'
                      )}
                    >
                      <div className='text-[11px] uppercase tracking-[0.16em] opacity-70'>
                        {entry.label}
                      </div>
                      <div className='mt-1 text-sm font-medium leading-snug break-words'>
                        {entry.value}
                      </div>
                    </div>
                  ))}
              </div>
            ) : null}
          </div>
        );
      })}
    </div>
  );
}
