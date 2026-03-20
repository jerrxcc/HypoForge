'use client';

import { useMemo } from 'react';
import { useRuns } from '@/hooks/use-runs';
import { Card, CardContent } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';

interface StatItemProps {
  readonly label: string;
  readonly value: number;
}

function StatItem({ label, value }: StatItemProps) {
  return (
    <Card className="flex-1 min-w-[120px]">
      <CardContent className="flex flex-col items-center gap-1 py-4">
        <span className="text-2xl font-semibold">{value.toLocaleString()}</span>
        <span className="text-xs text-muted-foreground">{label}</span>
      </CardContent>
    </Card>
  );
}

function StatSkeleton() {
  return (
    <Card className="flex-1 min-w-[120px]">
      <CardContent className="flex flex-col items-center gap-2 py-4">
        <Skeleton className="h-7 w-12" />
        <Skeleton className="h-3 w-16" />
      </CardContent>
    </Card>
  );
}

export function StatsBar() {
  const { data: runs, isLoading } = useRuns();

  const stats = useMemo(() => {
    if (!runs) return { totalRuns: 0, totalPapers: 0, totalHypotheses: 0 };
    return {
      totalRuns: runs.length,
      totalPapers: runs.reduce((sum, r) => sum + r.selected_paper_count, 0),
      totalHypotheses: runs.reduce((sum, r) => sum + r.hypothesis_count, 0),
    };
  }, [runs]);

  if (isLoading) {
    return (
      <div className="flex gap-4">
        <StatSkeleton />
        <StatSkeleton />
        <StatSkeleton />
      </div>
    );
  }

  return (
    <div className="flex gap-4">
      <StatItem label="Total Runs" value={stats.totalRuns} />
      <StatItem label="Total Papers" value={stats.totalPapers} />
      <StatItem label="Total Hypotheses" value={stats.totalHypotheses} />
    </div>
  );
}
