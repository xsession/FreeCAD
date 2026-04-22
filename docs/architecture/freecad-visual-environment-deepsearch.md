# FreeCAD Visual Environment Deepsearch

Version: 0.1
Date: 2026-04-22
Status: Research synthesis and application plan

## Purpose

This document defines how FreeCAD should evolve its visual environment so it
feels intuitive, spatially stable, and natural for a mechanical engineer with a
strong visual mindset.

This is not a styling-only document. The goal is to make the frontend behave
like a coherent engineering workspace where geometry, intent, state, and next
actions are always legible.

It complements, rather than replaces:

- `docs/architecture/frontend-shell-ux-plan.md`
- `docs/INVENTOR_QUALITY_ROADMAP.md`
- `docs/MODERNIZATION_PLAN.md`
- `src/Mod/FlowStudio/docs/CST_STUDIO_SUITE_LAYOUT_DEEPSEARCH.md`

## Deepsearch Baseline

This document synthesizes:

- Current FreeCAD frontend architecture in `src/Gui`
- Current FlowStudio workflow-oriented UI work in `src/Mod/FlowStudio`
- Existing repository planning documents on ribbon, shell UX, and rendering
- Public UX principles from Nielsen Norman Group on:
  - recognition over recall
  - progressive disclosure
  - visibility of system status

## Core Thesis

Mechanical engineers do not primarily think in terms of menus, module trees, or
backend categories. They think in terms of shape, fit, motion, reference,
constraint, load path, manufacturability, and whether the current operation
visibly moved the model closer to the intended result.

The FreeCAD visual environment should therefore optimize for five things:

1. Spatial certainty: the user should always know what object is active, where
   it is, and what will change.
2. Visual recognition over memory: the user should recognize likely actions
   from context instead of recalling command names.
3. Stable left-to-right narrative: identify object, inspect geometry, edit
   parameters, confirm result.
4. Explicit state communication: selection, edit mode, validation, recompute,
   solve, and preview status must always be visible.
5. Progressive depth: common engineering actions should be immediate while rare
   or dangerous controls remain one step deeper.

## What A Visual Mechanical Engineer Actually Needs

For daily CAD or CAE work, the user constantly asks:

1. What am I editing right now?
2. What geometry or result does this act on?
3. What changed after my last action?
4. What are the next likely actions in this workflow?
5. Where do I inspect and tune the important parameters without losing my 3D
   context?

When FreeCAD feels hard to use, it is often because one of those five questions
is not answered directly by the shell.

## Human-Centered Design Principles

### 1. Recognition Over Recall

FreeCAD should surface likely actions, recent modes, and contextual commands in
visible places. Users should not have to remember internal workbench names,
hidden commands, or solver-specific vocabulary before they can continue.

Implications:

- keep visible workbench favorites and recent workbenches
- show contextual command groups near the active object type
- label actions in engineering language, not implementation language
- use task summaries and next-step cues instead of silent forms

### 2. Progressive Disclosure

Most engineering dialogs contain a small set of high-frequency controls and a
much larger set of infrequent expert controls. Both are necessary, but they
must not compete visually.

Implications:

- first viewport height should contain the core controls
- advanced controls should be grouped in explicit secondary sections
- avoid more than two disclosure levels inside a single panel
- keep dependencies visible when advanced controls are hidden

### 3. Visibility Of System Status

Users trust CAD when the application clearly communicates what is selected,
which mode is active, whether the model is dirty, whether a recompute is
running, and why an operation is blocked.

Implications:

- selection state must be unmistakable in both 3D and side panels
- edit mode should have a visible shell-level state marker
- recompute and solve state should appear in the viewport periphery and bottom
  surfaces, not only in logs
- validation warnings should explain what is missing and what to do next

### 4. Stable Spatial Memory

The shell should remain stable while the context changes inside it. A user with
strong spatial reasoning builds muscle memory very quickly and loses time when
major parts of the UI rearrange unexpectedly.

Implications:

- left remains object and model structure
- center remains geometry and result scene
- right remains property and task editing
- bottom remains status, reports, logs, and execution feedback

### 5. Geometry First, Text Second

The model and its feedback should do more explanatory work than prose. Text
should clarify and confirm, not carry the full mental load.

Implications:

- direct-manipulation previews should be preferred over abstract settings when
  feasible
- selections should be reinforced with overlays, labels, and local hints
- constraints, loads, BCs, and detectors should have strong glyph or scene
  cues when possible

