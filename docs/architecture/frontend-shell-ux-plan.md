# Frontend Shell UX Plan

## Purpose

This document defines how the FreeCAD frontend should organize the ribbon bar,
the workbench chooser, and the task panels so the application feels natural to
use for visually oriented engineering users, especially mechanical engineers.

The goal is not to imitate another CAD product blindly. The goal is to make the
current FreeCAD shell easier to read, easier to predict, and easier to learn
without discarding the existing workbench model, command system, docking model,
or Python extensibility.

This plan is based on the current frontend architecture in:

- `src/Gui/MainWindow.h`
- `src/Gui/Workbench.h`
- `src/Gui/WorkbenchSelector.h`
- `src/Gui/RibbonBar.h`
- `src/Gui/TaskView/TaskView.h`
- `src/Gui/TaskView/TaskDialog.h`
- `src/Gui/CommandSearch.h`
- `src/Mod/FlowStudio/InitGui.py`
- `src/Mod/FlowStudio/flow_studio/taskpanels/base_taskpanel.py`
- `src/Mod/FlowStudio/flow_studio/taskpanels/task_physics_model.py`
- `docs/architecture/ADR-0005-ribbon-bar-architecture.md`
- `docs/MODERNIZATION_PLAN.md`

## What A Mechanical Engineer Needs From The Shell

A visually minded engineering user does not think in terms of menus first. They
think in terms of:

1. What object am I working on?
2. What stage of the workflow am I in?
3. What are the next 3 likely actions?
4. Where do I see the result of the action immediately?
5. Where do I adjust the important parameters without losing spatial context?

That means the shell should optimize for:

- stable spatial memory
- workflow sequencing instead of command dumps
- visual grouping by intent, not by implementation detail
- short travel between object selection, command launch, and parameter editing
- progressive disclosure for advanced controls
- persistent access to search for expert users

The current architecture already supports most of the required primitives:

- workbench activation via `Workbench::activate()`
- multiple toolbar groups via `setupToolBars()` and Python `appendToolbar()`
- ribbon display via `Gui::RibbonBar`
- searchable command palette via `Gui::CommandSearch`
- docked task editing via `TaskView`
- contextual panels in task view via `TaskView::addContextualPanel()`

The main problem is not the absence of primitives. The problem is information
architecture.

## Design Principles

### 1. Object First

The left side should answer what exists. The center should answer what it looks
like. The right side should answer what it means and how it changes.

### 2. Workflow Before Taxonomy

Commands should be grouped by the order an engineer tends to use them, not by
module ownership or solver internals.

### 3. Stable Shell, Contextual Details

The shell layout should stay stable. Context should change inside a stable
frame. The user should not feel that the whole application rearranges itself
whenever a workbench changes.

### 4. Fewer But Stronger Choices

The ribbon should expose the most likely actions clearly. Rare actions should be
reachable through overflow, expanders, right-click actions, or search.

### 5. Edit On The Right, Read On The Left

Model structure belongs on the left. Detailed editing belongs on the right.
Properties and task editing should cooperate instead of competing for space.

### 6. Preview Before Commitment

Whenever possible, task panels should show a concise summary, validation state,
and preview impact before the user accepts changes.

## Target Shell Layout

The target shell should follow this pattern:

```text
+--------------------------------------------------------------------------------+
| QAT: Save Undo Redo Recompute | Workbench favorites | Search commands          |
+--------------------------------------------------------------------------------+
| File | Home | Model | Sketch | Part | Assembly | Simulation | Inspect | View   |
| Contextual tabs appear to the right only when editing a specific object type   |
+------------------------+--------------------------------+----------------------+
| Model / Selection      | 3D View                        | Properties / Task     |
| - document tree        | - primary spatial feedback     | - object properties   |
| - rollback / status    | - transient previews           | - edit panels         |
| - active object        | - selection cues               | - validation / apply  |
+------------------------+--------------------------------+----------------------+
| Report | Python | Selection Filter | Solver Output | Notifications             |
+--------------------------------------------------------------------------------+
```

This keeps a left-to-right narrative that matches how most engineers work:

- identify the object
- inspect the geometry
- edit the parameters

## Ribbon Bar Organization

