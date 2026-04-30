# Shell Protocol Expansion Draft

Status: shell contracts reviewed and promoted into proto-first form

## Purpose

This document defines the next shell-facing protocol slices needed for the Qt-to-TypeScript migration.

The current protocol package already covers documents, object tree, properties, selection, commands, diagnostics, jobs, and lightweight task panels. The next gap is shell composition.

## Contract Areas

The next protocol expansion should cover:

1. workbench catalog and active workbench state
2. menu model
3. toolbar model
4. shell layout and visible panel state
5. shell snapshot payload used by parity capture and frontend hydration

## Design Rules

1. backend state is authoritative
2. frontend renders structure but does not infer missing semantics
3. command references should point to existing command identifiers, not duplicate behavior
4. layout state should be explicit and portable, not Qt-specific
5. parity capture should be able to serialize shell state with no Qt widget references

## Proposed Payloads

### Workbench Catalog

Defines the full available workbench list plus the active entry.

### Menu Bar State

Defines ordered top-level menus with nested items, separators, command references, and visibility state.

### Toolbar Band State

Defines ordered toolbar bands, toolbar groups, actions, overflow behavior, and visibility state.

### Shell Layout State

Defines visible panels, dock regions, ordering, sizing hints, split ratios, and active tabs.

### Shell Snapshot

Combines document, workbench, menus, toolbars, layout, and visible shell surfaces for frontend hydration and parity capture.

## Rollout Status

1. schema review in JSON first
2. `.proto` promotion after field stability
3. backend adapter implementation
4. TypeScript rendering against snapshot payload

Current state:

- steps 1 and 2 are complete for workbench, menu, toolbar, layout, and shell snapshot contracts
- backend adapters and TS rendering are still pending

## Related Files

- `schemas/workbench-catalog.schema.json`
- `schemas/menu-bar.schema.json`
- `schemas/toolbar-band.schema.json`
- `schemas/shell-layout.schema.json`
- `schemas/shell-snapshot.schema.json`