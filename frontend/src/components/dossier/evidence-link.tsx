'use client';

import { useCallback } from 'react';
import { useDossierStore } from '@/stores/dossier-store';

const STYLE = {
  default: 'inline-flex max-w-full items-center rounded-full border px-2 py-0.5 text-left font-mono text-xs whitespace-normal [overflow-wrap:anywhere] transition-colors hover:bg-primary/10 hover:text-primary focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none',
  counter: 'inline-flex max-w-full items-center rounded-full border border-destructive/40 px-2 py-0.5 text-left font-mono text-xs text-destructive whitespace-normal [overflow-wrap:anywhere] transition-colors hover:bg-destructive/10 focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none',
} as const;

interface EvidenceLinkProps {
  readonly evidenceId: string;
  readonly variant?: 'default' | 'counter';
}

export function EvidenceLink({ evidenceId, variant = 'default' }: EvidenceLinkProps) {
  const select = useDossierStore((s) => s.select);
  const expandGroup = useDossierStore((s) => s.expandGroup);

  const handleClick = useCallback(() => {
    expandGroup('evidence');
    select('evidence', evidenceId);
  }, [expandGroup, select, evidenceId]);

  return (
    <button
      type="button"
      aria-label={`View evidence ${evidenceId}`}
      className={STYLE[variant]}
      onClick={handleClick}
    >
      {evidenceId}
    </button>
  );
}

export function PaperLink({ paperId }: { readonly paperId: string }) {
  const select = useDossierStore((s) => s.select);
  const expandGroup = useDossierStore((s) => s.expandGroup);

  const handleClick = useCallback(() => {
    expandGroup('papers');
    select('paper', paperId);
  }, [expandGroup, select, paperId]);

  return (
    <button
      type="button"
      aria-label={`View paper ${paperId}`}
      className={STYLE.default}
      onClick={handleClick}
    >
      {paperId}
    </button>
  );
}
