# Sketch Workflow Unification Plan

## 1. Problem analysis

FreeCAD currently lets equivalent sketch actions enter the system through multiple behavioral paths. The user intent is the same, but the resulting workflow can differ in workbench state, active edit context, task panel content, toolbar composition, camera behavior, selection cleanup, and recovery behavior.

The most visible symptom is sketch inconsistency:

- `New Sketch` from PartDesign follows a richer workflow and body-aware setup path.
- `New Sketch` from Sketcher creates and edits directly.
- `Edit Sketch` from command actions routes differently than tree double-click.
- Some paths normalize the active 3D view and hide backstage surfaces, others do not.

That breaks the principle that the same user intent must yield the same workflow.

## 2. Root-cause analysis of why FreeCAD currently becomes inconsistent

The inconsistency is structural, not cosmetic.

### 2.1 Command identity is coupled to entry point

Today, the action meaning is often encoded by the command class that owns the UI trigger instead of a normalized intent. That leaves separate owners for equivalent behavior:

- `src/Mod/PartDesign/Gui/Command.cpp`: `CmdPartDesignNewSketch`
- `src/Mod/Sketcher/Gui/Command.cpp`: `CmdSketcherNewSketch`
- `src/Mod/Sketcher/Gui/Command.cpp`: `CmdSketcherEditSketch`
- `src/Mod/Sketcher/Gui/ViewProviderSketch.cpp`: tree double-click path

These do not all converge into one canonical handler.

### 2.2 Edit-mode entry is partially centralized but not fully normalized

`src/Mod/PartDesign/Gui/Utils.cpp` already centralizes a stronger `PartDesignGui::setEdit()` path. It hides the backstage, activates a 3D view, resolves active body context, and only then routes into `setEdit(...)`.

By contrast, several sketcher paths still call `Gui.activeDocument().setEdit(...)` or `Gui::Application::Instance->activeDocument()->setEdit(this)` directly, bypassing the same normalization steps.

### 2.3 Creation logic is split between workbenches

`src/Mod/PartDesign/Gui/SketchWorkflow.cpp` already behaves like a proto-canonical workflow for PartDesign sketch creation. It resolves body/support state, handles support selection, creates the object, and enters edit mode through `PartDesignGui::setEdit(...)`.

`src/Mod/Sketcher/Gui/Command.cpp` still owns an independent creation flow with its own orientation dialog and direct edit entry. That means “new sketch” semantics depend on which workbench command was used.

### 2.4 UI state policy is implicit and scattered

Workbench activation, toolbar visibility, task-panel ownership, selection reset, and view activation are handled as side effects spread across commands and view providers. No explicit policy object defines the expected edit environment.

### 2.5 Tree actions and context actions bypass command semantics

`src/Mod/Sketcher/Gui/ViewProviderSketch.cpp` opens edit mode directly on double-click. That makes the tree a separate behavioral owner rather than a thin trigger for the same `Edit Sketch` intent.

### 2.6 Regression protection is local, not systemic

`tests/src/Mod/PartDesign/Gui/SketchWorkflowSetEdit.cpp` guards a specific Start-page / active-view ordering fix, but the architecture does not yet enforce the same normalization across all sketch entry points.

## 3. Target UX principles

The target UX should be defined by intent, not by click origin.

- Same intent, same result.
- Entry point must not alter workflow.
- Workbench transitions must be explicit and inspectable.
- View behavior must follow a declared policy.
- Toolbar and task panel state must be deterministic for the same context.
- Selection preconditions and cleanup must be uniform.
- Cancel, error, and recovery behavior must be uniform.
- Logs and tests must be able to prove path equivalence.

For sketches, that means:

- every valid `New Sketch` trigger produces the same support-resolution and edit-entry flow
- every valid `Edit Sketch` trigger produces the same sketch editing environment
- the exit path restores the same normalized post-edit state

## 4. Proposed architecture

Introduce a five-layer workflow model and make UI elements thin intent emitters.

### 4.1 Intent layer

Add a normalized action model in `src/Gui` or a new `src/Mod/CommonGui/Workflow` area.

Suggested enum and payload:

```cpp
enum class WorkflowIntentId {
    CreateSketch,
    EditSketch,
    CreatePad,
    CreatePocket,
    CreateBody,
    OpenTechDrawPage,
    EnterAssemblyEdit
};

enum class WorkflowEntryPoint {
    Toolbar,
    Menu,
    ContextMenu,
    TreeDoubleClick,
    Shortcut,
    TaskPanel,
    WorkbenchButton,
    Api
};

struct WorkflowIntent {
    WorkflowIntentId id;
    WorkflowEntryPoint entryPoint;
    Gui::Document* guiDocument;
    std::vector<Gui::SelectionObject> selection;
    App::DocumentObject* explicitTarget {nullptr};
};
```

