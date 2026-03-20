'use client';

import { FileText } from 'lucide-react';
import { ScrollArea } from '@/components/ui/scroll-area';
import { useDossierStore } from '@/stores/dossier-store';
import { HypothesisDetail } from './detail-views/hypothesis-detail';
import { ConflictDetail } from './detail-views/conflict-detail';
import { EvidenceDetail } from './detail-views/evidence-detail';
import { PaperDetailView } from './detail-views/paper-detail';
import type { RunResult } from '@/types';

interface DetailPanelProps {
  readonly run: RunResult;
}

export function DetailPanel({ run }: DetailPanelProps) {
  const selectedType = useDossierStore((s) => s.selectedType);
  const selectedId = useDossierStore((s) => s.selectedId);

  if (!selectedType || !selectedId) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-3 text-muted-foreground">
        <FileText className="size-10 opacity-40" />
        <p className="text-sm">Select an item from the left panel to view details</p>
      </div>
    );
  }

  const content = (() => {
    switch (selectedType) {
      case 'hypothesis': {
        const hypothesis = run.hypotheses.find((h) => String(h.rank) === selectedId);
        return hypothesis ? <HypothesisDetail hypothesis={hypothesis} /> : null;
      }
      case 'conflict': {
        const conflict = run.conflict_clusters.find((c) => c.cluster_id === selectedId);
        return conflict ? <ConflictDetail conflict={conflict} /> : null;
      }
      case 'evidence': {
        const evidence = run.evidence_cards.find((e) => e.evidence_id === selectedId);
        return evidence ? <EvidenceDetail evidence={evidence} /> : null;
      }
      case 'paper': {
        const paper = run.selected_papers.find((p) => p.paper_id === selectedId);
        return paper ? <PaperDetailView paper={paper} /> : null;
      }
      default:
        return null;
    }
  })();

  if (!content) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-3 text-muted-foreground">
        <FileText className="size-10 opacity-40" />
        <p className="text-sm">Item not found</p>
      </div>
    );
  }

  return (
    <ScrollArea className="h-full">
      {content}
    </ScrollArea>
  );
}
