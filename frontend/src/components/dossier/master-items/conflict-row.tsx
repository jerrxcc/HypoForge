'use client';

import { forwardRef, memo } from 'react';
import { Badge } from '@/components/ui/badge';
import { Tooltip, TooltipTrigger, TooltipContent } from '@/components/ui/tooltip';
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

export const ConflictRow = memo(forwardRef<HTMLButtonElement, ConflictRowProps>(
  function ConflictRow({ conflict, isSelected }, ref) {
    const select = useDossierStore((s) => s.select);
    const needsTooltip = conflict.topic_axis.length > 55;

    return (
      <button
        ref={ref}
        type="button"
        onClick={() => select('conflict', conflict.cluster_id)}
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
                {truncate(conflict.topic_axis, 55)}
              </span>
            </TooltipTrigger>
            <TooltipContent side="top" className="max-w-xs">
              {conflict.topic_axis}
            </TooltipContent>
          </Tooltip>
        ) : (
          <span className="min-w-0 flex-1 truncate">
            {conflict.topic_axis}
          </span>
        )}
        <Badge variant="outline" className="shrink-0 text-[10px] px-1.5 py-0">
          {CONFLICT_TYPE_LABEL[conflict.conflict_type] ?? conflict.conflict_type}
        </Badge>
      </button>
    );
  },
));
