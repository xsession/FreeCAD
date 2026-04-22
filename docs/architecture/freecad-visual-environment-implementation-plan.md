# FreeCAD Visual Environment Implementation Plan

Version: 0.1
Date: 2026-04-22
Status: Action plan for current frontend

## Purpose

This document converts the research and design direction from
`docs/architecture/freecad-visual-environment-deepsearch.md` into an
implementation plan that can be executed against the current FreeCAD frontend.

Companion execution backlog:

- `docs/architecture/freecad-visual-environment-backlog.md`

The plan assumes the existing shell remains in place:

- `MainWindow`
- dock windows
- ribbon bar
- workbench model
- task view
- Python and C++ workbench registration

## Delivery Strategy

Apply the visual-environment improvements in layers:

1. Improve shell wayfinding first
2. Standardize the right-side editing experience
3. Improve viewport legibility and visible system state
4. Pilot the full pattern in FlowStudio
5. Reuse the resulting contract across major workbenches

This order is deliberate. If the shell remains ambiguous, improving isolated
dialogs will not materially change usability.

## Current Progress Snapshot

Status as of 2026-04-22:

- Phase 1 is substantially implemented for the pilot path: workbench purpose
   metadata, searchable overflow, and stronger `Home` tab behavior are in code.
- Phase 2 is implemented as a reusable task-view contract: summary and
   validation metadata now flow from Python task panels into the shared C++
   task dialog surface, including live refresh while widgets change.
- Phase 3 is implemented for the first visible slice: selection and
   preselection defaults are aligned, selection bounding boxes are stronger, and
   the 3D viewer now exposes a compact state badge for ready, modified,
   recomputing, pending, and skip-recompute states.
- Phase 4 is in active pilot rollout: FlowStudio now uses workflow-oriented
   stable tabs, contextual domain tabs, and summary-first task panels. The
   latest pass extended the shared validation contract across additional
   boundary-condition and setup/result panels so open, outlet, wall, inlet,
   mesh, solver, initial conditions, fluid material, domain materials,
   measurement probes, measurement surfaces/volumes, geometry helpers,
   Geant4 result surfaces, result plots, and post-processing surfaces follow
   the same guidance pattern.

Still open:

- broader FlowStudio task-panel consistency across remaining setup and result
   panels
- richer viewport overlays for edit targets and domain-specific cues
- cross-workbench rollout beyond the FlowStudio pilot

## Phase 1: Shell Wayfinding

Goal: make navigation, mode switching, and likely next actions obvious.

### Scope

- workbench favorites and recency
- searchable workbench overflow
- clearer `Home` tab semantics
- stronger command search integration
- stable, human-readable workbench descriptions

### Target Files

- `src/Gui/Action.cpp`
- `src/Gui/Action.h`
- `src/Gui/WorkbenchSelector.cpp`
- `src/Gui/WorkbenchSelector.h`
- `src/Gui/CommandSearch.cpp`
- `src/Gui/CommandSearch.h`
- `src/Gui/RibbonBar.cpp`
- `src/Gui/RibbonBar.h`

### Tasks

1. Add or refine workbench purpose metadata so overflow and tooltips answer what
   the workbench is for.
2. Add searchable workbench overflow with favorite and recent bias preserved.
3. Ensure the `Home` tab surfaces likely next actions for the active workbench,
   not only inherited toolbar groups.
4. Extend command search with recent commands and active-workbench relevance.
5. Ensure the quick-access area stays globally stable and does not become a
   second ribbon.

### Acceptance Criteria

1. A new user can reach the main mechanical workbenches without scanning a long
   unordered list.
2. The visible top shell explains what mode the user is in and what the likely
   next actions are.
3. Command search accelerates expert flow but is not required to compensate for
   poor discoverability.

### Suggested Tests

- GUI unit or behavior tests for favorite and recent ordering
- source-level regression tests for workbench selector population
- tests for `Home` tab generation rules where feasible

## Phase 2: Right-Side Editing Contract

Goal: make properties and task panels feel like one guided editing surface.

### Scope

- task summary standardization
- grouped sections and advanced sections
- validation summaries
- stable action placement
- clearer relationship between inspect mode and edit mode

