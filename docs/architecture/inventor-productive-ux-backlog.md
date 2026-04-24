# Inventor-Productive UX Backlog

Version: 0.1
Date: 2026-04-24
Status: Execution backlog

## Purpose

This backlog turns the strategy in `docs/INVENTOR_PRODUCTIVE_UI_UX_PLAN.md` into a concrete execution model that fits the current FreeCAD frontend roadmap.

It is intended to work with, not replace, the existing shell and visual-environment documents:

- `docs/architecture/frontend-shell-ux-plan.md`
- `docs/architecture/freecad-visual-environment-backlog.md`
- `docs/architecture/freecad-visual-environment-p0-roadmap.md`
- `docs/FREECAD_CONSISTENCY_REFACTOR_PLAN.md`

## Product Outcome

When this backlog is substantially complete, FreeCAD should behave like a coherent mechanical CAD product rather than a collection of independent workbench shells.

The user-facing outcomes are:
- faster transition from launch to real work
- clearer next actions during modeling and assembly workflows
- less context loss while editing
- stronger muscle memory across workbenches
- a more comfortable and legible daily-use interface

## Priority Model

- `P0`: foundational; blocks cross-workbench UX coherence
- `P1`: high-value workflow acceleration after the shell contract is stable
- `P2`: important expansion and comfort improvements
- `P3`: exploratory or later-stage polish

## Implementation Status Snapshot

Status as of 2026-04-24:

- The workbench selector already includes more of the shell-wayfinding slice than the original backlog assumed.
- `src/Gui/RibbonBar.cpp` now includes an initial adaptive `Home` pilot for PartDesign, Sketcher, Assembly, TechDraw, and FlowStudio.
- `Home` is no longer limited to one static panel pick at ribbon-setup time; it is rebuilt from active workbench and contextual-panel state during ribbon refresh.
- `src/Gui/Action.cpp` already provides:
  - workbench purpose metadata via `workbenchPurpose()`
  - favorites persistence
  - recent-workbench persistence and ranking
  - tooltip composition that appends purpose text
- `src/Gui/WorkbenchSelector.cpp` already provides:
  - searchable overflow in the tabbed selector via the `More` popup
  - pinned-workbench management from the overflow menu
  - primary tabs derived from favorites
- The remaining shell-wayfinding gap is therefore narrower:
  - parity between tabbed and combo-box selector modes
  - stronger visible workbench guidance, not just tooltips
  - better category/purpose presentation in the overflow path
  - more explicit “mode navigation” behavior instead of relying mostly on action ordering

## Epic A: Shell-State Governance

### UX-001 Shared Shell-State Contract

- Priority: `P0`
- Goal: establish one canonical shell-state policy for edit and create workflows
- Problem:
  - ribbon, classic toolbar, task panel, and workbench refresh behavior still depend on scattered command logic
- Related docs:
  - `docs/FREECAD_CONSISTENCY_REFACTOR_PLAN.md`
- Target files:
  - `src/Gui/Application.cpp`
  - `src/Gui/MainWindow.cpp`
  - `src/Gui/WorkbenchManager.cpp`
  - `src/Gui/RibbonBar.cpp`
- Deliverables:
  - explicit shell-state contract document in code comments or adjacent docs
  - reusable normalizers for edit entry, shell refresh, and contextual surfaces
  - one canonical replay path for workbench shell surfaces
- Acceptance:
  - identical workflow context produces equivalent shell surfaces regardless of entry route

### UX-002 Canonical Workflow Entry For Sketch And Feature Edit

- Priority: `P0`
- Goal: ensure the most common modeling entry paths behave identically
- Target files:
  - `src/Mod/PartDesign/Gui/SketchWorkflow.cpp`
  - `src/Gui/Control.*`
  - `src/Mod/Sketcher/Gui/*`
  - relevant command files in `src/Mod/PartDesign/Gui/`
- Deliverables:
  - shared create/edit workflow services
  - thin command adapters for different entry points
  - regression checks for bypass routes
- Acceptance:
  - sketch and feature edit routes no longer diverge in workbench, task-panel, or ribbon behavior

## Epic B: Human-Centered Shell Navigation

### UX-003 Workbench Favorites, Recents, And Purpose Layer

- Priority: `P0`
- Goal: make workbench switching feel like mode switching instead of internal-name lookup
- Target files:
  - `src/Gui/WorkbenchSelector.cpp`
  - `src/Gui/WorkbenchSelector.h`
  - `src/Gui/Action.cpp`
- Deliverables:
  - visible favorites row or segmented favorites surface
  - searchable overflow for all selector modes
  - short purpose descriptions for major workbenches
  - clearer category or grouping cues in overflow surfaces
