'use client';

import { forwardRef } from 'react';
import { Badge } from '@/components/ui/badge';
import { useDossierStore } from '@/stores/dossier-store';
import { truncate, cn } from '@/lib/utils';
import type { EvidenceCard, Direction } from '@/types';

function directionVariant(direction: Direction): 'success' | 'error' | 'warning' | 'secondary' {
  switch (direction) {
    case 'positive':
      return 'success';
    case 'negative':
      return 'error';
    case 'mixed':
      return 'warning';
    case 'null':
    case 'unclear':
    default:
      return 'secondary';
  }
}

interface EvidenceRowProps {
  readonly evidence: EvidenceCard;
  readonly isSelected: boolean;
}

export const EvidenceRow = forwardRef<HTMLButtonElement, EvidenceRowProps>(
  function EvidenceRow({ evidence, isSelected }, ref) {
    const select = useDossierStore((s) => s.select);

    return (
      <button
        ref={ref}
        type="button"
        onClick={() => select('evidence', evidence.evidence_id)}
        className={cn(
          'flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-left text-sm transition-colors',
          isSelected
            ? 'bg-primary/10 border-l-2 border-primary'
            : 'hover:bg-muted/50',
        )}
      >
        <span className="min-w-0 flex-1 truncate">
          {truncate(evidence.title, 55)}
        </span>
        <Badge variant={directionVariant(evidence.direction)} className="shrink-0 text-[10px] px-1.5 py-0">
          {evidence.direction}
        </Badge>
      </button>
    );
  },
);