### Target Files

- `src/Gui/TaskView/TaskView.cpp`
- `src/Gui/TaskView/TaskView.h`
- `src/Gui/TaskView/TaskDialogPython.cpp`
- `src/Gui/TaskView/TaskDialog.h`
- `src/Mod/FlowStudio/flow_studio/taskpanels/base_taskpanel.py`

### Tasks

1. Formalize task summary fields as a supported task-panel contract.
2. Add optional validation-summary support above the dialog content.
3. Define a standard section pattern for core settings, advanced settings, and
   context summary.
4. Keep the action area visually stable for long forms.
5. Make it clear when the right side is in inspect mode versus guided edit mode.

### Acceptance Criteria

1. Every guided edit begins with object identity, purpose, and current state.
2. Most task panels expose core settings in the first visible viewport.
3. Missing inputs and warnings are visible before confirmation.

### Suggested Tests

- source-level tests for task summary metadata
- task-panel runtime smoke tests
- visual regression checks for summary rendering if test coverage allows it

## Phase 3: Viewport Legibility And State Feedback

Goal: make the viewport communicate intent, state, and confidence rather than
only rendering geometry.

### Scope

- selection and preselection quality
- professional visual defaults
- visible recompute or execution state
- contextual overlays for edit-heavy workflows
- smoother navigation behavior where already supported

### Target Files

- `src/Gui/View3DInventorViewer.cpp`
- `src/Gui/View3DInventorViewer.h`
- `src/Gui/Selection/SoFCUnifiedSelection.cpp`
- `src/Gui/ViewParams.h`
- rendering and background helper files already referenced in
  `docs/INVENTOR_QUALITY_ROADMAP.md`

### Tasks

1. Audit default visual parameters against readability criteria.
2. Keep selection colors strong but professional.
3. Add or improve visible signals for dirty, recomputing, and pending result
   states near the viewport.
4. Define overlay patterns for edit targets, constraints, BCs, loads, and
   result planes where relevant.
5. Make standard views and navigation transitions feel smooth and predictable.

### Acceptance Criteria

1. Active selections are unmistakable.
2. The viewport communicates whether the model is ready, dirty, or updating.
3. Visual improvements improve engineering interpretation, not only aesthetics.

Implementation note:

- The current viewer implementation includes a compact state badge in
   `View3DInventorViewer` that reacts to touch, recompute, undo, redo, and save
   transitions. This satisfies the first visible system-status slice while
   leaving room for richer domain overlays later.

### Suggested Tests

- targeted GUI behavior tests for selection-state rendering hooks
- preference-based tests for visual-default values when practical

## Phase 4: FlowStudio Full Pilot

Goal: prove the complete visual-environment model in a workflow-heavy workbench.

### Scope

- workflow-shaped ribbon organization
- domain-aware contextual tabs
- sectioned task panels
- clearer validation and progression cues
- bottom-pane execution visibility
- domain-specific docking emphasis from layout metadata

### Target Files

- `src/Mod/FlowStudio/InitGui.py`
- `src/Mod/FlowStudio/flow_studio/ui/layouts.py`
- `src/Mod/FlowStudio/flow_studio/taskpanels/*.py`
- `src/Mod/FlowStudio/flow_studio/viewproviders/*.py`
- `src/Mod/FlowStudio/docs/*.md`

### Tasks

1. Keep stable FlowStudio tabs aligned to setup, inspect, solve, and results.
2. Reveal domain-specific contextual tabs only when the active analysis or
   object justifies them.
3. Continue converting flat forms into grouped, summary-first task panels.
4. Add local validation summaries that explain what is missing and what comes
   next.
5. Use layout metadata to define docking presets by domain where practical.
6. Improve bottom-pane messaging for job state, logs, monitors, and results.

### Acceptance Criteria

1. A user can move from analysis creation to results review with minimal shell
   ambiguity.
2. Irrelevant domain commands are not shown as first-class actions by default.
3. FlowStudio task panels feel structurally consistent across object types.

Implementation note:

- The current pilot already covers solver, mesh, inlet, outlet, wall, open
   boundary, initial conditions, fluid material, material assignment,
   measurement probes/surfaces/volumes, geometry helpers, Geant4 result
   panels, result plots, particle studies, generic boundary conditions,
   physics model, post-processing, and enterprise job panels with the shared
   summary/validation contract. Remaining work is now primarily cleanup,
   selective refinement, and broader build/runtime validation rather than new
   panel adoption.

### Suggested Tests

- extend `test_taskpanel_wiring.py`
- extend `test_taskpanel_runtime_smoke.py`
- add tests for layout metadata and contextual-tab exposure where possible

## Phase 5: Cross-Workbench Contract Rollout

Goal: make the improvements reusable without forcing a large migration.

### Candidate Workbenches

- Sketcher
- Part Design
- Assembly
- TechDraw
- FEM

### Contract Elements

- workbench purpose metadata
- stable-tab and `Home` membership metadata
- contextual-tab trigger metadata
- task summary metadata
- optional validation summary metadata
- optional advanced-section grouping hints

### Target Files

- `src/Gui/RibbonMetadata.py`
- workbench `InitGui.py` files and C++ workbench registration points
- workbench-specific task panels and edit dialogs

### Tasks

1. Publish a small frontend authoring contract for workbench maintainers.
2. Apply the contract to Sketcher, Part Design, and Assembly first.
3. Avoid bespoke frontend branches in the ribbon for each workbench when the
   metadata path is sufficient.
4. Keep classic toolbar mode operational while improving ribbon mode.

### Acceptance Criteria

1. Major workbenches share common edit and navigation language.
2. Contextual tabs are driven by declared metadata instead of per-workbench
   special casing wherever practical.
3. Users can move between major workbenches without relearning state cues.

## Phase 6: Mechanical Workflow Validation

Goal: verify the frontend changes improve real engineering tasks.

### Validation Scenarios

1. Start page to first sketch to padded part
2. Edit part, inspect feature order, adjust dimensions, regenerate
3. Open assembly, insert or constrain parts, inspect motion or collision
4. Create simulation setup, assign materials and BCs, mesh, solve, inspect
   results
5. Generate drawing or report output from a completed model

### Metrics

- time to successful completion
- number of shell transitions per workflow
- number of canceled edit attempts
- command-search reliance per workflow
- number of errors detected only after accept
- user confidence and perceived predictability during test sessions

### Exit Criteria

Ship the pattern forward only when it reduces ambiguity and interaction count on
real tasks, not only when the underlying code is cleaner.

## Backlog Summary

## Immediate Backlog

1. Add workbench-purpose metadata and improved overflow/search behavior.
2. Formalize task summary and validation-summary support in the right-side edit
   surface.
3. Audit viewport selection and state-feedback defaults.
4. Continue FlowStudio task-panel conversion using the summary-first grouped
   pattern.

## Next Backlog

1. Add contextual overlays and richer visible system status near the viewport.
2. Add domain-aware docking presets for FlowStudio.
3. Roll the contract into Sketcher and Assembly.

## Deferred Backlog

1. Larger rendering-pipeline work from `docs/INVENTOR_QUALITY_ROADMAP.md`
2. Advanced guided workflows or wizard flows for carefully selected linear
   operations
3. Deeper telemetry or usage-informed tuning of `Home` actions and disclosure
   defaults

## Risks

### Risk 1: Improving individual dialogs without fixing shell ambiguity

Mitigation: keep Phase 1 ahead of broad workbench dialog cleanup.

### Risk 2: Overfitting to one workbench

Mitigation: extract a small reusable contract after the FlowStudio pilot rather
than baking pilot assumptions into `src/Gui`.

### Risk 3: Reintroducing special-case ribbon logic

Mitigation: prefer metadata-driven contextual tabs and panel registration.

### Risk 4: Making expert users slower

Mitigation: preserve command search, shortcuts, and direct command access while
improving visual discoverability.

## Summary

The correct implementation path is incremental and architecture-aware:

- improve wayfinding first
- standardize the right-side edit narrative
- improve viewport legibility and visible state
- prove the full pattern in FlowStudio
- extract the contract and reuse it across major workbenches

This keeps the current FreeCAD frontend intact while materially improving how a
visually oriented mechanical engineer experiences it.