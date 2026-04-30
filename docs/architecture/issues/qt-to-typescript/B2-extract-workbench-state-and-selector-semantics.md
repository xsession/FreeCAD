# B2 Extract Workbench State and Selector Semantics

Status: proposed

## Outcome

Move workbench registration and active-workbench state behind backend services.

## Why This Matters

Workbench state currently shapes shell composition, command exposure, and user navigation. A TS shell cannot switch workbenches cleanly until workbench semantics stop living in Qt-owned selector logic.

## Primary Scope

- `src/Gui/Workbench*`
- `src/Gui/WorkbenchSelector*`

## In Scope

- workbench catalog extraction
- active-workbench state exposure
- selector-compatible data model for the TS shell
- alignment with command and shell snapshot payloads

## Out of Scope

- full workbench UI migration
- task panel migration inside individual workbenches

## Deliverables

- workbench catalog payload
- active-workbench switch contract
- selector semantics note covering labels, ordering, icons, and disabled states

## Repo Anchors

- `src/Gui/Workbench.cpp`
- `src/Gui/WorkbenchFactory.cpp`
- `src/Gui/WorkbenchManager.cpp`
- `src/Gui/WorkbenchSelector.cpp`
- `variants/asterforge/protocol/schemas/workbench-catalog.schema.json`

## Dependencies

- B1

## Acceptance Checklist

- the TypeScript shell can switch workbenches without Qt shell mediation
- available and active workbench state can be serialized for shell hydration
- workbench-dependent shell state can be expressed without a Qt selector widget

## Risks And Notes

- some workbench transitions may still trigger implicit Qt shell side effects that need separate cleanup