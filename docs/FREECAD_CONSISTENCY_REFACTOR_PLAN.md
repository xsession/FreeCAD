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

### Current implementation status

The sketch pilot has now expanded into a second consistency track: shell-state normalization during edit workflows.

Recent implementation work in this repository has already established several important consistency wins:

- Sketcher edit entry is no longer only a command-routing problem; it now has a canonical workflow controller and a Python bridge.
- Sketcher edit-context ribbon panels are registered independently of the currently active workbench so edit-mode command surfaces remain available even when sketch edit begins from PartDesign or another owner.
- ribbon-to-classic and classic-to-ribbon transitions now preserve more deterministic toolbar visibility and workbench activation side effects.
- `Gui::Application::refreshActiveWorkbench()` now acts as the shared shell-state replay primitive for caller sites that need to reapply the active workbench after external UI changes.
- ribbon toggle, backstage hide, macro-command refresh, and `Workbench.reloadActive()` now all reuse that helper instead of replaying workbench activation steps inline.
- PartDesign sketch creation flows that start from plane-pick or attachment workflows now reuse `SketchWorkflowController::prepareSketchEditViewport(...)` instead of carrying their own Start-page and 3D-view normalization logic.
- the ribbon contextual-refresh path has been hardened against hidden-widget and shutdown-time crashes.
- launcher-driven smoke coverage now exists for ribbon toggle behavior and for sketch edit-mode ribbon and classic toolbar equivalence.
- source-contract coverage now protects the shared shell-refresh helper itself and the migrated caller sites so future fixes do not drift back toward duplicated workbench replay logic.

This means the pilot is no longer just about canonical sketch edit entry. It is now also proving that workflow consistency must include the top-level shell state: active workbench signals, contextual ribbon population, classic toolbar fallback, and safe refresh sequencing.

For the detailed sketch-specific architecture, see:

- [docs/SKETCH_WORKFLOW_UNIFICATION_PLAN.md](docs/SKETCH_WORKFLOW_UNIFICATION_PLAN.md)

## Expanding The Philosophy To Other Workbenches

The sketch pilot is not an exception. It is a template.

Other workbenches should not copy the exact Sketcher implementation, but they should adopt the same architectural philosophy:

- commands emit intent instead of owning workflow policy
- context is resolved once, centrally
- shell state is normalized before execution or edit entry
- task panels, ribbons, and classic toolbars follow resolved context
- exit and recovery paths are explicit and testable

The practical question is not whether every workbench needs a `SketchWorkflowController` equivalent. The practical question is whether each workbench has a canonical owner for equivalent user intent.

### Workbench families and their consistency targets

#### 1. PartDesign and Sketcher

These remain the reference implementation for cross-workbench create and edit consistency.

Primary target:

- unify feature creation, sketch creation, sketch edit, datum edit, and feature parameter edit under shared workflow services

Consistency problems already visible:

- body-aware behavior is still partly trapped inside PartDesign-owned helpers
- edit entry still depends on a mix of commands, view providers, and task dialogs
- shell-state policy is only partially shared

What this family should prove:

- one intent can span multiple workbenches without changing semantics
- workbench activation, task panel ownership, and ribbon or classic command surfaces can be policy outputs instead of side effects

#### 2. Part and Surface

These workbenches expose many geometry-creation and parameter-edit flows that still enter edit mode directly from command handlers or task dialogs.

Primary target:

- normalize parameter-edit workflows for geometry features so direct `setEdit(...)` and `resetEdit()` calls stop acting as the public workflow API

Consistency problems already visible:

- multiple commands create an object and immediately enter edit mode from the command body
- task dialogs often own their own completion and cancel cleanup logic
- edit-state restoration can vary by feature type instead of by resolved workflow class

What this family should prove:

- feature parameter editing can use a common edit-session model
- cancel, confirm, and re-entry behavior can be shared across geometric feature tools

#### 3. FEM

FEM is one of the clearest examples of workflow duplication outside Sketcher. Many commands create an analysis object or constraint and then immediately enter edit mode through direct GUI document calls.

Primary target:

- introduce a canonical analysis-object edit workflow for constraints, materials, loads, meshes, and post objects

