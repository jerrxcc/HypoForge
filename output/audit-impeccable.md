# HypoForge Frontend Audit Report — Impeccable Standard

**Date**: 2026-03-21
**Branch**: `feature/frontend-v3`
**Scope**: All 83 frontend files (`frontend/src/`)
**Standard**: WCAG 2.1 AA + frontend-design anti-pattern checklist
**Previous audit**: Same date (pre-fix-pass). This is a re-audit after commits `36f875c`–`53ef203`.

---

## Anti-Patterns Verdict

**PASS.** This does **not** look AI-generated.

The codebase avoids every major AI slop tell:
- **Warm terracotta palette** (`rgb(217 119 86)`) — no cyan-on-dark, no purple-to-blue gradients
- **Tinted neutrals** — cream `rgb(250 246 241)`, dark mode warm brown `rgb(42 37 32)`, never pure black/white in custom tokens
- **No gradient text**, no glassmorphism-as-decoration (only functional `backdrop-blur` on sticky nav)
- **No hero metrics** layout, no identical card grids, no bounce/elastic easing
- **DM Sans + JetBrains Mono** — intentional pairing, mono only for identifiers
- **Button hierarchy** applied correctly — primary for CTAs, ghost for back, outline for secondary
- **Asymmetric master-detail layout** — sidebar + flex detail panel, not centered everything
- **Spacing rhythm** — `gap-1.5` / `gap-2` / `gap-3` / `gap-5` / `gap-12` with clear hierarchy

**Residual anti-pattern traces** (3 hard-coded colors in UI primitives):
- `bg-black/50` in dialog overlay (`dialog.tsx:42`)
- `bg-white` on slider thumb (`slider.tsx:56`)
- `text-white` on destructive button (`button.tsx:14`)

---

## Executive Summary

| Severity | Count |
|----------|-------|
| Critical | 3 |
| High | 8 |
| Medium | 16 |
| Low | 17 |
| **Total** | **44** |

**Top 5 issues:**
1. `<div role="button">` in TraceRow — should be native `<button>` (a11y, Critical)
2. `<Badge role="button">` in EvidenceLink/PaperLink — `<span>` as button (a11y, Critical)
3. No `aria-live` regions anywhere — search results, stage progress, error banners all silent (a11y, Critical)
4. `watch()` called 5 times in ConstraintFields — extreme re-render noise (perf, High)
5. `h-[calc(100vh-280px)]` magic numbers + `100vh` not `100dvh` — fragile layout (responsive, High)

**Quality score**: 7.8/10 — strong visual design and component architecture, but accessibility gaps need immediate attention. The global `staleTime: 30_000` in `query-provider.tsx` resolved the previous audit's worst perf finding, but new a11y issues surfaced from deeper inspection.

**Delta from previous audit**: +13 net new issues found. 0 issues from previous audit were fixed (all 31 remain). The global `staleTime` default was already present but undercounted.

---

## Detailed Findings

### Critical Issues

#### C1. `<div role="button">` in TraceRow
- **Location**: `components/trace/trace-list.tsx:29-36`
- **Category**: Accessibility
- **Description**: `TraceRow` renders `<div role="button" tabIndex={0} aria-pressed={isSelected}>`. A `<div>` with `role="button"` requires manual implementation of all button behaviors. Mobile touch activation without the JS key handler is not guaranteed.
- **Impact**: Inconsistent activation across assistive technologies and mobile browsers.
- **WCAG**: 4.1.2 Name, Role, Value
- **Recommendation**: Replace with `<button type="button">`. Remove manual `tabIndex` and `onKeyDown`.
- **Suggested command**: `/harden`

#### C2. Badge-as-button in EvidenceLink / PaperLink
- **Location**: `components/dossier/evidence-link.tsx:33-43,63-74`
- **Category**: Accessibility
- **Description**: `<Badge>` renders a `<span>` but receives `role="button"` + `tabIndex={0}`. Screen readers announce it inconsistently. Focus ring styles from Badge's base class (`focus-visible:ring-[3px]`) and the STYLE string (`focus-visible:ring-2`) may conflict.
- **Impact**: Keyboard/screen reader users get degraded experience.
- **WCAG**: 4.1.2 Name, Role, Value
- **Recommendation**: Use `<button type="button">` styled to look like a badge.
- **Suggested command**: `/harden`

