'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { Search } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { useDossierStore } from '@/stores/dossier-store';

const DEBOUNCE_MS = 200;

export function SearchFilter() {
  const searchQuery = useDossierStore((s) => s.searchQuery);
  const setSearchQuery = useDossierStore((s) => s.setSearchQuery);
  const [localValue, setLocalValue] = useState(searchQuery);
  const timerRef = useRef<ReturnType<typeof setTimeout>>(undefined);

  useEffect(() => () => clearTimeout(timerRef.current), []);

  // Sync when store is externally reset (e.g. run change)
  const storeResetKey = searchQuery === '' ? 0 : 1;
  useEffect(() => {
    setLocalValue(''); // eslint-disable-line react-hooks/set-state-in-effect -- legitimate sync from external store reset
  }, [storeResetKey]);

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const value = e.target.value;
      setLocalValue(value);
      clearTimeout(timerRef.current);
      timerRef.current = setTimeout(() => setSearchQuery(value), DEBOUNCE_MS);
    },
    [setSearchQuery],
  );

  return (
    <div className="relative min-w-0">
      <Search aria-hidden="true" className="pointer-events-none absolute left-2.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
      <label htmlFor="dossier-filter" className="sr-only">Filter items</label>
      <Input
        id="dossier-filter"
        placeholder="Filter items..."
        value={localValue}
        onChange={handleChange}
        className="min-w-0 pl-9 text-sm"
      />
    </div>
  );
}
