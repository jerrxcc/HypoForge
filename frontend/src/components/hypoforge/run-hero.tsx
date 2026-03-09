import { formatDistanceToNow } from 'date-fns';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { RunStatusBadge } from '@/components/hypoforge/run-status-badge';
import { StageProgressBand } from '@/components/hypoforge/stage-progress-band';
import { RunDetailNav } from '@/components/hypoforge/run-detail-nav';
import type { RunResult } from '@/lib/hypoforge';

export function RunHero({
  run,
  runId
}: {
  run: RunResult;
  runId: string;
}) {
  return (
    <Card className='gap-0 overflow-hidden border-border/70 bg-card/95 shadow-sm'>
      <CardHeader className='border-b border-border/70 pb-6'>
        <div className='flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between'>
          <div className='space-y-3'>
            <div className='text-muted-foreground text-xs uppercase tracking-[0.24em]'>
              Run dossier
            </div>
            <CardTitle className='font-serif text-3xl leading-tight tracking-tight md:text-4xl'>
              Editorial review workspace
            </CardTitle>
            <div className='text-muted-foreground max-w-2xl space-y-2 text-sm leading-relaxed'>
              <p>Evidence-backed hypothesis generation with full trace visibility.</p>
              <div className='inline-flex max-w-full rounded-full border border-border/70 bg-background/75 px-3 py-1 font-mono text-[12px] break-all'>
                {runId}
              </div>
            </div>
          </div>
          <div className='space-y-3 lg:text-right'>
            <RunStatusBadge status={run.status} />
            <div className='text-muted-foreground text-sm'>
              Updated{' '}
              {run.stage_summaries.at(-1)?.completed_at
                ? formatDistanceToNow(new Date(run.stage_summaries.at(-1)!.completed_at!), {
                    addSuffix: true
                  })
                : 'recently'}
            </div>
          </div>
        </div>
        <div className='pt-4'>
          <RunDetailNav runId={runId} />
        </div>
      </CardHeader>
      <CardContent className='space-y-6 pt-6'>
        <StageProgressBand
          runStatus={run.status}
          stageSummaries={run.stage_summaries}
        />
      </CardContent>
    </Card>
  );
}