Consistency problems already visible:

- many command handlers directly call `Gui.activeDocument().setEdit(...)`
- task dialogs own substantial cleanup behavior independently
- analysis activation, mesh visibility, object visibility, and task panel ownership are coupled but not modeled as one workflow

What this family should prove:

- domain-specific preconditions can stay rich without making every command a workflow owner
- analysis-state normalization, object visibility normalization, and task-panel lifecycle can be expressed as one canonical policy

#### 4. Assembly

Assembly has a strong edit-session model, but much of that behavior currently lives in view providers and double-click handlers.

Primary target:

- make assembly activation and edit entry explicit workflow intents instead of view-provider-owned behavior

Consistency problems already visible:

- tree double-click owns meaningful workflow semantics
- workbench switching and edit restoration are coupled to object-view behavior
- assembly task panel ownership and active-object state are managed inside edit-entry code paths instead of a reusable session policy

What this family should prove:

- object-centric interactive sessions can still follow the same intent -> resolve -> normalize -> execute -> finalize model
- edit restoration across nested workflows such as "leave assembly edit to edit a sketch, then return" can be formalized instead of inferred

#### 5. TechDraw

TechDraw is less about `setEdit(...)` frequency and more about command-surface consistency, page context, and mode-sensitive tool availability.

Primary target:

- normalize page-centric workflows such as page creation, view insertion, annotation, and dimension editing around explicit page context

Consistency problems already visible:

- toolbar shape and command grouping depend on user preferences and module-local logic
- page, view, and annotation operations are spread across many command groups without one workflow model for page-active context
- command-surface state is rich but mostly declarative only at the toolbar level, not at the workflow level

What this family should prove:

- workflow consistency is not only about edit mode; it also applies to page ownership, selection gating, and mode-dependent tool exposure
- the same page-oriented intent can drive both ribbon and classic command surfaces from one resolved page context

#### 6. CAM, Robot, and other task-heavy domain workbenches

These modules often combine object creation, parameter editing, and document-side cleanup in command and task-dialog code.

Primary target:

- normalize long-running task sessions so object creation, task ownership, edit entry, preview state, and completion or cancel cleanup follow one session contract

Consistency problems already visible:

- command files directly enter edit mode after object creation
- task dialogs frequently own reset behavior themselves
- preview, selection, and active-object state are often handled locally per tool

What this family should prove:

- the workflow model can support domain tools that are more procedural than Sketcher or PartDesign without collapsing into a giant abstract framework

### A generalized consistency rule for all workbenches

For every major workbench, FreeCAD should answer the same five questions explicitly:

1. What is the canonical intent for this action?
2. What context must be resolved before UI changes happen?
3. What shell state must be normalized before execution or edit begins?
4. What component owns completion, cancel, and edit-exit behavior?
5. What tests prove that equivalent entry points are behaviorally identical?

If a workbench cannot answer those questions for a user-facing action, then that action is still route-owned instead of workflow-owned.

### Common workflow archetypes across workbenches

The philosophy becomes easier to apply if FreeCAD stops thinking only in terms of modules and starts also thinking in terms of workflow archetypes.

Most workbench actions fall into a small number of reusable shapes:

#### 1. Create-and-enter-edit workflows

Examples:

- Sketcher or PartDesign `New Sketch`
- FEM constraint creation followed by immediate parameter editing
- Part and Surface feature creation that immediately opens a task dialog
- CAM or Robot object creation that begins a session immediately

Shared requirements:

- resolve creation context before mutating the document
- normalize shell state before opening edit mode
- enter one canonical edit-session path after object creation

#### 2. Edit-existing-object workflows

Examples:

- `Edit Sketch`
- editing a PartDesign datum or feature parameters
- editing an FEM analysis object or constraint
- editing an existing Assembly object session

Shared requirements:

- resolve the target object and owning container explicitly
- normalize workbench, active view, and command surface before edit entry
- use one explicit owner for completion, cancel, and restore behavior

#### 3. Interactive session workflows

Examples:

- Assembly manipulation or joint editing
- task-driven CAM setup
- Surface tools with preview-driven interaction
- Robot trajectory and edge selection sessions

