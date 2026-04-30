# C2 Replace Docking and Layout Persistence

Status: proposed

## Outcome

Replace Qt docking and layout persistence with shell-neutral layout state.

## Why This Matters

Docking and layout persistence are part of FreeCAD’s core shell experience. If they remain Qt-owned, the TypeScript shell can only imitate the current product superficially.

## Primary Scope

- `src/Gui/DockWindow*`
- `src/Gui/DockWindowManager*`
- `src/Gui/ComboView*`
- `src/Gui/ToolBox*`

## In Scope

- portable layout state model
- panel visibility, ordering, region, and sizing hints
- initial save and restore behavior for the TS shell

## Out of Scope

- every advanced docking edge case on day one
- deep viewport interactions that happen to live inside split-view widgets

## Deliverables

- shell layout schema or promoted protocol contract
- TS layout persistence implementation
- migration note documenting unsupported or deferred docking behaviors

## Repo Anchors

- `src/Gui/DockWindow.cpp`
- `src/Gui/DockWindowManager.cpp`
- `src/Gui/ComboView.cpp`
- `src/Gui/ToolBox.cpp`
- `variants/asterforge/protocol/schemas/shell-layout.schema.json`

## Dependencies

- C1

## Acceptance Checklist

- the TypeScript shell can persist and restore the major panel layout states
- panel region and order are backend-describable instead of Qt-widget-local
- layout persistence is stable enough for parity review flows

## Risks And Notes

- Qt docking may hide historical quirks that need to be handled intentionally rather than copied blindly