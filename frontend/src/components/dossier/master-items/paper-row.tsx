'use client';

import { forwardRef, memo } from 'react';
import { Tooltip, TooltipTrigger, TooltipContent } from '@/components/ui/tooltip';
import { useDossierStore } from '@/stores/dossier-store';
import { truncate, cn } from '@/lib/utils';
import type { PaperDetail } from '@/types';

interface PaperRowProps {
  readonly paper: PaperDetail;
  readonly isSelected: boolean;
}

export const PaperRow = memo(forwardRef<HTMLButtonElement, PaperRowProps>(
  function PaperRow({ paper, isSelected }, ref) {
    const select = useDossierStore((s) => s.select);
    const needsTooltip = paper.title.length > 50;

    return (
      <button
        ref={ref}
        type="button"
        onClick={() => select('paper', paper.paper_id)}
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
                {truncate(paper.title, 50)}
              </span>
            </TooltipTrigger>
            <TooltipContent side="top" className="max-w-xs">
              {paper.title}
            </TooltipContent>
          </Tooltip>
        ) : (
          <span className="min-w-0 flex-1 truncate">
            {paper.title}
          </span>
        )}
        {paper.year && (
          <span className="shrink-0 text-xs text-muted-foreground">
            {paper.year}
          </span>
        )}
        {paper.venue && (
          <span className="hidden shrink-0 text-xs text-muted-foreground lg:inline">
            {truncate(paper.venue, 15)}
          </span>
        )}
      </button>
    );
  },
));
