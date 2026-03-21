'use client';

import { forwardRef, memo } from 'react';
import { Badge } from '@/components/ui/badge';
import { Tooltip, TooltipTrigger, TooltipContent } from '@/components/ui/tooltip';
import { useDossierStore } from '@/stores/dossier-store';
import { truncate, cn } from '@/lib/utils';
import { scoreVariant } from '../detail-views/shared';
import type { Hypothesis } from '@/types';

interface HypothesisRowProps {
  readonly hypothesis: Hypothesis;
  readonly isSelected: boolean;
}

export const HypothesisRow = memo(forwardRef<HTMLButtonElement, HypothesisRowProps>(
  function HypothesisRow({ hypothesis, isSelected }, ref) {
    const select = useDossierStore((s) => s.select);
    const needsTooltip = hypothesis.title.length > 50;

    return (
      <button
        ref={ref}
        type="button"
        onClick={() => select('hypothesis', String(hypothesis.rank))}
        className={cn(
          'flex w-full items-center gap-2 rounded-md px-2 py-2.5 md:py-1.5 text-left text-sm transition-colors focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none',
          isSelected
            ? 'bg-primary/10 border-l-2 border-primary'
            : 'hover:bg-muted/50',
        )}
      >
        <Badge variant="outline" className="shrink-0 text-xs px-1.5 py-0 font-mono">
          #{hypothesis.rank}
        </Badge>
        {needsTooltip ? (
          <Tooltip>
            <TooltipTrigger asChild>
              <span className="min-w-0 flex-1 truncate">
                {truncate(hypothesis.title, 50)}
              </span>
            </TooltipTrigger>
            <TooltipContent side="top" className="max-w-xs">
              {hypothesis.title}
            </TooltipContent>
          </Tooltip>
        ) : (
          <span className="min-w-0 flex-1 truncate">
            {hypothesis.title}
          </span>
        )}
        <Badge variant={scoreVariant(hypothesis.overall_score)} className="shrink-0 text-xs px-1.5 py-0">
          {hypothesis.overall_score.toFixed(2)}
        </Badge>
      </button>
    );
  },
));
