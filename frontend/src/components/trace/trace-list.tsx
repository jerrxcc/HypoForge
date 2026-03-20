'use client';

import { useCallback } from 'react';
import { CheckCircle2, XCircle } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { cn } from '@/lib/utils';
import type { ToolTrace } from '@/types';

interface TraceListProps {
  readonly traces: ToolTrace[];
  readonly selectedId: string | null;
  readonly onSelect: (id: string) => void;
}

export function TraceList({ traces, selectedId, onSelect }: TraceListProps) {
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLDivElement>, id: string) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        onSelect(id);
      }
    },
    [onSelect],
  );

  return (
    <ScrollArea className="h-full">
      <div className="flex flex-col divide-y divide-border">
        {traces.map((trace) => (
          <div
            key={trace.id}
            role="button"
            tabIndex={0}
            onClick={() => onSelect(trace.id)}
            onKeyDown={(e) => handleKeyDown(e, trace.id)}
            className={cn(
              'flex items-center gap-3 px-3 py-2.5 cursor-pointer transition-colors hover:bg-muted/50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring',
              selectedId === trace.id && 'bg-primary/10',
            )}
          >
            {/* Status icon */}
            {trace.success ? (
              <CheckCircle2 className="size-4 shrink-0 text-success" />
            ) : (
              <XCircle className="size-4 shrink-0 text-destructive" />
            )}

            {/* Tool name */}
            <span className="min-w-0 flex-1 truncate text-sm font-medium text-foreground">
              {trace.tool_name}
            </span>

            {/* Agent badge */}
            <Badge variant="outline" className="shrink-0 text-[10px] px-1.5 py-0 font-mono">
              {trace.agent_name}
            </Badge>

            {/* Latency */}
            <span className="shrink-0 text-xs text-muted-foreground tabular-nums">
              {trace.latency_ms}ms
            </span>
          </div>
        ))}
      </div>
    </ScrollArea>
  );
}
