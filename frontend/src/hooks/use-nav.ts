'use client';

import { useMemo } from 'react';
import type { NavItem } from '@/types';

export function useFilteredNavItems(items: NavItem[]) {
  return useMemo(() => items, [items]);
}
