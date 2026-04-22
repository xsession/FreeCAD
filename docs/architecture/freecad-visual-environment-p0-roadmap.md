# FreeCAD Visual Environment P0 Roadmap

Version: 0.1
Date: 2026-04-22
Status: Sprint-ready roadmap

## Purpose

This roadmap narrows the visual-environment backlog to the first implementation
slice that should be completed before broader rollout.

Scope is limited to the `P0` items from
`docs/architecture/freecad-visual-environment-backlog.md`.

## P0 Outcome

When this roadmap is complete, FreeCAD should have:

1. Clearer workbench wayfinding in the shell
2. A stronger and more consistent `Home` tab
3. A documented summary-first right-side edit contract
4. Local validation surfaces for guided edits
5. Stronger selection clarity in the viewport
6. A FlowStudio pilot that demonstrates the pattern end to end

## Implementation Status Snapshot

Status as of 2026-04-22:

- `P0-1`, `P0-2`, and `P0-3` are implemented in the shell and ribbon pilot.
- `P0-4` and `P0-5` are implemented as a reusable task-view metadata contract
  with live refresh and Python-to-C++ forwarding.
- `P0-6` is implemented for the initial viewport legibility slice, including
  consistent selection defaults and stronger selection bounding boxes.
- `P0-7` is implemented in the FlowStudio ribbon pilot.
- `P0-8` is in progress, with summary-first and validation-enabled coverage now
  applied to solver, mesh, inlet, outlet, wall, open boundary, initial
  conditions, fluid/material assignment, measurement, geometry-helper,
  Geant4 result, result-plot, particle-study, generic-BC, physics-model,
  post-processing, and enterprise workflow surfaces.

## Sequencing Rule

Do not start broad FlowStudio cleanup before shell and right-side contract work
is stable enough to reuse.

Execution order:

1. Shell wayfinding
2. Right-side edit contract
3. Viewport selection clarity
4. FlowStudio pilot

## Roadmap Items

## P0-1 Workbench Purpose Metadata

- Backlog item: `VENV-001`
- Goal: explain what major workbenches are for at the point of selection
- Primary files:
  - `src/Gui/Action.cpp`
  - `src/Gui/WorkbenchSelector.cpp`
- Implementation notes:
  - add a small, centralized purpose mapping for major workbenches
  - surface purpose text in selector tooltips and overflow entries
  - keep wording task-oriented and short
- Verification:
  - selector surfaces show purpose text for major workbenches
  - favorite, primary, and overflow behavior still works
- Risks:
  - inconsistent naming between internal workbench IDs and visible labels

## P0-2 Searchable Workbench Overflow

- Backlog item: `VENV-002`
- Goal: let users reach non-pinned workbenches without long visual scans
- Primary files:
  - `src/Gui/WorkbenchSelector.cpp`
  - `src/Gui/WorkbenchSelector.h`
- Implementation notes:
  - prefer a lightweight popup or filterable menu instead of a new heavy shell
    component
  - preserve favorites and recent ordering as ranking hints
  - support keyboard use from the start
- Verification:
  - a non-pinned workbench can be reached by a short search path
  - no regression in existing tabbed selector behavior
- Dependencies:
  - `P0-1` preferred first, so searchable results can also show purpose text

## P0-3 Stable Home Tab Tuning

- Backlog item: `VENV-003`
- Goal: make `Home` a predictable next-action surface
- Primary files:
  - `src/Gui/RibbonBar.cpp`
  - `src/Gui/RibbonMetadata.py`
  - selected workbench registration files
- Implementation notes:
  - codify what belongs on `Home`
  - bias toward one to three dominant next actions plus a small number of
    secondary actions
  - avoid mirroring legacy toolbar names directly when they are weak user
    language
- Verification:
  - `Home` is useful in at least FlowStudio, Assembly, and Sketcher contexts
  - no tab duplication or empty `Home` states in supported workbenches
- Dependencies:
  - none hard, but more effective after `P0-1`

## P0-4 Task Summary Contract

- Backlog item: `VENV-005`
- Goal: make every guided edit start with object identity and purpose
- Primary files:
  - `src/Gui/TaskView/TaskView.cpp`
  - `src/Gui/TaskView/TaskView.h`
  - `src/Gui/TaskView/TaskDialogPython.cpp`
- Implementation notes:
  - preserve the current summary path already used by FlowStudio
  - explicitly document expected properties and fallback behavior
  - keep summary rendering visually compact and consistent
- Verification:
  - Python task panels without custom summary still show sensible fallback text
  - existing FlowStudio task summaries continue to render correctly
- Dependencies:
  - none

## P0-5 Validation Summary Surface

- Backlog item: `VENV-006`
- Goal: keep missing inputs and actionable warnings near the edit surface
- Primary files:
  - `src/Gui/TaskView/TaskView.cpp`
  - `src/Gui/TaskView/TaskDialog.h`
  - workbench task-panel helpers as needed
