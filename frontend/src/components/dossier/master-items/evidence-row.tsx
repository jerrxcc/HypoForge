'use client';

import { forwardRef, memo } from 'react';
import { Badge } from '@/components/ui/badge';
import { Tooltip, TooltipTrigger, TooltipContent } from '@/components/ui/tooltip';
import { useDossierStore } from '@/stores/dossier-store';
import { truncate, cn } from '@/lib/utils';
import { directionVariant } from '../detail-views/shared';
import type { EvidenceCard } from '@/types';

interface EvidenceRowProps {
  readonly evidence: EvidenceCard;
  readonly isSelected: boolean;
}

export const EvidenceRow = memo(forwardRef<HTMLButtonElement, EvidenceRowProps>(
  function EvidenceRow({ evidence, isSelected }, ref) {
    const select = useDossierStore((s) => s.select);
    const needsTooltip = evidence.title.length > 55;

    return (
      <button
        ref={ref}
        type="button"
        onClick={() => select('evidence', evidence.evidence_id)}
        className={cn(
          'flex w-full items-center gap-2 rounded-md px-2 py-2.5 md:py-1.5 text-left text-sm transition-colors focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none',
          isSelected
            ? 'bg-primary/10 border-l-2 border-primary'
            : 'hover:bg-muted/50',
        )}
      >
        {needsTooltip ? (
          <Tooltip>
            <TooltipTrigger asChild>
              <span className="min-w-0 flex-1 truncate">
                {truncate(evidence.title, 55)}
              </span>
            </TooltipTrigger>
            <TooltipContent side="top" className="max-w-xs">
              {evidence.title}
            </TooltipContent>
          </Tooltip>
        ) : (
          <span className="min-w-0 flex-1 truncate">
            {evidence.title}
          </span>
        )}
        <Badge variant={directionVariant(evidence.direction)} className="shrink-0 text-[10px] px-1.5 py-0">
          {evidence.direction}
        </Badge>
      </button>
    );
  },
));
