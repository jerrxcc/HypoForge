'use client';

import { useState } from 'react';

import { RunHero } from '@/components/hypoforge/run-hero';
import { RunStatusBadge } from '@/components/hypoforge/run-status-badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup
} from '@/components/ui/resizable';
import { ScrollArea } from '@/components/ui/scroll-area';
import { useRun, useRunTrace } from '@/hooks/use-hypoforge';
import { getTraceSummaryEntries } from '@/lib/hypoforge-display';
import type { ToolTrace } from '@/lib/hypoforge';
import { cn } from '@/lib/utils';

function TraceList({
  traces,
  activeTrace,
  onSelect,
  isLoading,
  error
}: {
  traces: ToolTrace[] | undefined;
  activeTrace: ToolTrace | null;
  onSelect: (traceId: string) => void;
  isLoading: boolean;
  error: string | null;
}) {
  return (
    <div className='space-y-2 p-4'>
      {isLoading && !traces ? (
        <div className='text-muted-foreground text-sm'>Loading trace…</div>
      ) : null}
      {error ? <div className='text-sm text-destructive'>{error}</div> : null}
      {traces?.map((trace, index) => (
        <button
          type='button'
          key={trace.id}
          onClick={() => onSelect(trace.id)}
          className={cn(
            'w-full rounded-[1.5rem] border p-4 text-left transition-colors',
            activeTrace?.id === trace.id
              ? 'border-primary/25 bg-primary/8'
              : 'border-border/70 bg-background/70 hover:bg-background'
          )}
        >
          <div className='mb-2 flex items-start justify-between gap-3'>
            <div className='min-w-0'>
              <div className='line-clamp-2 font-medium leading-6'>{trace.tool_name}</div>
              <div className='text-muted-foreground mt-1 text-xs uppercase tracking-[0.18em]'>
                {trace.agent_name} • step {index + 1}
              </div>
            </div>
            <RunStatusBadge status={trace.success ? 'done' : 'failed'} />
          </div>
          <div className='text-muted-foreground text-xs leading-6'>
            {trace.latency_ms} ms
            {trace.input_tokens ? ` • in ${trace.input_tokens}` : ''}
            {trace.output_tokens ? ` • out ${trace.output_tokens}` : ''}
          </div>
          <div className='mt-3 flex flex-wrap gap-2'>
            {getTraceSummaryEntries(trace)
              .slice(0, 2)
              .map((entry) => (
                <span
                  key={`${trace.id}-${entry.label}`}
                  className='rounded-full border border-border/70 bg-card px-2.5 py-1 text-[11px] text-muted-foreground'
                >
                  {entry.label}: {entry.value}
                </span>
              ))}
          </div>
        </button>
      ))}
    </div>
  );
}

function TraceInspector({ trace }: { trace: ToolTrace | null }) {
  if (!trace) {
    return <div className='text-muted-foreground text-sm'>No trace entries yet.</div>;
  }

  const summaryEntries = getTraceSummaryEntries(trace);

  return (
    <div className='space-y-4 p-6'>
      <div className='space-y-2'>
        <div className='text-muted-foreground text-xs uppercase tracking-[0.24em]'>
          Trace inspector
        </div>
        <div className='font-serif text-3xl'>{trace.tool_name}</div>
        <p className='text-muted-foreground text-sm leading-7'>
          Inspect tool inputs, summarized outputs, and token/latency metadata before you
          trust the downstream report.
        </p>
      </div>

      <div className='grid gap-3 md:grid-cols-2 xl:grid-cols-4'>
        {[
          ['Agent', trace.agent_name],
          ['Model', trace.model_name],
          ['Latency', `${trace.latency_ms} ms`],
          ['Status', trace.success ? 'success' : 'failed']
        ].map(([label, value]) => (
          <div key={label} className='rounded-2xl border border-border/70 bg-background/70 p-4'>
            <div className='text-muted-foreground text-xs uppercase tracking-[0.18em]'>
              {label}
            </div>
            <div className='mt-2 text-sm font-medium break-all'>{value}</div>
          </div>
        ))}
      </div>

      {summaryEntries.length ? (
        <div className='grid gap-3 md:grid-cols-2'>
          {summaryEntries.map((entry) => (
            <div key={entry.label} className='rounded-2xl border border-border/70 bg-card px-4 py-4'>
              <div className='text-muted-foreground text-xs uppercase tracking-[0.18em]'>
                {entry.label}
              </div>
              <div className='mt-2 text-sm font-medium leading-6 break-words'>{entry.value}</div>
            </div>
          ))}
        </div>
      ) : null}

      {trace.error_message ? (
        <div className='rounded-2xl border border-destructive/20 bg-destructive/10 px-4 py-3 text-sm text-destructive'>
          {trace.error_message}
        </div>
      ) : null}

      <div className='grid gap-4 xl:grid-cols-2'>
        <div className='space-y-2'>
          <div className='font-medium'>Tool args</div>
          <pre className='max-h-[360px] overflow-x-auto rounded-[1.5rem] border border-border/70 bg-muted/40 p-4 font-mono text-xs leading-relaxed whitespace-pre-wrap break-words'>
            {JSON.stringify(trace.args, null, 2)}
          </pre>
        </div>
        <div className='space-y-2'>
          <div className='font-medium'>Result summary</div>
          <pre className='max-h-[360px] overflow-x-auto rounded-[1.5rem] border border-border/70 bg-muted/40 p-4 font-mono text-xs leading-relaxed whitespace-pre-wrap break-words'>
            {JSON.stringify(trace.result_summary, null, 2)}
          </pre>
        </div>
      </div>
    </div>
  );
}

