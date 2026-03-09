'use client';

import { useState } from 'react';

import { RunHero } from '@/components/hypoforge/run-hero';
import { Card, CardContent } from '@/components/ui/card';
import { ResizableHandle, ResizablePanel, ResizablePanelGroup } from '@/components/ui/resizable';
import { ScrollArea } from '@/components/ui/scroll-area';
import { useRun, useRunTrace } from '@/hooks/use-hypoforge';
import { cn } from '@/lib/utils';

export function TraceView({ runId }: { runId: string }) {
  const { data: run, error: runError } = useRun(runId);
  const { data: traces, error: traceError, isLoading } = useRunTrace(runId);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  if (!run) {
    return <div className='p-8 text-sm text-destructive'>{runError ?? 'Run not found'}</div>;
  }

  const activeTrace =
    traces?.find((trace) => trace.id === selectedId) ?? traces?.[0] ?? null;

  return (
    <div className='flex flex-1 flex-col gap-6 p-4 md:p-8'>
      <RunHero run={run} runId={runId} />
      <Card className='min-h-[640px] border-border/70 bg-card/95 shadow-sm'>
        <CardContent className='h-full p-0'>
          <ResizablePanelGroup direction='horizontal'>
            <ResizablePanel defaultSize={38} minSize={28}>
              <ScrollArea className='h-[640px]'>
                <div className='space-y-2 p-4'>
                  {isLoading && !traces ? (
                    <div className='text-muted-foreground text-sm'>Loading trace…</div>
                  ) : null}
                  {traceError ? (
                    <div className='text-sm text-destructive'>{traceError}</div>
                  ) : null}
                  {traces?.map((trace, index) => (
                    <button
                      type='button'
                      key={trace.id}
                      onClick={() => setSelectedId(trace.id)}
                      className={cn(
                        'w-full rounded-3xl border p-4 text-left transition-colors',
                        activeTrace?.id === trace.id
                          ? 'border-primary bg-primary/8'
                          : 'border-border/70 bg-background/70'
                      )}
                    >
                      <div className='mb-2 flex items-center justify-between gap-3'>
                        <div className='font-medium'>{trace.tool_name}</div>
                        <div className='text-muted-foreground text-xs'>#{index + 1}</div>
                      </div>
                      <div className='text-muted-foreground text-sm'>
                        {trace.agent_name} • {trace.model_name}
                      </div>
                      <div className='text-muted-foreground mt-2 text-xs'>
                        {trace.latency_ms} ms
                        {trace.input_tokens ? ` • in ${trace.input_tokens}` : ''}
                        {trace.output_tokens ? ` • out ${trace.output_tokens}` : ''}
                      </div>
                    </button>
                  ))}
                </div>
              </ScrollArea>
            </ResizablePanel>
            <ResizableHandle withHandle />
            <ResizablePanel defaultSize={62}>
              <ScrollArea className='h-[640px]'>
                <div className='space-y-4 p-6'>
                  {activeTrace ? (
                    <>
                      <div>
                        <div className='text-muted-foreground text-xs uppercase tracking-[0.24em]'>
                          Trace inspector
                        </div>
                        <div className='mt-2 font-serif text-3xl'>{activeTrace.tool_name}</div>
                      </div>
                      <div className='grid gap-3 md:grid-cols-4'>
                        {[
                          ['Agent', activeTrace.agent_name],
                          ['Model', activeTrace.model_name],
                          ['Latency', `${activeTrace.latency_ms} ms`],
                          ['Request', activeTrace.request_id ?? 'n/a']
                        ].map(([label, value]) => (
                          <div key={label} className='rounded-2xl border border-border/70 bg-background/70 p-4'>
                            <div className='text-muted-foreground text-xs uppercase tracking-[0.18em]'>
                              {label}
                            </div>
                            <div className='mt-2 text-sm font-medium break-all'>{value}</div>
                          </div>
                        ))}
                      </div>
                      {activeTrace.error_message ? (
                        <div className='rounded-2xl border border-destructive/20 bg-destructive/10 px-4 py-3 text-sm text-destructive'>
                          {activeTrace.error_message}
                        </div>
                      ) : null}
                      <div className='grid gap-4 xl:grid-cols-2'>
                        <div className='space-y-2'>
                          <div className='font-medium'>Tool args</div>
                          <pre className='overflow-x-auto rounded-3xl border border-border/70 bg-muted/40 p-4 font-mono text-xs whitespace-pre-wrap'>
                            {JSON.stringify(activeTrace.args, null, 2)}
                          </pre>
                        </div>
                        <div className='space-y-2'>
                          <div className='font-medium'>Result summary</div>
                          <pre className='overflow-x-auto rounded-3xl border border-border/70 bg-muted/40 p-4 font-mono text-xs whitespace-pre-wrap'>
                            {JSON.stringify(activeTrace.result_summary, null, 2)}
                          </pre>
                        </div>
                      </div>
                    </>
                  ) : (
                    <div className='text-muted-foreground text-sm'>No trace entries yet.</div>
                  )}
                </div>
              </ScrollArea>
            </ResizablePanel>
          </ResizablePanelGroup>
        </CardContent>
      </Card>
    </div>
  );
}
