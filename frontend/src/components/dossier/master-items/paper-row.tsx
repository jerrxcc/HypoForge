'use client';

import { forwardRef } from 'react';
import { useDossierStore } from '@/stores/dossier-store';
import { truncate, cn } from '@/lib/utils';
import type { PaperDetail } from '@/types';

interface PaperRowProps {
  readonly paper: PaperDetail;
  readonly isSelected: boolean;
}

export const PaperRow = forwardRef<HTMLButtonElement, PaperRowProps>(
  function PaperRow({ paper, isSelected }, ref) {
    const select = useDossierStore((s) => s.select);

    return (
      <button
        ref={ref}
        type="button"
        onClick={() => select('paper', paper.paper_id)}
        className={cn(
          'flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-left text-sm transition-colors',
          isSelected
            ? 'bg-primary/10 border-l-2 border-primary'
            : 'hover:bg-muted/50',
        )}
      >
        <span className="min-w-0 flex-1 truncate">
          {truncate(paper.title, 50)}
        </span>
        {paper.year && (
          <span className="shrink-0 text-[10px] text-muted-foreground">
            {paper.year}
          </span>
        )}
        {paper.venue && (
          <span className="hidden shrink-0 text-[10px] text-muted-foreground lg:inline">
            {truncate(paper.venue, 15)}
          </span>
        )}
      </button>
    );
  },
);
