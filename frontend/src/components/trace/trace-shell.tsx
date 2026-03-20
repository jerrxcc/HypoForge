'use client';

import { useState } from 'react';
import { TraceList } from './trace-list';
import { TraceDetail } from './trace-detail';
import type { ToolTrace } from '@/types';

interface TraceShellProps {
  readonly traces: ToolTrace[];
}

export function TraceShell({ traces }: TraceShellProps) {
  const [selectedId, setSelectedId] = useState<string | null>(
    traces.length > 0 ? traces[0].id : null,
  );

  const selectedTrace = traces.find((t) => t.id === selectedId) ?? null;

  return (
    <div className="flex gap-4 h-[calc(100vh-220px)] min-h-[500px]">
      {/* Left: trace list */}
      <div className="w-80 shrink-0 rounded-lg border border-border overflow-hidden">
        <TraceList traces={traces} selectedId={selectedId} onSelect={setSelectedId} />
      </div>

      {/* Right: trace detail */}
      <div className="flex-1 min-w-0">
        {selectedTrace ? (
          <TraceDetail trace={selectedTrace} />
        ) : (
          <div className="flex h-full items-center justify-center rounded-lg border border-border text-muted-foreground text-sm">
            Select a tool call to inspect it.
          </div>
        )}
      </div>
    </div>
  );
}
