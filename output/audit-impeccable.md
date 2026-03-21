# HypoForge Frontend Audit Report — Impeccable Standard (Final)

**Date**: 2026-03-21
**Branch**: `feature/frontend-v3`
**Scope**: All 80 frontend files (`frontend/src/`)
**Standard**: WCAG 2.1 AA + frontend-design anti-pattern checklist
**Audit history**: Initial (31) → Re-audit (44) → Post-remediation (8) → **Final (7)**

---

## Anti-Patterns Verdict

**PASS.** Clean on all AI slop tells.

- Warm terracotta palette — no cyan, no purple-to-blue gradients
- Tinted neutrals — zero `bg-black`, `bg-white`, `text-white` in entire codebase
- No gradient text, no glassmorphism, no hero metrics, no bounce easing
- DM Sans + JetBrains Mono — intentional pairing
- Proper button hierarchy, asymmetric layouts, varied spacing rhythm
- CSS-only animations respecting `prefers-reduced-motion` globally
- Warm dialog overlay (`bg-foreground/40`)

---

## Executive Summary

| Severity | Count |
|----------|-------|
| Critical | 0 |
| High | 0 |
| Medium | 2 |
| Low | 5 |
| **Total** | **7** |

**Audit progression: 44 → 8 → 7. All Critical and High issues resolved.**

**Quality score: 9.5/10** — production-ready, WCAG AA compliant.

The previous H1 (`text-muted-foreground` contrast) is now resolved: `rgb(118 103 88)` passes on all surfaces in both modes (5.07:1 on background, 5.45:1 on card, 4.56:1 on muted in light; 6.64:1, 5.74:1, 4.90:1 in dark).

---

## Detailed Findings

### Critical Issues

None.

### High-Severity Issues

None.

### Medium-Severity Issues

#### M1. `<h2>` headings styled as muted labels
- **Location**: `dashboard/recent-runs-strip.tsx:61`, `dashboard/page.tsx:36`
- **Category**: UX
- **Description**: Semantic `<h2>` styled with `text-muted-foreground` — while contrast now passes AA, using muted color for headings reduces visual hierarchy. These function more as section labels than navigational headings.
- **Recommendation**: Use `text-foreground` for heading prominence, or change to `<p>` if they aren't structural headings.
- **Suggested command**: `/typeset`

#### M2. Calc-based heights with magic offsets
- **Location**: `dossier-shell.tsx:64`, `trace-shell.tsx:52`
- **Category**: Responsive
- **Description**: Both shells use `h-[calc(100dvh-var(--nav-height,56px)-120px)]`. Documented in trace-shell but not dossier-shell. A flex-based approach would be more robust.
- **Recommendation**: Refactor to `flex-1 min-h-0` in a future pass. Low urgency.
- **Suggested command**: `/adapt`

### Low-Severity Issues

#### L1. Tooltip triggers not independently focusable
- **Location**: `master-items/*-row.tsx` (4 files)
- **Category**: Accessibility
- **Description**: `<TooltipTrigger asChild>` wraps `<span>` inside a focusable `<button>`. Acceptable — parent button receives focus.

#### L2. MarkdownRenderer `aria-label` could be dynamic
- **Location**: `report/markdown-renderer.tsx:11`
- **Category**: Accessibility
- **Description**: Static `aria-label="Research report"`. Could use `aria-labelledby` pointing to the page `<h1>` for context-specific labels.

#### L3. RunCard Link aria-label loses metadata context
- **Location**: `components/run/run-card.tsx:26`
- **Category**: Accessibility
- **Description**: `aria-label={run.topic}` is concise but omits status/counts. Acceptable trade-off.

#### L4. Runs page search has no debounce
- **Location**: `app/dashboard/runs/page.tsx:56-63`
- **Category**: Performance
- **Description**: Filters on every keystroke. Negligible at current scale (dozens of runs).

#### L5. Dossier-shell calc offset lacks comment
- **Location**: `dossier-shell.tsx:64`
- **Category**: Maintainability
- **Description**: `120px` offset not documented (trace-shell has a comment, dossier-shell doesn't).

---

## Positive Findings

1. **WCAG AA compliant** — all text/background combinations pass 4.5:1 in both modes
2. **Zero hard-coded colors** — entire codebase uses design tokens
3. **Native semantic elements** — no `role="button"` on non-buttons
4. **aria-live regions** on search results, stage progress, error banners
5. **aria-describedby + aria-invalid** on all form error messages
6. **focus-visible rings** on every interactive element
7. **`prefers-reduced-motion`** globally respected via CSS
8. **No JS animation library** — ~50KB removed, CSS-only animations
9. **Intelligent staleTime** — Infinity for immutable data, dynamic for polling
10. **200ms debounce** on dossier search filter
11. **Single `useWatch`** instead of 5 `watch()` calls
12. **`100dvh`** everywhere (no mobile Safari bug)
13. **Stepped responsive panel widths** (`md:260/lg:320/xl:380`)
14. **Touch target expansion** on xs buttons
15. **Proper heading hierarchy** (h1→h2→h3)
16. **Skip-to-content**, semantic nav landmarks, breadcrumbs
17. **Scroll fade indicator** on horizontal strip
18. **Warm tinted overlay** and slider thumb use design tokens

---

## Recommendations by Priority

### Short-term (nice-to-have)
1. Restyle `<h2>` section labels with `text-foreground` (M1) — `/typeset`
2. Add comment to dossier-shell calc offset (L5) — trivial inline fix

### Long-term (future sprint)
3. Refactor calc heights to flex layout (M2) — `/adapt`
4. Add `useDeferredValue` to runs search if list grows (L4) — `/optimize`

---

## Suggested Commands for Fixes

| Command | Issues | Count |
|---------|--------|-------|
| `/typeset` | M1 | 1 |
| `/adapt` | M2 | 1 |

No immediate action required. All remaining issues are Medium or Low severity with no accessibility, performance, or theming blockers.
