'use client';

import { forwardRef, memo } from 'react';
import { Badge } from '@/components/ui/badge';
import { useDossierStore } from '@/stores/dossier-store';
import { cn } from '@/lib/utils';
import { directionVariant } from '../detail-views/shared';
import type { EvidenceCard } from '@/types';

interface EvidenceRowProps {
  readonly evidence: EvidenceCard;
  readonly isSelected: boolean;
}

export const EvidenceRow = memo(forwardRef<HTMLButtonElement, EvidenceRowProps>(
  function EvidenceRow({ evidence, isSelected }, ref) {
    const select = useDossierStore((s) => s.select);

    return (
      <button
        ref={ref}
        type="button"
        onClick={() => select('evidence', evidence.evidence_id)}
        className={cn(
          'flex w-full min-w-0 items-start gap-2 rounded-md px-2 py-2.5 text-left text-sm transition-colors focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none md:py-1.5',
          isSelected
            ? 'bg-primary/10 border-l-2 border-primary'
            : 'hover:bg-muted/50',
        )}
      >
        <span className="min-w-0 flex-1 whitespace-normal leading-snug [overflow-wrap:anywhere]">
          {evidence.title}
        </span>
        <Badge variant={directionVariant(evidence.direction)} className="mt-0.5 shrink-0 px-1.5 py-0 text-xs">
          {evidence.direction}
        </Badge>
      </button>
    );
  },
));
