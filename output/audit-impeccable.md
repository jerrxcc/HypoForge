# HypoForge Frontend Audit Report — Impeccable Standard

**Date**: 2026-03-21
**Branch**: `feature/frontend-v3`
**Scope**: All 82 frontend files (`frontend/src/`)
**Standard**: WCAG 2.1 AA + frontend-design anti-pattern checklist

---

## Anti-Patterns Verdict

**PASS.** This does **not** look AI-generated.

The codebase deliberately avoids every major AI slop tell:
- **Warm terracotta palette** (`rgb(217 119 86)`) — no cyan-on-dark, no purple-to-blue gradients
- **Tinted neutrals** — background `rgb(250 246 241)` (warm cream), dark mode `rgb(42 37 32)` (warm brown), never pure black/white in custom tokens
- **No gradient text**, no glassmorphism-as-decoration (only functional `backdrop-blur` on sticky nav)
- **No hero metrics** layout, no identical card grids, no bounce/elastic easing
- **DM Sans + JetBrains Mono** — intentional pairing, monospace only for actual identifiers
- **Button hierarchy** applied correctly — primary for CTAs, ghost for back, outline for secondary
- **Asymmetric layouts** — 320px sidebar + flex detail panel, not centered everything
- **Spacing rhythm** — `gap-1.5` / `gap-2` / `gap-3` / `gap-5` / `gap-12` with clear hierarchy

**Minor anti-pattern residue** (3 instances in UI primitives):
- `bg-black/50` in dialog overlay — should be tinted (`globals.css` line 58, `dialog.tsx`)
- `bg-white` on slider thumb — should be `bg-background` (`slider.tsx:56`)
- `text-white` on destructive button — should use `text-destructive-foreground` (`button.tsx:14`)

---

## Executive Summary

| Severity | Count |
|----------|-------|
| Critical | 2 |
| High | 6 |
| Medium | 15 |
| Low | 8 |
| **Total** | **31** |

**Top 5 issues:**
1. Badge `<span>` used as button without semantic element (a11y, Critical)
2. Missing `aria-live` on StageProgress for dynamic updates (a11y, Critical)
3. Missing `staleTime` on `useReport`, `useTrace`, `useRun` hooks (perf, High)
4. Search filter updates store on every keystroke without debounce (perf, High)
5. Motion library (~40KB) used for simple opacity/translate animations (perf, High)

**Quality score**: 8.2/10 — solid foundation, needs accessibility hardening and minor perf tuning.

---

## Detailed Findings

### Critical Issues

#### C1. Badge-as-button missing semantic element
- **Location**: `components/dossier/evidence-link.tsx:32-44`, also `PaperLink:63-75`
- **Category**: Accessibility
- **Description**: `<Badge>` renders a `<span>` but receives `role="button"` + `tabIndex={0}`. Screen readers announce it inconsistently compared to native `<button>`.
- **Impact**: Keyboard/screen reader users get degraded experience.
- **WCAG**: 4.1.2 Name, Role, Value
- **Recommendation**: Use `<button>` element directly or wrap Badge with `asChild` pointing to a `<button>`.
- **Suggested command**: `/harden`

#### C2. Missing aria-live on StageProgress
- **Location**: `components/run/stage-progress.tsx:92`
- **Category**: Accessibility
- **Description**: Pipeline stages update dynamically during a run but have no `aria-live` region. Screen readers don't announce status transitions.
- **Impact**: Blind users cannot track pipeline progress.
- **WCAG**: 4.1.3 Status Messages
- **Recommendation**: Add `aria-live="polite"` to the `<ol>`.
- **Suggested command**: `/harden`

---

### High-Severity Issues

#### H1. Missing staleTime across query hooks
- **Location**: `hooks/use-report.ts`, `hooks/use-trace.ts`, `hooks/use-run.ts`
- **Category**: Performance
- **Description**: No `staleTime` set (defaults to 0). Every tab switch or focus regain triggers a refetch. `useRuns` correctly sets `staleTime: 30_000` but sibling hooks don't.
- **Impact**: Unnecessary network requests, slower perceived navigation.
- **Recommendation**: Set `staleTime: 60_000` for `useRun`, `staleTime: Infinity` for `useReport`/`useTrace` (immutable after generation).
- **Suggested command**: `/optimize`

#### H2. Search filter missing debounce
- **Location**: `components/dossier/search-filter.tsx:12-16`
- **Category**: Performance
- **Description**: Updates Zustand store on every keystroke. MasterPanel recomputes `toLowerCase()` + filters all 4 item arrays (hypotheses, conflicts, evidence, papers) per character.
- **Impact**: Janky typing on large dossiers (36 papers + dozens of evidence cards).
- **Recommendation**: Add 200-300ms debounce before `setSearchQuery`.
- **Suggested command**: `/optimize`

