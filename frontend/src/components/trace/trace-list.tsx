'use client';

import { memo, useCallback } from 'react';
import { CheckCircle2, XCircle } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { cn } from '@/lib/utils';
import type { ToolTrace } from '@/types';

interface TraceRowProps {
  readonly trace: ToolTrace;
  readonly isSelected: boolean;
  readonly onSelect: (id: string) => void;
}

const TraceRow = memo(function TraceRow({ trace, isSelected, onSelect }: TraceRowProps) {
  const handleClick = useCallback(() => onSelect(trace.id), [onSelect, trace.id]);

  return (
    <button
      type="button"
      aria-pressed={isSelected}
      onClick={handleClick}
      className={cn(
        'flex w-full items-center gap-3 px-3 py-2.5 text-left transition-colors hover:bg-muted/50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring',
        isSelected && 'bg-primary/10',
      )}
    >
      {trace.success ? (
        <CheckCircle2 aria-hidden="true" className="size-4 shrink-0 text-success" />
      ) : (
        <XCircle aria-hidden="true" className="size-4 shrink-0 text-destructive" />
      )}
      <span className="min-w-0 flex-1 truncate text-sm font-medium text-foreground">
        {trace.tool_name}
      </span>
      <Badge variant="outline" className="shrink-0 text-[10px] px-1.5 py-0 font-mono">
        {trace.agent_name}
      </Badge>
      <span className="shrink-0 text-xs text-muted-foreground tabular-nums">
        {trace.latency_ms}ms
      </span>
    </button>
  );
});

interface TraceListProps {
  readonly traces: ToolTrace[];
  readonly selectedId: string | null;
  readonly onSelect: (id: string) => void;
}

export function TraceList({ traces, selectedId, onSelect }: TraceListProps) {
  return (
    <ScrollArea className="h-full">
      <div className="flex flex-col divide-y divide-border">
        {traces.map((trace) => (
          <TraceRow
            key={trace.id}
            trace={trace}
            isSelected={selectedId === trace.id}
            onSelect={onSelect}
          />
        ))}
      </div>
    </ScrollArea>
  );
}
