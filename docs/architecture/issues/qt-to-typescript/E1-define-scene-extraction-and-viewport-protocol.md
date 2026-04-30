# E1 Define Scene Extraction and Viewport Protocol

Status: proposed

## Outcome

Establish the payload boundary between native geometry and TS viewport rendering.

## Why This Matters

The viewport is one of the hard blockers for Qt retirement. A real shell migration needs an explicit scene boundary instead of implicit Qt plus Coin3D ownership.

## Primary Scope

- `variants/asterforge/protocol`
- `variants/asterforge/native/freecad-bridge`
- viewport extraction points in `src/Gui/ViewProvider*`

## In Scope

- scene payload boundaries
- geometry identity and selection identifiers
- visibility, transform, and material metadata required for first-pass rendering
- camera and scene update strategy at the contract level

## Out of Scope

- complete renderer implementation
- every advanced visualization mode on first slice

## Deliverables

- scene protocol draft
- field-level reasoning for required viewport data
- extraction-point inventory for current view providers and viewer code

## Repo Anchors

- `variants/asterforge/protocol`
- `variants/asterforge/native/freecad-bridge`
- `src/Gui/ViewProviderDocumentObject.cpp`
- `src/Gui/ViewProviderLink.cpp`
- `src/Gui/ViewProviderPart.cpp`
- `src/Gui/View3DInventor.cpp`

## Dependencies

- ADR-0010 follow-on decision for viewport transport

## Acceptance Checklist

- the scene protocol can carry visible geometry, transforms, visibility, and selection identifiers
- backend and frontend teams can use the same contract vocabulary for viewport state
- the contract is sufficient to begin TS renderer work without hidden Qt dependencies

## Risks And Notes

- avoid designing a transport that merely mirrors Coin3D internals instead of the shell’s actual needs