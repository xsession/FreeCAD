# FreeCAD Productive UI/UX Plan

## Goal

Make FreeCAD feel like a productive, comfortable, professional mechanical CAD environment in the same class of day-to-day usability as Autodesk Inventor, while preserving FreeCAD strengths:
- open architecture
- Python extensibility
- multi-workbench flexibility
- cross-platform delivery

This plan focuses on the user experience layer, workflow coherence, and shell behavior rather than a full kernel rewrite.

## Executive Assessment

FreeCAD already contains many of the right structural pieces for a modern CAD experience:
- a ribbon shell with contextual tab support
- a backstage-style file/start surface
- task panels with summary and validation infrastructure
- a command palette
- multiple navigation presets, including Inventor-style navigation
- a workbench framework with strong modularity
- a unified combo view for model tree and properties

The main problem is not the absence of UI infrastructure. The main problem is inconsistency.

Today, FreeCAD behaves like a set of powerful subsystems that share a window rather than a single coherent product. The result is friction in exactly the places Inventor feels strong:
- entering workflows
- knowing what to do next
- editing without losing context
- moving between modeling, assembly, and documentation
- building muscle memory

## What Inventor Gets Right

The productive comfort of Inventor comes less from visual polish alone and more from these UX characteristics:
- one stable shell across workflows
- clear workflow stages and next actions
- adaptive but predictable command surfaces
- constrained, guided editing dialogs
- visible model state and edit state
- minimal context loss while editing features
- strong assembly and documentation handoff
- defaults optimized for daily work, not configurability first

FreeCAD should target those behaviors directly.

## Current-State Diagnosis

### Strengths already present in the repo
- `src/Gui/RibbonBar.*` provides an Inventor-style shell foundation with contextual tabs, quick access toolbar, panel grouping, and command search.
- `src/Gui/TaskView/TaskView.*` already supports summary and validation areas, but adoption is inconsistent.
- `src/Gui/WorkbenchSelector.*` and `src/Gui/WorkbenchManager.*` provide the base for a smarter workbench switcher.
- `src/Gui/Selection/*` and `src/Mod/PartDesign/Gui/ReferenceSelection.*` provide strong selection filtering and gating.
- `src/Mod/PartDesign/Gui/Workbench.cpp` already uses context-aware command watchers and is the best current model for guided workflow activation.
- `src/Mod/Start/Gui/StartView.*` and `src/Gui/BackstageView.*` provide an entry surface that can evolve into a real task-oriented home.
- `src/Gui/CommandSearch.*` provides a power-user escape hatch that should remain central.

### Main weaknesses
- workflow entry points are inconsistent across workbenches and command paths
- ribbon semantics are weak because grouping is still driven mostly by toolbars rather than workflow stages
- task panels do not present a unified editing pattern
- property editing and task editing compete for the same space and attention
- workbench switching is still too technical and too flat
- the model tree does not communicate enough workflow state
- assembly UX is not yet integrated to the same quality level as part modeling
- startup does not guide users into productive tasks quickly enough

## Design Principles

### 1. One shell, many domains
The main window should feel the same everywhere. Workbenches can specialize tools, but not the user’s mental model of how FreeCAD behaves.

### 2. Workflow first, command second
Commands should be organized around user intent and stage, not internal module boundaries.

### 3. Editing must stay contextual
When editing a sketch, feature, joint, or drawing element, the user should always see:
- what is being edited
- what inputs are required
- what is invalid
- what the next likely action is

### 4. Stable muscle memory matters more than flexibility
Do not let five different paths to the same action produce five different UI states.

### 5. Advanced power belongs behind clean defaults
FreeCAD can remain deeply configurable, but default behavior should be optimized for speed, clarity, and comfort.

## Priority UX Problems To Solve

### P0. Workflow coherence
The same task should follow the same shell behavior regardless of entry point.

Examples:
- creating a sketch
- editing a feature
- selecting references
- switching to assembly operations

Primary anchors:
- `src/Mod/PartDesign/Gui/SketchWorkflow.cpp`
- `src/Gui/Control.*`
- workbench command implementations under `src/Mod/*/Gui/`

### P0. Adaptive but predictable shell
The ribbon, task panel, and inspector must coordinate around the active workflow state.

Primary anchors:
- `src/Gui/RibbonBar.*`
- `src/Gui/MainWindow.*`
- `src/Gui/ComboView.*`
- `src/Gui/TaskView/TaskView.*`

### P0. Productive assembly experience
Assembly must feel like a first-class mechanical workflow, not a separate technical module.

Primary anchors:
- `src/Mod/Assembly/Gui/`
- `src/Gui/Selection/*`
- `src/Gui/TaskView/*`

### P1. Tree and inspector clarity
Users need immediate visibility into active object state, edit state, invalid state, and dependency consequences.

