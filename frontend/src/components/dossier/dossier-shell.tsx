'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import type { PointerEvent as ReactPointerEvent } from 'react';
import { ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useMediaQuery } from '@/hooks/use-media-query';
import { useDossierStore } from '@/stores/dossier-store';
import { MasterPanel } from './master-panel';
import { DetailPanel } from './detail-panel';
import type { RunResult } from '@/types';

interface DossierShellProps {
  readonly run: RunResult;
}

const MIN_MASTER_WIDTH = 300;
const DEFAULT_MASTER_WIDTH = 380;
const MAX_MASTER_WIDTH = 560;
const MIN_DETAIL_WIDTH = 360;

function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max);
}

export function DossierShell({ run }: DossierShellProps) {
  const isMobile = useMediaQuery('(max-width: 767px)');
  const selectedType = useDossierStore((s) => s.selectedType);
  const selectedId = useDossierStore((s) => s.selectedId);
  const select = useDossierStore((s) => s.select);
  const clearSelection = useDossierStore((s) => s.clearSelection);
  const shellRef = useRef<HTMLDivElement>(null);
  const [masterWidth, setMasterWidth] = useState(DEFAULT_MASTER_WIDTH);

  const hasSelection = selectedType !== null && selectedId !== null;

  // Auto-select first hypothesis when hypotheses first appear
  const hypothesisCount = run.hypotheses.length;
  useEffect(() => {
    if (hypothesisCount > 0 && !hasSelection) {
      const first = [...run.hypotheses].sort((a, b) => a.rank - b.rank)[0];
      select('hypothesis', String(first.rank));
    }
  }, [hypothesisCount, hasSelection, select]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleResizeStart = useCallback((event: ReactPointerEvent<HTMLButtonElement>) => {
    event.preventDefault();
    const shell = shellRef.current;
    if (!shell) return;

    const startX = event.clientX;
    const startWidth = masterWidth;
    const shellWidth = shell.getBoundingClientRect().width;
    const maxWidth = Math.max(
      MIN_MASTER_WIDTH,
      Math.min(MAX_MASTER_WIDTH, shellWidth - MIN_DETAIL_WIDTH),
    );

    const handlePointerMove = (moveEvent: PointerEvent) => {
      setMasterWidth(clamp(startWidth + moveEvent.clientX - startX, MIN_MASTER_WIDTH, maxWidth));
    };
    const handlePointerUp = () => {
      window.removeEventListener('pointermove', handlePointerMove);
      window.removeEventListener('pointerup', handlePointerUp);
    };

    window.addEventListener('pointermove', handlePointerMove);
    window.addEventListener('pointerup', handlePointerUp);
  }, [masterWidth]);

  // Mobile layout
  if (isMobile) {
    if (hasSelection) {
      return (
        <div className="flex flex-col">
          <Button
            variant="ghost"
            size="sm"
            className="mb-2 w-fit"
            onClick={clearSelection}
          >
            <ArrowLeft aria-hidden="true" className="size-4" />
            Back
          </Button>
          <div className="min-h-[300px]">
            <DetailPanel run={run} />
          </div>
        </div>
      );
    }

    return (
      <div className="min-h-[300px]">
        <MasterPanel run={run} />
      </div>
    );
  }

  // Desktop layout — flex column fills remaining viewport height
  return (
    <div
      ref={shellRef}
      className="flex min-w-0 h-[calc(100dvh-var(--nav-height,56px)-120px)] min-h-[400px]"
    >
      <div
        className="min-w-0 shrink-0 overflow-hidden"
        style={{ width: masterWidth }}
      >
        <div className="h-full min-w-0 overflow-hidden rounded-lg border shadow-sm">
          <MasterPanel run={run} />
        </div>
      </div>
      <button
        type="button"
        aria-label="Resize dossier list"
        className="group flex w-4 shrink-0 cursor-col-resize items-stretch justify-center focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        onPointerDown={handleResizeStart}
      >
        <span className="my-2 w-px rounded-full bg-border transition-colors group-hover:bg-primary/60 group-focus-visible:bg-primary" />
      </button>
      <div className="min-w-0 flex-1 overflow-hidden">
        <div className="h-full min-w-0 overflow-hidden rounded-lg border shadow-sm">
          <DetailPanel run={run} />
        </div>
      </div>
    </div>
  );
}
