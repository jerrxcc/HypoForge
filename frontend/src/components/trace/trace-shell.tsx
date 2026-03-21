'use client';

import { useState } from 'react';
import { ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useMediaQuery } from '@/hooks/use-media-query';
import { TraceList } from './trace-list';
import { TraceDetail } from './trace-detail';
import type { ToolTrace } from '@/types';

interface TraceShellProps {
  readonly traces: ToolTrace[];
}

export function TraceShell({ traces }: TraceShellProps) {
  const isMobile = useMediaQuery('(max-width: 767px)');
  const [selectedId, setSelectedId] = useState<string | null>(
    traces.length > 0 ? traces[0].id : null,
  );

  const selectedTrace = traces.find((t) => t.id === selectedId) ?? null;

  // Mobile: master-detail toggle
  if (isMobile) {
    if (selectedTrace) {
      return (
        <div className="flex flex-col gap-2">
          <Button
            variant="ghost"
            size="sm"
            className="w-fit"
            onClick={() => setSelectedId(null)}
          >
            <ArrowLeft aria-hidden="true" className="size-4" />
            Back to list
          </Button>
          <TraceDetail trace={selectedTrace} />
        </div>
      );
    }

    return (
      <div className="min-h-[300px] rounded-lg border border-border overflow-hidden">
        <TraceList traces={traces} selectedId={selectedId} onSelect={setSelectedId} />
      </div>
    );
  }

  // Desktop: side-by-side
  // 120px offset = main padding (24px*2) + breadcrumb (~20px) + header (~28px) + actions gap (~24px)
  return (
    <div className="flex gap-4 h-[calc(100dvh-var(--nav-height,56px)-120px)] min-h-[400px]">
      <div className="md:w-[260px] lg:w-80 shrink-0 rounded-lg border border-border overflow-hidden">
        <TraceList traces={traces} selectedId={selectedId} onSelect={setSelectedId} />
      </div>
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
