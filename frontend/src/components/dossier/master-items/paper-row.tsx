'use client';

import { forwardRef, memo } from 'react';
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

    return (
      <button
        ref={ref}
        type="button"
        onClick={() => select('paper', paper.paper_id)}
        className={cn(
          'flex w-full min-w-0 items-start gap-2 rounded-md px-2 py-2.5 text-left text-sm transition-colors focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none md:py-1.5',
          isSelected
            ? 'bg-primary/10 border-l-2 border-primary'
            : 'hover:bg-muted/50',
        )}
      >
        <span className="min-w-0 flex-1 whitespace-normal leading-snug [overflow-wrap:anywhere]">
          {paper.title}
        </span>
        {paper.year && (
          <span className="mt-0.5 shrink-0 text-xs text-muted-foreground">
            {paper.year}
          </span>
        )}
        {paper.venue && (
          <span className="mt-0.5 hidden shrink-0 text-xs text-muted-foreground lg:inline">
            {truncate(paper.venue, 15)}
          </span>
        )}
      </button>
    );
  },
));