- Acceptance:
  - a new user can choose the correct workbench without already knowing FreeCAD vocabulary

Current status:

- partially implemented
- current implementation already covers favorites, recents, tooltips, and searchable overflow for the tabbed selector path
- remaining work should focus on visibility and parity rather than rebuilding the feature from scratch

### UX-004 Stable And Adaptive Home Tab

- Priority: `P0`
- Goal: make `Home` the trusted next-action surface for each major workflow
- Target files:
  - `src/Gui/RibbonBar.cpp`
  - `src/Gui/RibbonBar.h`
  - `src/Gui/RibbonMetadata.py`
  - workbench registration files as needed
- Deliverables:
  - selection rules for `Home`
  - active-object and workflow-stage heuristics
  - initial support for PartDesign, Sketcher, Assembly, TechDraw, and FlowStudio
- Acceptance:
  - `Home` is never empty, noisy, or semantically meaningless in supported workbenches

Current status:

- partially implemented
- `Home` now rebuilds dynamically in `RibbonBar.cpp` instead of remaining fixed after initial setup
- pilot priorities are in place for:
  - PartDesign helper/modeling/dress-up/transformation flows
  - Sketcher base/edit geometry and constraint flows
  - Assembly workflow/joints/solve flows
  - FlowStudio analysis/setup/solve simulation flows
  - TechDraw page/view/dimension drafting flows
- sketch-edit contextual panels and assembly contextual panels can now seed `Home` before fallback workbench panels
- remaining work should focus on:
  - validating whether the current `MaxHomePanels` cap is still optimal for complex workflows
  - moving from label-based heuristics toward richer declared workflow-stage metadata where needed

## Epic C: Unified Right-Side Editing Surface

### UX-005 Inspector/Edit/Validate Surface

- Priority: `P0`
- Goal: resolve the current conflict between properties and task editing
- Target files:
  - `src/Gui/ComboView.cpp`
  - `src/Gui/ComboView.h`
  - `src/Gui/PropertyView.*`
  - `src/Gui/TaskView/TaskView.*`
- Deliverables:
  - right-side surface model with inspect, edit, and validate modes
  - persistence rules for when object context remains visible during editing
  - migration plan for legacy task dialogs
- Acceptance:
  - users can edit without losing basic object context and without competing dock behavior

### UX-006 Task Summary And Validation Contract Expansion

- Priority: `P0`
- Goal: make structured editing mandatory for high-frequency workflows
- Target files:
  - `src/Gui/TaskView/TaskView.cpp`
  - `src/Gui/TaskView/TaskDialogPython.cpp`
  - task panels under `src/Mod/PartDesign/Gui/`, `src/Mod/Sketcher/Gui/`, `src/Mod/Assembly/Gui/`, `src/Mod/TechDraw/Gui/`
- Deliverables:
  - shared task-panel contract for identity, summary, validation, preview, and next steps
  - fallback rules for legacy Python and C++ dialogs
  - pilot conversions in top workflows
- Acceptance:
  - major edit dialogs visibly explain what is being edited, what is missing, and what happens next

## Epic D: Workflow-State Visibility

### UX-007 Tree State Badges And Active Context Cues

- Priority: `P1`
- Goal: make the model tree communicate active and invalid state clearly
- Target files:
  - `src/Gui/Tree.cpp`
  - `src/Gui/Tree.h`
  - `src/Gui/TreeParams.*`
  - relevant view providers
- Deliverables:
  - active-body cue
  - active-sketch cue
  - invalid or warning badge system
  - edit-state and suppressed/frozen-state cues where applicable
- Acceptance:
  - users can understand current model state without relying on hidden conventions

### UX-008 Near-Viewport Status Feedback

- Priority: `P1`
- Goal: show recompute, solving, and long-running state near the user’s attention center
- Target files:
  - `src/Gui/View3DInventorViewer.cpp`
  - `src/Gui/MainWindow.*`
  - overlay/status infrastructure
- Deliverables:
  - visible dirty/recompute indicator
  - solve/progress state for long operations
  - minimal interruption design
- Acceptance:
  - users can tell whether the system is busy, updating, or waiting for input without scanning the report view

## Epic E: Mechanical Workflow Excellence

### UX-009 PartDesign Workflow Pass

- Priority: `P1`
- Goal: make body, sketch, pad, pocket, and edit iteration feel like one continuous workflow
- Target files:
  - `src/Mod/PartDesign/Gui/`
  - shell-state related GUI files
- Deliverables:
  - canonical entry rules
  - adaptive Home behavior
  - structured task dialogs
  - clearer active-body and active-sketch feedback
- Acceptance:
  - common part modeling tasks require fewer shell/context shifts

