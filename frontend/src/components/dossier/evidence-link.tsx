'use client';

import { useDossierStore } from '@/stores/dossier-store';
import { Badge } from '@/components/ui/badge';

const STYLE = {
  default: 'cursor-pointer font-mono text-xs hover:bg-primary/10 hover:text-primary transition-colors focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none',
  counter: 'cursor-pointer font-mono text-xs border-destructive/40 text-destructive hover:bg-destructive/10 transition-colors focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none',
} as const;

interface EvidenceLinkProps {
  readonly evidenceId: string;
  readonly variant?: 'default' | 'counter';
}

export function EvidenceLink({ evidenceId, variant = 'default' }: EvidenceLinkProps) {
  const select = useDossierStore((s) => s.select);
  const expandGroup = useDossierStore((s) => s.expandGroup);

  function handleClick() {
    expandGroup('evidence');
    select('evidence', evidenceId);
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      handleClick();
    }
  }

  return (
    <Badge
      role="button"
      tabIndex={0}
      aria-label={`View evidence ${evidenceId}`}
      variant="outline"
      className={STYLE[variant]}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
    >
      {evidenceId}
    </Badge>
  );
}

export function PaperLink({ paperId }: { readonly paperId: string }) {
  const select = useDossierStore((s) => s.select);
  const expandGroup = useDossierStore((s) => s.expandGroup);

  function handleClick() {
    expandGroup('papers');
    select('paper', paperId);
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      handleClick();
    }
  }

  return (
    <Badge
      role="button"
      tabIndex={0}
      aria-label={`View paper ${paperId}`}
      variant="outline"
      className={STYLE.default}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
    >
      {paperId}
    </Badge>
  );
}
