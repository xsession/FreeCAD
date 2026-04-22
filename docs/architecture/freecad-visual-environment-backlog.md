# FreeCAD Visual Environment Backlog

Version: 0.1
Date: 2026-04-22
Status: Execution backlog

## Purpose

This backlog translates the visual-environment strategy and implementation plan
into concrete work items that can be scheduled and implemented in the current
FreeCAD frontend.

Related documents:

- `docs/architecture/freecad-visual-environment-deepsearch.md`
- `docs/architecture/freecad-visual-environment-implementation-plan.md`
- `docs/architecture/freecad-visual-environment-p0-roadmap.md`
- `docs/architecture/frontend-shell-ux-plan.md`

## Priority Model

- `P0`: foundational; blocks broader rollout or causes recurring ambiguity
- `P1`: high-value; should follow immediately after P0
- `P2`: valuable polish or expansion after the pilot path is proven
- `P3`: deferred or exploratory

## Workstream A: Shell Wayfinding

### VENV-001 Workbench Purpose Metadata

- Priority: `P0`
- Goal: make workbench switching feel like mode switching, not raw name lookup
- Target files:
  - `src/Gui/Action.cpp`
  - `src/Gui/WorkbenchSelector.cpp`
  - workbench registration files as needed
- Deliverables:
  - one-line purpose text for major workbenches
  - stronger tooltips in primary and overflow workbench surfaces
  - consistent human-readable wording
- Acceptance:
  - a user can infer the purpose of a workbench without already knowing its
    internal name

### VENV-002 Searchable Workbench Overflow

- Priority: `P0`
- Goal: avoid long cognitive scans through workbench overflow surfaces
- Target files:
  - `src/Gui/WorkbenchSelector.cpp`
  - `src/Gui/WorkbenchSelector.h`
- Deliverables:
  - searchable overflow or popup path for all workbenches
  - preserve favorites and recents as ranking signals
- Acceptance:
  - a user can reach a non-pinned workbench in one short search interaction

### VENV-003 Stable Home Tab Semantics

- Priority: `P0`
- Goal: ensure the `Home` tab always represents likely next actions
- Target files:
  - `src/Gui/RibbonBar.cpp`
  - `src/Gui/RibbonBar.h`
  - `src/Gui/RibbonMetadata.py`
- Deliverables:
  - documented selection rules for `Home`
  - heuristics or metadata tuning for major workbenches
- Acceptance:
  - `Home` is understandable and useful in each major workbench, not just
    technically populated

### VENV-004 Command Search Relevance Tuning

- Priority: `P1`
- Goal: make command search reflect active workbench and recent usage
- Target files:
  - `src/Gui/CommandSearch.cpp`
  - `src/Gui/CommandSearch.h`
- Deliverables:
  - recent-command ranking
  - optional active-workbench bias
  - optional edit-context bias
- Acceptance:
  - the first results are usually the intended commands during common workflows

## Workstream B: Right-Side Editing Contract

### VENV-005 Task Summary Contract

- Priority: `P0`
- Goal: every guided edit should begin with object identity, purpose, and state
- Target files:
  - `src/Gui/TaskView/TaskView.cpp`
  - `src/Gui/TaskView/TaskView.h`
  - `src/Gui/TaskView/TaskDialogPython.cpp`
- Deliverables:
  - documented task summary behavior
  - consistent fallback summary behavior
  - clear support path for Python task panels
- Acceptance:
  - right-side edit surfaces consistently show what is being edited and why

### VENV-006 Validation Summary Surface

- Priority: `P0`
- Goal: show missing inputs and actionable warnings before confirmation
- Target files:
  - `src/Gui/TaskView/TaskView.cpp`
  - `src/Gui/TaskView/TaskDialog.h`
  - task-panel base helpers where appropriate
- Deliverables:
  - optional validation summary block above edit content
  - status states such as info, warning, incomplete, error
- Acceptance:
  - users can see what blocks completion without scanning logs or clicking OK

### VENV-007 Sectioned Task Panel Pattern

- Priority: `P1`
- Goal: replace flat forms with grouped, readable edit narratives
- Target files:
  - `src/Mod/FlowStudio/flow_studio/taskpanels/base_taskpanel.py`
  - target task panels across pilot workbenches
