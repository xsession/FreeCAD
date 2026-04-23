# FreeCAD Consistency Refactor Plan

## Scope

This document summarizes the architecture and implementation direction discussed in the recent refactoring work around sketch creation and editing. The immediate trigger was sketch workflow inconsistency, but the underlying issue is broader: FreeCAD often lets the same user intent take different execution paths depending on where the action started.

The goal of this plan is to move FreeCAD toward a more consistent, predictable, and logically coherent application where identical intent produces identical workflow state, UI state, tool availability, and recovery behavior.

This plan is not a full product rewrite. It is a staged refactor focused on normalizing behavior without breaking FreeCAD's modular structure.

## Executive Goal

Refactor FreeCAD so that:

- the same user intent always routes through the same canonical workflow
- entry point does not change behavior
- workbench, task panel, toolbar, selection, and view state are explicit parts of workflow policy
- edit-mode entry and exit are deterministic
- cross-workbench behavior is understandable and testable
- GUI state changes are centralized instead of being scattered across command handlers and view providers

## Core Diagnosis

The main consistency problems are structural.

### 1. Intent is split across entry points

Equivalent actions are often implemented separately in toolbar commands, menu commands, tree double-click handlers, Python command helpers, and workbench-specific command classes.

That makes the trigger location act like hidden business logic.

### 2. UI normalization is scattered

Important behavior such as:

- hiding the Start page or backstage surfaces
- activating a 3D view
- switching workbenches
- opening the correct task panel
- normalizing selection
- restoring state on exit

is currently distributed across unrelated files instead of being owned by a single workflow layer.

### 3. Workbench ownership is too strong

FreeCAD modules often behave like independent mini-applications. That is useful for extensibility, but it becomes a UX problem when identical user goals like creating or editing a sketch behave differently depending on whether the user came from Sketcher, PartDesign, a tree interaction, or a Python-created feature.

### 4. Regression protection is too local

Historically, fixes have been applied to individual symptoms instead of enforcing workflow equivalence across all routes for the same intent.

## Product Principles For A Coherent FreeCAD

The consistency model should follow these rules:

1. Same intent, same behavior.
2. Entry point may change metadata, not semantics.
3. Workbench transitions must be explicit.
4. View activation is workflow policy, not a side effect.
5. Task panels and toolbars must follow resolved context.
6. Selection handling must be deterministic.
7. Cancel, confirm, and error recovery must be consistent.
8. Equivalent workflows must be provable in tests.

## Proposed Architecture Direction

Introduce a workflow-based GUI architecture on top of the existing command system.

### 1. Intent layer

Commands, tree interactions, context menus, shortcuts, and Python entry points should all emit a normalized intent object instead of directly performing workflow steps.

Examples:

- `CreateSketch`
- `EditSketch`
- `CreatePad`
- `CreatePocket`
- `CreateBody`
- `EditFeatureParameters`

The intent object should also capture entry-point metadata such as toolbar, menu, tree double-click, shortcut, or API.

### 2. Context resolution layer

Each intent should be resolved into a deterministic execution context.

For sketch-related workflows this includes:

- active document
- active body
- explicit target sketch if any
- support object and subelement
- whether body creation is required
- whether user input is still needed
- whether detached creation is legal

This layer should answer context questions once, centrally, instead of leaving each command to improvise its own logic.

### 3. GUI normalization layer

Before entering execution or edit mode, a shared normalizer should apply the expected GUI state for the resolved workflow.

This includes:

- active document selection
- active 3D view selection
- hiding backstage surfaces
- workbench activation
- task panel ownership
- toolbar profile
- selection cleanup or gating
- camera policy where appropriate

### 4. Execution layer

The execution step should perform the actual domain action only after the context and GUI state are already normalized.

Examples:

- create a sketch object
- attach a sketch
- open an existing object in edit mode
- start a feature parameter session

Execution should not decide GUI policy on its own.

### 5. Post-state normalization layer

Entering, completing, or canceling a workflow should pass through a common exit policy.

That policy should restore or preserve:

- expected workbench
- expected active view
- task panel cleanup
- selection cleanup
- logging and diagnostics

## Sketch Workflow As The Pilot Refactor

Sketch workflows are the right first pilot because they expose the broader problem clearly.

### Problems already identified

- PartDesign `New Sketch` had richer context handling than Sketcher `New Sketch`.
- Sketcher command edit and tree double-click were separate behavioral owners.
- some paths normalized the active view and hid backstage surfaces while others did not.
- Python-created PartDesign sketch features could bypass the stronger workflow path entirely.

### Refactor direction already established

The current implementation work in this repository has already started moving sketch behavior toward a canonical route:

- a shared `SketchWorkflowController` now exists in SketcherGui
- Sketcher edit entry points have been routed through it
- PartDesign sketch-related viewport normalization now reuses shared logic
- Python-created sketch-entry commands now use a SketcherGui bridge instead of direct `setEdit(...)`
- source-level regression guards now protect several of these routes

