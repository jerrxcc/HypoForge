'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import {
  FileSearch,
  FlaskConical,
  Gauge,
  LibraryBig,
  NotebookPen,
  Sparkles,
  type LucideIcon
} from 'lucide-react';

import { GoldenTopicLauncher } from '@/components/hypoforge/golden-topic-launcher';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Checkbox } from '@/components/ui/checkbox';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { createRun, defaultConstraints } from '@/lib/hypoforge';

const DOSSIER_OUTPUTS: Array<{ icon: LucideIcon; label: string; detail: string }> = [
  { icon: FileSearch, label: 'Selected papers', detail: 'A curated shortlist carried into review.' },
  { icon: NotebookPen, label: 'Trace log', detail: 'Every tool call, request id, and latency checkpoint.' },
  { icon: FlaskConical, label: 'Evidence cards', detail: 'Structured claims and counterevidence.' },
  { icon: Sparkles, label: 'Hypotheses', detail: 'Three ranked outputs plus a narrative report.' }
];

export function NewRunForm() {
  const router = useRouter();
  const [topic, setTopic] = useState('');
  const [constraints, setConstraints] = useState(defaultConstraints);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSubmitting(true);
    setError(null);

    try {
      const result = await createRun({ topic, constraints });
      router.push(`/dashboard/runs/${result.run_id}`);
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : 'failed to start run');
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className='grid gap-6 xl:grid-cols-[minmax(0,1.24fr)_minmax(320px,0.76fr)]'>
      <Card className='border-border/70 bg-card/95 shadow-sm'>
        <CardHeader>
          <div className='flex flex-wrap items-center gap-3'>
            <div className='text-muted-foreground text-xs uppercase tracking-[0.24em]'>
              New run
            </div>
            <div className='rounded-full border border-border/70 bg-background/80 px-3 py-1 text-[11px] uppercase tracking-[0.18em] text-muted-foreground'>
              Live pipeline
            </div>
          </div>
          <CardTitle className='font-serif text-3xl tracking-tight md:text-4xl'>
            Launch a topic through the full editorial pipeline.
          </CardTitle>
          <CardDescription className='max-w-2xl text-base leading-relaxed'>
            Start a real retrieval, review, critic, and planner cycle. The run detail
            view will expose every stage summary, trace entry, and final report.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form className='space-y-6' onSubmit={handleSubmit}>
            <div className='rounded-[1.75rem] border border-border/70 bg-background/70 p-5'>
              <div className='mb-4 space-y-1'>
                <div className='text-muted-foreground text-[11px] uppercase tracking-[0.18em]'>
                  Research topic
                </div>
                <p className='text-muted-foreground text-sm leading-6'>
                  Phrase the topic as a concrete research brief, not a keyword list. The
                  retrieval stage will broaden it from there.
                </p>
              </div>
              <Textarea
                id='topic'
                value={topic}
                onChange={(event) => setTopic(event.target.value)}
                placeholder='e.g. solid-state battery electrolyte additives for interfacial stability'
                className='min-h-36 rounded-3xl border-0 bg-card shadow-none'
              />
            </div>

            <div className='grid gap-6 lg:grid-cols-[minmax(0,1.15fr)_minmax(240px,0.85fr)]'>
              <div className='rounded-[1.75rem] border border-border/70 bg-background/70 p-5'>
                <div className='mb-4 space-y-1'>
                  <div className='text-muted-foreground text-[11px] uppercase tracking-[0.18em]'>
                    Search window
                  </div>
                  <p className='text-muted-foreground text-sm leading-6'>
                    Tune the literature window and paper budget before the dossier is
                    assembled.
                  </p>
                </div>
                <div className='grid gap-4 md:grid-cols-2 xl:grid-cols-3'>
                  <div className='space-y-2'>
                    <Label htmlFor='year_from'>Year from</Label>
                    <Input
                      id='year_from'
                      type='number'
                      value={constraints.year_from}
                      onChange={(event) =>
                        setConstraints((current) => ({
                          ...current,
                          year_from: Number(event.target.value)
                        }))
                      }
                    />
                  </div>
                  <div className='space-y-2'>
                    <Label htmlFor='year_to'>Year to</Label>
                    <Input
                      id='year_to'
                      type='number'
                      value={constraints.year_to}
                      onChange={(event) =>
                        setConstraints((current) => ({
                          ...current,
                          year_to: Number(event.target.value)
                        }))
                      }
                    />
                  </div>
                  <div className='space-y-2'>
                    <Label htmlFor='max_selected_papers'>Paper cap</Label>
                    <Input
                      id='max_selected_papers'
                      type='number'
                      value={constraints.max_selected_papers}
                      onChange={(event) =>
                        setConstraints((current) => ({
                          ...current,
                          max_selected_papers: Number(event.target.value)
                        }))
                      }
                    />
                  </div>
                </div>
              </div>

              <div className='grid gap-4 rounded-[1.75rem] border border-border/70 bg-background/70 p-5'>
                <div className='space-y-1'>
                  <div className='text-muted-foreground text-[11px] uppercase tracking-[0.18em]'>
                    Constraints
                  </div>
                  <p className='text-muted-foreground text-sm leading-6'>
                    Shape how the planner thinks about experimental context and access.
                  </p>
                </div>
                <div className='space-y-2'>
                  <Label>Lab mode</Label>
                  <Select
                    value={constraints.lab_mode}
                    onValueChange={(value: 'wet' | 'dry' | 'either') =>
                      setConstraints((current) => ({ ...current, lab_mode: value }))
                    }
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value='either'>Either</SelectItem>
                      <SelectItem value='wet'>Wet lab</SelectItem>
                      <SelectItem value='dry'>Dry lab</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className='flex items-center gap-3 rounded-2xl border border-border/70 bg-card px-4 py-3'>
                  <Checkbox
                    id='open_access_only'
                    checked={constraints.open_access_only}
                    onCheckedChange={(checked) =>
                      setConstraints((current) => ({
                        ...current,
                        open_access_only: Boolean(checked)
                      }))
                    }
                  />
                  <Label htmlFor='open_access_only'>Prefer open-access only</Label>
                </div>
              </div>
            </div>

            <div className='rounded-[1.75rem] border border-border/70 bg-background/70 p-5'>
              <div className='mb-4 space-y-1'>
                <div className='text-[11px] uppercase tracking-[0.18em] text-muted-foreground'>
                  Golden topics
                </div>
                <p className='text-muted-foreground text-sm leading-6'>
                  Use a known benchmark topic to verify the full live chain before trying a
                  new research brief.
                </p>
              </div>
              <GoldenTopicLauncher onPick={setTopic} />
            </div>

            {error ? (
              <div className='rounded-2xl border border-destructive/20 bg-destructive/10 px-4 py-3 text-sm text-destructive'>
                {error}
              </div>
            ) : null}

            <div className='flex flex-col items-start gap-4 rounded-[1.75rem] border border-border/70 bg-card/80 px-5 py-4 sm:flex-row sm:items-center sm:justify-between'>
              <div className='space-y-1'>
                <div className='text-[11px] uppercase tracking-[0.18em] text-muted-foreground'>
                  Launch note
                </div>
                <p className='text-muted-foreground max-w-2xl text-sm leading-6'>
                  The first run is synchronous. Keep this tab open while the pipeline
                  finishes and the dossier is written.
                </p>
              </div>
              <Button
                type='submit'
                size='lg'
                className='w-full rounded-full px-6 sm:w-auto'
                disabled={isSubmitting || !topic.trim()}
              >
                {isSubmitting ? 'Running…' : 'Start real run'}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      <div className='grid gap-6 xl:sticky xl:top-8 xl:self-start'>
        <Card className='border-border/70 bg-gradient-to-b from-card to-secondary/40 shadow-sm'>
          <CardHeader>
            <div className='text-muted-foreground text-xs uppercase tracking-[0.24em]'>
              Pipeline
            </div>
            <CardTitle className='font-serif text-3xl tracking-tight'>
              Four stages, one dossier.
            </CardTitle>
            <CardDescription className='text-base'>
              Every run preserves stage summaries, tool traces, and the final report for
              audit.
            </CardDescription>
          </CardHeader>
          <CardContent className='space-y-4'>
            {[
              ['Retrieval', 'Expand queries, merge sources, keep only evidence-rich papers.'],
              ['Review', 'Extract evidence cards and preserve partial results on degradation.'],
              ['Critic', 'Cluster conflicts, annotate likely explanations, surface weaknesses.'],
              ['Planner', 'Produce three grounded hypotheses and a readable markdown report.']
            ].map(([title, description], index) => (
              <div key={title} className='rounded-3xl border border-border/70 bg-background/80 p-4'>
                <div className='mb-2 flex items-center gap-3'>
                  <div className='bg-primary/12 text-primary flex size-8 items-center justify-center rounded-full text-xs font-semibold'>
                    0{index + 1}
                  </div>
                  <div className='font-medium'>{title}</div>
                </div>
                <p className='text-muted-foreground text-sm leading-relaxed'>{description}</p>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card className='border-border/70 bg-card/95 shadow-sm'>
          <CardHeader>
            <div className='text-muted-foreground text-xs uppercase tracking-[0.18em]'>
              Launch profile
            </div>
            <CardTitle className='font-serif text-2xl'>Before you hit run</CardTitle>
            <CardDescription>
              This desk is optimized for real API runs, not static placeholder demos.
            </CardDescription>
          </CardHeader>
          <CardContent className='grid gap-3'>
            {[
              {
                icon: Gauge,
                label: 'Synchronous first pass',
                detail: 'Keep the tab open while retrieval, review, critic, and planner finish.'
              },
              {
                icon: LibraryBig,
                label: 'Evidence-first archive',
                detail: 'Every run lands in the archive with trace entries and a report-ready dossier.'
              }
            ].map(({ icon: Icon, label, detail }) => (
              <div
                key={label}
                className='rounded-[1.4rem] border border-border/70 bg-background/75 p-4'
              >
                <div className='flex items-center gap-3'>
                  <div className='bg-primary/10 text-primary flex size-9 items-center justify-center rounded-2xl'>
                    <Icon className='size-4' />
                  </div>
                  <div className='font-medium'>{label}</div>
                </div>
                <p className='text-muted-foreground mt-3 text-sm leading-6'>{detail}</p>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card className='border-border/70 bg-card/95 shadow-sm'>
          <CardHeader>
            <div className='text-muted-foreground text-xs uppercase tracking-[0.18em]'>
              Dossier outputs
            </div>
            <CardTitle className='font-serif text-2xl'>What you will get back</CardTitle>
          </CardHeader>
          <CardContent className='grid gap-3 sm:grid-cols-2 xl:grid-cols-1'>
            {DOSSIER_OUTPUTS.map(({ icon: Icon, label, detail }) => (
              <div
                key={label}
                className='rounded-[1.4rem] border border-border/70 bg-background/75 p-4'
              >
                <div className='flex items-center gap-3'>
                  <div className='bg-primary/10 text-primary flex size-9 items-center justify-center rounded-2xl'>
                    <Icon className='size-4' />
                  </div>
                  <div className='font-medium'>{label}</div>
                </div>
                <p className='text-muted-foreground mt-3 text-sm leading-6'>{detail}</p>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
