'use client';

import { useState } from 'react';
import { FileText } from 'lucide-react';
import { PaperCard } from './paper-card';
import { PaperDetailModal } from './paper-detail-modal';
import type { PaperDetail } from '@/types';

interface PapersTabProps {
  papers: PaperDetail[];
}

export function PapersTab({ papers }: PapersTabProps) {
  const [selectedPaper, setSelectedPaper] = useState<PaperDetail | null>(null);

  if (papers.length === 0) {
    return (
      <div className="rounded-lg border border-gray-200 bg-white p-8 text-center">
        <FileText className="mx-auto h-12 w-12 text-gray-300" />
        <p className="mt-2 text-gray-500">No papers selected for this run.</p>
      </div>
    );
  }

  return (
    <>
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900">Selected Papers</h3>
        <span className="text-sm text-gray-500">{papers.length} papers</span>
      </div>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {papers.map((paper) => (
          <PaperCard
            key={paper.paper_id}
            paper={paper}
            onClick={() => setSelectedPaper(paper)}
          />
        ))}
      </div>
      <PaperDetailModal
        paper={selectedPaper}
        open={!!selectedPaper}
        onOpenChange={(open) => !open && setSelectedPaper(null)}
      />
    </>
  );
}
