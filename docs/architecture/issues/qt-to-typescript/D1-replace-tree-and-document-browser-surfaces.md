# D1 Replace Tree and Document Browser Surfaces

Status: proposed

## Outcome

Move tree rendering and document browsing into protocol-driven TS components.

## Why This Matters

The document tree is one of the main daily-use surfaces in FreeCAD. Without it, the TypeScript shell cannot serve as a practical editing environment.

## Primary Scope

- `src/Gui/Tree*`
- `src/Gui/TreeView*`
- `src/Gui/Document*`
- `src/Gui/DocumentModel*`

## In Scope

- document tree rendering
- object hierarchy display
- expansion and selection state sync
- tree updates driven by backend payloads

## Out of Scope

- complete property editing
- complete task workflow migration
- full selection filter parity if that requires separate work

## Deliverables

- TS tree component
- document and object hierarchy payload implementation
- update and selection synchronization contract

## Repo Anchors

- `src/Gui/Tree.cpp`
- `src/Gui/TreeView.cpp`
- `src/Gui/Document.cpp`
- `src/Gui/DocumentModel.cpp`
- `variants/asterforge/protocol/schemas/object-tree.schema.json`
- `variants/asterforge/protocol/schemas/shell-snapshot.schema.json`

## Dependencies

- B1
- C2

## Acceptance Checklist

- the document tree works in the TypeScript shell with correct selection and update behavior
- large hierarchies remain usable in the TS shell
- tree state is not sourced from a Qt view widget

## Risks And Notes

- document and selection synchronization bugs will surface quickly here; keep state authority on the backend side