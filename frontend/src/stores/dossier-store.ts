import { create } from 'zustand';

export type ItemType = 'hypothesis' | 'conflict' | 'evidence' | 'paper';

interface DossierState {
  selectedType: ItemType | null;
  /**
   * Selected item ID:
   * - hypothesis → String(rank)
   * - conflict   → cluster_id
   * - evidence   → evidence_id
   * - paper      → paper_id
   */
  selectedId: string | null;
  searchQuery: string;
  expandedGroups: Record<string, boolean>;

  // Actions
  select: (type: ItemType, id: string) => void;
  clearSelection: () => void;
  setSearchQuery: (q: string) => void;
  toggleGroup: (group: string) => void;
  expandGroup: (group: string) => void;
  reset: () => void;
}

const DEFAULT_EXPANDED_GROUPS: Record<string, boolean> = {
  hypotheses: true,
  conflicts: true,
  evidence: true,
  papers: false,
};

const initialState: Pick<
  DossierState,
  'selectedType' | 'selectedId' | 'searchQuery' | 'expandedGroups'
> = {
  selectedType: null,
  selectedId: null,
  searchQuery: '',
  expandedGroups: DEFAULT_EXPANDED_GROUPS,
};

export const useDossierStore = create<DossierState>((set) => ({
  ...initialState,

  select: (type, id) =>
    set(() => ({ selectedType: type, selectedId: id })),

  clearSelection: () =>
    set(() => ({ selectedType: null, selectedId: null })),

  setSearchQuery: (q) =>
    set(() => ({ searchQuery: q })),

  toggleGroup: (group) =>
    set((state) => ({
      expandedGroups: {
        ...state.expandedGroups,
        [group]: !state.expandedGroups[group],
      },
    })),

  expandGroup: (group) =>
    set((state) => ({
      expandedGroups: {
        ...state.expandedGroups,
        [group]: true,
      },
    })),

  reset: () =>
    set(() => ({ ...initialState, expandedGroups: { ...DEFAULT_EXPANDED_GROUPS } })),
}));
