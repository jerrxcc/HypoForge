'use client';

import { AlertTriangle, Microscope, Search, Sparkles, Split } from 'lucide-react';

import { RunHero } from '@/components/hypoforge/run-hero';
import {
  getActiveStageName,
  getStageDescription,
  getStageStateLabel,
  getStageSummaryEntries,
  isRunActive
} from '@/lib/hypoforge-display';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Skeleton } from '@/components/ui/skeleton';
import { RunStatusBadge } from '@/components/hypoforge/run-status-badge';
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
        <div className='flex items-center justify-between gap-3'>
          <CardDescription className='uppercase tracking-[0.18em]'>{title}</CardDescription>
          <Icon className='text-muted-foreground size-4' />
        </div>
        <CardTitle className='font-serif text-3xl'>{value}</CardTitle>
      </CardHeader>
      <CardContent className='text-muted-foreground text-sm leading-6'>{detail}</CardContent>
    </Card>
  );
}

function OverviewSkeleton() {
  return (
    <div className='workspace-shell flex w-full flex-1 flex-col gap-6 p-4 md:p-8'>
      <Card className='border-border/70 bg-card/95 shadow-sm'>
        <CardContent className='space-y-6 p-6'>
          <Skeleton className='h-4 w-28' />
          <Skeleton className='h-12 w-3/4' />
          <Skeleton className='h-5 w-2/3' />
          <div className='grid gap-4 md:grid-cols-2 xl:grid-cols-4'>
            {Array.from({ length: 4 }).map((_, index) => (
              <Skeleton key={index} className='h-32 rounded-[1.4rem]' />
            ))}
          </div>
        </CardContent>
      </Card>
      <div className='grid gap-4 md:grid-cols-2 xl:grid-cols-4'>
        {Array.from({ length: 4 }).map((_, index) => (
          <Skeleton key={index} className='h-36 rounded-[1.4rem]' />
        ))}
      </div>
    </div>
  );
}