### UX-010 Assembly Workflow Pass

- Priority: `P1`
- Goal: make placing and constraining parts feel like a first-class workflow
- Target files:
  - `src/Mod/Assembly/Gui/`
  - `src/Gui/Selection/*`
  - `src/Gui/TaskView/*`
- Deliverables:
  - assembly task watchers or equivalent context-driven command availability
  - structured joint editing panels
  - visible grounded/DOF/constraint-state feedback
- Acceptance:
  - basic place-and-constrain workflows are understandable without assembly-specific tribal knowledge

### UX-011 TechDraw Workflow Pass

- Priority: `P2`
- Goal: express drawing work as a clear stage-based flow
- Target files:
  - `src/Mod/TechDraw/Gui/`
  - ribbon metadata files
- Deliverables:
  - stage-oriented command grouping
  - right-side editing contract for drawing tasks
  - Home tab tuned for documentation workflow
- Acceptance:
  - users can create a sheet and place views without hunting through workbench-specific commands

## Epic F: Startup And Backstage Productivity

### UX-012 Task-Oriented Start Surface

- Priority: `P1`
- Goal: reduce time from launch to productive modeling action
- Target files:
  - `src/Mod/Start/Gui/StartView.*`
  - `src/Gui/BackstageView.*`
- Deliverables:
  - high-frequency task cards
  - workbench-aware creation shortcuts
  - start actions for import-to-model and drawing-from-part flows
- Acceptance:
  - the start experience offers useful tasks, not just file recall

## Epic G: Visual Comfort And Daily Use Quality

### UX-013 Professional Default Visuals

- Priority: `P1`
- Goal: make the default viewer and shell feel calm, readable, and modern
- Target files:
  - `src/Gui/View3DInventorViewer.cpp`
  - `src/Gui/ViewParams.h`
  - selection and theme parameter files
- Deliverables:
  - professional default backgrounds, lighting, and edge settings
  - reviewed selection and preselection palette
  - documented rationale tied to readability
- Acceptance:
  - the default environment feels suitable for all-day mechanical work without immediate customization

### UX-014 Interaction Comfort Sweep

- Priority: `P2`
- Goal: reduce friction during repetitive daily use
- Target areas:
  - button sizing
  - command hit targets
  - mode transitions
  - shortcut discoverability
  - panel restore stability
- Acceptance:
  - measurable reduction in context-switching and accidental UI friction in top workflows

## Milestones

### M1: Shell Contract Baseline

- `UX-001`
- `UX-002`
- `UX-003`
- `UX-004`

Outcome:
- a stable shell contract exists and major workflow entry points stop diverging

### M2: Unified Editing Baseline

- `UX-005`
- `UX-006`

Outcome:
- the right-side editing surface is structurally coherent for pilot workflows

### M3: Mechanical Workflow Baseline

- `UX-007`
- `UX-008`
- `UX-009`
- `UX-010`

Outcome:
- part modeling and assembly feel materially more guided and readable

### M4: Productive Launch And Documentation

- `UX-011`
- `UX-012`
- `UX-013`

Outcome:
- launch, drawing handoff, and default visual experience align with a professional CAD product

## Recommended First Slices

These are the best next implementation slices because they create the most leverage.

### Slice 1
- selector-mode parity for workbench wayfinding
- stronger visible purpose and category presentation
- favorites/recents refinement based on current implementation

Reason:
- the infrastructure already exists, so this is now a low-risk refinement slice with immediate user-facing payoff

### Slice 2
- `Home` tab semantic rules
- PartDesign and Sketcher pilot tuning

Reason:
- immediately improves “what do I do next?” behavior

### Slice 3
- right-side summary and validation contract extended from current pilot work
- prototype unified inspect/edit surface behavior

Reason:
- resolves one of the most persistent shell-friction points

### Slice 4
- Assembly watcher pattern and structured joint edit panels

Reason:
- assembly UX is one of the largest gaps versus Inventor-class productivity

## Success Metrics

### Wayfinding
- time to reach a non-favorite workbench
- number of search/scan interactions before correct workbench selection

### Workflow continuity
- number of shell-state changes during sketch creation and feature editing
- equivalent-entry-route pass rate for canonical workflows

### Editing clarity
- percentage of major task panels exposing summary and validation blocks
- user-visible error recovery without report-view dependence

### Productivity
- time from launch to first sketch
- time from open assembly to first valid joint
- time from modeled part to first drawing view

## Governance Rule

No major new workflow should ship without explicitly defining:
- its entry points
- its resolved workflow context
- its shell-state behavior
- its task-panel behavior
- its selection behavior
- its exit and recovery behavior

Without that rule, FreeCAD will continue to accumulate workbench-local UX drift.