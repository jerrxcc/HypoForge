'use client';

import ReactMarkdown from 'react-markdown';

import { RunHero } from '@/components/hypoforge/run-hero';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { useRun, useRunReport } from '@/hooks/use-hypoforge';

export function ReportView({ runId }: { runId: string }) {
  const { data: run, error: runError } = useRun(runId);
  const { data: report, error: reportError, isLoading } = useRunReport(runId);

  if (!run) {
    return <div className='p-8 text-sm text-destructive'>{runError ?? 'Run not found'}</div>;
  }

  return (
    <div className='flex flex-1 flex-col gap-6 p-4 md:p-8'>
      <RunHero run={run} runId={runId} />
      <div className='grid gap-6 xl:grid-cols-[minmax(0,1.25fr)_minmax(280px,0.75fr)]'>
        <Card className='border-border/70 bg-card/95 shadow-sm'>
          <CardHeader>
            <CardTitle className='font-serif text-2xl'>Markdown report</CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading && !report ? (
              <div className='text-muted-foreground text-sm'>Loading report…</div>
            ) : null}
            {reportError ? (
              <div className='text-sm text-destructive'>{reportError}</div>
            ) : null}
            {report ? (
              <article className='prose prose-slate max-w-none prose-headings:font-serif prose-h1:text-4xl prose-h2:text-2xl prose-p:text-sm prose-p:leading-7'>
                <ReactMarkdown>{report}</ReactMarkdown>
              </article>
            ) : null}
          </CardContent>
        </Card>
        <Card className='border-border/70 bg-card/95 shadow-sm'>
          <CardHeader>
            <CardTitle className='font-serif text-2xl'>Hypothesis outline</CardTitle>
          </CardHeader>
          <CardContent>
            <ScrollArea className='h-[620px] pr-4'>
              <div className='space-y-4'>
                {run.hypotheses.map((hypothesis) => (
                  <div key={hypothesis.rank} className='rounded-3xl border border-border/70 bg-background/70 p-4'>
                    <div className='text-muted-foreground text-xs uppercase tracking-[0.18em]'>
                      Rank 0{hypothesis.rank}
                    </div>
                    <div className='mt-2 font-medium'>{hypothesis.title}</div>
                    <p className='text-muted-foreground mt-2 text-sm leading-relaxed'>
                      {hypothesis.prediction}
                    </p>
                    <div className='mt-3 text-xs text-muted-foreground'>
                      Supporting evidence: {hypothesis.supporting_evidence_ids.length} • Counterevidence:{' '}
                      {hypothesis.counterevidence_ids.length}
                    </div>
                  </div>
                ))}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