## Current FreeCAD Strengths To Build On

The current codebase already contains most of the necessary primitives.

### Shell And Docking

- `src/Gui/DockWindowManager.cpp` already manages persistent dock behavior
- `src/Gui/ComboView.cpp` already establishes the basic left-side tree and
  property relationship
- `src/Gui/TaskView/TaskView.cpp` already acts as the right-side guided editing
  surface

### Command And Mode Discovery

- `src/Gui/CommandSearch.cpp` already provides a searchable palette
- `src/Gui/Action.cpp` and `src/Gui/WorkbenchSelector.cpp` already support
  workbench favorites, recency, overflow, and tabbed mode navigation
- `src/Gui/RibbonBar.cpp` already supports stable tabs, a synthesized `Home`
  tab, and metadata-driven contextual tabs

### View Quality And Perception

- `src/Gui/View3DInventorViewer.cpp` already includes stronger ambient,
  backlight, fill light, and post-processing hooks
- `docs/INVENTOR_QUALITY_ROADMAP.md` already frames rendering quality as a UX
  issue rather than a cosmetic issue

### Guided Editing Pilot

- `src/Mod/FlowStudio/flow_studio/taskpanels/base_taskpanel.py` already exposes
  summary metadata and section helpers
- `src/Gui/TaskView/TaskView.cpp` already renders task summaries above dialogs
- `src/Mod/FlowStudio/flow_studio/ui/layouts.py` already encodes workspace
  layout intent by domain

This means FreeCAD does not need a shell rewrite to improve the visual
environment. It needs stronger information architecture and more disciplined
application of the primitives that already exist.

## Target Visual Environment

## 1. Shell Composition

The target shell should remain stable and read left to right:

```text
+--------------------------------------------------------------------------------+
| QAT | Workbench Favorites | Command Search | Active Mode | Dirty/Recompute     |
+--------------------------------------------------------------------------------+
| File | Home | Model | Inspect | View | Contextual Tabs                           |
+----------------------+--------------------------------+------------------------+
| Model / Selection    | 3D View / Result View         | Properties / Task      |
| - tree               | - geometry                    | - summary              |
| - active object      | - preview                     | - core controls        |
| - filter             | - overlays                    | - advanced sections    |
+----------------------+--------------------------------+------------------------+
| Report | Python | Notifications | Solver Output | Validation | Jobs            |
+--------------------------------------------------------------------------------+
```

The shell should answer:

- left: what exists and what is active
- center: what it looks like and what changed
- right: what it means and how to edit it
- bottom: what the system is doing and whether it succeeded

## 2. Workbench Navigation Should Feel Like Mode Navigation

The workbench picker should behave as a mode strip for humans, not a raw enum.

Target behavior:

- show six or fewer pinned workbenches as primary tabs
- bias recent workbenches upward in overflow
- show one-line purpose tooltips for each workbench
- keep a searchable overflow path
- never require a novice user to remember rarely used workbench names to keep
  moving

The current implementation in `src/Gui/Action.cpp` and
`src/Gui/WorkbenchSelector.cpp` is already close enough to serve as the rollout
 base.

## 3. Ribbon Should Express Workflow, Not Ownership

The ribbon should be organized by intent and stage, not by backend module or
legacy toolbar inheritance.

Stable top-level tabs should remain small in number:

- `File`
- `Home`
- `Model`
- `Inspect`
- `View`
- `Automate` or `Tools`

Contextual tabs should appear only when the current object or edit mode makes
them obvious:

- `Sketch`
- `Assembly`
- `Simulation`
- `Results`

Panel rules:

- each panel expresses one intention
- one primary action may be large if the workflow has a dominant next step
- no panel should feel like a junk drawer
- avoid exposing solver-specific or expert-only controls in the first layer
  unless the active object makes them core

## 4. Right-Side Editing Must Behave Like One Surface

Properties and task panels should cooperate, not compete.

The right side should always include:

- what object is being edited
- what this edit changes
- what is missing
- what will happen on accept

Task panel anatomy should be standardized:

1. Header summary
2. Selection context
3. Core parameters
4. Advanced groups
5. Validation and preview summary
6. Stable action area

The FlowStudio task panel pattern already points in the right direction and is
the best immediate pilot for broader adoption.

## 5. Viewport Should Carry More Meaning

The viewport is the main cognitive anchor for visually minded engineers. It must
communicate state, not just render triangles.