- Deliverables:
  - section helper guidance
  - advanced-section convention
  - examples for simple, medium, and complex panels
- Acceptance:
  - core settings fit near the top and advanced settings are clearly secondary

### VENV-008 Sticky Action Area For Long Forms

- Priority: `P2`
- Goal: keep confirm and cancel actions stable while scrolling long forms
- Target files:
  - `src/Gui/TaskView/TaskView.cpp`
  - task dialog container widgets
- Deliverables:
  - action area behavior spec
  - implementation or prototype for long-form dialogs
- Acceptance:
  - users do not need to scroll to relocate primary actions

## Workstream C: Viewport Legibility And Visible State

### VENV-009 Selection And Preselection Audit

- Priority: `P0`
- Goal: make active and hovered geometry unmistakable
- Target files:
  - `src/Gui/Selection/SoFCUnifiedSelection.cpp`
  - selection-related theme or parameter files
- Deliverables:
  - color and contrast audit
  - recommended default values
  - regression checks where feasible
- Acceptance:
  - users can clearly distinguish active, hovered, and unselected geometry

### VENV-010 Professional Visual Defaults

- Priority: `P1`
- Goal: align default viewer appearance with readability and depth perception
- Target files:
  - `src/Gui/View3DInventorViewer.cpp`
  - `src/Gui/ViewParams.h`
  - files referenced by `docs/INVENTOR_QUALITY_ROADMAP.md`
- Deliverables:
  - reviewed background, lighting, edge, and visual-default settings
  - documented rationale tied to usability rather than style preference
- Acceptance:
  - defaults improve shape readability and reduce visual harshness

### VENV-011 Recompute And Execution Status Near Viewport

- Priority: `P1`
- Goal: keep state visible where the user's attention already is
- Target files:
  - `src/Gui/View3DInventorViewer.cpp`
  - `src/Gui/MainWindow.*`
  - related overlay/status infrastructure
- Deliverables:
  - visible dirty or updating indicator
  - visible long-running-operation state for recompute or solve-related flows
- Acceptance:
  - users do not need to guess whether the system registered an action

### VENV-012 Overlay Pattern For Guided Operations

- Priority: `P2`
- Goal: make the viewport explain edit targets and implications
- Target files:
  - viewer overlay infrastructure
  - workbench-specific view providers or edit handlers
- Deliverables:
  - overlay conventions for references, BCs, detectors, domains, or edit
    targets
- Acceptance:
  - major guided operations include visible scene-level cues, not just side-panel
    text

## Workstream D: FlowStudio Pilot

### VENV-013 FlowStudio Ribbon Cleanup

- Priority: `P0`
- Goal: make FlowStudio feel like a coherent engineering workflow
- Target files:
  - `src/Mod/FlowStudio/InitGui.py`
  - `src/Gui/RibbonMetadata.py`
- Deliverables:
  - stable top-level ribbon structure
  - domain-aware contextual tab exposure
  - reduced duplication across setup, solve, and results surfaces
- Acceptance:
  - a user can infer the overall setup flow from the ribbon alone

### VENV-014 FlowStudio Task Panel Consistency Pass

- Priority: `P0`
- Goal: make FlowStudio task panels structurally consistent
- Target files:
  - `src/Mod/FlowStudio/flow_studio/taskpanels/*.py`
  - `src/Mod/FlowStudio/flow_studio/viewproviders/*.py`
- Deliverables:
  - summary-first task panels
  - grouped sections in common setup dialogs
  - local validation hints where obvious
- Acceptance:
  - task panels share common reading order and do not feel ad hoc

### VENV-015 FlowStudio Layout Presets By Domain

- Priority: `P1`
- Goal: use domain context to emphasize the right panes and surfaces
- Target files:
  - `src/Mod/FlowStudio/flow_studio/ui/layouts.py`
  - docking integration points
- Deliverables:
  - domain-specific docking or visibility presets where practical
  - mapping from layout metadata to shell behavior
- Acceptance:
  - CFD, thermal, structural, EM, and optical users see the most relevant panes
    without manual rearrangement every session

### VENV-016 FlowStudio Operational Feedback Pass

