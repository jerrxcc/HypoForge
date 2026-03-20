import Link from 'next/link';
import { Card, CardContent } from '@/components/ui/card';
import { RunStatusBadge } from '@/components/run/run-status-badge';
import { formatDate } from '@/lib/utils';
import type { RunSummary } from '@/types';

interface RunCardProps {
  readonly run: RunSummary;
}

export function RunCard({ run }: RunCardProps) {
  return (
    <Link href={`/dashboard/runs/${run.run_id}`}>
      <Card className="transition-colors hover:border-primary/50">
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
