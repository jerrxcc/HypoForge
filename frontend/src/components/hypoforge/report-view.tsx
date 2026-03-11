'use client';

import ReactMarkdown from 'react-markdown';

import { RunHero } from '@/components/hypoforge/run-hero';
import { RunStatusBadge } from '@/components/hypoforge/run-status-badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Skeleton } from '@/components/ui/skeleton';
import { useRun, useRunReport } from '@/hooks/use-hypoforge';
import { getActiveStageName, isRunActive } from '@/lib/hypoforge-display';

export function ReportView({ runId }: { runId: string }) {
  const { data: run, error: runError } = useRun(runId);
  const { data: report, error: reportError, isLoading } = useRunReport(runId);

  if (!run) {
    return <div className='p-8 text-sm text-destructive'>{runError ?? 'Run not found'}</div>;
  }

  const totalLimitations = run.hypotheses.reduce(
    (count, hypothesis) => count + hypothesis.limitations.length,
    0
  );
  const totalUncertaintyNotes = run.hypotheses.reduce(
    (count, hypothesis) => count + hypothesis.uncertainty_notes.length,
    0
  );
  const avgScore =
    run.hypotheses.reduce((sum, hypothesis) => sum + hypothesis.overall_score, 0) /
      Math.max(run.hypotheses.length, 1);
  const runIsActive = isRunActive(run.status);
  const activeStage = getActiveStageName(run.status);
  const retrievalSummary = run.stage_summaries.find((summary) => summary.stage_name === 'retrieval');
  const reviewSummary = run.stage_summaries.find((summary) => summary.stage_name === 'review');
  const criticSummary = run.stage_summaries.find((summary) => summary.stage_name === 'critic');
  const retrievalCoverage =
    typeof retrievalSummary?.summary.coverage_assessment === 'string'
      ? retrievalSummary.summary.coverage_assessment
      : 'not reported';
  const dominantAxes =
    Array.isArray(reviewSummary?.summary.dominant_axes) &&
    reviewSummary.summary.dominant_axes.length
      ? reviewSummary.summary.dominant_axes.map(String)
      : [];
  const topConflictAxes =
    Array.isArray(criticSummary?.summary.top_axes) && criticSummary.summary.top_axes.length
      ? criticSummary.summary.top_axes.map(String)
      : run.conflict_clusters.map((cluster) => cluster.topic_axis);
  const referencedEvidenceCounts = new Map<string, number>();
  for (const hypothesis of run.hypotheses) {
    for (const evidenceId of hypothesis.supporting_evidence_ids) {
      referencedEvidenceCounts.set(
        evidenceId,
        (referencedEvidenceCounts.get(evidenceId) ?? 0) + 1
      );
    }
  }
  const topReferencedEvidence = [...run.evidence_cards]
    .sort((left, right) => {
      const countDiff =
        (referencedEvidenceCounts.get(right.evidence_id) ?? 0) -
        (referencedEvidenceCounts.get(left.evidence_id) ?? 0);
      if (countDiff !== 0) {
        return countDiff;
      }
      return right.confidence - left.confidence;
    })
    .slice(0, 5);

  return (
    <div className='workspace-shell flex w-full flex-1 flex-col gap-6 p-4 md:p-8'>
      <RunHero run={run} runId={runId} />
      {runIsActive ? (
        <Card className='border-primary/20 bg-primary/8 shadow-sm'>
          <CardContent className='flex flex-col gap-4 p-5 lg:flex-row lg:items-center lg:justify-between'>
            <div className='space-y-2'>
              <div className='text-[11px] uppercase tracking-[0.18em] text-muted-foreground'>
                Draft status
              </div>
              <div className='font-serif text-2xl capitalize'>
                The report will appear after {activeStage} completes.
              </div>
              <p className='text-muted-foreground max-w-3xl text-sm leading-6'>
                This panel keeps polling in the background. You can switch between
                overview and trace while the editorial draft is still being assembled.
              </p>
            </div>
            <RunStatusBadge status={run.status} />
          </CardContent>
        </Card>
      ) : null}
      <div className='grid gap-4 md:grid-cols-2 2xl:grid-cols-4'>
        {[
          ['Coverage', retrievalCoverage, 'Retrieval footing carried into the briefing.'],
          ['Evidence cards', run.evidence_cards.length, 'Structured support carried into drafting.'],
          ['Average score', avgScore.toFixed(2), `${totalLimitations} limitation note(s) across all ranks.`],
          ['Conflict axes', topConflictAxes.length, `${totalUncertaintyNotes} uncertainty note(s) preserved.`]
        ].map(([label, value, detail]) => (
          <div
            key={String(label)}
            className='rounded-[1.55rem] border border-border/70 bg-card/95 px-5 py-4 shadow-sm'
          >
            <div className='text-muted-foreground text-[11px] uppercase tracking-[0.18em]'>
              {label}
            </div>
            <div className='mt-3 font-serif text-3xl'>{value}</div>
            <div className='text-muted-foreground mt-2 text-sm leading-6'>{detail}</div>
          </div>
        ))}
      </div>

      <div className='grid gap-6 2xl:grid-cols-[minmax(0,1.3fr)_minmax(320px,0.7fr)]'>
        <Card className='border-border/70 bg-card/95 shadow-sm'>
          <CardHeader>
            <div className='text-muted-foreground text-xs uppercase tracking-[0.18em]'>
              Final report
            </div>
            <CardTitle className='font-serif text-3xl'>Editorial draft</CardTitle>
            <CardDescription>
              Read the synthesized argument in narrative form before drilling into the
              structured outline.
            </CardDescription>
          </CardHeader>
          <CardContent>
            {isLoading && !report ? (
              <div className='text-muted-foreground text-sm'>Loading report…</div>
            ) : null}
            {reportError ? (
              <div className='text-sm text-destructive'>{reportError}</div>
            ) : null}
            {report ? (
              <div className='rounded-[2rem] border border-border/60 bg-background/75 px-6 py-6'>
                <article className='prose prose-slate mx-auto max-w-4xl prose-headings:font-serif prose-headings:tracking-tight prose-h1:text-4xl prose-h1:leading-tight prose-h2:border-t prose-h2:border-border/60 prose-h2:pt-6 prose-h2:text-2xl prose-p:text-[15px] prose-p:leading-8 prose-li:text-[15px] prose-li:leading-7 prose-strong:text-foreground'>
                  <ReactMarkdown>{report}</ReactMarkdown>
                </article>
              </div>
            ) : runIsActive ? (
              <div className='space-y-4 rounded-[2rem] border border-border/60 bg-background/75 px-6 py-6'>
                <div className='space-y-2'>
                  <div className='text-[11px] uppercase tracking-[0.18em] text-muted-foreground'>
                    Editorial draft pending
                  </div>
                  <p className='text-muted-foreground text-sm leading-6'>
                    Planner output has not landed yet. A report skeleton is shown here so
                    the page does not collapse while the run is still active.
                  </p>
                </div>
                <Skeleton className='h-10 w-1/2' />
                <Skeleton className='h-4 w-full' />
                <Skeleton className='h-4 w-11/12' />
                <Skeleton className='h-4 w-10/12' />
                <Skeleton className='mt-4 h-8 w-56' />
                <Skeleton className='h-4 w-full' />
                <Skeleton className='h-4 w-9/12' />
                <Skeleton className='mt-4 h-32 w-full rounded-[1.5rem]' />
              </div>
            ) : null}
          </CardContent>
        </Card>

        <div className='grid gap-6'>
          <Card className='border-border/70 bg-card/95 shadow-sm'>
            <CardHeader>
              <div className='text-muted-foreground text-xs uppercase tracking-[0.18em]'>
                Dossier footing
              </div>
              <CardTitle className='font-serif text-2xl'>Hypothesis outline</CardTitle>
              <CardDescription>
                Use this side rail to compare rank, support volume, and uncertainty at a
                glance.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ScrollArea className='h-[520px] pr-4'>
                <div className='space-y-4'>
                  {run.hypotheses.map((hypothesis) => (
                    <div
                      key={hypothesis.rank}
                      className='rounded-[1.55rem] border border-border/70 bg-background/80 p-4'
                    >
                      <div className='flex items-start justify-between gap-3'>
                        <div>
                          <div className='text-muted-foreground text-xs uppercase tracking-[0.18em]'>
                            Rank 0{hypothesis.rank}
                          </div>
                          <div className='mt-2 font-medium leading-6'>{hypothesis.title}</div>
                        </div>
                        <div className='rounded-full border border-border/70 bg-card px-3 py-1 font-mono text-xs'>
                          {hypothesis.overall_score.toFixed(2)}
                        </div>
                      </div>
                      <p className='text-muted-foreground mt-3 text-sm leading-6'>
                        {hypothesis.prediction}
                      </p>
                      <div className='mt-4 grid gap-2 sm:grid-cols-2'>
                        <div className='rounded-2xl border border-border/70 bg-card px-3 py-3'>
                          <div className='text-muted-foreground text-[11px] uppercase tracking-[0.16em]'>
                            Evidence footing
                          </div>
                          <div className='mt-1 text-sm font-medium'>
                            {hypothesis.supporting_evidence_ids.length} supporting •{' '}
                            {hypothesis.counterevidence_ids.length} counter
                          </div>
                        </div>
                        <div className='rounded-2xl border border-border/70 bg-card px-3 py-3'>
                          <div className='text-muted-foreground text-[11px] uppercase tracking-[0.16em]'>
                            Constraints
                          </div>
                          <div className='mt-1 text-sm font-medium'>
                            {hypothesis.limitations.length
                              ? `${hypothesis.limitations.length} limitation(s)`
                              : 'No extra limitations'}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>

          <Card className='border-border/70 bg-card/95 shadow-sm'>
            <CardHeader>
              <CardTitle className='font-serif text-2xl'>Reading route</CardTitle>
            </CardHeader>
            <CardContent className='space-y-3 text-sm leading-7 text-muted-foreground'>
              <p>
                Start with the executive summary, then move through retrieval coverage and
                the conflict map before reading the ranked hypotheses in detail.
              </p>
              <p>
                Treat the evidence appendix and paper appendix as your grounding layer when
                you need to verify whether a strong claim is backed by enough material.
              </p>
            </CardContent>
          </Card>

          <Card className='border-border/70 bg-card/95 shadow-sm'>
            <CardHeader>
              <CardTitle className='font-serif text-2xl'>Coverage notes</CardTitle>
            </CardHeader>
            <CardContent className='space-y-3 text-sm leading-7 text-muted-foreground'>
              <p>
                Retrieval coverage is currently <span className='font-medium capitalize text-foreground'>{retrievalCoverage}</span>.
              </p>
              <p>
                {dominantAxes.length
                  ? `Review concentrated on: ${dominantAxes.slice(0, 3).join(' • ')}.`
                  : 'Review did not report dominant axes for this run.'}
              </p>
              <p>
                {topConflictAxes.length
                  ? `Critic highlighted: ${topConflictAxes.slice(0, 3).join(' • ')}.`
                  : 'Critic did not record explicit conflict axes.'}
              </p>
            </CardContent>
          </Card>

          <Card className='border-border/70 bg-card/95 shadow-sm'>
            <CardHeader>
              <CardTitle className='font-serif text-2xl'>Most cited evidence</CardTitle>
            </CardHeader>
            <CardContent className='space-y-3'>
              {topReferencedEvidence.length ? (
                topReferencedEvidence.map((card) => (
                  <div
                    key={card.evidence_id}
                    className='rounded-[1.4rem] border border-border/70 bg-background/80 p-4'
                  >
                    <div className='flex items-start justify-between gap-3'>
                      <div className='text-[11px] uppercase tracking-[0.16em] text-muted-foreground'>
                        {card.evidence_id}
                      </div>
                      <div className='rounded-full border border-border/70 bg-card px-3 py-1 text-[11px] uppercase tracking-[0.14em] text-muted-foreground'>
                        cited {referencedEvidenceCounts.get(card.evidence_id) ?? 0}x
                      </div>
                    </div>
                    <p className='mt-2 text-sm leading-6'>{card.claim_text}</p>
                    <div className='text-muted-foreground mt-2 text-xs leading-5'>
                      {card.system_or_material} • {card.intervention} • {card.outcome}
                    </div>
                  </div>
                ))
              ) : (
                <div className='text-sm text-muted-foreground'>No evidence cards to summarize yet.</div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