#### H3. Motion library overhead for simple animations
- **Location**: `components/dossier/master-panel.tsx:4`
- **Category**: Performance
- **Description**: `motion/react` (Framer Motion, ~40KB gzipped) imported for `AnimatePresence` on list items with simple `opacity: 0→1, y: 8→0` transitions (0.15s). CSS can do this natively.
- **Impact**: Bundle bloat; JS-driven animations on potentially 100+ list items.
- **Recommendation**: Replace with CSS `@starting-style` or Tailwind `animate-*` classes. Remove motion dependency entirely if unused elsewhere.
- **Suggested command**: `/optimize`

#### H4. Barrel export in UI index
- **Location**: `components/ui/index.ts:1`
- **Category**: Performance
- **Description**: `export *` from single barrel file. While modern bundlers tree-shake, this pattern can defeat tree-shaking in edge cases and makes dependency tracking harder.
- **Impact**: Potential unused Radix primitives in bundle.
- **Recommendation**: Use direct path imports (`@/components/ui/button`) throughout — which the codebase already does. Delete the barrel file if unused.
- **Suggested command**: `/optimize`

#### H5. Dossier shell fixed panel widths
- **Location**: `components/dossier/dossier-shell.tsx:65-68`
- **Category**: Responsive
- **Description**: Desktop master panel uses `w-[320px] shrink-0 lg:w-[380px]` with `shrink-0`. On medium screens (768-1024px), this leaves limited space for the detail panel.
- **Impact**: Cramped detail view on tablet-landscape.
- **Recommendation**: Use ratio-based widths (`w-2/5 max-w-[380px]`) or clamp.
- **Suggested command**: `/adapt`

#### H6. Magic number height calculations
- **Location**: `dossier-shell.tsx:66` (`h-[calc(100vh-280px)]`), `trace-shell.tsx:51` (`h-[calc(100dvh-var(--nav-height,56px)-164px)]`)
- **Category**: Responsive
- **Description**: Hard-coded pixel offsets (280px, 164px) are fragile — any layout change breaks them.
- **Impact**: Height mismatch if breadcrumb/action bar changes.
- **Recommendation**: Use flex layout (`flex-1 min-h-0`) instead of calc-based heights.
- **Suggested command**: `/adapt`

---

### Medium-Severity Issues

#### M1. Pervasive `text-[10px]` font size
- **Location**: `master-items/paper-row.tsx:48,53`, `evidence-row.tsx:49`, `hypothesis-row.tsx:52`, `conflict-row.tsx:54`, `trace-list.tsx:48`, `item-group.tsx:34`
- **Category**: Responsive / A11y
- **Description**: 10px is below WCAG minimum recommended text size and doesn't scale with user font preferences.
- **Recommendation**: Replace with `text-xs` (12px / 0.75rem).
- **Suggested command**: `/normalize`

#### M2. Progress bar aria-label lacks numeric value
- **Location**: `detail-views/hypothesis-detail.tsx:23`
- **Category**: Accessibility
- **Description**: ScoreBar `aria-label` is just the label name (e.g., "Novelty"). Screen readers don't hear the actual score value without reading the visual number.
- **Recommendation**: `aria-label={\`${label}: ${score.toFixed(2)} out of 1\`}`
- **Suggested command**: `/harden`

#### M3. CollapsibleTrigger missing focus-visible
- **Location**: `components/dossier/item-group.tsx:26`
- **Category**: Accessibility
- **Description**: No `focus-visible:ring-*` classes on the collapsible trigger. Keyboard users can't see focus position.
- **Recommendation**: Add `focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none`.
- **Suggested command**: `/harden`

#### M4. Constraint slider re-renders entire form
- **Location**: `components/run/constraint-fields.tsx:35-46`
- **Category**: Performance
- **Description**: `watch('novelty_weight')` causes full component re-render on every slider tick. Debounce is 100ms but `watch` still triggers React re-renders.
- **Recommendation**: Use `useWatch` with isolated subscription, or extract slider into sub-component.
- **Suggested command**: `/optimize`

#### M5. Zustand multi-selector in MasterPanel
- **Location**: `components/dossier/master-panel.tsx:32-34`
- **Category**: Performance
- **Description**: Three separate `useDossierStore` calls create three independent subscriptions, each potentially causing re-renders.
- **Recommendation**: Combine into single selector returning an object (with `useShallow` from zustand).
- **Suggested command**: `/optimize`

#### M6. Prose typography not responsive
- **Location**: `components/report/markdown-renderer.tsx:11`
- **Category**: Responsive
- **Description**: `prose` has fixed sizing. On mobile, line lengths may be too wide and font sizes suboptimal.
- **Recommendation**: Add `prose-sm sm:prose` and reduce padding `p-4 sm:p-6`.
- **Suggested command**: `/adapt`

