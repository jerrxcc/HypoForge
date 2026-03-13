'use client';

import Link from 'next/link';
import { ArrowRight } from 'lucide-react';
import { Card, Badge } from '@/components/primitives';
import { formatDate, truncate } from '@/lib/utils';

interface RunCardProps {
  run: {
    run_id: string;
    topic: string;
    status: string;
    updated_at: string;
    selected_paper_count: number;
    evidence_card_count: number;
    hypothesis_count: number;
    error_message: string | null;
  };
}

export function RunCard({ run }: RunCardProps) {
  return (
    <Link href={`/dashboard/runs/${run.run_id}`}>
      <Card className="p-4 transition-shadow hover:shadow-md">
        <div className="flex items-start justify-between gap-4">
          <div className="min-w-0 flex-1">
            <div className="mb-2 flex items-center gap-2">
              <Badge
                variant={
                  run.status === 'done'
                    ? 'success'
                    : run.status === 'failed'
                    ? 'error'
                    : run.status === 'queued'
                    ? 'secondary'
                    : 'default'
                }
              >
                {run.status}
              </Badge>
              <span className="text-xs text-gray-400">
                {formatDate(run.updated_at)}
              </span>
            </div>
            <h3 className="truncate font-medium text-gray-900">
              {truncate(run.topic, 80)}
            </h3>
            <div className="mt-2 flex items-center gap-4 text-sm text-gray-500">
              <span>{run.selected_paper_count} papers</span>
              <span>{run.evidence_card_count} evidence</span>
              <span>{run.hypothesis_count} hypotheses</span>
            </div>
            {run.error_message && (
              <p className="mt-2 truncate text-sm text-rose-600">
                {run.error_message}
              </p>
            )}
          </div>
          <ArrowRight className="h-5 w-5 flex-shrink-0 text-gray-400" />
        </div>
      </Card>
    </Link>
  );
}