#### C3. No `aria-live` regions in the entire codebase
- **Location**: Multiple — no matches for `aria-live` anywhere in `frontend/src/`
- **Category**: Accessibility
- **Description**: Three key dynamic regions lack live announcements:
  1. **Search filter results** (`master-panel.tsx:154-162`) — empty state not announced
  2. **Stage progress** (`stage-progress.tsx:92`) — status transitions invisible to screen readers
  3. **Error banner** (`runs/[id]/page.tsx:46-49`) — run failure not announced
- **Impact**: Blind users cannot track any dynamic state changes.
- **WCAG**: 4.1.3 Status Messages
- **Recommendation**: Add `aria-live="polite"` to search results area, wrap StageProgress in `aria-live="polite"`, add `role="alert"` to error banner.
- **Suggested command**: `/harden`

---

### High-Severity Issues

#### H1. `watch()` called 5 times in ConstraintFields — extreme re-render noise
- **Location**: `components/run/constraint-fields.tsx:32,70,89,116,121`
- **Category**: Performance
- **Description**: Five separate `watch()` calls each independently subscribe the component to all form state changes. Every keystroke in any field triggers 5 re-renders.
- **Impact**: Noisy render path, especially with slider live-updating.
- **Recommendation**: Replace with `useWatch({ control, name: ['novelty_weight', 'lab_mode', 'open_access_only', 'feasibility_weight'] })` for a single subscription.
- **Suggested command**: `/optimize`

#### H2. Search filter missing debounce
- **Location**: `components/dossier/search-filter.tsx:12-16`
- **Category**: Performance
- **Description**: Every keystroke calls `setSearchQuery` → Zustand update → MasterPanel re-render → `useMemo` filter across 4 arrays → `AnimatePresence` diffs list → Motion animates exits/enters. No debounce.
- **Impact**: Janky typing on large dossiers (36 papers + dozens of evidence cards).
- **Recommendation**: Add 200ms debounce before `setSearchQuery`, or use `useDeferredValue` in MasterPanel.
- **Suggested command**: `/optimize`

#### H3. Motion library (~50KB) for simple opacity/translate animations
- **Location**: `components/dossier/master-panel.tsx:4`
- **Category**: Performance
- **Description**: `motion/react` is imported in exactly 1 file for `AnimatePresence` with `opacity: 0→1, y: 8→0` transitions (0.15s). CSS can do this natively.
- **Impact**: ~50KB gzipped added to the dossier page bundle.
- **Recommendation**: Replace with CSS `@starting-style` or Tailwind `animate-*` classes. Remove the dependency entirely.
- **Suggested command**: `/optimize`

#### H4. Motion library ignores `prefers-reduced-motion`
- **Location**: `master-panel.tsx:4` (Motion import) + `globals.css:117-124` (CSS rule)
- **Category**: Accessibility / Performance
- **Description**: The global CSS rule sets `animation-duration: 0.01ms` for reduced-motion users, but `motion/react` drives animations via JavaScript, not CSS transitions. The CSS rule has no effect on Motion-driven animations.
- **Impact**: Users with vestibular disorders still see list item animations despite enabling reduced-motion.
- **Recommendation**: Use Motion's `useReducedMotion()` hook, or replace with CSS animations (which the global rule already handles).
- **Suggested command**: `/harden`

#### H5. `h-[calc(100vh-280px)]` — magic number + `100vh` instead of `100dvh`
- **Location**: `components/dossier/dossier-shell.tsx:66,71`
- **Category**: Responsive
- **Description**: `280px` is an unexplained constant. Uses `100vh` which causes the classic mobile browser address-bar overflow bug (should be `100dvh`). No responsive variants.
- **Impact**: Broken height on mobile Safari; any layout change breaks the offset.
- **Recommendation**: Use `100dvh` at minimum. Prefer `flex-1 min-h-0` layout to eliminate the magic number entirely.
- **Suggested command**: `/adapt`

