'use client';

import { useState } from 'react';
import { ChevronDown, ChevronUp, AlertTriangle, GitBranch } from 'lucide-react';
import { Card, Badge, Button } from '@/components/primitives';
import { cn } from '@/lib/utils';
import type { ConflictCluster as ConflictClusterType, EvidenceCard } from '@/types';

interface ConflictsTabProps {
  conflicts: ConflictClusterType[];
  evidence: EvidenceCard[];
}

export function ConflictsTab({ conflicts, evidence }: ConflictsTabProps) {
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const getEvidenceById = (id: string) => evidence.find((e) => e.evidence_id === id);

  if (conflicts.length === 0) {
    return (
      <div className="rounded-lg border border-gray-200 bg-white p-8 text-center">
        <GitBranch className="mx-auto h-12 w-12 text-gray-300" />
        <p className="mt-2 text-gray-500">No conflict clusters identified for this run.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900">Conflict Clusters</h3>
        <span className="text-sm text-gray-500">{conflicts.length} clusters</span>
      </div>

      <div className="space-y-3">
        {conflicts.map((cluster) => (
          <Card key={cluster.cluster_id} className="overflow-hidden">
            <button
              onClick={() =>
                setExpandedId(expandedId === cluster.cluster_id ? null : cluster.cluster_id)
              }
              className="w-full p-4 text-left"
            >
              <div className="flex items-start justify-between">
                <div className="min-w-0 flex-1">
                  <div className="mb-1 flex items-center gap-2">
                    <AlertTriangle className="h-4 w-4 text-amber-500" />
                    <h4 className="font-medium text-gray-900">{cluster.topic_axis}</h4>
                    <Badge
                      variant={
                        cluster.conflict_type === 'direct_conflict'
                          ? 'error'
                          : cluster.conflict_type === 'conditional_divergence'
                          ? 'warning'
                          : 'secondary'
                      }
                    >
                      {cluster.conflict_type.replace(/_/g, ' ')}
                    </Badge>
                  </div>
                  <p className="text-sm text-gray-600">{cluster.critic_summary}</p>
                </div>
                {expandedId === cluster.cluster_id ? (
                  <ChevronUp className="h-5 w-5 text-gray-400" />
                ) : (
                  <ChevronDown className="h-5 w-5 text-gray-400" />
                )}
              </div>
            </button>

            {expandedId === cluster.cluster_id && (
              <div className="border-t border-gray-200 bg-gray-50 p-4">
                <div className="grid gap-4 sm:grid-cols-2">
                  <div>
                    <h5 className="mb-2 text-sm font-medium text-emerald-700">
                      Supporting ({cluster.supporting_evidence_ids.length})
                    </h5>
                    <ul className="space-y-2">
                      {cluster.supporting_evidence_ids.slice(0, 5).map((id) => {
                        const ev = getEvidenceById(id);
                        return ev ? (
                          <li key={id} className="text-sm text-gray-600">
                            {ev.title}
                          </li>
                        ) : null;
                      })}
                    </ul>
                  </div>
                  <div>
                    <h5 className="mb-2 text-sm font-medium text-rose-700">
                      Conflicting ({cluster.conflicting_evidence_ids.length})
                    </h5>
                    <ul className="space-y-2">
                      {cluster.conflicting_evidence_ids.slice(0, 5).map((id) => {
                        const ev = getEvidenceById(id);
                        return ev ? (
                          <li key={id} className="text-sm text-gray-600">
                            {ev.title}
                          </li>
                        ) : null;
                      })}
                    </ul>
                  </div>
                </div>
                {cluster.likely_explanations.length > 0 && (
                  <div className="mt-4">
                    <h5 className="mb-2 text-sm font-medium text-gray-700">
                      Likely Explanations
                    </h5>
                    <ul className="list-inside list-disc space-y-1 text-sm text-gray-600">
                      {cluster.likely_explanations.map((exp, i) => (
                        <li key={i}>{exp}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </Card>
        ))}
      </div>
    </div>
  );
}
