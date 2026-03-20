import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import type { RunStatus } from '@/types';

const ACTIVE_STATUSES: ReadonlySet<RunStatus> = new Set([
  'retrieving',
  'reviewing',
  'criticizing',
  'planning',
  'reflecting',
]);

function getVariant(status: RunStatus) {
  switch (status) {
    case 'done':
      return 'success' as const;
    case 'failed':
      return 'error' as const;
    case 'queued':
      return 'secondary' as const;
    default:
      return 'warning' as const;
  }
}

interface RunStatusBadgeProps {
  readonly status: RunStatus;
  readonly className?: string;
}

export function RunStatusBadge({ status, className }: RunStatusBadgeProps) {
  const isActive = ACTIVE_STATUSES.has(status);

  return (
    <Badge
      variant={getVariant(status)}
      className={cn(isActive && 'animate-pulse', className)}
    >
      {status}
    </Badge>
  );
}
