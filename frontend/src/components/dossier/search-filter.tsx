'use client';

import { useCallback } from 'react';
import { Search } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { useDossierStore } from '@/stores/dossier-store';

export function SearchFilter() {
  const searchQuery = useDossierStore((s) => s.searchQuery);
  const setSearchQuery = useDossierStore((s) => s.setSearchQuery);

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      setSearchQuery(e.target.value);
    },
    [setSearchQuery],
  );

  return (
    <div className="relative">
      <Search aria-hidden="true" className="pointer-events-none absolute left-2.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
      <label htmlFor="dossier-filter" className="sr-only">Filter items</label>
      <Input
        id="dossier-filter"
        placeholder="Filter items..."
        value={searchQuery}
        onChange={handleChange}
        className="pl-9 text-sm"
      />
    </div>
  );
}
