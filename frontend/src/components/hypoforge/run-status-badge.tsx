import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import type { RunStatus } from '@/lib/hypoforge';

const statusClasses: Record<RunStatus, string> = {
  queued: 'bg-muted text-muted-foreground border-border',
  retrieving: 'bg-primary/10 text-primary border-primary/20',
  reviewing: 'bg-primary/10 text-primary border-primary/20',
  criticizing: 'bg-chart-3/20 text-foreground border-chart-3/30',
  planning: 'bg-chart-2/20 text-foreground border-chart-2/30',
  done: 'bg-emerald-100 text-emerald-900 border-emerald-200',
  failed: 'bg-destructive/12 text-destructive border-destructive/25'
};

const statusLabels: Record<RunStatus, string> = {
  queued: 'Queued',
  retrieving: 'Retrieval',
  reviewing: 'Review',
  criticizing: 'Critic',
  planning: 'Planner',
  done: 'Done',
  failed: 'Failed'
};

export function RunStatusBadge({ status }: { status: RunStatus }) {
  return (
    <Badge
      variant='outline'
      className={cn(
        'rounded-full px-3 py-1 font-medium tracking-[0.08em] uppercase',
        statusClasses[status]
      )}
    >
      {statusLabels[status]}
    </Badge>
  );
}