Every GUI trigger should build one `WorkflowIntent` and hand it to a router.

### 4.2 Context resolution layer

Centralize deterministic context discovery in resolvers:

- active document
- active body / part / group container
- selected object and selected support geometry
- whether an existing sketch is the target
- whether support selection is sufficient
- whether user interaction is still needed
- whether the intent is legal in the current document state

This layer should return typed results instead of letting commands improvise.

```cpp
struct SketchWorkflowContext {
    App::Document* appDocument;
    Gui::Document* guiDocument;
    PartDesign::Body* activeBody {nullptr};
    Sketcher::SketchObject* targetSketch {nullptr};
    App::DocumentObject* supportObject {nullptr};
    std::string supportSubElement;
    bool needsBodyCreation {false};
    bool needsSupportDialog {false};
    bool allowDetachedSketch {false};
};
```

### 4.3 Workflow state transition layer

Create an explicit GUI normalization subsystem that owns:

- active workbench selection
- active MDI view activation
- dock visibility profile
- task panel lifecycle
- toolbar profile
- selection filter and cleanup
- navigation restrictions during edit mode
- camera transition policy
- edit-mode enable/disable state

This should be policy-driven instead of hard-coded in command classes.

### 4.4 Execution layer

Execution performs the minimal action for the already-resolved context:

- create sketch object
- attach or map it if required
- open existing sketch for edit

Execution should not decide view/tool/task state on its own.

### 4.5 Post-state normalization layer

This layer guarantees:

- consistent final toolbar and task-panel state after enter
- consistent cleanup after cancel or completion
- consistent restoration of selection and workbench policy
- consistent logging and telemetry completion events

## 5. Canonical `New Sketch` workflow

This should replace all local `New Sketch` logic in PartDesign, Sketcher, context menus, shortcuts, and task-panel shortcuts.

### 5.1 Canonical workflow specification

1. Build `WorkflowIntent { CreateSketch, entryPoint, guiDocument, selection, explicitTarget }`.
2. Route through `WorkflowRouter::dispatch(intent)`.
3. `SketchContextResolver::resolveCreate(intent)` determines:
   - active document
   - active body or legal target container
   - whether body activation/creation is needed
   - whether selected support is valid
   - whether a support/orientation dialog is required
4. `WorkflowGuard` validates prerequisites and returns a normalized error model.
5. `SketchEntryStateNormalizer::prepare(context, policy)` performs:
   - hide backstage
   - ensure 3D view active
   - activate required workbench explicitly
   - apply toolbar/task-panel profile
   - clear or normalize selection
   - configure selection gate
   - apply view-transition policy
6. `CreateSketchExecutor::run(context)` creates the sketch and attaches it if needed.
7. `SketchEditSession::enter(newSketch, context, editPolicy)` enters the edit environment.
8. `WorkflowPostNormalizer::afterEnter(...)` guarantees stable post-entry UI state.

### 5.2 Uniform rules for `New Sketch`

- If the selected support is a planar face, datum plane, or sketch support candidate, the same support validation rules apply from every entry point.
- If no active body exists and body context is required, the same body resolution dialog or recovery action must appear everywhere.
- If the sketch is created detached, the same orientation/support dialog must be used everywhere.
- If view alignment is configured, the same policy must execute everywhere.
- The same toolbars, task panel, selection gate, and command availability must result for the same resolved context.

### 5.3 Preferred migration path

Keep `PartDesignGui::SketchWorkflow` as the first extraction source. It already contains valuable support/body creation logic. Refactor it from a PartDesign-owned helper into a shared canonical sketch-create workflow service, then make `CmdPartDesignNewSketch` and `CmdSketcherNewSketch` both call it.

## 6. Canonical `Edit Sketch` workflow

Every edit entry path must converge before entering sketch edit mode.

### 6.1 Canonical workflow specification

1. Build `WorkflowIntent { EditSketch, entryPoint, guiDocument, selection, explicitTarget }`.
2. `SketchContextResolver::resolveEdit(intent)` determines the target sketch and owning body/container.
3. `SketchEditStateNormalizer::prepare(context, policy)` performs:
   - hide backstage
   - ensure active 3D view
   - activate target workbench explicitly
   - normalize selection state
   - close/replace conflicting task dialogs through one policy path
   - apply camera policy
   - install edit selection restrictions