Primary anchors:
- `src/Gui/Tree.*`
- `src/Gui/PropertyView.*`
- `src/Gui/ComboView.*`

### P1. Faster startup into real work
The start experience should help users begin a real CAD task in one click.

Primary anchors:
- `src/Mod/Start/Gui/StartView.*`
- `src/Gui/BackstageView.*`

## Target Experience

## 1. Home shell

The default shell should behave like a professional mechanical CAD environment:
- quick access toolbar for universal actions
- a stable `Home` tab with adaptive next actions
- a clear workbench switcher with favorites and recent workbenches
- a unified right-side editing surface
- left-side model structure and history emphasis
- consistent command search everywhere

### Desired shell behavior
- `Home` is not a generic command dump. It is the “what should I do next?” tab.
- contextual tabs appear for sketch, feature edit, assembly joint edit, drawing edit, and simulation setup.
- the command palette stays available for experts, but the ribbon becomes trustworthy for normal users.

## 2. Workflow-specific UX

### Part / PartDesign
- entering sketch mode always triggers the same shell state
- the user sees active body, active sketch, edit scope, and next actions clearly
- feature dialogs present summary, inputs, validation, and preview consistently
- rollback/history affordances are exposed more clearly in the UI

### Sketcher
- constraint editing should feel immediate and guided
- the task surface should show selection intent, solver status, conflicts, and likely next steps
- constraints and dimensions should feel less modal and more progressive

### Assembly
- a joint workflow should feel as direct as Inventor’s place-and-constrain loop
- DOF, grounded state, reference quality, and invalid constraints should be visible without searching the tree or report view
- command availability should react to assembly context like PartDesign watchers already do

### TechDraw
- drawing creation should be stage-based: create sheet, place views, annotate, publish
- the shell should expose these stages explicitly instead of relying on workbench knowledge

## 3. Start and backstage UX

The first screen should support high-frequency goals, not just recent files.

Top-level entry cards should include:
- New Part
- New Assembly
- Open Recent Project
- Import STEP and Prepare Model
- Create Drawing from Part
- Start Simulation Setup

Each card should open the document in the correct workbench and shell state.

## Phased Implementation Plan

## Phase 1: Shell Unification

### Objective
Make FreeCAD behave like one product before redesigning every detail.

### Deliverables
- formal shell-state model for workflow modes
- normalized behavior for sketch edit, feature edit, and task dialog opening
- consistent docking and focus rules for ribbon, task panel, combo/property views, and 3D view
- smart workbench picker with favorites, recents, and grouped categories

### Concrete work
- create a shell-state contract in the GUI layer to coordinate ribbon, task view, and inspector surfaces
- stop letting workbench commands drive their own ad-hoc window behavior
- use `PartDesign` watcher patterns as the base for other workbenches

### Primary files
- `src/Gui/MainWindow.*`
- `src/Gui/Application.*`
- `src/Gui/RibbonBar.*`
- `src/Gui/WorkbenchSelector.*`
- `src/Gui/TaskView/TaskView.*`

## Phase 2: Unified Editing Surface

### Objective
End the property panel versus task panel conflict.

### Desired model
Replace the current split with a unified inspector/edit surface containing three modes:
- Inspect
- Edit
- Validate

The same dock area should show object properties when browsing and switch into structured edit mode when a feature, sketch, or joint enters edit state.

### Concrete work
- redesign `ComboView` and `PropertyView` so task editing can coexist with persistent object context
- standardize task dialogs to publish summary and validation metadata
- keep view properties accessible but deprioritized during feature editing

### Primary files
- `src/Gui/ComboView.*`
- `src/Gui/PropertyView.*`
- `src/Gui/TaskView/TaskView.*`
- task dialog implementations under `src/Mod/*/Gui/`

## Phase 3: Workflow-Led Ribbon

### Objective
Make the ribbon semantic, staged, and adaptive.

### Desired tab model
- Home
- Model
- Sketch
- Assemble
- Annotate
- Inspect
- View
- Tools

Contextual tabs appear only during active editing modes.

### Concrete work
- define ribbon taxonomy centrally rather than deriving behavior only from legacy toolbar names
- add workbench metadata for stage and purpose
- implement an adaptive Home tab driven by active object type, workflow stage, and likely next command

### Primary files
- `src/Gui/RibbonBar.*`
- `src/Gui/Workbench.*`
- `src/Gui/WorkbenchManager.*`
- workbench setup files under `src/Mod/*/Gui/Workbench.cpp` and `InitGui.py`

## Phase 4: Guided Task Panels

### Objective
Make editing flows feel deliberate and dependable.

### Standard task-panel contract
Every major task panel should expose:
- current object or operation name
- required inputs
- current status
- validation errors and recovery hints
- preview controls
- next likely actions

