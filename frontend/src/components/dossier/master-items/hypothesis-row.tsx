'use client';

import { forwardRef, memo } from 'react';
import { Badge } from '@/components/ui/badge';
import { useDossierStore } from '@/stores/dossier-store';
import { cn } from '@/lib/utils';
import { scoreVariant } from '../detail-views/shared';
import type { Hypothesis } from '@/types';

interface HypothesisRowProps {
  readonly hypothesis: Hypothesis;
  readonly isSelected: boolean;
}

export const HypothesisRow = memo(forwardRef<HTMLButtonElement, HypothesisRowProps>(
  function HypothesisRow({ hypothesis, isSelected }, ref) {
    const select = useDossierStore((s) => s.select);

    return (
      <button
        ref={ref}
        type="button"
        onClick={() => select('hypothesis', String(hypothesis.rank))}
        className={cn(
          'flex w-full min-w-0 items-start gap-2 rounded-md px-2 py-2.5 text-left text-sm transition-colors focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none md:py-1.5',
          isSelected
            ? 'bg-primary/10 border-l-2 border-primary'
            : 'hover:bg-muted/50',
        )}
      >
        <Badge variant="outline" className="mt-0.5 shrink-0 px-1.5 py-0 font-mono text-xs">
          #{hypothesis.rank}
        </Badge>
        <span className="min-w-0 flex-1 whitespace-normal leading-snug [overflow-wrap:anywhere]">
          {hypothesis.title}
        </span>
        <Badge variant={scoreVariant(hypothesis.overall_score)} className="mt-0.5 shrink-0 px-1.5 py-0 text-xs">
          {hypothesis.overall_score.toFixed(2)}
        </Badge>
      </button>
    );
  },
));