#### H6. Fixed `w-[320px]` panel with no intermediate breakpoint
- **Location**: `components/dossier/dossier-shell.tsx:65`
- **Category**: Responsive
- **Description**: `w-[320px] shrink-0 lg:w-[380px]` — jumps from 320px to 380px at `lg:`. On 768-1024px viewports, 320px is too wide relative to remaining space for the detail panel.
- **Impact**: Cramped detail view on tablet-landscape.
- **Recommendation**: Use stepped widths (`md:w-[260px] lg:w-[320px] xl:w-[380px]`) or fraction-based (`w-1/3`).
- **Suggested command**: `/adapt`

#### H7. Form errors not associated with inputs via `aria-describedby`
- **Location**: `dashboard/research-input.tsx:92-96`, `dashboard/new/page.tsx:84-88`
- **Category**: Accessibility
- **Description**: Validation error `<p>` elements are visually near inputs but not programmatically linked. Neither input has `aria-describedby` or `aria-invalid="true"` set when errors are present.
- **Impact**: Screen readers don't associate errors with inputs. Error styling (`aria-invalid:border-destructive`) on the Input component never triggers.
- **WCAG**: 1.3.1 / 3.3.1 Error Identification
- **Recommendation**: Add `aria-describedby="topic-error"` to Input, `id="topic-error"` to error `<p>`, and `aria-invalid={!!errors.topic}`.
- **Suggested command**: `/harden`

#### H8. Magic calc height in TraceShell
- **Location**: `components/trace/trace-shell.tsx:51`
- **Category**: Responsive
- **Description**: `h-[calc(100dvh-var(--nav-height,56px)-164px)]` — the `164px` is unexplained. Correctly uses `100dvh` (unlike dossier-shell), but still fragile.
- **Impact**: Layout breaks if breadcrumb/header row height changes.
- **Recommendation**: Document the `164px` origin, or replace with flex layout.
- **Suggested command**: `/adapt`

---

### Medium-Severity Issues

#### M1. Pervasive `text-[10px]` font size (8 instances)
- **Location**: `master-items/hypothesis-row.tsx:33,52`, `evidence-row.tsx:49`, `conflict-row.tsx:54`, `paper-row.tsx:48,53`, `item-group.tsx:34`, `trace/trace-list.tsx:48`
- **Category**: Responsive / A11y
- **Description**: 10px is below the 12px minimum for legibility and doesn't scale with user font preferences.
- **Recommendation**: Replace with `text-xs` (12px / 0.75rem).
- **Suggested command**: `/normalize`

#### M2. ScoreBar `aria-label` lacks numeric value
- **Location**: `detail-views/hypothesis-detail.tsx:23`
- **Category**: Accessibility
- **Description**: `aria-label={label}` — screen readers hear "Novelty" but not the actual score.
- **Recommendation**: `aria-label={\`${label}: ${pct}%\`}`
- **Suggested command**: `/harden`

#### M3. ItemGroup CollapsibleTrigger missing `focus-visible` ring
- **Location**: `components/dossier/item-group.tsx:26`
- **Category**: Accessibility
- **Description**: No `focus-visible:ring-*` classes. Keyboard users can't see focus position.
- **WCAG**: 2.4.7 Focus Visible
- **Recommendation**: Add `focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none`.
- **Suggested command**: `/harden`

#### M4. ConstraintDrawer CollapsibleTrigger missing `focus-visible` ring
- **Location**: `components/run/constraint-drawer.tsx:26`
- **Category**: Accessibility
- **Description**: Same as M3 — no focus ring on the "Show advanced options" trigger.
- **WCAG**: 2.4.7 Focus Visible
- **Recommendation**: Add `focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none rounded`.
- **Suggested command**: `/harden`