4. `EditSketchExecutor::run(context)` enters edit through one canonical API.
5. `WorkflowPostNormalizer::afterEnter(...)` ensures task panel, toolbars, command groups, and navigation restrictions match the same edit profile.

### 6.2 Entry points that must be routed into the same handler

- `CmdSketcherEditSketch`
- tree double-click on sketch view provider
- any context-menu “Edit Sketch” action
- shortcut-driven sketch edit
- part/body-specific edit buttons that resolve to a sketch

### 6.3 Canonical edit API

Introduce a dedicated entry surface instead of calling `setEdit(...)` from multiple places:

```cpp
class SketchWorkflowController {
public:
    WorkflowResult createSketch(const WorkflowIntent& intent);
    WorkflowResult editSketch(const WorkflowIntent& intent);
};
```

Internally, it may still end at `Gui::Document::setEdit(...)`, but only after state normalization is complete.

### 6.4 Required behavioral changes

- `ViewProviderSketch::doubleClicked()` must no longer own edit semantics; it should emit `Intent::EditSketch`.
- `CmdSketcherEditSketch` must no longer call `Gui.activeDocument().setEdit(...)` directly.
- Any PartDesign feature or Python command that opens sketch editing must use the canonical controller.

## 7. Refactor strategy

The right strategy is staged extraction, not a single rewrite.

### Stage 1: Establish a shared workflow surface

Add a new workflow router/controller module without changing visible behavior yet.

- Introduce `WorkflowIntent`, `WorkflowResult`, logging hooks, and `SketchWorkflowController`.
- Keep existing code paths, but make PartDesign and Sketcher commands delegate into the new controller.

### Stage 2: Extract common normalization from PartDesignGui::setEdit()

Move these concerns into a reusable normalizer:

- backstage hide
- 3D view activation
- active workbench activation
- task-dialog replacement policy
- selection cleanup

`PartDesignGui::setEdit()` then becomes either a thin adapter or is retired.

### Stage 3: Unify sketch creation context resolution

Lift support/body-resolution logic out of `PartDesignGui::SketchWorkflow` into shared services.

- preserve existing behavior first
- remove Sketcher-local creation forks second

### Stage 4: Replace direct edit calls

Audit and replace direct calls that bypass canonical routing:

- `src/Mod/Sketcher/Gui/Command.cpp`
- `src/Mod/Sketcher/Gui/ViewProviderSketch.cpp`
- `src/Mod/PartDesign/SprocketFeature.py`
- `src/Mod/PartDesign/InvoluteGearFeature.py`
- any remaining `Gui.activeDocument().setEdit(...)` for sketch intents

### Stage 5: Normalize post-exit behavior

Introduce a shared exit policy so `resetEdit()` and completion/cancel flow restore the same UI state for all sketch sessions.

### Stage 6: Expand the same model to Pad, Pocket, datum-edit, Draft, TechDraw, Assembly

Do not duplicate sketch-specific infrastructure; generalize it into reusable workflow plumbing.

## 8. Suggested classes/modules/interfaces

The names below keep responsibilities narrow and testable.

### 8.1 Core routing and telemetry

- `src/Gui/Workflow/WorkflowIntent.h`
- `src/Gui/Workflow/WorkflowRouter.h/.cpp`
- `src/Gui/Workflow/WorkflowTrace.h/.cpp`
- `src/Gui/Workflow/WorkflowResult.h`

### 8.2 Sketch-specific controller and resolvers

- `src/Mod/Sketcher/Gui/SketchWorkflowController.h/.cpp`
- `src/Mod/Sketcher/Gui/SketchContextResolver.h/.cpp`
- `src/Mod/Sketcher/Gui/SketchCreateExecutor.h/.cpp`
- `src/Mod/Sketcher/Gui/SketchEditExecutor.h/.cpp`

### 8.3 GUI state normalization

- `src/Gui/Workflow/GuiStateNormalizer.h/.cpp`
- `src/Gui/Workflow/WorkbenchTransitionPolicy.h`
- `src/Gui/Workflow/ViewTransitionPolicy.h`
- `src/Gui/Workflow/ToolbarLayoutPolicy.h`
- `src/Gui/Workflow/TaskPanelPolicy.h`
- `src/Gui/Workflow/SelectionPolicy.h`

### 8.4 Sketch policy objects

- `src/Mod/Sketcher/Gui/SketchEntryPolicy.h`
- `src/Mod/Sketcher/Gui/SketchEditPolicy.h`

Suggested fields:

