'use client';

import { useEffect } from 'react';
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

export function DossierShell({ run }: DossierShellProps) {
  const isMobile = useMediaQuery('(max-width: 767px)');
  const selectedType = useDossierStore((s) => s.selectedType);
  const selectedId = useDossierStore((s) => s.selectedId);
  const select = useDossierStore((s) => s.select);
  const clearSelection = useDossierStore((s) => s.clearSelection);

  const hasSelection = selectedType !== null && selectedId !== null;

  // Auto-select first hypothesis when hypotheses first appear
  useEffect(() => {
    if (run.hypotheses.length > 0 && !hasSelection) {
      const first = [...run.hypotheses].sort((a, b) => a.rank - b.rank)[0];
      select('hypothesis', String(first.rank));
    }
  }, [run.hypotheses.length]); // eslint-disable-line react-hooks/exhaustive-deps

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
            <ArrowLeft className="size-4" />
            Back
          </Button>
          <div className="min-h-[500px]">
            <DetailPanel run={run} />
          </div>
        </div>
      );
    }

    return (
      <div className="min-h-[500px]">
        <MasterPanel run={run} />
      </div>
    );
  }

  // Desktop layout
  return (
    <div className="flex gap-4">
      <div className="w-[320px] shrink-0 lg:w-[380px]">
        <div className="h-[600px] rounded-lg border">
          <MasterPanel run={run} />
        </div>
      </div>
      <div className="min-w-0 flex-1">
        <div className="h-[600px] rounded-lg border">
          <DetailPanel run={run} />
        </div>
      </div>
    </div>
  );
}
