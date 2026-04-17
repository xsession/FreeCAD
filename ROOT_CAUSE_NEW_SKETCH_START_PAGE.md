# Root Cause Report: New Sketch From Start Page Fails

Date: 2026-04-17

## User-Repro Path

1. Start page
2. Empty Document
3. Part Design -> New Sketch
4. Select XY plane

Observed behavior: sketch workflow falls back to Start/Backstage state or fails to enter usable sketch-edit mode.

## True Root Cause

The core defect is in GUI view activation semantics, not in plane picking itself.

`Gui::Application::activateView(type, create=true)` created a 3D view when missing, but did **not** make that newly created view active synchronously.

Downstream PartDesign code immediately depends on `activeView` and `ActiveView.setActiveObject(...)` in the same call stack:

- body activation path (`makeBodyActive`) depends on active view context
- sketch entry path (`setEdit`) depends on active 3D view context
- plane-pick acceptance path (`SketchWorkflow::createSketch`) reaches `setEdit` immediately

Because the created 3D window was not forced active at creation time, these calls could still execute against a non-3D or stale UI context (Start/Backstage transition), causing body/sketch activation failure.

## Evidence From Code

- `src/Gui/Application.cpp` previously did:
  - `doc->createView(type);`
  - no `doc->setActiveWindow(...)` for the newly created view
- `src/Gui/Document.cpp` `createView(...)` builds/adds the view, but activation depends on separate window focus flow
- PartDesign call paths use active-view dependent operations immediately after `activateView(...)`

This is a timing/context coupling issue between view creation and immediate active-view-dependent commands.

## Why Earlier Fixes Were Incomplete

Earlier patches reduced symptoms by adding `activateView(...)` calls in PartDesign command/workflow points and by closing Backstage overlays.

Those were defensive but still relied on framework behavior that did not guarantee newly created view activation in the same call path.

## Final Fix Implemented

Framework fix:

- `src/Gui/Application.cpp`
  - In `Application::activateView(...)`, when `create=true` and no view exists:
    - store created view: `auto* createdView = doc->createView(type)`
    - explicitly activate it: `doc->setActiveWindow(createdView)`

This removes the race/context gap at the source and benefits all callers.

## Regression Protection Added

- `tests/src/Mod/PartDesign/Gui/SketchWorkflowSetEdit.cpp`
  - Added source guard ensuring `Application::activateView` sets created view active
  - Existing guards also verify PartDesign sketch workflow keeps 3D-view activation before `setEdit`

## Impact

- Fixes the reported Start-page -> New Sketch -> XY flow instability
- Hardens FreeCAD against similar active-view-context regressions in other workflows that create views on demand