#### M5. Grounding notes button missing `focus-visible` ring
- **Location**: `detail-views/evidence-detail.tsx:106`
- **Category**: Accessibility
- **Description**: Custom expand button has no `focus-visible:ring-*` styles, inconsistent with design system.
- **WCAG**: 2.4.7 Focus Visible
- **Recommendation**: Add focus ring classes.
- **Suggested command**: `/harden`

#### M6. Desktop `<nav>` missing `aria-label`
- **Location**: `components/layout/top-nav.tsx:16`
- **Category**: Accessibility
- **Description**: When breadcrumb `<nav aria-label="Breadcrumb">` also exists, screen readers can't distinguish the two nav landmarks.
- **Recommendation**: Add `aria-label="Main navigation"`.
- **Suggested command**: `/harden`

#### M7. RunNotFound uses `<h2>` with no `<h1>`
- **Location**: `app/dashboard/runs/[id]/not-found.tsx:6`
- **Category**: Accessibility
- **Description**: Heading hierarchy skips `<h1>`. Screen readers can't find a primary heading.
- **WCAG**: 1.3.1 Info and Relationships
- **Recommendation**: Change `<h2>` to `<h1>`.
- **Suggested command**: `/harden`

#### M8. Detail views use `<h3>` with no `<h2>` ancestor
- **Location**: `hypothesis-detail.tsx:54`, `conflict-detail.tsx:24`, `evidence-detail.tsx:34`, `paper-detail.tsx:17`
- **Category**: Accessibility
- **Description**: Page goes `<h1>` (run topic) → `<h3>` (item title) → `<h4>` (sections). `<h2>` level is skipped.
- **Recommendation**: Add visually-hidden `<h2>` around detail panel, or remap heading levels.
- **Suggested command**: `/harden`

#### M9. "Lab mode" Select label not programmatically associated
- **Location**: `components/run/constraint-fields.tsx:68-84`
- **Category**: Accessibility
- **Description**: `<FieldLabel>Lab mode</FieldLabel>` at line 68 renders without `htmlFor`. The `<SelectTrigger aria-label="Lab mode">` compensates, but the visible label is not programmatically linked to the trigger.
- **WCAG**: 1.3.1 Info and Relationships
- **Recommendation**: Add `id` to `<SelectTrigger>` and matching `htmlFor` to `<FieldLabel>`, or use `aria-labelledby`.
- **Suggested command**: `/harden`

#### M10. `required` attribute missing on topic inputs
- **Location**: `dashboard/research-input.tsx:73-79`, `dashboard/new/page.tsx:77-83`
- **Category**: Accessibility
- **Description**: Topic is validated as required via Zod, but neither `required` nor `aria-required="true"` is on the DOM element. Screen readers don't announce it as required.
- **WCAG**: 3.3.2 Labels or Instructions
- **Recommendation**: Add `required` to the `<Input>`.
- **Suggested command**: `/harden`

#### M10. `bg-black/50` in dialog overlay
- **Location**: `components/ui/dialog.tsx:42`
- **Category**: Theming
- **Description**: Pure black overlay clashes with warm palette and has no dark mode variant.
- **Recommendation**: Use `bg-foreground/40` or define a warm `--color-overlay` token.
- **Suggested command**: `/normalize`

#### M11. `bg-white` on slider thumb
- **Location**: `components/ui/slider.tsx:56`
- **Category**: Theming
- **Description**: Hard-coded `bg-white` — pure white thumb on warm dark backgrounds is jarring.
- **Recommendation**: Use `bg-card` or `bg-background`.
- **Suggested command**: `/normalize`

#### M12. `text-white` on destructive button
- **Location**: `components/ui/button.tsx:14`
- **Category**: Theming
- **Description**: Literal `text-white` bypasses the `--color-destructive-foreground` token.
- **Recommendation**: Use `text-destructive-foreground`.
- **Suggested command**: `/normalize`

#### M13. `border-t-[var(--color-success)]` inconsistent with sibling tokens
- **Location**: `components/dossier/detail-panel.tsx:16`
- **Category**: Theming
- **Description**: Other TYPE_ACCENT entries use Tailwind tokens (`border-t-primary`, `border-t-warning`). The `evidence` entry uses an inline CSS var. The `success` color IS registered in `@theme`.
- **Recommendation**: Replace with `border-t-success`.
- **Suggested command**: `/normalize`

