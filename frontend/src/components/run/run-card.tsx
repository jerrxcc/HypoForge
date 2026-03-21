import Link from 'next/link';
import { Card, CardContent } from '@/components/ui/card';
import { RunStatusBadge } from '@/components/run/run-status-badge';
import { formatDate, cn } from '@/lib/utils';
import type { RunSummary } from '@/types';

function statusAccent(status: string): string {
  switch (status) {
    case 'failed':
      return 'border-l-2 border-l-destructive';
    case 'running':
      return 'border-l-2 border-l-primary';
    case 'degraded':
      return 'border-l-2 border-l-warning';
    default:
      return '';
  }
}

interface RunCardProps {
  readonly run: RunSummary;
}

export function RunCard({ run }: RunCardProps) {
  return (
    <Link href={`/dashboard/runs/${run.run_id}`} aria-label={run.topic}>
      <Card className={cn(
        'transition-all hover:border-primary/30 dark:hover:border-primary/40 hover:shadow-md',
        statusAccent(run.status),
      )}>
        <CardContent className="flex flex-col gap-3 py-4">
          {/* Top row: topic + status */}
          <div className="flex items-start justify-between gap-2">
            <span className="font-medium leading-tight line-clamp-2">
              {run.topic}
            </span>
            <RunStatusBadge status={run.status} />
          </div>

          {/* Counts */}
          <p className="text-sm text-muted-foreground">
            {run.selected_paper_count} papers &middot;{' '}
            {run.evidence_card_count} evidence &middot;{' '}
            {run.hypothesis_count} hypotheses
          </p>

          {/* Timestamp */}
          <span className="text-xs text-muted-foreground">
            {formatDate(run.updated_at)}
          </span>
        </CardContent>
      </Card>
    </Link>
  );
}
