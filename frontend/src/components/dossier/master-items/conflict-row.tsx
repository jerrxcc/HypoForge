'use client';

import { forwardRef } from 'react';
import { Badge } from '@/components/ui/badge';
import { useDossierStore } from '@/stores/dossier-store';
import { truncate, cn } from '@/lib/utils';
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

export const ConflictRow = forwardRef<HTMLButtonElement, ConflictRowProps>(
  function ConflictRow({ conflict, isSelected }, ref) {
    const select = useDossierStore((s) => s.select);

    return (
      <button
        ref={ref}
        type="button"
        onClick={() => select('conflict', conflict.cluster_id)}
        className={cn(
          'flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-left text-sm transition-colors',
          isSelected
            ? 'bg-primary/10 border-l-2 border-primary'
            : 'hover:bg-muted/50',
        )}
      >
        <span className="min-w-0 flex-1 truncate">
          {truncate(conflict.topic_axis, 55)}
        </span>
        <Badge variant="outline" className="shrink-0 text-[10px] px-1.5 py-0">
          {CONFLICT_TYPE_LABEL[conflict.conflict_type] ?? conflict.conflict_type}
        </Badge>
      </button>
    );
  },
);