## The Ribbon Should Not Mirror Toolbars

The ribbon is not just a different skin for many independent toolbars. If the
same command grouping used for classic toolbars is copied directly into ribbon
tabs, the result still feels fragmented.

The ribbon should be organized into a small number of stable top-level tabs with
clear semantics.

## Recommended Tab Model

### Stable Tabs

- `File`: backstage, document actions, settings, import/export
- `Home`: the most common actions for the active workbench
- `Model`: object creation and structural edits
- `Inspect`: measure, validate, diagnostics, sectioning, reports
- `View`: visibility, display, selection filters, panel visibility
- `Automate`: macros, scripts, command search entry points, batch actions

### Contextual Tabs

Contextual tabs should appear only when the user is in a focused editing mode.
They should never replace stable tabs; they should supplement them.

Examples:

- `Sketch` while editing a sketch
- `Part Design Feature` while editing a feature
- `Assembly Constraint` while editing mates or joints
- `Simulation Setup` while editing analysis objects
- `Results` while inspecting solver output or post-processing objects

This aligns with the existing `RibbonBar::showContextualTab()` API.

## Panel Rules

Each ribbon tab should contain 4 to 7 panels. Each panel should represent one
user intention, not one backend category.

Good panel names:

- Create
- Modify
- Constrain
- Validate
- Mesh
- Solve
- Results

Weak panel names:

- Utilities
- Misc
- Advanced 1
- Solver Extras
- Geometry Tools if it contains unrelated commands

Each panel should follow these rules:

- 1 primary command at large size when there is a dominant action
- 3 to 8 secondary commands at small size
- no more than 2 levels of grouping inside the panel
- no duplicate commands across many panels unless the command is core enough to
  belong in `Home`

## Home Tab Rule

The `Home` tab should answer one question: what are the next likely actions for
the current object or workflow stage?

For engineering workflows, that usually means:

- create or select the active analysis, body, sketch, or assembly object
- run the next operation in the sequence
- validate the setup
- launch edit for the current object

## Quick Access Toolbar Rule

The quick access toolbar should stay globally stable. It should contain only
high-frequency shell actions, not workbench-specific modeling commands.

Recommended defaults:

- Save
- Undo
- Redo
- Recompute
- Fit All
- Command Search

## Workbench Chooser Organization

## Problem To Solve

Workbench switching is powerful, but it is cognitively expensive when the user
must remember a long list of internal workbench names before they can even begin
the next task.

The workbench chooser should behave like a mode navigator, not a raw enum list.

## Recommended Interaction Model

### 1. Favorites First

Show the user's pinned or recent workbenches as visible tabs or segmented
buttons near the top of the shell.

Recommended default favorites for a mechanical-engineering profile:

- Start
- Part Design
- Sketcher
- Assembly
- TechDraw
- FlowStudio or FEM when simulation tooling is installed

### 2. Searchable All-Workbench Picker

The full workbench list should open from a compact `More` button or chooser
control and must support search. The current combo-box path is functional, but
it should expose grouping and recency.

Recommended categories:

- Modeling
- Assembly
- Simulation
- Documentation
- Data / Utility
- Experimental

### 3. Recent And Suggested Switching

The chooser should remember the most recent workbenches and bias them upward.
If the user selects a simulation object while in another workbench, the chooser
can suggest the relevant simulation workbench without forcing a switch.

### 4. Keep Names Human

Display names should prioritize task language over internal branding. For
example, a tooltip can say what the workbench is for, not just its name.

Examples:

- `Assembly`: assemble and constrain components
- `TechDraw`: create manufacturing drawings
- `FlowStudio`: configure CFD and multi-physics studies

## Task Panel Organization

## Core Rule

Task panels should guide an editing conversation. They should not be generic
forms dumped into a dock.

The current FlowStudio task panel base is intentionally simple, but it is still
too flat for complex engineering workflows. Most panels need a stronger
structure.

## Recommended Task Panel Anatomy

Every task panel should follow the same top-to-bottom pattern:

### 1. Header Summary

At the top, show:

- object name
- object type
- short sentence about what the panel changes
- current status badge if validation fails or setup is incomplete

### 2. Selection Context