Target viewport behavior:

- clean neutral background and readable edge definition
- strong active-selection feedback that is visible without being garish
- persistent but subtle orientation and depth cues
- edit-mode overlays for active references, constraints, domains, loads, or
  result fields
- transient previews during parameter edits whenever feasible
- visible camera and navigation smoothness that reduces cognitive friction

This is where `src/Gui/View3DInventorViewer.cpp` and the rendering roadmap
matter directly to usability.

## 6. Bottom Surfaces Should Become Operational Feedback, Not Dumping Grounds

The bottom area should not only collect logs. It should explain operational
state.

Required categories:

- notifications: what just happened
- validation: what is incomplete or invalid
- execution: recompute, mesh, solve, run, import state
- diagnostics: why an operation failed
- history: recent actions or recent commands when useful

For CAE workflows especially, users need to see queue state, run state, partial
progress, and result availability without switching mental modes.

## Target Rules For Mechanical-Engineer Friendliness

The frontend should satisfy these rules by default.

### Rule 1: The active object is always obvious

The user should not need to inspect multiple panels to discover the edit target.

### Rule 2: The next action is always visible

Every major mode should expose the next one to three likely actions in the top
command surface.

### Rule 3: Parameter edits do not break spatial context

Editing on the right should preserve visual awareness in the center.

### Rule 4: Validation is local and actionable

Warnings should appear next to the task at hand, with language that suggests the
fix.

### Rule 5: Advanced controls never block basic flow

An engineer doing an 80 percent workflow should not fight the 20 percent expert
options.

### Rule 6: Visual cues are consistent across workbenches

Selection, active edit state, pending changes, warnings, and apply/accept flow
should feel consistent across Part Design, Sketcher, Assembly, FlowStudio, and
other major workbenches.

## Gaps In The Current Frontend

The current frontend has improved substantially, but several issues still block
the target experience.

### 1. Information Architecture Is Still Uneven

Some workbenches still expose commands in backend- or history-shaped groups
rather than workflow-shaped groups.

### 2. The Right Side Is Stronger Than Before But Not Yet Universal

FlowStudio task panels now include summary and section concepts, but that level
of guided structure is not yet a cross-workbench contract.

### 3. Visual State Is Still Too Fragmented

Important state often lives in separate places: selection in the viewport,
warnings in the report view, edit context in the task panel, and workflow stage
only in the user's head.

### 4. Command Search Exists But Is Not Yet Treated As A Core Bridge

Search is extremely valuable for experts, but it should also reinforce visible
navigation rather than compensate for weak command architecture.

### 5. Workbench Switching Still Carries Too Much Cognitive Weight

Favorites and recency help, but the shell should keep reinforcing why a
workbench is relevant and what it is for.

## Plan To Apply This In The Current Frontend

This section is intentionally implementation-oriented and limited to the current
FreeCAD frontend architecture.

## Phase 1: Finish The Shell-Level Wayfinding

Goal: make the top shell legible before changing many workbenches.

Primary files:

- `src/Gui/Action.cpp`
- `src/Gui/Action.h`
- `src/Gui/WorkbenchSelector.cpp`
- `src/Gui/WorkbenchSelector.h`
- `src/Gui/CommandSearch.cpp`
- `src/Gui/RibbonBar.cpp`

Actions:

- keep pinned and recent workbench behavior, but add stronger purpose tooltips
- add optional workbench categories for overflow grouping
- expose recent commands in command search
- expose command search suggestions scoped to active workbench and edit mode
- ensure the `Home` tab always shows the next likely actions, not merely a copy
  of legacy toolbar structure

Acceptance criteria:

- a new mechanical user can reach core workbenches in one interaction
- the top shell exposes likely next actions without requiring search
- search remains the expert accelerator, not the primary rescue path

## Phase 2: Make The Right Side A Formal Editing Contract

Goal: standardize the edit narrative.

Primary files:

- `src/Gui/TaskView/TaskView.cpp`
- `src/Gui/TaskView/TaskView.h`
- `src/Gui/TaskView/TaskDialogPython.cpp`
- `src/Mod/FlowStudio/flow_studio/taskpanels/base_taskpanel.py`

Actions:

- formalize task summary metadata as part of the workbench authoring contract
- add optional validation summary and completion-state badges above dialogs
- standardize grouped sections, advanced sections, and sticky action placement
- preserve scroll and width behavior so long forms remain readable

