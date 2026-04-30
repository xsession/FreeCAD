# E2 Build TypeScript Viewport Renderer

Status: proposed

## Outcome

Replace Qt-hosted Coin3D view ownership with a TypeScript-rendered viewport.

## Why This Matters

This is the visible center of the product. Without a usable TS viewport, the shell cannot become the production runtime no matter how complete the surrounding panels are.

## Primary Scope

- `src/Gui/View3DInventor*`
- `src/Gui/Quarter/**`
- `variants/asterforge/frontend/app`

## In Scope

- TS viewport host
- camera controls for familiar FreeCAD navigation
- basic scene rendering, selection, fit-all, and hide or show interactions

## Out of Scope

- every specialized overlay and visualization mode on day one
- complete VR or specialist viewer features

## Deliverables

- TS viewport implementation
- initial selection and camera integration against scene protocol
- parity notes for missing or deferred viewport features

## Repo Anchors

- `src/Gui/View3DInventor.cpp`
- `src/Gui/View3DInventorViewer.cpp`
- `src/Gui/Quarter/QuarterWidget.cpp`
- `src/Gui/Quarter/SoQTQuarterAdaptor.cpp`
- `variants/asterforge/frontend/app`

## Dependencies

- E1

## Acceptance Checklist

- open, navigate, select, hide/show, and fit-all work in the TypeScript shell on real models
- large-model inspection is viable enough for parity review
- viewport behavior is recognizable to existing FreeCAD users

## Risks And Notes

- this issue should be validated on large STEP imports and not only on trivial geometry