If the command depends on faces, edges, bodies, or analysis objects, show the
current selection target early and prominently.

The user should never have to infer what the command is acting on.

### 3. Core Parameters

Only the most important parameters should be visible initially. These should fit
in the first viewport height when practical.

### 4. Advanced Group

Less common controls belong in collapsible groups or secondary boxes.

### 5. Validation And Preview

Before `OK`, show:

- missing inputs
- warnings
- expected downstream effect
- preview or summary when feasible

### 6. Sticky Action Area

The bottom of the panel should keep the main actions stable:

- OK / Apply
- Cancel
- Help when meaningful

For long panels, the action area should not disappear after scrolling.

## Visual Rules For Task Panels

- use grouped sections instead of long undifferentiated forms
- prefer explicit labels with units visible next to the field
- keep related toggles close to the affected numeric fields
- avoid placing destructive actions near accept
- use short helper text where a domain term is ambiguous
- use read-only summary fields for derived values rather than forcing the user
  to infer them

## Relationship Between Properties And Task Panels

Properties are for inspection and precise edits. Task panels are for guided,
goal-oriented editing.

The right side of the shell should behave as one coordinated editing area:

- when nothing is in edit mode, show properties prominently
- when an object enters edit mode, show the task panel as primary and preserve a
  lightweight object summary or contextual properties above or beside it
- after accept, return to properties without losing the right-side layout

This matches the existing `TaskView` architecture and can be improved through
contextual panels rather than by creating a new dock model.

## Recommended Information Architecture For FlowStudio

FlowStudio is a strong pilot candidate because its workflow is already mostly
sequential, but the current grouping in `src/Mod/FlowStudio/InitGui.py` still
mixes workflow stages, domain layers, and solver details.

Current issues in the ribbon/classic grouping:

- geometry commands are duplicated conceptually between setup and geometry
- electrical, electromagnetic, and optical commands appear as parallel toolbar
  blocks even when the active analysis is not of that type
- results are separated from setup, but not always connected to the current
  analysis state
- the user must understand command families before they understand workflow

## Proposed FlowStudio Tab Structure

### Stable Tabs

- `Home`
- `Setup`
- `Boundary Conditions`
- `Mesh & Solve`
- `Results`
- `Inspect`

### Contextual Tabs

- `CFD`
- `Thermal`
- `Structural`
- `Electrostatic`
- `Electromagnetic`
- `Optical`

The contextual domain tab should appear only when the active analysis belongs to
that domain or when editing an object owned by that domain.

## Proposed FlowStudio Panel Structure

### Home

- Analysis: new analysis, switch active analysis
- Edit: physics model, fluid material, initial conditions
- Validate: check geometry, show fluid volume, leak tracking
- Solve: solver settings, run solver

### Setup

- Analysis Type: create CFD, thermal, structural, electrostatic,
  electromagnetic, optical analyses
- Materials: fluid, optical, electrostatic, electromagnetic material depending
  on active domain
- Physics: physics model, optical physics, electrostatic physics,
  electromagnetic physics

### Boundary Conditions

- Inlets / Outlets
- Walls / Symmetry / Open boundaries
- Sources: fan, volume source, optical source, detector

### Mesh & Solve

- Mesh: gmsh, mesh region, boundary layer
- Solve Setup: solver settings
- Run: run solver, enterprise submit if available

### Results

- Field Plots: surface plot, cut plot, contour
- Traces: streamlines, trajectories, particle study
- Probes And Reports: point parameters, XY plot, force report,
  Paraview export

### Inspect

- Diagnostics: geometry check, leak tracking, mesh quality
- Selection: isolate selected regions, inspect applied boundary conditions
- Reports: setup completeness, missing data, solver log shortcuts

## Task Panel Pattern For FlowStudio

FlowStudio panels should adopt a consistent pattern across all task panels.

Example for `TaskPhysicsModel`:

- Header: `Physics Model for AnalysisName`
- Context: current analysis type and target fluid domain
- Core: flow regime, turbulence model, compressibility, time model
- Couplings: gravity, heat transfer, buoyancy, free surface
- Advanced: passive scalar and uncommon solver knobs
- Validation: compatibility warnings, for example turbulent model hidden or
  disabled for laminar flow