This should remain the template for the broader consistency refactor.

For the detailed sketch-specific architecture, see:

- [docs/SKETCH_WORKFLOW_UNIFICATION_PLAN.md](docs/SKETCH_WORKFLOW_UNIFICATION_PLAN.md)

## Refactoring Roadmap

### Phase 1. Stabilize sketch intent routing

Goal: finish canonical routing for all sketch creation and edit entry paths.

Actions:

- complete the audit of remaining sketch-related bypasses
- keep all sketch edit entry on one controller path
- keep all Python sketch entry on the same bridge or equivalent canonical API
- preserve body-aware PartDesign context while removing redundant GUI-state logic
- expand regression coverage around entry-point equivalence

Success criteria:

- all sketch edit routes produce the same workbench and view state
- all sketch create routes produce the same preconditions and dialogs for the same context
- tests fail if a direct `setEdit(...)` bypass reappears in sketch entry paths

### Phase 2. Extract shared create-workflow services

Goal: move sketch creation semantics out of workbench-specific command files.

Actions:

- extract shared create-sketch context resolution from PartDesign-owned logic
- make Sketcher and PartDesign command owners become thin intent emitters
- separate support resolution from UI behavior and from object creation
- make detached-sketch handling follow the same dialog and policy regardless of entry point

Success criteria:

- `CmdPartDesignNewSketch` and `CmdSketcherNewSketch` use the same creation service
- support validation and recovery behavior are identical for the same selection state

### Phase 3. Generalize the workflow model beyond sketches

Goal: apply the same consistency pattern to other high-friction user actions.

Candidate targets:

- Pad
- Pocket
- datum creation and edit
- feature parameter editing
- TechDraw page creation
- assembly edit entry
- selection-driven context actions

Actions:

- define reusable workflow primitives for edit sessions and create sessions
- centralize workbench-switch policy
- centralize task-panel lifecycle handling
- centralize active-view and camera policy where workflows depend on them

Success criteria:

- cross-workbench create and edit commands stop owning their own private UI-state logic
- major user-facing actions can be traced as intent -> context -> normalize -> execute -> finalize

### Phase 4. Establish consistency governance

Goal: prevent future drift back into route-specific behavior.

Actions:

- add source-level regression guards for canonical routes
- add integration smoke tests for representative workflows
- add logging categories for workflow transitions
- require new GUI commands to justify any deviation from canonical routing
- document workflow ownership rules for contributors

Success criteria:

- new commands follow the workflow model by default
- regressions are caught during test review instead of after manual UX observation

## Technical Guidelines

### Keep command classes thin

Command classes should gather selection and construct an intent. They should not own large amounts of workflow policy.

### Prefer shared controllers over direct document editing calls

Direct `setEdit(...)` calls are appropriate at the deepest execution layer, not as a high-level workflow API. High-level routes should use canonical controllers or workflow services.

### Preserve valid domain-specific context

Consistency does not mean flattening everything into one workbench's behavior. PartDesign's body-aware logic is valid and should be preserved, but it should be reused by intent-based services instead of being trapped inside one entry point.

### Normalize view state explicitly

Active document, active 3D view, and backstage visibility are too important to leave implicit.

### Separate GUI normalization from object creation

This makes behavior easier to reason about and easier to test.

## Test Strategy

The consistency refactor should use two levels of protection.

### 1. Source-guard tests

These protect architectural invariants such as:

- a command calls the canonical controller
- a legacy bypass string no longer exists
- shared normalization helpers are invoked before edit entry

### 2. Integration tests

These should verify observable equivalence:

- same active workbench after equivalent actions
- same task panel class
- same active view type
- same object enters edit mode
- same exit behavior after cancel or finish

## Near-Term Deliverables

1. Finish sketch route unification.
2. Extract a shared create-sketch service.
3. Identify the next two or three inconsistent workflows after sketches.
4. Add contributor-facing documentation for the workflow model.
5. Establish a rule that equivalent user intents may not own independent GUI-state logic.

## Risks

### 1. Over-centralization

If the workflow layer becomes too abstract too quickly, it may become harder to maintain than the legacy code. The migration should stay incremental and use real user workflows as the organizing unit.

### 2. Cross-workbench regressions

PartDesign, Sketcher, and other modules do have legitimate differences. The refactor must normalize equivalent intent while preserving valid domain context.

### 3. Incomplete runtime verification

Some of the current work has source-level and diagnostic validation but not yet a complete configured build-and-run validation path in the IDE tooling. That verification gap should be closed as the next practical step.

## Recommended Next Step

The highest-value next step is to finish unifying `New Sketch` creation semantics so Sketcher and PartDesign stop owning separate creation workflows. That is the point where the refactor moves from shared edit-entry normalization into true intent-based workflow convergence.