'use client';

import { useEffect, useRef } from 'react';
import { X, Loader2, CheckCircle2, XCircle, Wifi, WifiOff } from 'lucide-react';
import { cn, formatDuration } from '@/lib/utils';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Button } from '@/components/ui/button';
import type { RunActivity } from '@/hooks/use-run-activity';
import type { ToolTrace, StageName } from '@/types';

const STAGE_ORDER: StageName[] = ['retrieval', 'review', 'critic', 'planner'];
const STAGE_LABELS: Record<string, string> = {
  retrieval: 'Retrieval',
  review: 'Review',
  critic: 'Critic',
  planner: 'Planner',
  unknown: 'Unknown',
};

interface ActivityDrawerProps {
  readonly activity: RunActivity;
  readonly open: boolean;
  readonly onClose: () => void;
}

export function ActivityDrawer({ activity, open, onClose }: ActivityDrawerProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [activity.traces.length]);

  if (!open) return null;

  // Group traces by stage_name + attempt
  const groups = groupTraces(activity.traces);

  return (
    <div className="fixed inset-y-0 right-0 z-40 flex w-[380px] flex-col border-l bg-background shadow-lg">
      {/* Header */}
      <div className="flex items-center justify-between border-b px-4 py-3">
        <div className="flex items-center gap-2">
          <h2 className="text-sm font-semibold">Agent Activity</h2>
          {activity.connected ? (
            <Wifi className="size-3.5 text-success" />
          ) : activity.error ? (
            <WifiOff className="size-3.5 text-destructive" />
          ) : null}
        </div>
        <Button variant="ghost" size="icon" className="size-7" onClick={onClose}>
          <X className="size-4" />
        </Button>
      </div>

      {/* SSE error bar */}
      {activity.error && (
        <div className="border-b border-destructive/30 bg-destructive/10 px-4 py-2 text-xs text-destructive">
          {activity.error}
        </div>
      )}

      {/* Metrics bar */}
      <div className="flex items-center gap-4 border-b px-4 py-2 text-xs text-muted-foreground">
        <span>{activity.metrics.totalTools} tool calls</span>
        <span>{formatDuration(activity.metrics.totalLatencyMs / 1000)} total</span>
      </div>

      {/* Thinking indicator */}
      {activity.activeToolName && (
        <div className="flex items-center gap-2 border-b bg-primary/5 px-4 py-2">
          <Loader2 className="size-3.5 animate-spin text-primary" />
          <span className="text-xs font-medium text-primary">
            {activity.activeAgent}: {activity.activeToolName}
          </span>
        </div>
      )}

      {/* Trace list */}
      <ScrollArea className="flex-1">
        <div className="flex flex-col gap-1 p-3">
          {groups.length === 0 && !activity.activeToolName && (
            <p className="py-8 text-center text-xs text-muted-foreground">
              No activity yet
            </p>
          )}
          {groups.map((group) => (
            <div key={group.key} className="mb-2">
              <div className="mb-1 flex items-center gap-1.5 text-xs font-medium text-muted-foreground">
                <span>{STAGE_LABELS[group.stageName] ?? group.stageName}</span>
                {group.attempt > 1 && (
                  <span className="rounded bg-muted px-1 text-[10px]">
                    attempt {group.attempt}
                  </span>
                )}
              </div>
              <div className="flex flex-col gap-0.5">
                {group.traces.map((trace) => (
                  <TraceItem key={trace.id} trace={trace} />
                ))}
              </div>
            </div>
          ))}
          <div ref={bottomRef} />
        </div>
      </ScrollArea>
    </div>
  );
}

function TraceItem({ trace }: { readonly trace: ToolTrace }) {
  return (
    <div
      className={cn(
        'flex items-center gap-2 rounded px-2 py-1.5 text-xs transition-colors',
        'animate-in fade-in-0 slide-in-from-right-2 duration-200',
        trace.success ? 'hover:bg-muted/50' : 'bg-destructive/5',
      )}
    >
      {trace.success ? (
        <CheckCircle2 className="size-3 shrink-0 text-success" />
      ) : (
        <XCircle className="size-3 shrink-0 text-destructive" />
      )}
      <span className="truncate font-mono">{trace.tool_name}</span>
      <span className="ml-auto shrink-0 text-muted-foreground">
        {trace.latency_ms}ms
      </span>
    </div>
  );
}

interface TraceGroup {
  key: string;
  stageName: string;
  attempt: number;
  traces: ToolTrace[];
}

function groupTraces(traces: ToolTrace[]): TraceGroup[] {
  const map = new Map<string, TraceGroup>();
  for (const trace of traces) {
    const key = `${trace.stage_name}:${trace.attempt}`;
    let group = map.get(key);
    if (!group) {
      group = {
        key,
        stageName: trace.stage_name,
        attempt: trace.attempt,
        traces: [],
      };
      map.set(key, group);
    }
    group.traces.push(trace);
  }
  // Sort by stage order, then attempt
  return Array.from(map.values()).sort((a, b) => {
    const aIdx = STAGE_ORDER.indexOf(a.stageName as StageName);
    const bIdx = STAGE_ORDER.indexOf(b.stageName as StageName);
    if (aIdx !== bIdx) return (aIdx === -1 ? 99 : aIdx) - (bIdx === -1 ? 99 : bIdx);
    return a.attempt - b.attempt;
  });
}