#### M7. Fixed label widths in detail views
- **Location**: `hypothesis-detail.tsx:20` (`w-20`), `trace-detail.tsx:21` (`w-32`)
- **Category**: Responsive
- **Description**: Hard-coded label widths may truncate on narrow screens.
- **Recommendation**: Use `min-w-fit` or responsive variants `w-16 sm:w-20`.
- **Suggested command**: `/adapt`

#### M8. Stats bar gap not optimized for mobile
- **Location**: `components/dashboard/stats-bar.tsx:59`
- **Category**: Responsive
- **Description**: `flex flex-wrap gap-4` doesn't tighten on mobile.
- **Recommendation**: `gap-2 sm:gap-4`.
- **Suggested command**: `/adapt`

#### M9. Recent runs strip lacks scroll indicators
- **Location**: `components/dashboard/recent-runs-strip.tsx:62`
- **Category**: UX
- **Description**: Horizontal scroll with hidden scrollbar provides no visual hint that more content exists.
- **Recommendation**: Add fade mask overlay or visible scroll dots.
- **Suggested command**: `/delight`

#### M10. `bg-black/50` in dialog overlay
- **Location**: `components/ui/dialog.tsx` (DialogOverlay)
- **Category**: Theming
- **Description**: Pure black overlay breaks warm tinting philosophy.
- **Recommendation**: Use `bg-foreground/50` or `bg-[rgb(42_37_32_/_0.5)]`.
- **Suggested command**: `/normalize`

#### M11. `bg-white` on slider thumb
- **Location**: `components/ui/slider.tsx:56`
- **Category**: Theming
- **Description**: Hard-coded `bg-white` doesn't respect dark mode theme.
- **Recommendation**: Use `bg-background`.
- **Suggested command**: `/normalize`

#### M12. `text-white` on destructive button
- **Location**: `components/ui/button.tsx:14`
- **Category**: Theming
- **Description**: Uses literal `text-white` instead of `text-destructive-foreground` token.
- **Recommendation**: Use the token.
- **Suggested command**: `/normalize`

#### M13. Missing heading elements in dashboard sections
- **Location**: `dashboard/stats-bar.tsx` (no heading), `recent-runs-strip.tsx:61` (uses `<h2>` - OK)
- **Category**: Accessibility
- **Description**: StatsBar section has no heading element. Screen readers can't navigate to it by heading.
- **Recommendation**: Add visually-hidden `<h2>` or visible section heading.
- **Suggested command**: `/harden`

#### M14. Grounding notes button missing focus-visible
- **Location**: `detail-views/evidence-detail.tsx:106`
- **Category**: Accessibility
- **Description**: Custom expand button has no `focus-visible:ring-*` styles.
- **Recommendation**: Add focus ring classes.
- **Suggested command**: `/harden`

#### M15. Redundant sm: breakpoint in mobile nav
- **Location**: `components/layout/mobile-nav.tsx:42`
- **Category**: Responsive
- **Description**: `max-w-[min(280px,85vw)] ... sm:max-w-[min(280px,85vw)]` — duplicate declaration.
- **Recommendation**: Remove the `sm:` duplicate.
- **Suggested command**: `/normalize`

---

### Low-Severity Issues

#### L1. Tooltip triggers not keyboard-accessible in list rows
- **Location**: `master-items/hypothesis-row.tsx:38`, `conflict-row.tsx:40`, `evidence-row.tsx:35`, `paper-row.tsx:33`
- **Category**: Accessibility
- **Description**: `<TooltipTrigger asChild>` wraps a `<span>` which isn't focusable independently. Keyboard users on the parent `<button>` can see tooltip, but assistive tech may miss it.
- **Recommendation**: Acceptable since parent button is focusable. Low priority.

#### L2. Select trigger has redundant aria-label
- **Location**: `constraint-fields.tsx:75`
- **Category**: Accessibility
- **Description**: Both a visual `<FieldLabel>` and `aria-label="Lab mode"` exist. Redundant.
- **Recommendation**: Remove `aria-label` and connect via `htmlFor`/`id`.

#### L3. usePollRun potential initial-state edge
- **Location**: `hooks/use-poll-run.ts:22-28`
- **Category**: Performance
- **Description**: `refetchInterval` reads `query.state.data` which is undefined on first render. Currently benign because `undefined` doesn't match terminal statuses, but fragile.
- **Recommendation**: Add explicit pending check.

#### L4. DossierShell sorts hypotheses in useEffect
- **Location**: `components/dossier/dossier-shell.tsx:29`
- **Category**: Performance
- **Description**: Sorts 3 hypotheses on each render in useEffect. Trivial cost but not memoized.
- **Recommendation**: Wrap in `useMemo`.