```cpp
struct SketchEntryPolicy {
    bool require3DView {true};
    bool hideBackstage {true};
    bool requireExplicitWorkbenchActivation {true};
    bool clearSelectionOnEnter {true};
    bool normalizeToolbars {true};
    bool normalizeTaskPanel {true};
    bool normalizeSelectionGate {true};
    ViewTransitionMode viewMode {ViewTransitionMode::AlignIfSupported};
};
```

### 8.5 Compatibility adapters

To reduce churn, keep temporary adapters:

- `PartDesignGui::SketchWorkflowAdapter`
- `SketcherGui::LegacySketchCommandAdapter`
- `PartDesignGui::LegacySetEditAdapter`

These should forward into the new controller and disappear over time.

### 8.6 Telemetry/debug tracing

Add structured trace events for every workflow transition:

- intent id
- entry point
- selected target summary
- resolved container/body
- chosen policies
- execution path
- success / cancel / validation failure

Use existing logging style, for example via a dedicated workflow log category.

## 9. Testing and regression strategy

The testing strategy must verify equivalence, not just success.

### 9.1 Command-path equivalence tests

For `New Sketch`, execute through:

- toolbar command
- menu command
- context-menu command
- shortcut command
- tree-triggered or task-panel-triggered entry if applicable

For `Edit Sketch`, execute through:

- command action
- tree double-click
- context-menu edit action
- shortcut action

Assert the same normalized state snapshot:

- active workbench id
- active edit object
- active body/container
- active task panel type
- visible toolbar profile
- selection gate / selection contents
- active command group set
- camera/view policy outcome
- dock visibility profile

### 9.2 GUI state snapshot tests

Add a small serializable snapshot model:

```cpp
struct GuiWorkflowSnapshot {
    std::string activeWorkbench;
    std::string activeEditObject;
    std::string activeBody;
    std::string taskDialogClass;
    std::vector<std::string> visibleToolbars;
    std::vector<std::string> enabledCommandGroups;
    std::string activeViewType;
    std::string cameraPolicyOutcome;
    std::vector<std::string> selectedObjects;
};
```

The equivalence test should compare snapshots after normalization.

### 9.3 Regression tests for previously fragile behavior

Extend the existing protection in `tests/src/Mod/PartDesign/Gui/SketchWorkflowSetEdit.cpp` so it no longer only covers the PartDesign path.

Add tests that prove:

- every sketch entry path activates a 3D view before entering edit
- every path hides backstage if visible
- every path reaches the same controller method

### 9.4 Edge-case tests

Required matrix:

- no active document
- no active body
- exactly one active body
- multiple selected objects
- planar face selected
- datum plane selected
- sketch selected as support/reference
- sketch inside body
- sketch outside body
- invocation from Sketcher workbench
- invocation from PartDesign workbench
- invocation with non-3D MDI surface active

### 9.5 Plugin and extension safety

Add tests that fail if new UI actions bypass the canonical router.

Examples:

- scan command registration metadata for sketch-equivalent actions and ensure they bind to the workflow controller
- add source-guard tests for known bypass strings where appropriate

## 10. Example pseudocode

```cpp
WorkflowResult WorkflowRouter::dispatch(const WorkflowIntent& intent)
{
    WorkflowTraceScope trace(intent);

    switch (intent.id) {
    case WorkflowIntentId::CreateSketch:
        return sketchController.createSketch(intent);
    case WorkflowIntentId::EditSketch:
        return sketchController.editSketch(intent);
    default:
        return WorkflowResult::unsupported(intent.id);
    }
}
```

```cpp
WorkflowResult SketchWorkflowController::createSketch(const WorkflowIntent& intent)
{
    auto context = sketchContextResolver.resolveCreate(intent);
    if (!context.ok()) {
        return workflowFailureHandler.reject(context.error());
    }

    guiStateNormalizer.prepare(
        GuiWorkflowMode::SketchEntry,
        context.value(),
        sketchEntryPolicyProvider.policyFor(context.value())
    );

    auto sketch = sketchCreateExecutor.run(context.value());
    if (!sketch.ok()) {
        guiStateNormalizer.rollback(context.value());
        return sketch.error();
    }

    auto enterResult = sketchEditExecutor.enter(sketch.value(), context.value());
    guiStateNormalizer.finalizeEnter(context.value(), enterResult);
    return enterResult;
}
```

