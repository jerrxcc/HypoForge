'use client';

import { forwardRef, memo } from 'react';
import { Badge } from '@/components/ui/badge';
import { useDossierStore } from '@/stores/dossier-store';
import { cn } from '@/lib/utils';
import type { ConflictCluster } from '@/types';

const CONFLICT_TYPE_LABEL: Record<string, string> = {
  direct_conflict: 'direct',
  conditional_divergence: 'conditional',
  weak_evidence_gap: 'gap',
};

interface ConflictRowProps {
  readonly conflict: ConflictCluster;
  readonly isSelected: boolean;
}

export const ConflictRow = memo(forwardRef<HTMLButtonElement, ConflictRowProps>(
  function ConflictRow({ conflict, isSelected }, ref) {
    const select = useDossierStore((s) => s.select);

    return (
      <button
        ref={ref}
        type="button"
        onClick={() => select('conflict', conflict.cluster_id)}
        className={cn(
          'flex w-full min-w-0 items-start gap-2 rounded-md px-2 py-2.5 text-left text-sm transition-colors focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none md:py-1.5',
          isSelected
            ? 'bg-primary/10 border-l-2 border-primary'
            : 'hover:bg-muted/50',
        )}
      >
        <span className="min-w-0 flex-1 whitespace-normal leading-snug [overflow-wrap:anywhere]">
          {conflict.topic_axis}
        </span>
        <Badge variant="outline" className="mt-0.5 shrink-0 px-1.5 py-0 text-xs">
          {CONFLICT_TYPE_LABEL[conflict.conflict_type] ?? conflict.conflict_type}
        </Badge>
      </button>
    );
  },
));
