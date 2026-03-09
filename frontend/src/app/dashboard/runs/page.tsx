'use client';

import Link from 'next/link';
import { useMemo, useState } from 'react';

import { RunsTable } from '@/components/hypoforge/runs-table';
import { RunStatusBadge } from '@/components/hypoforge/run-status-badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { useRuns } from '@/hooks/use-hypoforge';

function RunsPageSkeleton() {
  return (
    <div className='space-y-6'>
      <div className='grid gap-4 xl:grid-cols-[minmax(0,1.15fr)_minmax(0,0.85fr)]'>
        <Skeleton className='h-44 rounded-[1.7rem]' />
        <div className='grid gap-3'>
          <Skeleton className='h-36 rounded-[1.45rem]' />
          <Skeleton className='h-36 rounded-[1.45rem]' />
        </div>
      </div>
      <div className='grid gap-4 xl:grid-cols-[minmax(0,1.2fr)_minmax(0,0.8fr)]'>
        <Skeleton className='h-44 rounded-[1.7rem]' />
        <div className='grid gap-4 sm:grid-cols-2'>
          <Skeleton className='h-32 rounded-[1.5rem]' />
          <Skeleton className='h-32 rounded-[1.5rem]' />
        </div>
      </div>
      <div className='grid gap-4 md:grid-cols-2 xl:grid-cols-4'>
        {Array.from({ length: 4 }).map((_, index) => (
          <Skeleton key={index} className='h-32 rounded-[1.5rem]' />
        ))}
      </div>
      <div className='flex gap-2'>
        {Array.from({ length: 4 }).map((_, index) => (
          <Skeleton key={index} className='h-10 w-28 rounded-full' />
        ))}
      </div>
      <div className='grid gap-4 xl:hidden'>
        {Array.from({ length: 3 }).map((_, index) => (
          <Skeleton key={index} className='h-72 rounded-[1.65rem]' />
        ))}
      </div>
    </div>
  );
}