Shared requirements:

- define the session owner explicitly
- define preview-state, selection gate, and cancel semantics explicitly
- make nested edit/session restoration deterministic

#### 4. Page or analysis context workflows

Examples:

- TechDraw page and view insertion
- FEM analysis activation and object creation inside an analysis
- FlowStudio-style study or simulation context workflows

Shared requirements:

- resolve the owning page, analysis, or study first
- derive task panels, toolbars, and contextual surfaces from that resolved owner
- ensure the same owner context is preserved through confirm, cancel, and follow-up edits

By naming these archetypes explicitly, FreeCAD can adopt shared infrastructure without forcing every workbench into the same domain model.

### Cross-workbench adoption checklist

Before migrating a workbench family, contributors should complete the same checklist.

#### Step 1. Inventory the routes

List all entry points for the target action:

- toolbar command
- menu command
- tree double-click
- context menu
- shortcut
- Python or macro entry
- task-panel re-entry action

#### Step 2. Identify the hidden owners

Find where semantics actually live today:

- command class
- view provider
- task dialog
- workbench `activated()` hook
- helper utility
- Python bridge or macro helper

#### Step 3. Define the canonical intent

Write down one normalized intent name and the minimum payload it needs.

Examples:

- `CreateFemConstraint`
- `EditAssemblySession`
- `CreateTechDrawPage`
- `EditSurfaceFeatureParameters`

#### Step 4. Define the required context contract

For each intent, explicitly define:

- active document requirement
- owning container requirement such as body, page, analysis, or study
- explicit target object if any
- selection contract
- whether additional user input is needed before execution

#### Step 5. Define shell-state policy

For each intent, explicitly decide:

- required workbench
- required active view type
- required task panel owner
- required ribbon or classic-toolbar profile
- contextual tab behavior
- selection cleanup behavior
- cancel and restore behavior

#### Step 6. Move entry points to thin adapters

After the canonical path exists, all legacy triggers should become thin adapters that only:

- gather current selection and metadata
- build the normalized intent
- dispatch to the canonical controller or workflow service

#### Step 7. Add equivalence tests

Each migrated action should gain both:

- source guards that prevent reintroduction of known bypasses
- runtime tests that prove equivalent entry points produce equivalent shell state and edit state

### What should be shared globally vs locally

To keep this philosophy practical, not everything should be centralized in one giant framework.

#### Global shared infrastructure

These should become reusable across many workbenches:

- workflow intent definitions and routing patterns
- shell-state normalization primitives
- edit-session lifecycle primitives
- contextual ribbon and classic-toolbar profile rules
- integration-test harness patterns
- logging categories for workflow transitions

#### Workbench-local policies

These should stay domain-owned but plug into the shared model:

- body resolution in PartDesign
- analysis and mesh visibility rules in FEM
- page ownership rules in TechDraw
- joint or assembly activation rules in Assembly
- tool preview semantics in Surface, CAM, or Robot

The rule is simple: shared infrastructure should own workflow shape, while workbenches continue to own domain meaning.

### Signs that a workbench is ready for migration

A workbench is a good migration candidate when at least two of these are true:

- the same user-facing action has multiple entry points
- commands directly call `setEdit(...)` or `resetEdit()` repeatedly
- task dialogs own their own cleanup and restore behavior
- workbench switching is handled as an implicit side effect
- ribbon or toolbar state differs depending on route, not resolved context
- contributors struggle to explain which code path actually owns the workflow

By that standard, FEM and Assembly are strong next candidates, while TechDraw is the best proof that this philosophy also applies to non-edit-centric workflows.

### Recommended rollout beyond sketches

The next expansion should follow workbench families, not arbitrary command counts.

Recommended order:

1. PartDesign and Sketcher: finish the pilot completely, including create-sketch and shell-state policy extraction.
2. FEM: use it as the first non-sketch proof that repeated direct `setEdit(...)` command patterns can be replaced with canonical edit-session services.
3. Assembly: formalize nested edit restoration and interactive-session ownership.
4. Part and Surface: collapse feature-parameter editing into shared edit-session patterns.
5. TechDraw: apply the philosophy to page and command-surface context, proving the model works even when the main problem is not classic edit mode.