export function RunOverview({ runId }: { runId: string }) {
  const { data: run, error, isLoading } = useRun(runId);

  if (isLoading && !run) {
    return <OverviewSkeleton />;
  }

  if (!run) {
    return <div className='p-8 text-sm text-destructive'>{error ?? 'Run not found'}</div>;
  }

  const degradedStages = run.stage_summaries.filter(
    (summary) => summary.status === 'degraded' || summary.status === 'failed'
  );
  const runIsActive = isRunActive(run.status);
  const activeStage = getActiveStageName(run.status);

  return (
    <div className='workspace-shell flex w-full flex-1 flex-col gap-6 p-4 md:p-8'>
      <RunHero run={run} runId={runId} />

      {runIsActive ? (
        <Card className='border-primary/20 bg-primary/8 shadow-sm'>
          <CardContent className='flex flex-col gap-4 p-5 lg:flex-row lg:items-center lg:justify-between'>
            <div className='space-y-2'>
              <div className='text-[11px] uppercase tracking-[0.18em] text-muted-foreground'>
                Live pipeline
              </div>
              <div className='font-serif text-2xl capitalize'>
                {activeStage} is currently running.
              </div>
              <p className='text-muted-foreground max-w-3xl text-sm leading-6'>
                This dossier is still being assembled. Keep this page open while stage
                summaries and trace entries continue to refresh.
              </p>
            </div>
            <RunStatusBadge status={run.status} />
          </CardContent>
        </Card>
      ) : null}

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

      <div className='grid gap-6 2xl:grid-cols-[minmax(0,1.15fr)_minmax(360px,0.85fr)]'>
        <Card className='border-border/70 bg-card/95 shadow-sm'>
          <CardHeader>
            <CardTitle className='font-serif text-2xl'>Stage summaries</CardTitle>
            <CardDescription>
              Each stage keeps its own checkpoint, status, and recovery notes.
            </CardDescription>
          </CardHeader>
          <CardContent className='space-y-4'>
            {run.stage_summaries.map((summary) => (
              <div
                key={summary.stage_name}
                className='rounded-[1.75rem] border border-border/70 bg-background/75 p-5'
              >
                <div className='flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between'>
                  <div className='min-w-0'>
                    <div className='text-muted-foreground text-[11px] uppercase tracking-[0.18em]'>
                      {summary.stage_name}
                    </div>
                    <div className='mt-2 font-serif text-2xl capitalize'>
                      {getStageStateLabel(summary.status)}
                    </div>
                    <p className='text-muted-foreground mt-2 max-w-2xl text-sm leading-6'>
                      {getStageDescription(summary.stage_name)}
                    </p>
                  </div>
                  {summary.error_message ? (
                    <div className='rounded-full border border-destructive/20 bg-destructive/10 px-3 py-1 text-xs text-destructive'>
                      Attention needed
                    </div>
                  ) : (
                    <div className='rounded-full border border-border/70 bg-card px-3 py-1 text-xs uppercase tracking-[0.14em] text-muted-foreground'>
                      {summary.status}
                    </div>
                  )}
                </div>

                {summary.error_message ? (
                  <div className='mt-4 flex items-start gap-2 rounded-2xl border border-destructive/20 bg-destructive/10 px-3 py-3 text-sm text-destructive'>
                    <AlertTriangle className='mt-0.5 size-4 shrink-0' />
                    <span className='break-words'>{summary.error_message}</span>
                  </div>
                ) : null}

                <div className='mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-4'>
                  {getStageSummaryEntries(summary).map((entry) => (
                    <div
                      key={`${summary.stage_name}-${entry.label}`}
                      className='rounded-2xl border border-border/70 bg-card/80 px-4 py-3'
                    >
                      <div className='text-muted-foreground text-[11px] uppercase tracking-[0.16em]'>
                        {entry.label}
                      </div>
                      <div className='mt-2 text-sm font-medium leading-6 break-words'>
                        {entry.value}
                      </div>
                    </div>
                  ))}
                </div>

                <details className='mt-4 rounded-2xl border border-border/60 bg-muted/35 px-4 py-3'>
                  <summary className='cursor-pointer text-sm font-medium'>
                    View raw stage payload
                  </summary>
                  <pre className='mt-3 overflow-x-auto whitespace-pre-wrap break-words font-mono text-xs leading-relaxed'>
                    {JSON.stringify(summary.summary, null, 2)}
                  </pre>
                </details>
              </div>
            ))}
          </CardContent>
        </Card>

        <div className='grid gap-6'>
          <Card className='border-border/70 bg-card/95 shadow-sm'>
            <CardHeader>
              <CardTitle className='font-serif text-2xl'>Dossier health</CardTitle>
              <CardDescription>
                A quick operational read before you dive into trace and report.
              </CardDescription>
            </CardHeader>
            <CardContent className='space-y-4'>
              <div className='grid gap-3 sm:grid-cols-2'>
                <div className='rounded-2xl border border-border/70 bg-background/75 px-4 py-4'>
                  <div className='text-muted-foreground text-[11px] uppercase tracking-[0.16em]'>
                    Report
                  </div>
                  <div className='mt-2 text-sm font-medium'>
                    {run.report_markdown ? 'Rendered and ready to review.' : 'Not rendered yet.'}
                  </div>
                </div>
                <div className='rounded-2xl border border-border/70 bg-background/75 px-4 py-4'>
                  <div className='text-muted-foreground text-[11px] uppercase tracking-[0.16em]'>
                    Degraded stages
                  </div>
                  <div className='mt-2 text-sm font-medium'>
                    {degradedStages.length
                      ? `${degradedStages.length} stage(s) need extra scrutiny.`
                      : 'No degraded stages detected.'}
                  </div>
                </div>
              </div>
              {degradedStages.length ? (
                <div className='rounded-2xl border border-amber-300/50 bg-amber-100/65 px-4 py-4 text-sm text-amber-950'>
                  {degradedStages.map((summary) => summary.stage_name).join(', ')} flagged
                  the run for partial or failed completion. Review the trace before reusing
                  the output downstream.
                </div>
              ) : null}
            </CardContent>
          </Card>

          <Card className='border-border/70 bg-card/95 shadow-sm'>
            <CardHeader>
              <CardTitle className='font-serif text-2xl'>Hypotheses</CardTitle>
              <CardDescription>Ranked outputs, each grounded in evidence.</CardDescription>
            </CardHeader>
            <CardContent className='space-y-4'>
              {run.hypotheses.map((hypothesis) => (
                <div
                  key={hypothesis.rank}
                  className='rounded-[1.55rem] border border-border/70 bg-background/80 p-4'
                >
                  <div className='text-muted-foreground text-xs uppercase tracking-[0.18em]'>
                    Rank 0{hypothesis.rank}
                  </div>
                  <div className='mt-2 font-medium'>{hypothesis.title}</div>
                  <p className='text-muted-foreground mt-2 text-sm leading-6'>
                    {hypothesis.hypothesis_statement}
                  </p>
                  <div className='mt-4 grid gap-2 sm:grid-cols-3'>
                    {[
                      ['Novelty', hypothesis.novelty_score],
                      ['Feasibility', hypothesis.feasibility_score],
                      ['Overall', hypothesis.overall_score]
                    ].map(([label, value]) => (
                      <div
                        key={String(label)}
                        className='rounded-2xl border border-border/70 bg-card px-3 py-3'
                      >
                        <div className='text-muted-foreground text-[11px] uppercase tracking-[0.16em]'>
                          {label}
                        </div>
                        <div className='mt-1 font-mono text-sm'>
                          {Number(value).toFixed(2)}
                        </div>
                      </div>
                    ))}
                  </div>
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
              <ScrollArea className='h-[420px] pr-4'>
                <div className='space-y-3'>
                  {run.selected_papers.map((paper) => (
                    <div
                      key={paper.paper_id}
                      className='rounded-2xl border border-border/70 bg-background/70 p-3'
                    >
                      <div className='font-medium leading-6'>{paper.title}</div>
                      <div className='text-muted-foreground mt-1 text-xs leading-5'>
                        {(paper.authors ?? []).slice(0, 3).join(', ') || 'Authors unavailable'}
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
