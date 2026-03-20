'use client';

import { useState, useMemo } from 'react';
import Link from 'next/link';
import { Search, Plus } from 'lucide-react';
import { useRuns } from '@/hooks/use-runs';
import { RunCard } from '@/components/run/run-card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { Card, CardContent } from '@/components/ui/card';

function RunCardSkeleton() {
  return (
    <Card>
      <CardContent className="flex flex-col gap-3 py-4">
        <div className="flex items-start justify-between gap-2">
          <Skeleton className="h-5 w-3/4" />
          <Skeleton className="h-5 w-16 rounded-full" />
        </div>
        <Skeleton className="h-4 w-1/2" />
        <Skeleton className="h-3 w-24" />
      </CardContent>
    </Card>
  );
}

export default function RunsPage() {
  const { data: runs, isLoading } = useRuns();
  const [search, setSearch] = useState('');

  const filteredRuns = useMemo(() => {
    if (!runs) return [];
    if (!search.trim()) return runs;
    const lower = search.toLowerCase();
    return runs.filter((r) => r.topic.toLowerCase().includes(lower));
  }, [runs, search]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Your Runs</h1>
        <Button asChild>
          <Link href="/dashboard">
            <Plus className="size-4" />
            New Run
          </Link>
        </Button>
      </div>

      {/* Search */}
      <div className="relative max-w-md">
        <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          placeholder="Search by topic..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="pl-10"
        />
      </div>

      {/* Grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }, (_, i) => (
            <RunCardSkeleton key={i} />
          ))}
        </div>
      ) : filteredRuns.length === 0 ? (
        <div className="flex flex-col items-center gap-3 py-16 text-center">
          <p className="text-muted-foreground">
            {search
              ? `No runs match "${search}". Try a different keyword or clear the search.`
              : 'You haven\u2019t run any research yet.'}
          </p>
          {!search && (
            <Button asChild variant="outline">
              <Link href="/dashboard">Start your first run</Link>
            </Button>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
          {filteredRuns.map((run) => (
            <RunCard key={run.run_id} run={run} />
          ))}
        </div>
      )}
    </div>
  );
}
