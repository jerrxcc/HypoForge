'use client';

import Link from 'next/link';
import { ArrowRight, Loader2 } from 'lucide-react';
import { Card, Badge, Button } from '@/components/primitives';
import { useRuns } from '@/hooks/use-runs';
import { formatDate, truncate, getStatusColor } from '@/lib/utils';
import { STAGE_LABELS } from '@/lib/constants';

export function RecentRuns() {
  const { data: runs, isLoading, error } = useRuns();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-lg border border-rose-200 bg-rose-50 p-4 text-rose-700">
        Failed to load runs: {error.message}
      </div>
    );
  }

  const recentRuns = runs?.slice(0, 5) ?? [];

  if (recentRuns.length === 0) {
    return (
      <Card className="p-8 text-center">
        <p className="text-gray-500">No runs yet. Create your first research run to get started.</p>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-900">Recent Runs</h2>
        <Link href="/dashboard/runs">
          <Button variant="ghost" size="sm">
            View all
            <ArrowRight className="ml-1 h-4 w-4" />
          </Button>
        </Link>
      </div>

      <div className="space-y-3">
        {recentRuns.map((run) => (
          <Link key={run.run_id} href={`/dashboard/runs/${run.run_id}`}>
            <Card className="p-4 transition-shadow hover:shadow-md">
              <div className="flex items-start justify-between gap-4">
                <div className="min-w-0 flex-1">
                  <div className="mb-1 flex items-center gap-2">
                    <Badge
                      variant={
                        run.status === 'done'
                          ? 'success'
                          : run.status === 'failed'
                          ? 'error'
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
                    {truncate(run.topic, 60)}
                  </h3>
                  <div className="mt-2 flex items-center gap-4 text-sm text-gray-500">
                    <span>{run.selected_paper_count} papers</span>
                    <span>{run.evidence_card_count} evidence</span>
                    <span>{run.hypothesis_count} hypotheses</span>
                  </div>
                </div>
                <ArrowRight className="h-5 w-5 text-gray-400" />
              </div>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}
