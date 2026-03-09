'use client';

import { AlertTriangle, Microscope, Search, Sparkles, Split } from 'lucide-react';

import { RunHero } from '@/components/hypoforge/run-hero';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { useRun } from '@/hooks/use-hypoforge';

function MetricCard({
  title,
  value,
  detail,
  icon: Icon
}: {
  title: string;
  value: number;
  detail: string;
  icon: typeof Search;
}) {
  return (
    <Card className='border-border/70 bg-card/95 shadow-sm'>
      <CardHeader className='pb-2'>
        <div className='flex items-center justify-between'>
          <CardDescription className='uppercase tracking-[0.18em]'>{title}</CardDescription>
          <Icon className='text-muted-foreground size-4' />
        </div>
        <CardTitle className='font-serif text-3xl'>{value}</CardTitle>
      </CardHeader>
      <CardContent className='text-muted-foreground text-sm'>{detail}</CardContent>
    </Card>
  );
}

export function RunOverview({ runId }: { runId: string }) {
  const { data: run, error, isLoading } = useRun(runId);

  if (isLoading && !run) {
    return <div className='p-8 text-sm text-muted-foreground'>Loading run…</div>;
  }

  if (!run) {
    return <div className='p-8 text-sm text-destructive'>{error ?? 'Run not found'}</div>;
  }

  return (
    <div className='flex flex-1 flex-col gap-6 p-4 md:p-8'>
      <RunHero run={run} runId={runId} />

      <div className='grid gap-4 md:grid-cols-2 xl:grid-cols-4'>
        <MetricCard
          title='Selected papers'
          value={run.selected_papers.length}
          detail='Shortlisted from the retrieval stage.'
          icon={Search}
        />
        <MetricCard
          title='Evidence cards'
          value={run.evidence_cards.length}
          detail='Structured claims retained from review.'
          icon={Microscope}
        />
        <MetricCard
          title='Conflict clusters'
          value={run.conflict_clusters.length}
          detail='Axes surfaced by the critic stage.'
          icon={Split}
        />
        <MetricCard
          title='Hypotheses'
          value={run.hypotheses.length}
          detail='Final ranked outputs from the planner.'
          icon={Sparkles}
        />
      </div>

      <div className='grid gap-6 2xl:grid-cols-[minmax(0,1.2fr)_minmax(320px,0.8fr)]'>
        <Card className='border-border/70 bg-card/95 shadow-sm'>
          <CardHeader>
            <CardTitle className='font-serif text-2xl'>Stage summaries</CardTitle>
            <CardDescription>Structured checkpoint output for each stage.</CardDescription>
          </CardHeader>
          <CardContent className='space-y-4'>
            {run.stage_summaries.map((summary) => (
              <div
                key={summary.stage_name}
                className='rounded-3xl border border-border/70 bg-background/70 p-4'
              >
                <div className='mb-3 flex items-center justify-between gap-3'>
                  <div className='font-medium capitalize'>{summary.stage_name}</div>
                  <div className='text-muted-foreground text-xs uppercase tracking-[0.18em]'>
                    {summary.status}
                  </div>
                </div>
                {summary.error_message ? (
                  <div className='mb-3 flex items-start gap-2 rounded-2xl border border-destructive/20 bg-destructive/10 px-3 py-2 text-sm text-destructive'>
                    <AlertTriangle className='mt-0.5 size-4 shrink-0' />
                    <span>{summary.error_message}</span>
                  </div>
                ) : null}
                <pre className='overflow-x-auto rounded-2xl bg-muted/50 p-3 font-mono text-xs leading-relaxed whitespace-pre-wrap'>
                  {JSON.stringify(summary.summary, null, 2)}
                </pre>
              </div>
            ))}
          </CardContent>
        </Card>

        <div className='grid gap-6'>
          <Card className='border-border/70 bg-card/95 shadow-sm'>
            <CardHeader>
              <CardTitle className='font-serif text-2xl'>Hypotheses</CardTitle>
              <CardDescription>Ranked outputs, each grounded in evidence.</CardDescription>
            </CardHeader>
            <CardContent className='space-y-4'>
              {run.hypotheses.map((hypothesis) => (
                <div key={hypothesis.rank} className='rounded-3xl border border-border/70 bg-background/80 p-4'>
                  <div className='mb-2 text-xs uppercase tracking-[0.18em] text-muted-foreground'>
                    Rank 0{hypothesis.rank}
                  </div>
                  <div className='font-medium'>{hypothesis.title}</div>
                  <p className='text-muted-foreground mt-2 text-sm leading-relaxed'>
                    {hypothesis.hypothesis_statement}
                  </p>
                </div>
              ))}
            </CardContent>
          </Card>

          <Card className='border-border/70 bg-card/95 shadow-sm'>
            <CardHeader>
              <CardTitle className='font-serif text-2xl'>Paper shortlist</CardTitle>
              <CardDescription>Selected material carried into review.</CardDescription>
            </CardHeader>
            <CardContent>
              <ScrollArea className='h-72 pr-4'>
                <div className='space-y-3'>
                  {run.selected_papers.map((paper) => (
                    <div key={paper.paper_id} className='rounded-2xl border border-border/70 bg-background/70 p-3'>
                      <div className='font-medium'>{paper.title}</div>
                      <div className='text-muted-foreground mt-1 text-xs'>
                        {(paper.authors ?? []).slice(0, 3).join(', ')}
                        {paper.year ? ` • ${paper.year}` : ''}
                      </div>
                    </div>
                  ))}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