```cpp
WorkflowResult SketchWorkflowController::editSketch(const WorkflowIntent& intent)
{
    auto context = sketchContextResolver.resolveEdit(intent);
    if (!context.ok()) {
        return workflowFailureHandler.reject(context.error());
    }

    guiStateNormalizer.prepare(
        GuiWorkflowMode::SketchEdit,
        context.value(),
        sketchEditPolicyProvider.policyFor(context.value())
    );

    auto result = sketchEditExecutor.enterExisting(context.value());
    guiStateNormalizer.finalizeEnter(context.value(), result);
    return result;
}
```

```cpp
bool ViewProviderSketch::doubleClicked()
{
    WorkflowIntent intent;
    intent.id = WorkflowIntentId::EditSketch;
    intent.entryPoint = WorkflowEntryPoint::TreeDoubleClick;
    intent.guiDocument = Gui::Application::Instance->activeDocument();
    intent.explicitTarget = getObject();

    return SketchWorkflowController::instance().editSketch(intent).accepted();
}
```

```cpp
void CmdSketcherEditSketch::activated(int)
{
    WorkflowIntent intent;
    intent.id = WorkflowIntentId::EditSketch;
    intent.entryPoint = WorkflowEntryPoint::Menu;
    intent.guiDocument = getActiveGuiDocument();
    intent.selection = Gui::Selection().getSelectionEx();

    SketchWorkflowController::instance().editSketch(intent);
}
```

## 11. Rollout strategy for applying the same consistency model across FreeCAD

The sketch workflow should be the template for a general workflow system.

### 11.1 First rollout target: Sketch

Sketch is the correct pilot because it already exposes the core problem:

- multiple entry points
- multiple workbench owners
- edit-mode side effects
- heavy task-panel and view normalization needs

### 11.2 Second rollout target: Pad and Pocket

After sketch routing is stable, move sketch-based PartDesign features to the same model:

- `Intent::CreatePad`
- `Intent::CreatePocket`

These workflows depend on the same context normalization patterns:

- active body
- active sketch
- consistent task dialog
- consistent command enablement

### 11.3 Third rollout target: datum, Draft, TechDraw, Assembly

Apply the same approach to workflows that currently depend on workbench-local behavior.

- datum creation/editing
- Draft tool entry/edit states
- TechDraw page creation and page edit routing
- Assembly edit mode and context transitions

### 11.4 Governance rule for future commands

New GUI triggers must not own workflow semantics.

Enforce a project rule:

- UI actions may create intents
- only workflow controllers may perform context resolution and GUI normalization
- direct `setEdit(...)` is allowed only inside canonical execution adapters, not in arbitrary UI triggers

### 11.5 Recommended audit list for immediate follow-up

Audit and migrate these first:

- `src/Mod/PartDesign/Gui/Command.cpp`
- `src/Mod/PartDesign/Gui/SketchWorkflow.cpp`
- `src/Mod/PartDesign/Gui/Utils.cpp`
- `src/Mod/Sketcher/Gui/Command.cpp`
- `src/Mod/Sketcher/Gui/ViewProviderSketch.cpp`
- `src/Mod/PartDesign/SprocketFeature.py`
- `src/Mod/PartDesign/InvoluteGearFeature.py`
- any remaining sketch-related `setEdit(...)` or `resetEdit()` entry calls discovered during migration

## Current inconsistent sketch-related entry points to audit

The current high-priority divergence points are:

- `src/Mod/PartDesign/Gui/Command.cpp`: `CmdPartDesignNewSketch` delegates to `SketchWorkflow` and already behaves closer to canonical.
- `src/Mod/Sketcher/Gui/Command.cpp`: `CmdSketcherNewSketch` still creates sketches and enters edit mode directly.
- `src/Mod/Sketcher/Gui/Command.cpp`: `CmdSketcherEditSketch` calls `Gui.activeDocument().setEdit(...)` directly.
- `src/Mod/Sketcher/Gui/ViewProviderSketch.cpp`: `ViewProviderSketch::doubleClicked()` directly enters edit mode.
- `src/Mod/PartDesign/Gui/Utils.cpp`: `PartDesignGui::setEdit()` contains important normalization logic that should become shared.
- `src/Mod/PartDesign/SprocketFeature.py`: direct sketch edit bypass through GUI command text.
- `src/Mod/PartDesign/InvoluteGearFeature.py`: direct sketch edit bypass through GUI command text.

## Recommended implementation direction

Do not try to solve this by tweaking toolbar visibility alone.

The correct fix is to make sketch creation and sketch editing into canonical workflow intents, centralize context resolution and GUI state normalization, and make every UI entry point delegate into those controllers. That addresses the root cause and creates a reusable architectural model for the rest of FreeCAD.