#### M14. Skeleton width diverges from actual panel width
- **Location**: `app/dashboard/runs/[id]/page.tsx:84`
- **Category**: Responsive
- **Description**: `<Skeleton className="h-[400px] w-[320px]">` — missing `lg:w-[380px]` that the actual panel uses.
- **Recommendation**: Mirror the real column's responsive classes.
- **Suggested command**: `/adapt`

#### M15. Prose typography not responsive
- **Location**: `components/report/markdown-renderer.tsx:11`
- **Category**: Responsive
- **Description**: Fixed `prose` sizing. On mobile, line lengths may be too wide.
- **Recommendation**: Add `prose-sm sm:prose` and reduce padding `p-4 sm:p-6`.
- **Suggested command**: `/adapt`

---

### Low-Severity Issues

#### L1. Barrel export unused but present
- **Location**: `components/ui/index.ts`
- **Category**: Performance
- **Description**: All 18 UI components re-exported. No consumer uses the barrel (all use direct paths). Risk of future misuse.
- **Recommendation**: Delete the file.
- **Suggested command**: `/optimize`

#### L2. `useRun` hook is dead code
- **Location**: `hooks/use-run.ts`
- **Category**: Performance
- **Description**: Never imported by any page — all run detail pages use `usePollRun` instead.
- **Recommendation**: Remove or document as a non-polling variant.
- **Suggested command**: `/optimize`

#### L3. `useReport`/`useTrace` staleTime should be Infinity for immutable data
- **Location**: `hooks/use-report.ts`, `hooks/use-trace.ts`
- **Category**: Performance
- **Description**: Both inherit the global 30s `staleTime`. Reports are immutable after generation; traces are append-only. 30s causes unnecessary refetches on tab focus.
- **Recommendation**: Set `staleTime: Infinity` on `useReport`. Set conditional `staleTime: Infinity` on `useTrace` when `active === false`.
- **Suggested command**: `/optimize`

#### L4. `usePollRun` refetches completed runs on tab focus
- **Location**: `hooks/use-poll-run.ts:18-29`
- **Category**: Performance
- **Description**: Polling stops for terminal runs, but TanStack Query still refetches on window focus after 30s staleTime. Payloads can be large.
- **Recommendation**: Use dynamic `staleTime` function: return `Infinity` when status is terminal.
- **Suggested command**: `/optimize`

#### L5. `will-change-transform` unnecessary on sticky header
- **Location**: `components/layout/top-nav.tsx:10`
- **Category**: Performance
- **Description**: Header doesn't animate — `will-change` just wastes GPU memory for a static sticky element.
- **Recommendation**: Remove `will-change-transform`.
- **Suggested command**: `/optimize`

#### L6. Stats bar gap not responsive
- **Location**: `components/dashboard/stats-bar.tsx:59`
- **Category**: Responsive
- **Description**: `gap-4` doesn't tighten on mobile.
- **Recommendation**: `gap-2 sm:gap-4`.
- **Suggested command**: `/adapt`

#### L7. Recent runs strip lacks scroll indicators
- **Location**: `components/dashboard/recent-runs-strip.tsx:62`
- **Category**: UX
- **Description**: Horizontal scroll with hidden scrollbar provides no visual hint that more content exists.
- **Recommendation**: Add fade mask overlay or visible scroll dots.
- **Suggested command**: `/delight`

#### L8. Redundant `sm:` breakpoint in mobile nav
- **Location**: `components/layout/mobile-nav.tsx:42`
- **Category**: Responsive
- **Description**: `max-w-[min(280px,85vw)] sm:max-w-[min(280px,85vw)]` — identical declaration.
- **Recommendation**: Remove the `sm:` duplicate.
- **Suggested command**: `/normalize`