### Concrete work
- promote `TaskView` summary and validation sections from optional to standard for major workflows
- migrate major PartDesign, Sketcher, Assembly, and TechDraw dialogs to the same structure
- define a common task-panel design system and widget library

### Primary files
- `src/Gui/TaskView/TaskView.*`
- `src/Mod/PartDesign/Gui/Task*`
- `src/Mod/Assembly/Gui/`
- `src/Mod/Sketcher/Gui/`
- `src/Mod/TechDraw/Gui/`

## Phase 5: Model Tree and Workflow Visibility

### Objective
Make model state legible at a glance.

### Desired improvements
- active body indicator
- active sketch indicator
- invalid feature badges
- suppressed/frozen/editing states
- lightweight dependency and recompute cues
- assembly grounded/under-constrained/over-constrained indicators

### Primary files
- `src/Gui/Tree.*`
- `src/Gui/TreeParams.*`
- view providers under `src/Mod/*/Gui/ViewProvider*`

## Phase 6: Mechanical Workflow Excellence

### Objective
Bring the top four mechanical workflows to Inventor-class usability.

### Focus workflows
- part creation
- sketch to feature iteration
- assembly placement and constraining
- drawing creation from modeled parts and assemblies

### Concrete work
- build golden workflow maps and friction audits for each
- drive shell behavior and command exposure from these workflows instead of workbench tradition
- add regression tests for shell state and workflow continuity

## Visual and Comfort Plan

The product should feel calmer, clearer, and more durable for all-day work.

### Visual direction
- neutral professional palette instead of legacy blue/gray bias
- stronger hierarchy in typography, spacing, and panel grouping
- consistent icon weight and semantics across all workbenches
- dark theme and light theme both treated as first-class
- reduced visual noise in properties and tree panels

### Interaction comfort
- larger click targets in ribbon primary actions
- consistent hotkeys and discoverable shortcuts
- smoother transitions in view changes and mode changes
- less surprise workbench switching
- stable panel positions and predictable restore behavior

### Technical anchors for visual quality work
- `src/Gui/RibbonBar.*`
- `src/Gui/Icons/`
- `src/Gui/Application.*`
- `src/Gui/View3DInventorViewer.*`
- style and theme systems already discussed in existing roadmap docs

## Governance Model

This plan will fail if each workbench evolves independently.

### Required governance
- one cross-workbench UX contract for shell behavior
- one ribbon taxonomy
- one task-panel design system
- one workbench metadata model
- one acceptance rubric for workflow coherence

### Product rule
No new major workflow should ship unless it defines:
- entry point behavior
- shell state behavior
- selection behavior
- validation behavior
- exit behavior

## Success Metrics

The UX plan should be measured with concrete outcomes.

### Productivity metrics
- time to first sketch from launch
- time to create a body from a clean document
- time to place and constrain first assembly component pair
- time to create first drawing view from a part

### Comfort metrics
- number of panel/context switches per core workflow
- number of times users must search for a command during top workflows
- startup-to-productive-action time
- frequency of accidental workbench switches or lost edit context

### Quality metrics
- percentage of major task panels using summary + validation contract
- percentage of top workflows with consistent shell-state transitions
- percentage of workbenches mapped into semantic ribbon taxonomy

## Recommended 12-Month Roadmap

### Quarter 1
- finalize shell-state UX contract
- ship favorites/recent workbench switcher
- define semantic ribbon taxonomy
- unify sketch-entry behavior

### Quarter 2
- ship unified inspector/edit surface prototype
- migrate PartDesign and Sketcher task panels to standard structure
- add adaptive Home tab for core modeling workflows

### Quarter 3
- overhaul Assembly workflow shell and task panels
- add model tree workflow-state badges
- redesign Start and Backstage as task-oriented launch surfaces

### Quarter 4
- unify TechDraw flow
- complete top-workflow regression coverage
- polish visual system and theme consistency

## First Implementation Targets

If the goal is maximum impact with limited engineering effort, start here:

1. Make workbench switching human-centered.
2. Standardize sketch and feature entry behavior.
3. Turn `Home` into an adaptive workflow tab.
4. Unify the right-side editing surface.
5. Bring Assembly onto the same task-panel and watcher patterns as PartDesign.

## Conclusion

FreeCAD does not need a full UI rewrite to become much more productive and comfortable. It needs disciplined unification.

The repo already contains the beginnings of an Inventor-like shell. The correct strategy is to turn those partial solutions into product rules, then migrate the highest-value workflows onto them systematically.

That approach will produce a FreeCAD experience that feels more professional, more teachable, and far more efficient for mechanical design work, without losing the openness and extensibility that make FreeCAD valuable.