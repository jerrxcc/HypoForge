'use client';

import { forwardRef } from 'react';
import { Badge } from '@/components/ui/badge';
import { useDossierStore } from '@/stores/dossier-store';
import { truncate, cn } from '@/lib/utils';
import type { Hypothesis } from '@/types';

function scoreVariant(score: number) {
  if (score >= 0.7) return 'success' as const;
  if (score >= 0.4) return 'warning' as const;
  return 'error' as const;
}

interface HypothesisRowProps {
  readonly hypothesis: Hypothesis;
  readonly isSelected: boolean;
}

export const HypothesisRow = forwardRef<HTMLButtonElement, HypothesisRowProps>(
  function HypothesisRow({ hypothesis, isSelected }, ref) {
    const select = useDossierStore((s) => s.select);

    return (
      <button
        ref={ref}
        type="button"
        onClick={() => select('hypothesis', String(hypothesis.rank))}
        className={cn(
          'flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-left text-sm transition-colors',
          isSelected
            ? 'bg-primary/10 border-l-2 border-primary'
            : 'hover:bg-muted/50',
        )}
      >
        <Badge variant="outline" className="shrink-0 text-[10px] px-1.5 py-0 font-mono">
          #{hypothesis.rank}
        </Badge>
        <span className="min-w-0 flex-1 truncate">
          {truncate(hypothesis.title, 50)}
        </span>
        <Badge variant={scoreVariant(hypothesis.overall_score)} className="shrink-0 text-[10px] px-1.5 py-0">
          {hypothesis.overall_score.toFixed(2)}
        </Badge>
      </button>
    );
  },
);