This order matters because it moves from the already-active pilot, to a command-heavy edit domain, to a session-heavy interactive domain, and finally to a page-context domain. If the philosophy survives all four shapes of workflow, it is general enough for the rest of FreeCAD.

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

### Phase 2.5. Extract shared shell-state policy for edit workflows

Goal: make workbench, ribbon, classic toolbar, and contextual-surface transitions follow one explicit policy instead of scattered side effects.

Actions:

- identify the minimum shared shell-state contract for edit entry and shell toggles
- centralize workbench-activation side effects that today are split across command handlers, main-window signals, and workbench `activated()` hooks
- define when contextual ribbon surfaces are registered, materialized, refreshed, and suppressed
- define the fallback policy when ribbon mode is disabled so classic toolbars remain usable for the same resolved edit context
- isolate shutdown-safe and hidden-widget-safe refresh rules for contextual UI surfaces

Success criteria:

- toggling ribbon mode does not change the resolved edit-session command surface for the same context
- contextual tabs and classic toolbars are driven by the same resolved edit profile instead of ad hoc refresh code
- workbench activation side effects no longer need to be reimplemented inside individual toggle commands
- sequential shell transitions like ribbon on -> off -> on are covered by dedicated regression tests

### Phase 3. Generalize the workflow model beyond sketches

Goal: apply the same consistency pattern to other high-friction user actions.

Candidate targets:

- Pad
- Pocket
- datum creation and edit
- feature parameter editing
- TechDraw page creation
- assembly edit entry
- FEM constraint and analysis-object editing
- Part and Surface feature-parameter sessions
- Robot and CAM task-driven edit sessions
- selection-driven context actions

Actions:

- define reusable workflow primitives for edit sessions and create sessions
- define reusable shell-state primitives for command-surface transitions
- centralize workbench-switch policy
- centralize task-panel lifecycle handling
- centralize active-view and camera policy where workflows depend on them

Success criteria:

- cross-workbench create and edit commands stop owning their own private UI-state logic
- ribbon, classic toolbar, and contextual command-surface state become policy outputs instead of per-workbench accidents
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

## Implementation Artifacts

The philosophy needs a small, repeatable set of implementation artifacts. Without those artifacts, teams will keep re-deriving the model ad hoc.

These artifacts do not all need to appear at once, but the refactor should converge toward them.

### 1. Intent and result types

Each migrated workflow family should use explicit types for:

- intent id
- entry-point metadata
- resolved context
- execution result
- cancel or error outcome

The purpose is not abstraction for its own sake. The purpose is to make workflow decisions inspectable and testable.

### 2. Context resolvers

Each workbench family should have one canonical context resolver per workflow family.

Examples:

- sketch create resolver
- sketch edit resolver
- FEM analysis-object edit resolver
- Assembly session-entry resolver
- TechDraw page-context resolver

If multiple commands still independently answer the same context questions, the migration is incomplete.

### 3. Shell-state normalizers

The refactor should converge on a shared set of shell-state helpers that can be reused by many workbenches.

The current shell-state pilot now has one concrete reusable primitive in `Gui::Application::refreshActiveWorkbench()`. That helper is intentionally narrow: it replays the active workbench shell surfaces, fails closed during shutdown, and gives caller sites a single place to reuse workbench-surface refresh policy.

Expected responsibility areas:

- workbench activation policy
- active-view normalization
- task-panel activation and replacement policy
- ribbon and classic-toolbar profile application
- contextual tab refresh and suppression policy
- selection cleanup and selection-gate installation
- safe exit and restore behavior

### 4. Canonical workflow controllers or services

Not every workbench needs the same class names, but each workflow family should have a recognizable canonical owner.

Acceptable shapes include:

- a controller class
- a service object
- a workbench-local workflow module using shared infrastructure

What is not acceptable is leaving the workflow fragmented across unrelated commands, view providers, and task dialogs.

### 5. Regression artifacts

Each migration should leave behind both architecture guards and runtime checks.

Expected artifact types:

- source-guard tests for canonical route usage
- runtime smoke tests for equivalent entry points
- shell-state equivalence checks for ribbon, classic toolbar, task panel, and workbench state
- logging hooks for workflow transitions where runtime diagnosis is otherwise difficult

