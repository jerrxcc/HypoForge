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
