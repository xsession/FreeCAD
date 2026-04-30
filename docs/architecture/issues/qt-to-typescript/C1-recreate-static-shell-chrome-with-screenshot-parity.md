# C1 Recreate Static Shell Chrome with Screenshot Parity

Status: proposed

## Outcome

Reproduce menu bar, toolbars, combo view shell, report view shell, and status bar visually in TypeScript.

## Why This Matters

The shell needs to become visually recognizable before deeper behavioral replacement begins. Otherwise parity discussions stay speculative and every later change lacks a stable baseline.

## Primary Scope

- `variants/asterforge/frontend/app`
- parity baselines under `docs/parity`

## In Scope

- static shell chrome rendering
- menu and toolbar bands as visual structures
- side panel and report area shell framing
- use of parity metadata and screenshots as acceptance inputs

## Out of Scope

- dynamic command execution
- editing-surface behavior
- viewport feature parity

## Deliverables

- static shell parity implementation
- first screenshot review pass against captured baselines
- visual deviation log for approved and unapproved differences

## Repo Anchors

- `variants/asterforge/frontend/app`
- `docs/parity/baselines/baseline-manifest.md`
- `docs/parity/acceptance/thresholds.md`
- `docs/FRONTEND_PARITY_BASELINE_SPEC.md`

## Dependencies

- A2

## Acceptance Checklist

- shell parity screenshots meet the agreed tolerance
- shell chrome is recognizable as FreeCAD without relying on Qt widgets
- deviations in spacing, grouping, or icon treatment are documented explicitly

## Risks And Notes

- do not let static shell work hard-code assumptions that should later come from protocol state