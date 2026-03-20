'use client';

import { useEffect, useCallback, useRef, useMemo } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { ScrollArea } from '@/components/ui/scroll-area';
import { useDossierStore } from '@/stores/dossier-store';
import { SearchFilter } from './search-filter';
import { ItemGroup } from './item-group';
import { HypothesisRow } from './master-items/hypothesis-row';
import { ConflictRow } from './master-items/conflict-row';
import { EvidenceRow } from './master-items/evidence-row';
import { PaperRow } from './master-items/paper-row';
import type { RunResult } from '@/types';

const MOTION_ITEM = {
  initial: { opacity: 0, y: 8 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -4 },
  transition: { duration: 0.15 },
} as const;

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
            <AnimatePresence initial={false}>
              {filteredHypotheses.map((h) => (
                <motion.div key={h.rank} {...MOTION_ITEM}>
                  <HypothesisRow
                    ref={setRef(`hypothesis:${h.rank}`)}
                    hypothesis={h}
                    isSelected={selectedType === 'hypothesis' && selectedId === String(h.rank)}
                  />
                </motion.div>
              ))}
            </AnimatePresence>
          </ItemGroup>
        )}

        {filteredConflicts.length > 0 && (
          <ItemGroup groupKey="conflicts" label="Conflicts" count={filteredConflicts.length}>
            <AnimatePresence initial={false}>
              {filteredConflicts.map((c) => (
                <motion.div key={c.cluster_id} {...MOTION_ITEM}>
                  <ConflictRow
                    ref={setRef(`conflict:${c.cluster_id}`)}
                    conflict={c}
                    isSelected={selectedType === 'conflict' && selectedId === c.cluster_id}
                  />
                </motion.div>
              ))}
            </AnimatePresence>
          </ItemGroup>
        )}

        {filteredEvidence.length > 0 && (
          <ItemGroup groupKey="evidence" label="Evidence" count={filteredEvidence.length}>
            <AnimatePresence initial={false}>
              {filteredEvidence.map((e) => (
                <motion.div key={e.evidence_id} {...MOTION_ITEM}>
                  <EvidenceRow
                    ref={setRef(`evidence:${e.evidence_id}`)}
                    evidence={e}
                    isSelected={selectedType === 'evidence' && selectedId === e.evidence_id}
                  />
                </motion.div>
              ))}
            </AnimatePresence>
          </ItemGroup>
        )}

        {filteredPapers.length > 0 && (
          <ItemGroup groupKey="papers" label="Papers" count={filteredPapers.length}>
            <AnimatePresence initial={false}>
              {filteredPapers.map((p) => (
                <motion.div key={p.paper_id} {...MOTION_ITEM}>
                  <PaperRow
                    ref={setRef(`paper:${p.paper_id}`)}
                    paper={p}
                    isSelected={selectedType === 'paper' && selectedId === p.paper_id}
                  />
                </motion.div>
              ))}
            </AnimatePresence>
          </ItemGroup>
        )}

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