export default function RunsPage() {
  const { data: runs, error, isLoading } = useRuns();
  const [filter, setFilter] = useState<'all' | 'active' | 'done' | 'failed'>('all');
  const runList = runs ?? [];
  const activeRuns = runList.filter((run) => !['done', 'failed'].includes(run.status));
  const completedRuns = runList.filter((run) => run.status === 'done');
  const failedRuns = runList.filter((run) => run.status === 'failed');
  const completionRate = runList.length
    ? Math.round((completedRuns.length / runList.length) * 100)
    : 0;
  const failureRate = runList.length
    ? Math.round((failedRuns.length / runList.length) * 100)
    : 0;
  const displayedRuns = useMemo(() => {
    switch (filter) {
      case 'active':
        return activeRuns;
      case 'done':
        return completedRuns;
      case 'failed':
        return failedRuns;
      default:
        return runList;
    }
  }, [activeRuns, completedRuns, failedRuns, filter, runList]);

  return (
    <div className='workspace-shell flex w-full flex-1 flex-col gap-6 p-4 md:p-8'>
      <Card className='border-border/70 bg-card/95 shadow-sm'>
        <CardHeader>
          <div className='text-muted-foreground text-xs uppercase tracking-[0.24em]'>
            Run archive
          </div>
          <CardTitle className='font-serif text-4xl tracking-tight'>
            Audit recent runs without losing the dossier.
          </CardTitle>
          <CardDescription className='text-base leading-relaxed'>
            Each row keeps the status, volume, and path into the full evidence trail.
          </CardDescription>
        </CardHeader>
        <CardContent className='space-y-6'>
          {activeRuns.length ? (
            <div className='grid gap-4 xl:grid-cols-[minmax(0,1.15fr)_minmax(0,0.85fr)]'>
              <div className='rounded-[1.7rem] border border-primary/20 bg-primary/8 px-5 py-5'>
                <div className='text-[11px] uppercase tracking-[0.18em] text-muted-foreground'>
                  Live docket
                </div>
                <div className='mt-3 font-serif text-3xl'>
                  {activeRuns.length} dossier{activeRuns.length > 1 ? 's' : ''} still moving.
                </div>
                <p className='text-muted-foreground mt-3 max-w-2xl text-sm leading-7'>
                  Use the active docket to jump straight into an in-flight run instead of
                  scanning the full archive.
                </p>
              </div>
              <div className='grid gap-3'>
                {activeRuns.slice(0, 2).map((run) => (
                  <Link
                    key={run.run_id}
                    href={`/dashboard/runs/${run.run_id}`}
                    className='rounded-[1.45rem] border border-border/70 bg-background/75 px-4 py-4 transition-transform hover:-translate-y-0.5'
                  >
                    <div className='flex items-start justify-between gap-3'>
                      <div className='min-w-0'>
                        <div className='line-clamp-2 font-medium leading-6'>{run.topic}</div>
                        <div className='text-muted-foreground mt-2 break-all font-mono text-[12px]'>
                          {run.run_id}
                        </div>
                      </div>
                      <RunStatusBadge status={run.status} />
                    </div>
                    <div className='mt-4 grid grid-cols-3 gap-2'>
                      {[
                        ['Papers', run.selected_paper_count],
                        ['Evidence', run.evidence_card_count],
                        ['Hypotheses', run.hypothesis_count]
                      ].map(([label, value]) => (
                        <div
                          key={String(label)}
                          className='rounded-2xl border border-border/70 bg-card px-3 py-2.5'
                        >
                          <div className='text-muted-foreground text-[10px] uppercase tracking-[0.14em]'>
                            {label}
                          </div>
                          <div className='mt-1 font-mono text-sm'>{value}</div>
                        </div>
                      ))}
                    </div>
                  </Link>
                ))}
              </div>
            </div>
          ) : null}

          <div className='grid gap-4 xl:grid-cols-[minmax(0,1.2fr)_minmax(0,0.8fr)]'>
            <div className='rounded-[1.7rem] border border-border/70 bg-background/75 px-5 py-5'>
              <div className='text-muted-foreground text-[11px] uppercase tracking-[0.18em]'>
                Archive posture
              </div>
              <div className='mt-3 font-serif text-3xl'>Research archive stays audit-ready.</div>
              <p className='text-muted-foreground mt-3 max-w-2xl text-sm leading-7'>
                Use this archive as a working ledger: check completion rate, spot stalled runs,
                and drill straight into trace or report before trusting a result downstream.
              </p>
            </div>
            <div className='grid gap-4 sm:grid-cols-2'>
              <div className='rounded-[1.5rem] border border-border/70 bg-background/75 px-5 py-4'>
                <div className='text-muted-foreground text-[11px] uppercase tracking-[0.18em]'>
                  Completion rate
                </div>
                <div className='mt-3 font-serif text-3xl'>{completionRate}%</div>
                <div className='text-muted-foreground mt-2 text-sm leading-6'>
                  Share of archived runs that reached a finished report.
                </div>
              </div>
              <div className='rounded-[1.5rem] border border-border/70 bg-background/75 px-5 py-4'>
                <div className='text-muted-foreground text-[11px] uppercase tracking-[0.18em]'>
                  Failure rate
                </div>
                <div className='mt-3 font-serif text-3xl'>{failureRate}%</div>
                <div className='text-muted-foreground mt-2 text-sm leading-6'>
                  Runs that still need rework or planner rerun attention.
                </div>
              </div>
            </div>
          </div>

          <div className='grid gap-4 md:grid-cols-2 xl:grid-cols-4'>
            {[
              ['Total runs', runList.length, 'All dossiers currently stored in the archive.'],
              ['Active now', activeRuns.length, 'Queued or in-flight runs that still need attention.'],
              ['Completed', completedRuns.length, 'Runs with hypotheses and a finished report.'],
              ['Failed', failedRuns.length, 'Runs that stopped before the planner completed.']
            ].map(([label, value, detail]) => (
              <div
                key={String(label)}
                className='rounded-[1.5rem] border border-border/70 bg-background/75 px-5 py-4'
              >
                <div className='text-muted-foreground text-[11px] uppercase tracking-[0.18em]'>
                  {label}
                </div>
                <div className='mt-3 font-serif text-3xl'>{value}</div>
                <div className='text-muted-foreground mt-2 text-sm leading-6'>{detail}</div>
              </div>
            ))}
          </div>

          {isLoading && !runs ? <RunsPageSkeleton /> : null}
          {error ? <div className='text-sm text-destructive'>{error}</div> : null}
          {runs ? (
            <div className='space-y-4'>
              <div className='flex flex-wrap gap-2'>
                {[
                  ['all', `All ${runList.length}`],
                  ['active', `Active ${activeRuns.length}`],
                  ['done', `Completed ${completedRuns.length}`],
                  ['failed', `Failed ${failedRuns.length}`]
                ].map(([value, label]) => (
                  <Button
                    key={value}
                    type='button'
                    variant={filter === value ? 'default' : 'outline'}
                    className='rounded-full'
                    onClick={() =>
                      setFilter(value as 'all' | 'active' | 'done' | 'failed')
                    }
                  >
                    {label}
                  </Button>
                ))}
              </div>
              <RunsTable runs={displayedRuns} />
            </div>
          ) : null}
        </CardContent>
      </Card>
    </div>
  );
}
