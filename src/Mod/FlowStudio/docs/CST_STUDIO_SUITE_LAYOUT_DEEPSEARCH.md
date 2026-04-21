# CST Studio Suite Inspired Workspace Blueprint

Version: 0.1
Date: 2026-04-21
Status: FlowStudio implementation note

## Purpose

This note captures the FlowStudio layout and workflow direction inspired by CST Studio Suite style project organization while remaining FreeCAD-native and solver-agnostic.

## Layout Principles Encoded in FlowStudio

- Left-side project tree remains the authoritative study navigator.
- Center viewport stays geometry-first, with domain overlays rather than standalone scene editors.
- Right-side properties and task panels are contextual and workflow-stage aware.
- Bottom panes concentrate jobs, logs, monitors, detector outputs, and results for execution-focused work.

## Domain Workspaces

- CFD: project tree, domains, mesh preview, residuals, and result scenes.
- Thermal: materials, heat loads, reports, and KPI-oriented bottom panes.
- Structural: bodies, load cases, constraints, mesh preview, and result plots.
- Electrostatic: dielectric setup, potentials, field regions, and probe outputs.
- Electromagnetic: components, excitations, frequency controls, monitors, and field results.
- Optical: optical components, sources and detectors, study controls, detector outputs, and optical result review.

## Workflow Direction

FlowStudio now treats workflows as domain profiles instead of a single generic checklist. The shared lifecycle is still:

1. Create study
2. Prepare geometry
3. Configure physics
4. Assign materials
5. Define excitations or boundaries
6. Prepare discretization
7. Review study controls
8. Run solver
9. Inspect results

Domain profiles override step names and hints where needed. The optical profile, for example, explicitly uses sources, detectors, and optical boundaries instead of CFD-style inlet or outlet language.

## Functional Implications

- Workflow guidance can now reflect the active physics domain without duplicating validation logic.
- Workspace metadata is available to GUI panels and future docking logic.
- Optical materials now carry richer preset data suitable for ray-tracing and wave-optics backends.

## Non-Goals

- No attempt is made to clone CST branding or exact screen composition.
- FlowStudio keeps FreeCAD document objects and Python automation as the source of truth.
- Solver adapters remain open and explicit rather than hidden behind opaque project state.