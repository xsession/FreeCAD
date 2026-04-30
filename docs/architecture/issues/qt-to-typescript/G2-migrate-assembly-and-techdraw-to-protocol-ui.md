# G2 Migrate Assembly and TechDraw to Protocol-Driven UI

Status: proposed

## Outcome

Bring two strategically important but dialog-heavy workflows into the new shell.

## Why This Matters

Assembly and TechDraw are important workflow surfaces with dialog and task-heavy interaction models. They are good tests of whether the new task runtime and shell protocols are adequate beyond core modeling.

## Primary Scope

- `src/Mod/Assembly/**`
- `src/Mod/TechDraw/**`

## In Scope

- protocol-driven task and dialog coverage for major Assembly and TechDraw workflows
- shell, tree, property, and viewport integration as required by those workflows

## Out of Scope

- every edge-case feature in both workbenches on first pass
- unrelated specialist workbenches

## Deliverables

- migrated Assembly workflow slice
- migrated TechDraw workflow slice
- parity review and gap list for both modules

## Repo Anchors

- `src/Mod/Assembly/**`
- `src/Mod/TechDraw/**`
- `docs/PYSIDE_USAGE_TABLE.md`
- `docs/QT_UI_FORM_INVENTORY.md`

## Dependencies

- D3
- E2

## Acceptance Checklist

- assembly task flows and technical drawing task flows are usable without Qt widgets
- both modules can be exercised through the TS shell with protocol-driven surfaces
- remaining module gaps are explicit and reviewable

## Risks And Notes

- these workflows are likely to expose missing capabilities in task schemas and shell state contracts