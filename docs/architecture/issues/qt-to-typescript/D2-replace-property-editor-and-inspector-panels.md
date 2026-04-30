# D2 Replace Property Editor and Inspector Panels

Status: proposed

## Outcome

Render properties from backend schemas instead of Qt editor widgets.

## Why This Matters

The property view is where much of FreeCAD’s parametric editing happens. Replacing the shell without replacing properties would leave the product functionally incomplete.

## Primary Scope

- `src/Gui/PropertyView*`
- `src/Gui/propertyeditor/**`

## In Scope

- grouped property rendering
- editable versus read-only property state
- schema-driven renderer selection by property kind
- undo-safe property mutation flow through backend commands or mutations

## Out of Scope

- every specialist workbench editor on first pass
- expression authoring UX beyond the core property rendering path

## Deliverables

- TS property panel renderer
- grouped property payload integration
- mutation pattern for common property edits

## Repo Anchors

- `src/Gui/PropertyView.cpp`
- `src/Gui/propertyeditor/PropertyEditor.cpp`
- `src/Gui/propertyeditor/PropertyModel.cpp`
- `variants/asterforge/protocol/schemas/property.schema.json`
- `variants/asterforge/protocol/schemas/property-groups.schema.json`

## Dependencies

- D1

## Acceptance Checklist

- primary property editing flows preserve undo and recompute behavior
- grouped property display matches shell expectations closely enough for parity review
- renderer choice is schema-driven rather than hard-coded to Qt widget classes

## Risks And Notes

- mutation semantics need to remain backend-owned to avoid frontend-side document logic drift