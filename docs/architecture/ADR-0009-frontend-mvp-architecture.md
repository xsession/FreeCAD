# ADR-0009 – Frontend MVP architecture for FreeCAD

**Status:** Proposed  
**Date:** 2026-04-25

## Context

FreeCAD's frontend currently combines several concerns inside the same classes and modules:

- desktop view code (`Qt`, `FreeCADGui`, `TaskView`, ribbon, docks)
- workflow orchestration and user-intent routing
- document and object mutation
- backend service access
- summary and validation state construction

This mixing exists in both major frontend surfaces:

- C++ shell and task-dialog code under `src/Gui/`
- Python workbench and task-panel code under `src/Mod/*`

The result is manageable for isolated dialogs, but it becomes expensive when we want to:

- make shell behavior consistent across workbenches
- test frontend logic without a full GUI runtime
- support alternative frontend technologies later, including web-based clients
- prevent every workbench from re-implementing its own task-state, validation, and command wiring model

Recent FlowStudio work has already demonstrated the value of an MVP split:

- `flow_studio.ui.project_cockpit_presenter` now shapes toolkit-neutral view state
- `flow_studio.app.project_cockpit_service` now provides backend-facing use-case access
- desktop-specific actions are isolated behind a FreeCAD adapter
- `flow_studio.ui.mesh_gmsh_presenter` and `flow_studio.app.mesh_gmsh_service` apply the same pattern to a task panel

These pilot slices show that FreeCAD can evolve toward a more explicit frontend architecture without an all-at-once rewrite.

## Decision

Adopt Model-View-Presenter as the default frontend organization principle for new work and incremental refactors.

The canonical layering is:

```text
Document / domain model
    ↓
Application services / use cases
    ↓
Presenters / view-state builders
    ↓
View adapters (Qt task panels, ribbon widgets, dock panels, future web views)
    ↓
Desktop integration adapters (FreeCADGui, TaskView, selection, edit routing)
```

### Layer responsibilities

#### 1. Model

The model layer contains document objects, geometry, topology, solver inputs, and canonical domain state.

Examples:

- `App::Document` and `App::DocumentObject`
- FreeCAD object properties and recompute state
- FlowStudio analysis objects and solver configuration objects

The model does not know about task panels, ribbon state, or desktop widgets.

#### 2. Application services

Application services expose use cases in a frontend-neutral way.

Examples:

- load current workflow context
- persist task-panel settings to an object
- launch mesh generation
- query run status and sync result surfaces
- activate edit routes through a stable application entry point

Rules:

- no direct Qt widget code
- no assumptions about a specific desktop layout
- may depend on document/domain/runtime code
- should be testable in headless or pure-Python / non-GUI contexts when practical

#### 3. Presenters

Presenters translate application/service output into view-ready state.

Examples:

- task validation banners
- summary text
- workflow step rows
- button enabled/blocked state
- result-opening intent decisions

Rules:

- no direct `FreeCADGui` or Qt widget calls
- no direct control ownership of dialogs/docks
- no direct mutation of the GUI tree
- return serializable or plain data structures when practical

#### 4. Views

Views render presenter state and forward user intents.

Examples:

- `TaskView` panels
- ribbon panels and contextual tabs
- dock widgets
- future web components

Rules:

- keep layout and widget concerns local
- delegate non-trivial decisions to presenters
- avoid direct backend access except through explicit adapters

#### 5. Desktop adapters

Desktop adapters isolate concrete FreeCAD/Qt behavior that cannot be made frontend-neutral.

Examples:

- `FreeCADGui.runCommand(...)`
- `ActiveDocument.setEdit(...)`
- selection APIs
- task-dialog show/close integration
- ribbon refresh entry points

Rules:

- keep them thin
- treat them as replaceable integration edges
- do not let them become a second business-logic layer

## Repository mapping

### C++ frontend (`src/Gui`)

Target organization:

- shell widgets remain in `src/Gui/`
- shared shell-state policies move toward application/service-style helpers
- task-dialog state shaping should move out of concrete widgets where possible
- `MainWindow`, ribbon, and task-surface integration should call stable orchestration APIs rather than embed workflow-specific logic

### Python workbenches (`src/Mod/*`)

Target organization:

- `*.app` packages hold use cases and backend-facing services
- `*.ui` packages hold presenters and view-state helpers
- `taskpanels/` hold Qt views and thin desktop adapters
- `commands.py` and workbench init files remain registration/integration shells, not the home of workflow logic

## Mandatory rules for new code

1. New non-trivial task panels should shape UI state through a presenter.
2. New presenter logic should depend on app-layer services, not on raw desktop APIs.
3. Direct `FreeCADGui` calls for command execution, selection, or edit routing should be isolated in adapters when the logic is expected to outlive the current desktop frontend.
4. Validation, summary, and next-step logic should not be buried inside Qt widget event handlers.
5. New tests should prefer pure presenter/service coverage first, with runtime smoke coverage for key integrations.

## Incremental migration strategy

Migration is explicitly incremental, not a flag-day rewrite.

Priority order:

1. high-frequency task panels and workflow entry points
2. shell-state orchestration in `src/Gui/`
3. command registration shells that still own business logic
4. workbench-specific right-side editing surfaces
5. optional alternative frontends after stable service/presenter contracts exist

## Consequences

**Positive:**

- frontend logic becomes easier to test without a full GUI runtime
- workbench behavior becomes easier to standardize
- desktop-specific APIs become explicit integration boundaries
- future web or hybrid frontends have a realistic migration path

**Negative:**

- more files and explicit indirection
- temporary duplication while legacy and MVP-style surfaces coexist
- some legacy dialogs will remain mixed for a long time unless migration is enforced slice by slice

## Current pilot examples

- `src/Mod/FlowStudio/flow_studio/app/project_cockpit_service.py`
- `src/Mod/FlowStudio/flow_studio/ui/project_cockpit_presenter.py`
- `src/Mod/FlowStudio/flow_studio/taskpanels/project_cockpit_desktop_actions.py`
- `src/Mod/FlowStudio/flow_studio/app/mesh_gmsh_service.py`
- `src/Mod/FlowStudio/flow_studio/ui/mesh_gmsh_presenter.py`

These are not the end state of the repository; they are the initial reference pattern for future migration.