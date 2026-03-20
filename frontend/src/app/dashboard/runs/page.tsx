'use client';

import { useState } from 'react';
import { Search, Grid3X3, List } from 'lucide-react';
import { Input, Button, Badge } from '@/components/primitives';
import { useRuns } from '@/hooks/use-runs';
import { RunCard } from '@/components/run/run-card';
import { Loader2 } from 'lucide-react';

export default function RunsPage() {
  const { data: runs, isLoading, error } = useRuns();
  const [searchQuery, setSearchQuery] = useState('');
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('list');

  const filteredRuns = runs?.filter((run) =>
    run.topic.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">All Runs</h1>
          <p className="mt-1 text-gray-500">
            Browse and search your research runs.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="secondary">{runs?.length ?? 0} runs</Badge>
        </div>
      </div>

      <div className="flex items-center gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
          <Input
            placeholder="Search runs..."
            className="pl-10"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
        <div className="flex items-center rounded-lg border border-gray-200 bg-white p-1">
          <Button
            variant={viewMode === 'grid' ? 'secondary' : 'ghost'}
            size="sm"
            onClick={() => setViewMode('grid')}
          >
            <Grid3X3 className="h-4 w-4" />
          </Button>
          <Button
            variant={viewMode === 'list' ? 'secondary' : 'ghost'}
            size="sm"
            onClick={() => setViewMode('list')}
          >
            <List className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
        </div>
      ) : error ? (
        <div className="rounded-lg border border-rose-200 bg-rose-50 p-4 text-rose-700">
          Failed to load runs: {error.message}
        </div>
      ) : filteredRuns?.length === 0 ? (
        <div className="rounded-lg border border-gray-200 bg-white p-8 text-center">
          <p className="text-gray-500">
            {searchQuery
              ? 'No runs match your search.'
              : 'No runs yet. Create your first research run to get started.'}
          </p>
        </div>
      ) : (
        <div
          className={
            viewMode === 'grid'
              ? 'grid gap-4 sm:grid-cols-2 lg:grid-cols-3'
              : 'space-y-3'
          }
        >
          {filteredRuns?.map((run) => <RunCard key={run.run_id} run={run} />)}
        </div>
      )}
    </div>
  );
}