Acceptance criteria:

- every guided edit begins with object, purpose, and status
- every task panel clearly separates core from advanced controls
- validation is visible before the user clicks accept

## Phase 3: Turn Viewport Quality Into Operational UX

Goal: make the center panel communicate meaning, not just rendering.

Primary files:

- `src/Gui/View3DInventorViewer.cpp`
- `src/Gui/Selection/SoFCUnifiedSelection.cpp`
- `docs/INVENTOR_QUALITY_ROADMAP.md`

Actions:

- align defaults for background, lighting, and selection with readability rather
  than legacy appearance
- ensure selection and preselection cues are professional and unmistakable
- make edit-mode overlays a first-class concept for targeted workflows
- add progress or stale-state indicators near the viewport when recompute or
  run-heavy actions are underway

Acceptance criteria:

- active geometry is readable at a glance
- the user can tell what is selected and what is merely hovered
- visual quality improvements improve engineering perception, not only beauty

## Phase 4: Pilot The Full Pattern In FlowStudio

Goal: prove a full workflow-oriented visual environment in one workbench family.

Primary files:

- `src/Mod/FlowStudio/InitGui.py`
- `src/Mod/FlowStudio/flow_studio/ui/layouts.py`
- `src/Mod/FlowStudio/flow_studio/taskpanels/*.py`
- `src/Mod/FlowStudio/flow_studio/viewproviders/*.py`
- `src/Mod/FlowStudio/docs/*.md`

Actions:

- keep stable tabs for setup, inspect, mesh and solve, and results
- reveal domain-specific contextual tabs only when analysis context justifies
  them
- continue converting flat forms into sectioned task panels
- add local validation and next-step summaries in the task surface
- use workspace layout metadata to guide docking presets and panel emphasis by
  domain

Why FlowStudio first:

- it already has the most explicit workflow structure
- it already uses task summary and layout metadata
- it benefits most from strong status visibility because solver workflows have
  many asynchronous or multi-stage operations

## Phase 5: Extract A Small Cross-Workbench UX Contract

Goal: reuse the pattern without forcing a rewrite.

Contract candidates:

- workbench purpose metadata
- preferred `Home` actions metadata
- contextual tab trigger metadata
- task summary metadata
- validation summary metadata
- optional advanced-section declaration

This can remain compatible with the current Python and C++ workbench model.

## Phase 6: Validate On Real Mechanical Workflows

The rollout should be measured on actual tasks, not only code coverage.

Suggested benchmark tasks:

1. Start page to first sketch to padded body
2. Open assembly, constrain parts, inspect collision or interference
3. Create simulation study, assign materials and BCs, mesh, run, inspect
   results
4. Create manufacturing drawing from a finished model

Suggested metrics:

- time to first successful task completion
- number of shell transitions during one workflow
- number of canceled edits
- number of search invocations per task
- number of validation failures discovered only after accept

## Priority Order

The most pragmatic implementation order for the current repository is:

1. Shell wayfinding: workbench chooser, ribbon semantics, command discovery
2. Right-side editing contract: summaries, sections, validation surface
3. Viewport legibility and state communication
4. Full workflow pilot in FlowStudio
5. Contract rollout to Sketcher, Assembly, Part Design, and TechDraw

This order is important. If the shell remains ambiguous, improving individual
task panels will not be enough.

## Non-Goals

- replacing the main window architecture
- abandoning classic toolbars immediately
- cloning Autodesk, Siemens, or Dassault products exactly
- building a separate standalone frontend before improving the host shell
- moving core workflows into modal wizards unless the workflow is truly linear

## Summary

FreeCAD should feel less like a collection of tool registries and more like a
visually legible engineering cockpit.

For a mechanical engineer with strong visual reasoning, the correct target is:

- stable shell
- geometry-first interaction
- clear mode and status feedback
- workflow-shaped command surfaces
- guided right-side editing
- expert speed without novice confusion

The current codebase is already close enough to begin. The necessary primitives
exist in `src/Gui` and the best pilot path already exists in FlowStudio. The
correct next step is disciplined application of this visual-environment model,
not another broad UI rewrite.

## Sources

- Nielsen Norman Group, "Memory Recognition and Recall in User Interfaces"
- Nielsen Norman Group, "Progressive Disclosure"
- Nielsen Norman Group, "Visibility of System Status"
- Internal repository documents and current GUI implementation files listed
  above