- Priority: `P1`
- Goal: make jobs, results, validation, and logs more legible during CAE work
- Target files:
  - FlowStudio enterprise and jobs UI surfaces
  - bottom-pane related integrations
- Deliverables:
  - clearer job state labels
  - validation and next-step messages
  - better result availability communication
- Acceptance:
  - users can tell what stage the study is in without parsing raw logs

## Workstream E: Cross-Workbench Reuse

### VENV-017 Sketcher Context Contract Rollout

- Priority: `P1`
- Goal: make Sketcher contextual surfaces follow the same shell semantics
- Target files:
  - `src/Mod/Sketcher/Gui/Workbench.cpp`
  - task or overlay surfaces as needed
- Deliverables:
  - confirm contextual-tab metadata remains sufficient
  - identify any remaining shell-level special casing
- Acceptance:
  - Sketcher uses the common shell language for context and next actions

### VENV-018 Assembly Context Contract Rollout

- Priority: `P1`
- Goal: align assembly editing with the same visible editing contract
- Target files:
  - `src/Mod/Assembly/InitGui.py`
  - related assembly edit surfaces
- Deliverables:
  - cleaner contextual workflow exposure
  - summary-first edit entry where appropriate
- Acceptance:
  - assembly operations feel consistent with the shell and right-side contract

### VENV-019 Part Design And TechDraw Evaluation

- Priority: `P2`
- Goal: determine the smallest reusable contract rollout for other major
  mechanical workbenches
- Target files:
  - relevant Part Design and TechDraw frontend entry points
- Deliverables:
  - gap analysis
  - rollout recommendation
- Acceptance:
  - clear decision on which contract pieces apply directly and which need local
    adaptation

## Workstream F: Validation And Measurement

### VENV-020 Mechanical Workflow Test Pack

- Priority: `P1`
- Goal: validate the frontend on actual engineering workflows rather than only
  feature presence
- Deliverables:
  - scenario list
  - expected interaction paths
  - pass or fail criteria
- Acceptance:
  - benchmark workflows can be rerun after major frontend changes

### VENV-021 Lightweight UX Metrics Instrumentation

- Priority: `P3`
- Goal: gather enough evidence to tune `Home` actions and disclosure defaults
- Deliverables:
  - proposal for low-risk, privacy-aware usage capture or manual test logging
- Acceptance:
  - team can compare discoverability improvements with actual workflow outcomes

## Recommended Delivery Order

1. `VENV-001` Workbench Purpose Metadata
2. `VENV-002` Searchable Workbench Overflow
3. `VENV-003` Stable Home Tab Semantics
4. `VENV-005` Task Summary Contract
5. `VENV-006` Validation Summary Surface
6. `VENV-013` FlowStudio Ribbon Cleanup
7. `VENV-014` FlowStudio Task Panel Consistency Pass
8. `VENV-009` Selection And Preselection Audit
9. `VENV-010` Professional Visual Defaults
10. `VENV-015` FlowStudio Layout Presets By Domain
11. `VENV-016` FlowStudio Operational Feedback Pass
12. `VENV-017` and `VENV-018` contract rollout to other major workbenches

## Suggested Milestones

### Milestone 1: Shell Clarity

- Complete `VENV-001` through `VENV-006`
- Outcome: the top shell and right-side edit surface become easier to read and
  predict

### Milestone 2: FlowStudio Proof

- Complete `VENV-013` through `VENV-016`
- Outcome: one workbench demonstrates the full visual-environment model

### Milestone 3: Viewport Confidence

- Complete `VENV-009` through `VENV-012`
- Outcome: the center view better communicates geometry, state, and intent

### Milestone 4: Cross-Workbench Contract

- Complete `VENV-017` through `VENV-020`
- Outcome: the visual-environment model becomes reusable across major workflows

## Definition Of Done

A backlog item is done only when:

1. The code change is implemented in the current frontend architecture.
2. The acceptance criteria above are met.
3. Regressions are covered by tests when practical.
4. The result improves user predictability, not just internal code structure.

## Summary

This backlog is intended to keep the visual-environment work focused on the
highest-leverage changes:

- shell clarity
- editing clarity
- viewport confidence
- one strong pilot
- reusable contract

That is the shortest path to making FreeCAD feel more natural for a visually
oriented mechanical engineer without destabilizing the existing frontend.