#### L9. Tooltip triggers not independently keyboard-accessible in list rows
- **Location**: `master-items/hypothesis-row.tsx:38`, `conflict-row.tsx:40`, `evidence-row.tsx:35`, `paper-row.tsx:33`
- **Category**: Accessibility
- **Description**: `<TooltipTrigger asChild>` wraps `<span>` which isn't independently focusable. Acceptable since parent button is focusable.

#### L10. `size-xs` button (24px) below 44px touch target
- **Location**: `components/ui/button.tsx:25`
- **Category**: Responsive
- **Description**: `h-6` = 24px. Any `size="xs"` button on mobile fails WCAG 2.5.5 target size.
- **Recommendation**: Reserve for desktop-only contexts, or add invisible touch-area expansion.
- **Suggested command**: `/adapt`

#### L11. Select trigger has redundant `aria-label`
- **Location**: `constraint-fields.tsx:75`
- **Category**: Accessibility
- **Description**: Both a visual `<FieldLabel>` and `aria-label="Lab mode"` exist. Redundant.
- **Recommendation**: Remove `aria-label` and connect via `htmlFor`/`id`.

#### L12. `Download` icon missing `aria-hidden`
- **Location**: `components/report/download-button.tsx:27`
- **Category**: Accessibility
- **Description**: `<Download>` icon rendered without `aria-hidden="true"` inside a button that has text "Download". Some screen readers may read "Download Download".
- **Recommendation**: Add `aria-hidden="true"` to the icon.
- **Suggested command**: `/harden`

#### L13. `Plus` icon missing `aria-hidden`
- **Location**: `app/dashboard/runs/page.tsx:46`
- **Category**: Accessibility
- **Description**: `<Plus>` icon in "New Run" link not marked `aria-hidden="true"`. Link text is sufficient.
- **Recommendation**: Add `aria-hidden="true"`.
- **Suggested command**: `/harden`

#### L14. RunCard `<Link>` produces verbose screen reader name
- **Location**: `components/run/run-card.tsx:26`
- **Category**: Accessibility
- **Description**: `<Link>` wrapping the entire card computes its name from all descendant text: topic + status + counts + date. Very verbose for AT.
- **Recommendation**: Add `aria-label={run.topic}` to the Link.
- **Suggested command**: `/harden`

#### L15. `<article>` in MarkdownRenderer lacks accessible name
- **Location**: `components/report/markdown-renderer.tsx:11`
- **Category**: Accessibility
- **Description**: `<article>` is a landmark. Screen readers list it without a name.
- **Recommendation**: Add `aria-label="Research report"`.
- **Suggested command**: `/harden`

#### L16. `text-muted-foreground` on headings may fail contrast
- **Location**: `dashboard/recent-runs-strip.tsx:61`, `dashboard/page.tsx:36`
- **Category**: Accessibility
- **Description**: `<h2>` elements using `text-muted-foreground` — verify the token meets 4.5:1 contrast against background in both modes.
- **Recommendation**: Verify with a contrast checker. Use `text-foreground` if ratio is insufficient.

#### L17. Slider debounce timer not cleaned on unmount
- **Location**: `constraint-fields.tsx:34-47`
- **Category**: Performance
- **Description**: `timerRef` is never cleared via a cleanup function in `useEffect`. If the component unmounts mid-debounce, `setTimeout` fires on an unmounted component.
- **Recommendation**: Add a cleanup effect: `useEffect(() => () => clearTimeout(timerRef.current), [])`.
- **Suggested command**: `/harden`

---

## Patterns & Systemic Issues

1. **Zero `aria-live` regions** — no dynamic content changes are announced. This is the single biggest a11y gap. Affects search filtering, stage progress, and error states.
2. **`text-[10px]` used in 8 components** — systematic badge-size pattern that should be `text-xs`
3. **Three focus-visible gaps** on custom interactive elements (ItemGroup trigger, ConstraintDrawer trigger, grounding notes button) — all other interactive elements have proper focus rings
4. **Three hard-coded colors** in UI primitives (`bg-black/50`, `bg-white`, `text-white`) bypassing design tokens
5. **Magic-number height calculations** in 2 shells (dossier + trace) — fragile pattern
6. **`motion/react` imported for 1 simple animation** — ~50KB for what CSS can do natively, and it ignores `prefers-reduced-motion`
7. **`watch()` overuse** in constraint form — 5 independent subscriptions instead of 1