- Implementation notes:
  - start with a minimal API for info, warning, incomplete, and error states
  - avoid designing a large validation framework in the first pass
  - allow task panels to opt in progressively
- Verification:
  - a task panel can publish a visible warning or incomplete state without using
    the report view
  - no regression in dialogs that do not use validation summaries
- Dependencies:
  - `P0-4` first, because the validation surface should sit in the same summary
    area family

## P0-6 Selection And Preselection Audit

- Backlog item: `VENV-009`
- Goal: make active and hovered geometry clearer at a glance
- Primary files:
  - `src/Gui/Selection/SoFCUnifiedSelection.cpp`
  - related viewer parameter files
- Implementation notes:
  - measure current colors and contrast against common backgrounds
  - favor professional, readable defaults over bright novelty colors
  - ensure active selection and hover remain distinct
- Verification:
  - active and hovered states are visually distinguishable
  - no loss of visibility in typical light or dark shell configurations
- Dependencies:
  - none

## P0-7 FlowStudio Ribbon Pilot

- Backlog item: `VENV-013`
- Goal: make FlowStudio a clear workflow-oriented pilot
- Primary files:
  - `src/Mod/FlowStudio/InitGui.py`
  - `src/Gui/RibbonMetadata.py`
- Implementation notes:
  - keep stable tabs aligned to setup, inspect, solve, and results
  - keep contextual domain tabs limited to real analysis context
  - reduce duplicated or prematurely exposed domain commands
- Verification:
  - a user can infer the high-level FlowStudio workflow from the ribbon
  - irrelevant domain commands are not shown by default outside their context
- Dependencies:
  - `P0-3` first, because FlowStudio should pilot the stabilized `Home` model

## P0-8 FlowStudio Task Panel Consistency Pass

- Backlog item: `VENV-014`
- Goal: make FlowStudio the first summary-first, sectioned pilot workbench
- Primary files:
  - `src/Mod/FlowStudio/flow_studio/taskpanels/*.py`
  - `src/Mod/FlowStudio/flow_studio/viewproviders/*.py`
- Implementation notes:
  - prioritize the highest-frequency panels first
  - keep the section structure consistent across object categories
  - publish local validation hints only where they are clear and low-risk
- Verification:
  - common FlowStudio panels share the same reading order and summary pattern
  - existing tests continue to pass, especially taskpanel wiring and runtime
    smoke tests
- Dependencies:
  - `P0-4` and `P0-5`

Current implementation notes:

- completed first pass for solver, mesh, inlet, outlet, wall, and open
  boundary panels plus initial conditions, fluid/material assignment,
  measurement and geometry-helper panels, Geant4 result surfaces, result plot
  surfaces, particle/generic-BC/physics editors, and the post-processing panel
- enterprise jobs panel also participates in the same summary/validation
  surface for execution-state visibility
- remaining work is concentrated in cleanup, refinement, and broader runtime
  validation rather than major panel adoption

## Recommended Sprint Breakdown

## Sprint A: Shell Contract

- `P0-1`
- `P0-2`
- `P0-3`

Expected result:

- shell wayfinding and `Home` behavior become clearer before deeper workbench
  changes begin

## Sprint B: Right-Side Contract

- `P0-4`
- `P0-5`

Expected result:

- guided edits gain a stable summary and validation surface that pilot
  workbenches can reuse

## Sprint C: Visual Confidence

- `P0-6`

Expected result:

- users can more reliably distinguish hover and active selection in the viewport

## Sprint D: FlowStudio Pilot

- `P0-7`
- `P0-8`

Expected result:

- one workflow-heavy workbench demonstrates the full visual-environment pattern

## Verification Matrix

| Item | Verification Type |
|------|-------------------|
| `P0-1` | source-level checks and manual shell pass |
| `P0-2` | keyboard and mouse workflow validation |
| `P0-3` | ribbon behavior regression checks |
| `P0-4` | task summary runtime smoke tests |
| `P0-5` | targeted panel opt-in tests |
| `P0-6` | manual visual comparison and any available GUI checks |
| `P0-7` | FlowStudio shell walkthrough |
| `P0-8` | existing FlowStudio task panel tests plus manual walkthrough |

## Recommended First Code Changes

If implementation starts immediately, the highest-leverage first patch set is:

1. Workbench purpose metadata and tooltip surfacing
2. Task summary contract documentation and fallback tightening
3. Minimal validation summary API above task dialogs

This combination creates visible user-facing gains with relatively contained
code movement.

## Definition Of Success

This roadmap succeeds if the first visible changes make FreeCAD easier to read
before they make it prettier.

Specifically:

- users know where they are
- users know what they are editing
- users know what to do next
- users know whether the system accepted the action

That is the correct `P0` bar for the visual environment work.