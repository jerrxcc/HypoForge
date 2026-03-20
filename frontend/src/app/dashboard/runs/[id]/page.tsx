'use client';

import React from 'react';
import { usePollRun } from '@/hooks/use-poll-run';
import { Loader2, RefreshCw, FileText, Terminal, BarChart3 } from 'lucide-react';
import { Tabs, TabsList, TabsTrigger, TabsContent, Button, Badge, Card } from '@/components/primitives';
import { StageProgress } from '@/components/run/stage-progress';
import { PapersTab } from '@/components/dossier/papers-tab';
import { EvidenceTab } from '@/components/dossier/evidence-tab';
import { ConflictsTab } from '@/components/dossier/conflicts-tab';
import { HypothesesTab } from '@/components/dossier/hypotheses-tab';
import Link from 'next/link';
import type { RunStatus, StageSummary, EvidenceCard, ConflictCluster } from '@/types';

interface RunDetailPageProps {
  params: Promise<{ id: string }>;
}

export default function RunDetailPage({ params }: RunDetailPageProps) {
  return <RunDetailContent params={params} />;
}

function RunDetailContent({ params }: { params: Promise<{ id: string }> }) {
  const [resolvedParams, setResolvedParams] = React.useState<{ id: string } | null>(null);

  React.useEffect(() => {
    params.then(setResolvedParams);
  }, [params]);

  const { data: run, isLoading, error, refetch } = usePollRun(resolvedParams?.id ?? '');

  if (!resolvedParams) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
      </div>
    );
  }

  if (isLoading && !run) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-lg border border-rose-200 bg-rose-50 p-4 text-rose-700">
        Failed to load run: {error.message}
      </div>
    );
  }

  if (!run) {
    return (
      <div className="rounded-lg border border-gray-200 bg-white p-8 text-center">
        <p className="text-gray-500">Run not found.</p>
      </div>
    );
  }

  // Type assertions for API response
  const status = run.status as RunStatus;
  const stageSummaries = run.stage_summaries as StageSummary[];
  const evidenceCards = run.evidence_cards as EvidenceCard[];
  const conflictClusters = run.conflict_clusters as ConflictCluster[];
  const isActive = !['done', 'failed'].includes(status);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0 flex-1">
          <div className="mb-2 flex items-center gap-2">
            <Badge
              variant={
                status === 'done'
                  ? 'success'
                  : status === 'failed'
                  ? 'error'
                  : 'default'
              }
            >
              {status}
            </Badge>
            {isActive && (
              <span className="flex items-center gap-1 text-xs text-blue-600">
                <Loader2 className="h-3 w-3 animate-spin" />
                Processing...
              </span>
            )}
          </div>
          <h1 className="text-2xl font-bold text-gray-900">{run.topic}</h1>
        </div>

        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={() => refetch()}>
            <RefreshCw className="mr-2 h-4 w-4" />
            Refresh
          </Button>
          <Link href={`/dashboard/runs/${resolvedParams.id}/trace`}>
            <Button variant="outline" size="sm">
              <Terminal className="mr-2 h-4 w-4" />
              Trace
            </Button>
          </Link>
          <Link href={`/dashboard/runs/${resolvedParams.id}/report`}>
            <Button variant="outline" size="sm">
              <FileText className="mr-2 h-4 w-4" />
              Report
            </Button>
          </Link>
        </div>
      </div>

      {/* Stage Progress */}
      <Card className="p-6">
        <StageProgress status={status} stageSummaries={stageSummaries} />
      </Card>

      {/* Stats */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <Card className="p-4">
          <div className="text-sm text-gray-500">Papers</div>
          <div className="text-2xl font-semibold text-gray-900">
            {run.selected_papers.length}
          </div>
        </Card>
        <Card className="p-4">
          <div className="text-sm text-gray-500">Evidence</div>
          <div className="text-2xl font-semibold text-gray-900">
            {run.evidence_cards.length}
          </div>
        </Card>
        <Card className="p-4">
          <div className="text-sm text-gray-500">Conflicts</div>
          <div className="text-2xl font-semibold text-gray-900">
            {run.conflict_clusters.length}
          </div>
        </Card>
        <Card className="p-4">
          <div className="text-sm text-gray-500">Hypotheses</div>
          <div className="text-2xl font-semibold text-gray-900">
            {run.hypotheses.length}
          </div>
        </Card>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="papers">
        <TabsList>
          <TabsTrigger value="papers">
            <FileText className="mr-2 h-4 w-4" />
            Papers
          </TabsTrigger>
          <TabsTrigger value="evidence">
            <BarChart3 className="mr-2 h-4 w-4" />
            Evidence
          </TabsTrigger>
          <TabsTrigger value="conflicts">
            Conflicts
          </TabsTrigger>
          <TabsTrigger value="hypotheses">
            Hypotheses
          </TabsTrigger>
        </TabsList>

        <TabsContent value="papers">
          <PapersTab papers={run.selected_papers} />
        </TabsContent>
        <TabsContent value="evidence">
          <EvidenceTab evidence={evidenceCards} />
        </TabsContent>
        <TabsContent value="conflicts">
          <ConflictsTab conflicts={conflictClusters} evidence={evidenceCards} />
        </TabsContent>
        <TabsContent value="hypotheses">
          <HypothesesTab hypotheses={run.hypotheses} evidence={evidenceCards} />
        </TabsContent>
      </Tabs>
    </div>
  );
}
