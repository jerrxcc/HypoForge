'use client';

import { useState, useEffect } from 'react';

/**
 * Subscribes to a CSS media query and returns whether it currently matches.
 *
 * @example
 * const isMobile = useMediaQuery('(max-width: 768px)');
 */
export function useMediaQuery(query: string): boolean {
  const [matches, setMatches] = useState<boolean>(() => {
    if (typeof window === 'undefined') return false;
    return window.matchMedia(query).matches;
  });

  useEffect(() => {
    if (typeof window === 'undefined') return;

    const mediaQueryList = window.matchMedia(query);

    const handleChange = (event: MediaQueryListEvent) => {
      setMatches(event.matches);
    };

    // Use addEventListener when available (modern browsers), fall back to addListener
    if (mediaQueryList.addEventListener) {
      mediaQueryList.addEventListener('change', handleChange);
      return () => mediaQueryList.removeEventListener('change', handleChange);
    } else {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      (mediaQueryList as any).addListener(handleChange);
      return () => {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        (mediaQueryList as any).removeListener(handleChange);
      };
    }
  }, [query]);

  return matches;
}
