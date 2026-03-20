'use client';

import { Check, Circle, Loader2, AlertCircle } from 'lucide-react';
import { cn } from '@/lib/utils';
import { STAGES, STAGE_LABELS } from '@/lib/constants';
import type { RunStatus, StageSummary } from '@/types';

interface StageProgressProps {
  status: RunStatus;
  stageSummaries: StageSummary[];
}

export function StageProgress({ status, stageSummaries }: StageProgressProps) {
  const getStageStatus = (stageName: string) => {
    const summary = stageSummaries.find((s) => s.stage_name === stageName);
    if (summary) return summary.status;

    // Infer from run status
    const stageIndex = STAGES.indexOf(stageName as typeof STAGES[number]);
    const getActiveStage = (): typeof STAGES[number] | null => {
      if (status === 'retrieving') return 'retrieval';
      if (status === 'reviewing') return 'review';
      if (status === 'criticizing') return 'critic';
      if (status === 'planning' || status === 'reflecting') return 'planner';
      return null;
    };
    const activeStage = getActiveStage();
    const activeIndex = activeStage ? STAGES.indexOf(activeStage) : -1;

    if (status === 'failed') {
      return activeIndex === stageIndex ? 'failed' : stageIndex < activeIndex ? 'completed' : undefined;
    }

    if (status === 'done') return 'completed';

    if (activeIndex > stageIndex) return 'completed';
    if (activeIndex === stageIndex) return 'started';

    return undefined;
  };

  const getIcon = (stageStatus?: string) => {
    switch (stageStatus) {
      case 'completed':
        return <Check className="h-4 w-4" />;
      case 'started':
        return <Loader2 className="h-4 w-4 animate-spin" />;
      case 'failed':
        return <AlertCircle className="h-4 w-4" />;
      case 'degraded':
        return <Check className="h-4 w-4 text-amber-500" />;
      default:
        return <Circle className="h-4 w-4" />;
    }
  };

  const getColor = (stageStatus?: string) => {
    switch (stageStatus) {
      case 'completed':
        return 'bg-emerald-50 border-emerald-200 text-emerald-700';
      case 'started':
        return 'bg-blue-50 border-blue-200 text-blue-700 animate-pulse-subtle';
      case 'failed':
        return 'bg-rose-50 border-rose-200 text-rose-700';
      case 'degraded':
        return 'bg-amber-50 border-amber-200 text-amber-700';
      default:
        return 'bg-gray-50 border-gray-200 text-gray-400';
    }
  };

  return (
    <div className="flex items-center justify-between gap-2">
      {STAGES.map((stage, index) => {
        const stageStatus = getStageStatus(stage);

        return (
          <div key={stage} className="flex flex-1 items-center gap-2">
            <div
              className={cn(
                'flex h-8 w-8 items-center justify-center rounded-full border-2 transition-colors',
                getColor(stageStatus)
              )}
            >
              {getIcon(stageStatus)}
            </div>
            <span className={cn(
              'text-sm font-medium',
              stageStatus ? 'text-gray-900' : 'text-gray-400'
            )}>
              {STAGE_LABELS[stage]}
            </span>
            {index < STAGES.length - 1 && (
              <div className="mx-2 h-px flex-1 bg-gray-200" />
            )}
          </div>
        );
      })}
    </div>
  );
}