---

## Positive Findings

1. **Warm, cohesive color system** with proper light/dark tokens — no AI palette
2. **`prefers-reduced-motion`** respected globally via CSS (`globals.css:117-124`)
3. **Skip-to-content link** present with proper styling (`dashboard/layout.tsx:6`)
4. **Proper ARIA on all icon buttons** — `aria-label` on theme toggle, hamburger, submit
5. **Semantic breadcrumbs** with `aria-label="Breadcrumb"` and `aria-current="page"`
6. **`memo` + `forwardRef`** on all list row components — good render perf foundation
7. **Radix UI primitives** provide strong a11y baseline (Dialog, Tooltip, Select, Collapsible)
8. **External links** have `rel="noopener noreferrer"` and sr-only "(opens in new tab)"
9. **Form validation** with Zod schemas and proper error display
10. **Global `staleTime: 30_000`** in QueryProvider — prevents default refetch-on-every-mount
11. **Mobile layout** properly switches to stacked master-detail with Back button
12. **`display: 'swap'`** on both font declarations — prevents FOIT

---

## Recommendations by Priority

### Immediate (blocks WCAG AA compliance)
1. Add `aria-live` regions to search results, stage progress, error banner (C3) — `/harden`
2. Replace `<div role="button">` with `<button>` in TraceRow (C1) — `/harden`
3. Replace `<Badge role="button">` with `<button>` in EvidenceLink/PaperLink (C2) — `/harden`
4. Add `aria-describedby` + `aria-invalid` to form error messages (H7) — `/harden`
5. Add `focus-visible` to 3 custom triggers (M3, M4, M5) — `/harden`

### Short-term (this sprint)
6. Replace all `text-[10px]` with `text-xs` (M1) — `/normalize`
7. Replace `bg-black/50`, `bg-white`, `text-white` with tokens (M10-M12) — `/normalize`
8. Fix `border-t-[var(--color-success)]` → `border-t-success` (M13) — `/normalize`
9. Add debounce to search filter (H2) — `/optimize`
10. Replace `watch()` with single `useWatch` (H1) — `/optimize`
11. Add `aria-label="Main navigation"` to desktop nav (M6) — `/harden`
12. Fix heading hierarchy issues (M7, M8) — `/harden`
13. Add `required` to topic inputs (M9) — `/harden`

### Medium-term (next sprint)
14. Replace Framer Motion with CSS animations — fixes both H3 and H4 — `/optimize`
15. Refactor calc-based heights to flex layouts (H5, H8) — `/adapt`
16. Make panel widths responsive with intermediate breakpoints (H6) — `/adapt`
17. Add responsive prose sizing (M15) — `/adapt`
18. Fix skeleton width to match actual panel (M14) — `/adapt`

### Long-term (nice-to-have)
19. Delete barrel export (L1) — `/optimize`
20. Remove dead `useRun` hook (L2) — `/optimize`
21. Set `staleTime: Infinity` for immutable queries (L3, L4) — `/optimize`
22. Add scroll indicators to recent runs strip (L7) — `/delight`
23. Remove unnecessary `will-change-transform` (L5) — `/optimize`

---

## Suggested Commands for Fixes

| Command | Issues addressed | Count |
|---------|-----------------|-------|
| `/harden` | C1, C2, C3, H4, H7, M2, M3, M4, M5, M6, M7, M8, M9, M10, L12, L13, L14, L15, L17 | 19 |
| `/normalize` | M1, M11, M12, M13, M14, L8 | 6 |
| `/optimize` | H1, H2, H3, L1, L2, L3, L4, L5 | 8 |
| `/adapt` | H5, H6, H8, M15, M16, L6, L10 | 7 |
| `/delight` | L7 | 1 |
