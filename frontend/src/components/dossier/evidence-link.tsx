'use client';

import { useDossierStore } from '@/stores/dossier-store';
import { Badge } from '@/components/ui/badge';

export function EvidenceLink({ evidenceId }: { readonly evidenceId: string }) {
  const select = useDossierStore((s) => s.select);
  const expandGroup = useDossierStore((s) => s.expandGroup);

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      expandGroup('evidence');
      select('evidence', evidenceId);
    }
  }

  return (
    <Badge
      role="button"
      tabIndex={0}
      variant="outline"
      className="cursor-pointer font-mono text-xs hover:bg-primary/10 hover:text-primary transition-colors"
      onClick={() => {
        expandGroup('evidence');
        select('evidence', evidenceId);
      }}
      onKeyDown={handleKeyDown}
    >
      {evidenceId}
    </Badge>
  );
}

export function PaperLink({ paperId }: { readonly paperId: string }) {
  const select = useDossierStore((s) => s.select);
  const expandGroup = useDossierStore((s) => s.expandGroup);

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      expandGroup('papers');
      select('paper', paperId);
    }
  }

  return (
    <Badge
      role="button"
      tabIndex={0}
      variant="outline"
      className="cursor-pointer font-mono text-xs hover:bg-primary/10 hover:text-primary transition-colors"
      onClick={() => {
        expandGroup('papers');
        select('paper', paperId);
      }}
      onKeyDown={handleKeyDown}
    >
      {paperId}
    </Badge>
  );
}