export function TraceView({ runId }: { runId: string }) {
  const { data: run, error: runError } = useRun(runId);
  const { data: traces, error: traceError, isLoading } = useRunTrace(runId);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  if (!run) {
    return <div className='p-8 text-sm text-destructive'>{runError ?? 'Run not found'}</div>;
  }

  const activeTrace = traces?.find((trace) => trace.id === selectedId) ?? traces?.[0] ?? null;
  const traceList = traces ?? [];
  const failedTraceCount = traceList.filter((trace) => !trace.success).length;
  const plannerTraceCount = traceList.filter((trace) => trace.agent_name === 'planner').length;
  const cacheHitCount = traceList.filter((trace) => trace.result_summary.cache_hit === true).length;

  return (
    <div className='workspace-shell flex w-full flex-1 flex-col gap-6 p-4 md:p-8'>
      <RunHero run={run} runId={runId} />

      <div className='grid gap-4 md:grid-cols-2 2xl:grid-cols-4'>
        {[
          ['Trace steps', traceList.length, 'Recorded tool calls in this dossier.'],
          ['Failed steps', failedTraceCount, 'Calls that need extra inspection or rerun.'],
          ['Planner turns', plannerTraceCount, 'Late-stage synthesis and report-writing steps.'],
          ['Cache hits', cacheHitCount, 'Connector responses reused without another external call.']
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

      <div className='grid gap-6 xl:hidden'>
        <Card className='border-border/70 bg-card/95 shadow-sm'>
          <CardHeader>
            <CardTitle className='font-serif text-2xl'>Trace steps</CardTitle>
            <CardDescription>
              Select a tool call to inspect its inputs, outputs, and request metadata.
            </CardDescription>
          </CardHeader>
          <CardContent className='p-0'>
            <TraceList
              traces={traces ?? undefined}
              activeTrace={activeTrace}
              onSelect={setSelectedId}
              isLoading={isLoading}
              error={traceError}
            />
          </CardContent>
        </Card>

        <Card className='border-border/70 bg-card/95 shadow-sm'>
          <CardContent>
            <TraceInspector trace={activeTrace} />
          </CardContent>
        </Card>
      </div>

      <Card className='hidden min-h-[680px] border-border/70 bg-card/95 shadow-sm xl:block'>
        <CardContent className='h-full p-0'>
          <ResizablePanelGroup direction='horizontal'>
            <ResizablePanel defaultSize={36} minSize={24}>
              <ScrollArea className='h-[680px]'>
                <TraceList
                  traces={traces ?? undefined}
                  activeTrace={activeTrace}
                  onSelect={setSelectedId}
                  isLoading={isLoading}
                  error={traceError}
                />
              </ScrollArea>
            </ResizablePanel>
            <ResizableHandle withHandle />
            <ResizablePanel defaultSize={64}>
              <ScrollArea className='h-[680px]'>
                <TraceInspector trace={activeTrace} />
              </ScrollArea>
            </ResizablePanel>
          </ResizablePanelGroup>
        </CardContent>
      </Card>
    </div>
  );
}
