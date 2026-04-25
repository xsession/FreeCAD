# FreeCAD MVP Migration Plan

Version: 0.1  
Date: 2026-04-25  
Status: Active migration guide

## Purpose

This document translates `ADR-0009-frontend-mvp-architecture.md` into a practical migration sequence for the current FreeCAD codebase.

It does not assume a rewrite of the whole repository. It defines how to move the existing frontend toward MVP in thin, testable slices.

## Target outcome

When this migration is substantially complete:

- frontend state shaping is mostly outside concrete widgets
- desktop integration points are explicit and thin
- workflow logic is testable without always launching the full GUI
- alternative frontends become feasible because core use cases are no longer trapped inside Qt panels and command handlers

## Layer contract

### Model

- document objects
- property state
- recompute and solver artifacts
- geometry/topology/domain state

### App service

- reads and mutates model state for a use case
- calls backend/runtime helpers
- owns workflow-oriented operations

### Presenter

- turns service/model output into view state
- decides validation, summaries, enabled state, and next-action guidance
- routes user intents through abstract action ports when needed

### View / adapter

- renders widgets
- forwards user actions to the presenter
- contains desktop-only code where necessary

## Migration workstreams

### Workstream A: Task panels

Goal:

- move task-panel logic out of Qt widget classes

Priority order:

1. project cockpit
2. mesh generation
3. solver settings
4. material and boundary-condition panels
5. geometry and post-processing panels

Acceptance for each task panel:

- validation is presenter-owned
- settings persistence is service-owned
- complex action execution is service-owned
- direct `FreeCADGui` calls are isolated to the view or a dedicated adapter
- at least one pure presenter/service test exists

### Workstream B: Command registration

Goal:

- convert `commands.py` files into thin registration shells

Target state:

- command classes gather UI entry parameters only
- backend actions move into app services
- command handlers call stable use cases rather than directly assembling domain state inline

Acceptance:

- creating analyses, launching workflows, and high-frequency study setup routes are service-driven

### Workstream C: Shell-state orchestration in `src/Gui/`

Goal:

- move shell replay and edit-entry logic toward application-level orchestration instead of per-widget branching

Priority slices:

1. task-dialog show/close and edit-entry replay
2. workbench shell refresh
3. contextual tab activation rules
4. inspector/task-surface normalization

Acceptance:

- shell decisions depend on shared orchestration helpers rather than duplicated widget-local logic

### Workstream D: Desktop action adapters

Goal:

- isolate concrete `FreeCADGui` actions behind replaceable adapters where the logic is expected to be reused by presenters or future frontends

Examples:

- command execution
- active-document edit routing
- selection read/write
- dialog show/close

Acceptance:

- no new presenter should need direct `FreeCADGui` imports for command or edit routing

## Current migration status

### Completed pilot slices

- FlowStudio project cockpit:
  - app service
  - presenter
  - desktop action adapter
  - pure presenter tests
  - runtime smoke
- FlowStudio Gmsh mesh panel:
  - app service
  - presenter
  - task-panel wiring
  - pure presenter tests
  - runtime metadata smoke coverage

### In progress

- extending the same pattern from pilot panels to more selection-heavy and document-mutating panels
- pushing more shell-state behavior in `src/Gui/` toward explicit orchestration

## Rules for future refactors

1. Do not rewrite whole workbenches at once.
2. Choose one user-visible slice with a clear validation path.
3. Extract service first when backend mutation is tangled.
4. Extract presenter when validation/summary/action-state logic is tangled.
5. Keep the legacy widget layout while moving logic behind it.
6. Add pure tests before relying on GUI smoke tests.

## Suggested next slices

### P0

- FlowStudio solver task panel
- FlowStudio material task panel
- one PartDesign high-frequency task dialog using the same summary/validation contract

### P1

- command-side analysis creation services
- shared desktop action adapters for common task-panel actions
- ribbon/taskview shell orchestration helpers in `src/Gui/`

### P2

- selection-heavy geometry tools
- post-processing panels
- web/frontend proof-of-concept backed by an MVP-style presenter/service pair