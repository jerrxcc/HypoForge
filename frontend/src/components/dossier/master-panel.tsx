'use client';

import { useEffect, useCallback, useRef, useMemo } from 'react';
import { ScrollArea } from '@/components/ui/scroll-area';
import { useDossierStore } from '@/stores/dossier-store';
import { SearchFilter } from './search-filter';
import { ItemGroup } from './item-group';
import { HypothesisRow } from './master-items/hypothesis-row';
import { ConflictRow } from './master-items/conflict-row';
import { EvidenceRow } from './master-items/evidence-row';
import { PaperRow } from './master-items/paper-row';
import type { RunResult } from '@/types';

function matchesQuery(text: string | null | undefined, query: string): boolean {
  if (!text) return false;
  return text.toLowerCase().includes(query);
}

interface MasterPanelProps {
  readonly run: RunResult;
}

export function MasterPanel({ run }: MasterPanelProps) {
  const searchQuery = useDossierStore((s) => s.searchQuery);
  const selectedType = useDossierStore((s) => s.selectedType);
  const selectedId = useDossierStore((s) => s.selectedId);

  const refsMap = useRef(new Map<string, HTMLButtonElement>());

  const setRef = useCallback((key: string) => (el: HTMLButtonElement | null) => {
    if (el) {
      refsMap.current.set(key, el);
    } else {
      refsMap.current.delete(key);
    }
  }, []);

  // Scroll to selected item
  useEffect(() => {
    if (!selectedId || !selectedType) return;
    const key = `${selectedType}:${selectedId}`;
    const el = refsMap.current.get(key);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
  }, [selectedType, selectedId]);

  const lowerQuery = useMemo(() => searchQuery.toLowerCase(), [searchQuery]);

  const filtered = useMemo(() => {
    const sorted = [...run.hypotheses].sort((a, b) => a.rank - b.rank);
    const hypotheses = lowerQuery
      ? sorted.filter(
          (h) =>
            matchesQuery(h.title, lowerQuery) ||
            matchesQuery(h.hypothesis_statement, lowerQuery),
        )
      : sorted;
    const conflicts = lowerQuery
      ? run.conflict_clusters.filter((c) => matchesQuery(c.topic_axis, lowerQuery))
      : run.conflict_clusters;
    const evidence = lowerQuery
      ? run.evidence_cards.filter(
          (e) =>
            matchesQuery(e.title, lowerQuery) ||
            matchesQuery(e.claim_text, lowerQuery),
        )
      : run.evidence_cards;
    const papers = lowerQuery
      ? run.selected_papers.filter((p) => matchesQuery(p.title, lowerQuery))
      : run.selected_papers;
    return { hypotheses, conflicts, evidence, papers };
  }, [run.hypotheses, run.conflict_clusters, run.evidence_cards, run.selected_papers, lowerQuery]);

  const { hypotheses: filteredHypotheses, conflicts: filteredConflicts, evidence: filteredEvidence, papers: filteredPapers } = filtered;

  return (
    <ScrollArea className="h-full">
      <div className="flex flex-col gap-2 p-3">
        <SearchFilter />

        {filteredHypotheses.length > 0 && (
          <ItemGroup groupKey="hypotheses" label="Hypotheses" count={filteredHypotheses.length}>
            {filteredHypotheses.map((h) => (
              <div key={h.rank} className="animate-[fade-in_0.15s_ease-out]">
                <HypothesisRow
                  ref={setRef(`hypothesis:${h.rank}`)}
                  hypothesis={h}
                  isSelected={selectedType === 'hypothesis' && selectedId === String(h.rank)}
                />
              </div>
            ))}
          </ItemGroup>
        )}

        {filteredConflicts.length > 0 && (
          <ItemGroup groupKey="conflicts" label="Conflicts" count={filteredConflicts.length}>
            {filteredConflicts.map((c) => (
              <div key={c.cluster_id} className="animate-[fade-in_0.15s_ease-out]">
                <ConflictRow
                  ref={setRef(`conflict:${c.cluster_id}`)}
                  conflict={c}
                  isSelected={selectedType === 'conflict' && selectedId === c.cluster_id}
                />
              </div>
            ))}
          </ItemGroup>
        )}

        {filteredEvidence.length > 0 && (
          <ItemGroup groupKey="evidence" label="Evidence" count={filteredEvidence.length}>
            {filteredEvidence.map((e) => (
              <div key={e.evidence_id} className="animate-[fade-in_0.15s_ease-out]">
                <EvidenceRow
                  ref={setRef(`evidence:${e.evidence_id}`)}
                  evidence={e}
                  isSelected={selectedType === 'evidence' && selectedId === e.evidence_id}
                />
              </div>
            ))}
          </ItemGroup>
        )}

        {filteredPapers.length > 0 && (
          <ItemGroup groupKey="papers" label="Papers" count={filteredPapers.length}>
            {filteredPapers.map((p) => (
              <div key={p.paper_id} className="animate-[fade-in_0.15s_ease-out]">
                <PaperRow
                  ref={setRef(`paper:${p.paper_id}`)}
                  paper={p}
                  isSelected={selectedType === 'paper' && selectedId === p.paper_id}
                />
              </div>
            ))}
          </ItemGroup>
        )}

        <div aria-live="polite" aria-atomic="true" className="sr-only">
          {lowerQuery && `${filteredHypotheses.length + filteredConflicts.length + filteredEvidence.length + filteredPapers.length} results`}
        </div>
        {lowerQuery &&
          filteredHypotheses.length === 0 &&
          filteredConflicts.length === 0 &&
          filteredEvidence.length === 0 &&
          filteredPapers.length === 0 && (
            <p className="py-8 text-center text-sm text-muted-foreground">
              No hypotheses, evidence, or conflicts match &ldquo;{searchQuery}&rdquo;
            </p>
          )}
      </div>
    </ScrollArea>
  );
}