## Contributor Review Checklist

When reviewing a new GUI feature or a refactor of an existing workflow, reviewers should ask these questions explicitly.

### 1. Intent ownership

- Is there one canonical owner for the user intent?
- Are multiple entry points thin adapters, or do they still carry their own workflow semantics?

### 2. Context ownership

- Is selection and document context resolved once in a predictable place?
- Does the command still improvise context instead of calling a shared resolver?

### 3. Shell-state ownership

- Is workbench activation explicit?
- Is active-view normalization explicit?
- Are task panel, ribbon, and classic-toolbar changes derived from resolved context?
- Does the code rely on incidental side effects from `setEdit(...)`, `activated()`, or view-provider callbacks?

### 4. Exit and recovery ownership

- Is cancel behavior explicit?
- Is confirm behavior explicit?
- Is nested edit restoration explicit?
- Is reset or cleanup behavior centralized rather than repeated across task dialogs?

### 5. Regression protection

- Is there a source guard or other architectural check if the migration is protecting against a known bypass pattern?
- Is there a runtime check for observable equivalence if the action has multiple entry points?

If the answer to these questions is unclear from the patch itself, then the workflow is probably still too implicit.

## Migration Scorecard Template

Each workbench family should eventually be evaluated with the same scorecard. The point is not bureaucracy; the point is to make migration completeness visible.

Suggested scorecard dimensions:

- intent routing
- context resolution
- shell-state normalization
- edit-session lifecycle
- task-panel lifecycle
- ribbon and classic-toolbar equivalence
- cancel and recovery consistency
- source-guard coverage
- runtime equivalence coverage

Suggested status values:

- `Not Started`
- `Explored`
- `Pilot In Progress`
- `Partially Canonical`
- `Canonical For Primary Routes`
- `Fully Canonical And Guarded`

Applying the same scorecard to Sketcher, FEM, Assembly, Part/Surface, and TechDraw will make it easier to compare migration maturity across very different workbench families.

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
- same contextual ribbon or classic-toolbar command surface for the same resolved context
- same exit behavior after cancel or finish
- same behavior across shell transitions such as ribbon enable, disable, and re-enable

## Near-Term Deliverables

1. Finish sketch route unification.
2. Extract a shared create-sketch service.
3. Extract a shared shell-state policy for edit workflows and ribbon/classic transitions.
4. Define the first cross-workbench migration targets by family: FEM, Assembly, Part/Surface, and TechDraw.
5. Add contributor-facing documentation for the workflow model.
6. Establish a rule that equivalent user intents may not own independent GUI-state logic.

## Risks

### 1. Over-centralization

If the workflow layer becomes too abstract too quickly, it may become harder to maintain than the legacy code. The migration should stay incremental and use real user workflows as the organizing unit.

### 2. Cross-workbench regressions

PartDesign, Sketcher, and other modules do have legitimate differences. The refactor must normalize equivalent intent while preserving valid domain context.

### 3. Incomplete runtime verification

Some of the current work has source-level and diagnostic validation but not yet a complete configured build-and-run validation path in the IDE tooling. That verification gap should be closed as the next practical step.

### 4. Shell-state policy fragmentation

Even after recent fixes, ribbon visibility, contextual tab refresh, classic toolbar fallback, and workbench activation still span multiple owners. If that state remains distributed, future feature work can easily reintroduce route-specific inconsistencies.

## Recommended Next Step

The highest-value next step is now a paired move:

1. finish unifying `New Sketch` creation semantics so Sketcher and PartDesign stop owning separate creation workflows
2. extract a shared shell-state policy for sketch edit sessions so workbench activation, ribbon/classic command surfaces, and contextual refresh behavior stop depending on scattered command-side logic

Those two steps together move the refactor from isolated edit-entry normalization into a full consistency model where intent resolution and shell-state resolution are both canonical.

Immediately after that, the best proof of generality is FEM. It has enough repeated direct edit-entry patterns to make consistency wins obvious, but it is different enough from Sketcher that success there would show the philosophy scales beyond geometry-sketch workflows.