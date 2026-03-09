'use client';

import { RunsTable } from '@/components/hypoforge/runs-table';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { useRuns } from '@/hooks/use-hypoforge';

export default function RunsPage() {
  const { data: runs, error, isLoading } = useRuns();
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

          {isLoading && !runs ? (
            <div className='text-muted-foreground text-sm'>Loading runs…</div>
          ) : null}
          {error ? <div className='text-sm text-destructive'>{error}</div> : null}
          {runs ? <RunsTable runs={runs} /> : null}
        </CardContent>
      </Card>
    </div>
  );
}