#### L5. Markdown renderer lacks heading enforcement
- **Location**: `components/report/markdown-renderer.tsx:12`
- **Category**: Accessibility
- **Description**: ReactMarkdown renders whatever headings the API returns. Could skip levels.
- **Recommendation**: Add custom renderers if heading hierarchy matters.

#### L6. Form error not linked to input via aria-describedby
- **Location**: `dashboard/research-input.tsx:92-96`, `dashboard/new/page.tsx:84-88`
- **Category**: Accessibility
- **Description**: Error `<p>` is visually near the input but not programmatically linked.
- **Recommendation**: Add `aria-describedby` to input pointing to error element id.

#### L7. No `<main>` landmark on root layout
- **Location**: `app/layout.tsx`
- **Category**: Accessibility
- **Description**: Root layout has no `<main>` — it's in `dashboard/layout.tsx` which is good, but non-dashboard pages (404, root redirect) lack landmarks.
- **Recommendation**: Add `<main>` to root or ensure all page layouts include it.

#### L8. Empty page.tsx redirect lacks semantic structure
- **Location**: `app/page.tsx`
- **Category**: Accessibility
- **Description**: Landing page likely just redirects. Should have basic landmarks for screen readers during redirect.
- **Recommendation**: Low priority — redirect is instant.

---

## Patterns & Systemic Issues

1. **`text-[10px]` used in 7 components** — should be a consistent badge-size utility or just `text-xs`
2. **Missing `focus-visible` on 2 custom interactive elements** (ItemGroup trigger, grounding notes button) — all other interactive elements have proper focus rings
3. **Inconsistent `staleTime`** — only `useRuns` sets it; sibling hooks don't
4. **Magic-number height calculations** in 2 master-detail shells — fragile pattern
5. **3 hard-coded color values** in UI primitives (`bg-black`, `bg-white`, `text-white`) that bypass theming tokens

---

## Positive Findings

1. **Warm, cohesive color system** with proper light/dark tokens — no AI palette
2. **`prefers-reduced-motion`** respected globally (`globals.css:117-124`)
3. **Skip-to-content link** present (`dashboard/layout.tsx:6`)
4. **Proper ARIA on all icon buttons** — `aria-label` on theme toggle, hamburger, submit
5. **Semantic breadcrumbs** with `aria-label="Breadcrumb"` and `aria-current="page"`
6. **`memo` + `forwardRef`** on all list row components — good render perf
7. **Radix UI primitives** provide strong a11y foundation (Dialog, Tooltip, Select, etc.)
8. **External links** have `rel="noopener noreferrer"` and sr-only "(opens in new tab)"
9. **Form validation** with Zod schemas and proper error display
10. **Master-detail pattern** adapts cleanly between mobile (stacked) and desktop (side-by-side)

---

## Recommendations by Priority

### Immediate (blocks WCAG AA compliance)
1. Fix badge-as-button semantic element (C1) — `/harden`
2. Add `aria-live="polite"` to StageProgress (C2) — `/harden`
3. Add `focus-visible` to ItemGroup trigger + grounding notes button (M3, M14) — `/harden`

### Short-term (this sprint)
4. Replace all `text-[10px]` with `text-xs` (M1) — `/normalize`
5. Add `staleTime` to query hooks (H1) — `/optimize`
6. Add debounce to search filter (H2) — `/optimize`
7. Replace `bg-black/50`, `bg-white`, `text-white` with tokens (M10-M12) — `/normalize`
8. Add `aria-describedby` for form errors (L6) — `/harden`

### Medium-term (next sprint)
9. Replace Framer Motion with CSS animations (H3) — `/optimize`
10. Refactor calc-based heights to flex layouts (H6) — `/adapt`
11. Make panel widths flexible (H5) — `/adapt`
12. Add scroll indicators to recent runs (M9) — `/delight`
13. Responsive prose in markdown renderer (M6) — `/adapt`

### Long-term (nice-to-have)
14. Delete barrel export if unused (H4) — `/optimize`
15. Combine Zustand selectors with `useShallow` (M5) — `/optimize`
16. Extract slider debounce into sub-component (M4) — `/optimize`

---

## Suggested Commands for Fixes

| Command | Issues addressed | Count |
|---------|-----------------|-------|
| `/harden` | C1, C2, M2, M3, M13, M14, L6 | 7 |
| `/normalize` | M1, M10, M11, M12, M15 | 5 |
| `/optimize` | H1, H2, H3, H4, M4, M5 | 6 |
| `/adapt` | H5, H6, M6, M7, M8 | 5 |
| `/delight` | M9 | 1 |