- Footer: apply, cancel, help

This is more intuitive than a flat list because it reflects how an engineer
thinks about setup dependencies.

## Implementation Plan For Current FreeCAD Frontend

## Phase 0: Lock The Shell Contract

Do not rewrite the frontend stack. Use the current shell contract:

- `MainWindow` remains the host shell
- `Workbench` remains the unit of activation
- `RibbonBar` remains the top command surface
- `TaskView` remains the edit dock
- Python workbenches continue to register commands and toolbars

This keeps adoption incremental and compatible with existing workbenches.

## Phase 1: Improve Workbench Chooser Behavior

Target files:

- `src/Gui/WorkbenchSelector.h`
- `src/Gui/WorkbenchSelector.cpp`
- `src/Gui/Action.h`
- `src/Gui/Action.cpp`

Changes:

- add favorite workbench support
- add recent-workbench ordering
- add category metadata or a lightweight mapping table
- add searchable all-workbench popup from the chooser
- keep combo-box and tab-widget modes, but improve their information density

Acceptance criteria:

- a new user can reach the 5 most relevant workbenches without opening a long
  list
- an expert user can switch workbenches in 1 to 2 interactions
- workbench names show a one-line purpose tooltip

## Phase 2: Make Ribbon Tabs Workflow-Driven

Target files:

- `src/Gui/RibbonBar.h`
- `src/Gui/RibbonBar.cpp`
- `src/Gui/CommandSearch.h`
- `src/Gui/CommandSearch.cpp`

Changes:

- introduce stable shell tabs that persist across workbenches
- reserve contextual tabs for edit-mode or domain-mode situations
- allow workbenches to declare ribbon intent metadata, not just toolbar names
- keep command search permanently reachable in the ribbon area
- support a panel-level overflow or expand affordance for long command sets

Acceptance criteria:

- the active workbench exposes a predictable `Home` tab
- contextual tabs appear only when the context is strong enough to justify them
- the number of simultaneously visible panels stays readable on common laptop
  widths

## Phase 3: Standardize The Right-Side Editing Area

Target files:

- `src/Gui/TaskView/TaskView.h`
- `src/Gui/TaskView/TaskView.cpp`
- `src/Gui/TaskView/TaskDialog.h`
- `src/Gui/TaskView/TaskDialog.cpp`

Changes:

- add a standard summary slot above task dialogs
- support persistent contextual panels for object state and validation
- preserve panel width and action button placement more aggressively
- define a standard task panel section model for workbench authors

Acceptance criteria:

- the right side behaves like one editing surface rather than two unrelated
  docks
- users can see what they are editing, what is missing, and how to finish the
  command without scrolling through an unstructured form

## Phase 4: Pilot The Pattern In FlowStudio

Target files:

- `src/Mod/FlowStudio/InitGui.py`
- `src/Mod/FlowStudio/flow_studio/taskpanels/base_taskpanel.py`
- `src/Mod/FlowStudio/flow_studio/taskpanels/*.py`
- `src/Mod/FlowStudio/flow_studio/viewproviders/*.py`

Changes:

- reorganize FlowStudio command groups into workflow tabs and contextual domain
  tabs
- remove conceptually duplicated command placement
- update the base task panel to support summary, grouped sections, validation,
  and optional advanced blocks
- make view providers show richer contextual edit information through the task
  view path that already exists

Acceptance criteria:

- a CFD user can complete analysis setup in a clear left-to-right workflow
- a non-CFD analysis does not expose irrelevant CFD-specific commands by default
- task panels across FlowStudio feel structurally consistent

## Phase 5: Roll Out To Other Workbenches Through A Small UI Contract

Add a lightweight frontend contract for workbench authors.

Possible metadata fields:

- preferred home tab commands
- stable tab membership
- contextual tab triggers
- workbench category
- task panel summary provider

Current extracted contract in code:

- `Ribbon::<Tab>::<Panel>` for stable tab membership and panel naming
- `::Home` to opt a panel into the synthesized `Home` tab
- `::Order=<n>` to stabilize panel ordering within a tab and on `Home`
- `RibbonContext::<Tab>::<Panel>[::Workbench=<name>][::Types=a,b][::Color=#rrggbb][::Order=<n>]` for declarative contextual ribbon panels driven by edit context
- `Gui.registerContextualRibbonPanel(name, commands)` lets a workbench contribute contextual ribbon panels without depending on the active workbench’s toolbar collection
- `src/Gui/RibbonMetadata.py` centralizes Python-side metadata name generation for adopting workbenches

This can start in Python workbenches and later gain a C++ path.

Current implementation status:

- FlowStudio now uses the ribbon metadata contract in ribbon mode
- Assembly now uses the same contract for its `Workflow` and `Joints` panels in ribbon mode
- CAM now uses the same contract in ribbon mode for `Job Setup`, `Tools & Simulation`, `Operations`, and `Path Modification`
- task panel summary metadata is available to Python workbenches through the existing task dialog bridge
- FlowStudio now declares its `Simulation` contextual tab through contextual ribbon metadata instead of a FlowStudio-specific `RibbonBar.cpp` branch
- Assembly now declares its `Assembly` contextual tab through the same contextual ribbon metadata contract
- Assembly's declarative contextual tab now also preserves a dedicated `Joint Presets` panel so the metadata-driven path does not flatten the richer joint workflow into only generic command groups
- FlowStudio and Assembly now register their contextual ribbon panels through the GUI application layer, so those contextual definitions remain available even when another workbench owns the visible toolbar set
- Sketcher now registers its edit-context ribbon panels from the C++ workbench itself, reusing the real toolbar command groups instead of a RibbonBar-owned special case
- `RibbonBar.cpp` no longer contains any Sketch-specific contextual panel definitions; contextual tabs are now materialized only from declarative metadata and the shared registry
- `src/Mod/FlowStudio/flow_studio/tests/test_ribbon_shell_contract.py` now provides headless regression coverage for the shared ribbon helper, GUI API, FlowStudio, Assembly, CAM, Sketcher registration, and the absence of the old Sketch-specific `RibbonBar` branch
- `tests/test_ribbon_contextual_tabs.py` now provides a GUI runtime harness that enables ribbon mode, enters Sketch, Assembly, and FlowStudio edit contexts, and checks that their contextual tabs appear and disappear again after reset-edit; it is intended to run through `run_freecad.bat` inside a real FreeCAD GUI session
- `tools/build/run_ribbon_context_validation.bat` now wraps that GUI harness and sets a deterministic report path so a runtime validation pass leaves a file artifact even when `FreeCAD.exe` does not stream reliable terminal output

## Phase 6: Validate With Engineering Workflows

Test with real scenarios instead of only command coverage.

Mechanical workflow examples:

- create part, sketch, pad, fillet, drawing export
- open assembly, edit mate, inspect interference, update drawing
- create flow analysis, assign material, set inlet and outlet, mesh, solve,
  inspect results

Measure:

- time to first successful setup
- number of panel switches
- number of failed or canceled edit attempts
- command search usage rate
- workbench switch frequency during one workflow

## Concrete Application Order

The most practical order for the current codebase is:

1. Improve workbench chooser discoverability in C++
2. Stabilize ribbon semantics in C++
3. Strengthen task view structure in C++
4. Use FlowStudio as the first workflow-oriented pilot in Python
5. Extract the reusable contract for additional workbenches

This order reduces risk because it improves the shell primitives before asking
each workbench to adopt new structure.

## Non-Goals

- replacing the docking framework
- removing classic toolbar mode immediately
- forcing all workbenches into one universal tab set on day one
- rewriting workbench activation or the command system
- moving task panels out of the right dock into modal dialogs

## Summary

For a visually minded mechanical engineer, the shell should feel like a guided
workspace, not a toolbox warehouse.

That means:

- a ribbon organized by workflow stage
- a workbench chooser organized by human intent and recency
- task panels organized as guided edit narratives
- stable shell structure with contextual detail layered in

FreeCAD already has the underlying architecture to do this. The next step is to
apply a stronger information architecture on top of the current `MainWindow`,
`RibbonBar`, `WorkbenchSelector`, and `TaskView` systems, then prove the model
through a FlowStudio pilot.