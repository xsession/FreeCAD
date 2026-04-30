# F1 Migrate Start, Part, PartDesign, and Sketcher

Status: proposed

## Outcome

Make the core modeling workflows usable in the TypeScript shell.

## Why This Matters

These are the primary product workflows. Without them, the migration remains a shell experiment instead of a credible replacement path.

## Primary Scope

- `src/Mod/Start`
- `src/Mod/Part`
- `src/Mod/PartDesign`
- `src/Mod/Sketcher`

## In Scope

- workbench command exposure in the new shell
- primary task and property flows for these workbenches
- enough viewport and editing integration to complete normal modeling sequences

## Out of Scope

- every specialist or low-frequency command on first pass
- non-core workbenches

## Deliverables

- migrated primary workflows in the TS shell
- parity review notes for Start, Part, PartDesign, and Sketcher
- missing-command or missing-surface gap list

## Repo Anchors

- `src/Mod/Start`
- `src/Mod/Part`
- `src/Mod/PartDesign`
- `src/Mod/Sketcher`
- `docs/GUI_OWNERSHIP_TABLE.md`

## Dependencies

- D3
- E2

## Acceptance Checklist

- a user can perform primary modeling workflows without using the Qt shell
- the migration set covers shell, tree, properties, task panels, and viewport integration for these workflows
- parity review exists for the main user journeys in these workbenches

## Risks And Notes

- keep scope disciplined around the daily-use path or the issue will balloon uncontrollably