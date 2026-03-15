'use client';

import { useState } from 'react';
import { Search, GitBranch } from 'lucide-react';
import { Card, Input, Badge } from '@/components/primitives';
import { truncate } from '@/lib/utils';
import type { EvidenceCard as EvidenceCardType } from '@/types';

interface EvidenceTabProps {
  evidence: EvidenceCardType[];
}

export function EvidenceTab({ evidence }: EvidenceTabProps) {
  const [searchQuery, setSearchQuery] = useState('');

  const filteredEvidence = evidence.filter(
    (e) =>
      e.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      e.claim_text.toLowerCase().includes(searchQuery.toLowerCase())
  );

  if (evidence.length === 0) {
    return (
      <div className="rounded-lg border border-gray-200 bg-white p-8 text-center">
        <GitBranch className="mx-auto h-12 w-12 text-gray-300" />
        <p className="mt-2 text-gray-500">No evidence cards extracted for this run.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900">Evidence Cards</h3>
        <span className="text-sm text-gray-500">{evidence.length} cards</span>
      </div>

      <div className="relative">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
        <Input
          placeholder="Search evidence..."
          className="pl-10"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
      </div>

      <div className="space-y-3">
        {filteredEvidence.map((e) => (
          <Card key={e.evidence_id} className="p-4">
            <div className="flex items-start justify-between gap-4">
              <div className="min-w-0 flex-1">
                <div className="mb-1 flex items-center gap-2">
                  <h4 className="font-medium text-gray-900">{e.title}</h4>
                  <Badge
                    variant={
                      e.direction === 'positive'
                        ? 'success'
                        : e.direction === 'negative'
                        ? 'error'
                        : 'secondary'
                    }
                  >
                    {e.direction}
                  </Badge>
                </div>
                <p className="text-sm text-gray-600">{truncate(e.claim_text, 200)}</p>
                <div className="mt-2 flex flex-wrap gap-2 text-xs text-gray-500">
                  <span>System: {e.system_or_material}</span>
                  <span>·</span>
                  <span>Intervention: {e.intervention}</span>
                  <span>·</span>
                  <span>Confidence: {(e.confidence * 100).toFixed(0)}%</span>
                </div>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
