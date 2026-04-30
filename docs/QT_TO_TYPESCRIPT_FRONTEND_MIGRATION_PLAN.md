# FreeCAD Qt Removal and TypeScript Frontend Migration Plan

Status: active implementation plan

## Related Documents

- `docs/QT_SURFACE_INVENTORY.md`
- `docs/QT_UI_FORM_INVENTORY.md`
- `docs/PYSIDE_USAGE_TABLE.md`
- `docs/GUI_OWNERSHIP_TABLE.md`
- `docs/SRC_GUI_FILE_LEVEL_OWNERSHIP_INVENTORY.md`
- `docs/FRONTEND_PARITY_BASELINE_SPEC.md`
- `docs/QT_TO_TYPESCRIPT_REPO_EXECUTION_PLAN.md`
- `docs/architecture/ADR-0010-typescript-shell-and-qt-retirement.md`
- `docs/architecture/qt-to-typescript-migration-checklist.md`
- `docs/architecture/qt-to-typescript-milestone-issues.md`

## Current Implementation State

The repository is no longer at planning-only status for shell migration. The AsterForge variant already implements a backend-owned TypeScript shell slice with these verified capabilities:

- protocol-owned shell snapshot hydration through Rust and TypeScript generated types
- backend-owned active workbench state and shell-driven workbench switching
- backend-owned recent documents, workspace sessions, and shell session management actions
- backend-owned combo view and bottom dock tabs, visibility, and size hints
- persisted shell workspace state restored on gateway startup
- session restore that reapplies workbench, selection mode, selection, dock tabs, dock visibility, and dock size hints
- React-rendered task panel with differentiated PartDesign, Sketcher, and Part workspace behavior

The main remaining gap is not shell-state ownership but deeper workflow parity: command extraction, editing surfaces, viewport behavior, plugin compatibility, and dual-shell validation still remain unfinished.

## 1. Goal

Replace the current Qt-based FreeCAD application shell with a TypeScript-based frontend while preserving the current product visuality, interaction patterns, workbench structure, and document workflows.

This is not a one-step library swap. Qt is currently embedded into:

- application chrome and window management
- actions, menus, toolbars, docks, and task panels
- workbench activation and command routing
- Python and PySide tooling in many workbenches
- 3D viewport hosting and GUI lifecycle

The correct strategy is a staged shell replacement where Qt is first isolated, then hollowed out, then removed after the TypeScript shell reaches proven parity.

## 2. Target End State

The target desktop product should look and behave like FreeCAD, but the UI stack should be:

- frontend: React plus TypeScript
- desktop shell: Tauri preferred, Electron only if required by a hard blocker
- backend orchestration: Rust service layer
- native CAD bridge: C++ FreeCAD and OCCT retained behind explicit APIs
- rendering: web-native viewport stack hosted by the TypeScript shell, with native services for scene extraction, picking data, and heavy geometry tasks

Qt should be fully absent from the runtime UI shell in the final state.

## 3. Non-Negotiable Constraints

1. Do not rewrite the modeling kernel first.
2. Do not let frontend code own recompute logic or document truth.
3. Do not attempt full workbench migration before shell parity exists.
4. Do not remove Qt from the build until the TypeScript shell can run the primary workflows end to end.
5. Visual parity must be measured, not guessed.

## 4. Definition of "Same Visuality"

"Keep the same visuality" should be treated as a hard engineering requirement with measurable outputs.

The TypeScript shell must preserve:

- menu hierarchy and labels
- toolbar grouping and iconography
- dock and panel layout model
- tree view structure and affordances
- property editor grouping and editing behavior
- task panel flow and button placement
- viewport background, navigation affordances, and selection overlays
- typography scale, spacing rhythm, icon sizes, and density
- light and dark theme appearance
- command discoverability, shortcut behavior, and workbench switching patterns

Visual parity should be validated through:

- screenshot baselines for major screens
- layout metric baselines such as panel widths, toolbar heights, padding, and font sizes
- interaction recordings for core workflows
- user acceptance review against the current Qt shell

## 5. Recommended Repository Shape

The repository already points toward the right architecture through the AsterForge variant. The migration should converge toward a structure like this:

```text
frontend/
  app/
  design-system/
  viewport/
  workbench-shell/
backend/
  api-gateway/
  command-service/
  document-service/
  session-service/
  ui-layout-service/
native/
  freecad-bridge/
protocol/
  ui.proto or schema definitions
  generated types
src/
  legacy native FreeCAD core and remaining bridge code
```

## 6. Migration Strategy Summary

Use a 10-phase migration.

1. inventory the Qt surface area
2. freeze the existing visual contract
3. define backend-owned UI contracts
4. build the TypeScript shell skeleton
5. replicate the shell chrome with static parity
6. migrate command, document, and layout state behind APIs
7. replace tree, property, and task panels
8. replace viewport hosting and scene presentation
9. migrate workbench UIs incrementally
10. remove Qt and PySide dependencies from production UI paths

Each phase must end with explicit acceptance criteria.

## 7. Step-by-Step Plan

### Step 1. Create a Qt Dependency Inventory

Map every direct and indirect Qt dependency across:

- `src/Gui`
- workbench GUI modules under `src/Mod/*/Gui`
- Python GUI code using PySide
- resource pipelines such as icons, translations, and UI forms
- startup lifecycle and main window creation

Deliverables:

- `qt-surface-inventory.md`
- module ownership table
- dependency heatmap: easy to replace, hard to replace, blocked by native assumptions

Exit criteria:

- every Qt class category is accounted for
- every PySide-dependent workbench is identified
- all startup-critical Qt dependencies are listed

### Step 2. Capture the Existing Visual Contract

Before replacing anything, capture the current UI as a reproducible baseline.

Produce a visual parity suite for:

- start screen
- empty document shell
- Part workbench
- PartDesign workbench
- Sketcher task flow
- import/open workflow
- preferences window
- dark theme and light theme states

Capture:

- full-window screenshots
- panel-level screenshots
- spacing and typography tokens
- icon atlas and toolbar composition
- keyboard shortcut map

Deliverables:

- `frontend-parity-baseline/` screenshots
- `design-tokens-baseline.json`
- `interaction-baseline.md`

Exit criteria:

- design baselines can be compared automatically in CI
- visual regressions can be reported numerically

### Step 3. Define a UI Protocol Owned by the Backend

Do not re-encode FreeCAD semantics in React components. Introduce a backend-owned contract for UI composition.

Define protocol messages for:

- application layout state
- menu definitions
- toolbar definitions
- command state: enabled, checked, visible, tooltip, icon, shortcut
- workbench list and active workbench
- document tree model
- property panel schema and editors
- task panel schema
- notifications, progress, jobs, and diagnostics
- selection and preselection state

Recommended representation:

- schema-first contracts under `protocol/`
- generated Rust and TypeScript types
- versioned API rules

Deliverables:

- initial protocol schema
- generated TS and Rust models
- backend adapter layer that translates current FreeCAD state into protocol payloads

Exit criteria:

- no frontend feature requires direct access to Qt objects
- menus, toolbars, and command state can be rendered from protocol payloads alone

### Step 4. Build the TypeScript Desktop Shell

Create the production shell using:

- Tauri desktop host
- React plus TypeScript frontend
- Vite build pipeline
- design token system for theme control
- persistent layout state

At this stage, do not connect full document semantics yet. Only establish:

- window frame
- menu bar region
- toolbar bands
- left and right dock regions
- central viewport region
- status bar
- command palette

Deliverables:

- bootable desktop shell
- routing and shell state model
- theme token implementation

Exit criteria:

- app launches with native desktop packaging
- shell matches the FreeCAD frame proportions and density

### Step 5. Recreate the Application Chrome with Static Visual Parity

Replicate the current FreeCAD chrome exactly before wiring complex behavior.

Rebuild in TypeScript:

- menu bar
- top and side toolbars
- combo view region
- report view region
- tree panel shell
- property panel shell
- status bar zones
- workbench selector

Use the captured baseline to tune:

- font sizes
- toolbar padding
- icon scale
- border and divider styling
- panel spacing
- hover and pressed states

Deliverables:

- screenshot-diff clean room shell
- icon and theme asset pipeline

Exit criteria:

- baseline screenshots match within agreed tolerance
- product team can switch between Qt shell and TS shell and recognize no major visual drift

### Step 6. Move Command and Workbench State Behind Services

Replace Qt `QAction`, `QMenu`, `QToolBar`, and workbench-selector logic with backend-driven state.

Implement services for:

- command registry
- command execution
- command enablement and check state
- shortcut registration
- workbench activation
- recent files and document tabs

This is the key step that stops Qt from being the command backbone.

Deliverables:

- backend command service
- TS command store
- protocol events for command-state updates

Exit criteria:

- menus and toolbars in the TS shell function without Qt action objects
- active workbench changes are driven through backend APIs

### Step 7. Replace the Tree View, Property Editor, and Task Panels

These three surfaces define most of FreeCAD's day-to-day UX and must be migrated before Qt can disappear.

Sub-steps:

1. Replace the document tree with a virtualized TS tree component.
2. Replace the property editor with schema-driven editors.
3. Replace task panels with backend-described workflows.
4. Replace report and diagnostics views.
5. Replace selection synchronization between panels and viewport.

Important rule:

The backend owns object identity, property metadata, read-only rules, and transaction boundaries. The frontend only renders and edits through commands.

Deliverables:

- TS tree component with large-document support
- property schema renderer
- task panel runtime
- selection sync service

Exit criteria:

- primary editing flows can be completed without any Qt panel widgets
- tree and property edits preserve undo and recompute behavior

### Step 8. Replace the Viewport Host

Qt removal fails if the project does not replace the viewport correctly.

Do not try to port Coin3D widget hosting directly. Instead:

- define a scene payload API from native backend to frontend
- stream tessellated geometry, transforms, materials, visibility, and selection IDs
- render with a web-native viewport stack in TypeScript
- move camera, navigation, overlays, and hit-testing integration into the frontend
- keep heavy geometry generation and authoritative picking metadata in native or backend services

Recommended path:

- frontend rendering with Three.js or a similar GPU-friendly stack
- backend-generated scene graph payloads and incremental updates
- backend-owned selection IDs and stable object mapping

Deliverables:

- viewport scene protocol
- TS viewport renderer
- navigation controls matching current FreeCAD behavior
- overlay layer for preselection, sectioning, measurement, and gizmos

Exit criteria:

- open, navigate, select, hide/show, fit, and isolate work reliably
- camera and selection behavior are familiar to current FreeCAD users

### Step 9. Migrate Workbench UI Surfaces Incrementally

After shell parity exists, migrate workbench UI one domain at a time.

Suggested order:

1. Start
2. Part
3. PartDesign
4. Sketcher
5. Draft
6. TechDraw
7. FEM and specialist workbenches
8. addon and plugin compatibility surfaces

For each workbench:

- convert commands to backend descriptors
- convert task panels to protocol-driven forms
- replace PySide widgets with TS components
- preserve labels, icons, ordering, and flow structure unless a deliberate redesign is approved

Deliverables:

- workbench migration checklist
- parity review for each migrated workbench

Exit criteria:

- the workbench can run in the TS shell without Qt widgets
- visual and workflow parity are signed off

### Step 10. Build a PySide and Plugin Compatibility Strategy

Qt removal will break plugins and macros unless compatibility is planned explicitly.

Introduce three compatibility modes:

1. pure backend plugin API for new extensions
2. TS frontend contribution API for UI extensions
3. temporary legacy adapter for PySide-heavy plugins during transition

Rules:

- no new plugin should depend on Qt after the migration midpoint
- legacy PySide plugins may run in a compatibility lane for a limited time
- each major bundled workbench should get a de-Qt plan before the final cutover

Deliverables:

- plugin migration guide
- deprecation schedule for PySide GUI plugins
- compatibility adapter design

Exit criteria:

- extension authors have a supported path forward
- core bundled workflows no longer rely on PySide

### Step 11. Move Preferences, Theming, and Layout Persistence Out of Qt

Qt currently provides much of the application preferences and layout persistence behavior.

Replace it with backend-owned services for:

- preferences schema
- persisted layout state
- theme tokens and overrides
- shortcut customization
- recent files and shell memory

Deliverables:

- preferences service
- TS preferences UI
- layout serialization format

Exit criteria:

- user layout survives restarts without Qt state restoration
- themes and shortcuts can be managed entirely in the new shell

### Step 12. Run Dual-Shell Operation

Do not cut over immediately. Run both shells in parallel during a controlled transition period.

Mode A:

- legacy Qt shell

Mode B:

- TypeScript shell backed by the same native document and command services

Use this period to compare:

- startup times
- workflow completion rates
- crash rates
- visual parity
- missing commands
- extension compatibility

Deliverables:

- dual-shell launch option
- telemetry and acceptance dashboards

Exit criteria:

- TS shell is good enough for daily engineering workflows
- remaining Qt-only blockers are small and enumerated

### Step 13. Remove Qt from Production Runtime Paths

Only after parity is proven should you begin actual removal.

Removal order:

1. stop launching Qt shell by default
2. remove Qt-only UI modules from production startup path
3. remove PySide dependencies from bundled workbenches
4. remove Qt resource and form pipelines no longer used
5. shrink `src/Gui` to bridge-only or remove it entirely where superseded
6. remove Qt from build requirements for the shipping product

Keep a temporary legacy branch if required, but avoid permanent dual maintenance.

Deliverables:

- production build without Qt runtime dependency
- cleanup PR series removing dead Qt code

Exit criteria:

- packaged product runs without Qt libraries
- core workflows and bundled workbenches are supported in the TS shell

## 8. Visual Parity Management Plan

To preserve the same visuality, create a dedicated parity workstream.

### 8.1 Design Token Extraction

Extract and codify:

- fonts
- font sizes
- icon sizes
- spacing scale
- border radii
- panel gaps
- colors
- shadows
- hover and selected states

Store these as explicit TS design tokens, not informal CSS values.

### 8.2 Screenshot Testing

Add screenshot baselines for:

- app shell states
- each primary workbench
- dialogs and task flows
- light and dark themes
- high-DPI layouts

### 8.3 Interaction Parity Testing

Test:

- keyboard shortcuts
- toolbar overflow behavior
- menu traversal
- property editing sequences
- sketch workflow and task completion flows
- docking and panel resizing behavior

### 8.4 User Review Gates

Require sign-off from users familiar with current FreeCAD before declaring parity on:

- shell chrome
- modeling workflow surfaces
- viewport feel
- preferences and customization

## 9. Technical Risks and Mitigations

### Risk 1. Qt is too deeply coupled into `src/Gui`

Mitigation:

- isolate GUI semantics behind protocol adapters first
- avoid direct replacement attempts inside the existing Qt widget tree

### Risk 2. PySide workbenches block removal

Mitigation:

- treat PySide migration as a separate tracked workstream
- provide temporary compatibility adapters

### Risk 3. Viewport replacement regresses usability

Mitigation:

- preserve camera and selection behavior by contract
- validate against real models and large assemblies early

### Risk 4. Frontend becomes a hidden second application core

Mitigation:

- keep command rules, recompute, and document truth in backend services
- use schema-driven rendering instead of hardcoded domain logic in React

### Risk 5. Plugin ecosystem fragments

Mitigation:

- publish extension APIs early
- document migration paths and deprecation windows

## 10. Milestone Sequence

### Milestone A. Discovery and Baselines

- Qt inventory complete
- screenshot and interaction baselines complete
- migration ownership assigned

### Milestone B. Static TS Shell Parity

- TS shell launches
- shell chrome visually matches FreeCAD
- no core workflow behavior yet required

### Milestone C. Command and Layout Parity

- menus, toolbars, and workbench switching functional
- preferences and layout persistence functional

### Milestone D. Editing Surface Parity

- tree, property panel, report view, and task panels functional

### Milestone E. Viewport Parity

- open, inspect, select, and navigate models in TS shell

### Milestone F. Core Workbench Parity

- Start, Part, PartDesign, and Sketcher usable in TS shell

### Milestone G. Cutover Readiness

- TS shell is stable for daily use
- Qt shell is no longer required for bundled primary workflows

### Milestone H. Qt Removal

- production runtime no longer depends on Qt

## 11. Recommended First 90 Days

### Days 1-15

- build Qt dependency inventory
- capture screenshot baselines
- define parity metrics

### Days 16-30

- define protocol contracts for commands, layout, tree, properties, and tasks
- generate TS and Rust types

### Days 31-45

- stand up TS desktop shell
- recreate static FreeCAD chrome

### Days 46-60

- wire menus, toolbars, workbench selector, and status bar to backend state

### Days 61-75

- implement tree and property panel protocol rendering

### Days 76-90

- prototype viewport bridge and validate with real documents
- decide final viewport stack

## 12. Recommended Acceptance Metrics

- less than 5 percent screenshot delta on approved parity views
- 100 percent menu and toolbar command coverage for migrated workbenches
- no mandatory Qt widget dependency for migrated shell surfaces
- startup and open-document flows complete in the TS shell
- no regression in primary workflow completion for Part, PartDesign, and Sketcher pilot users
- all bundled primary workflows pass parity review before Qt runtime removal

## 13. Final Recommendation

Do not try to "remove Qt from FreeCAD" as a direct refactor inside the existing UI layer.

The viable plan is:

1. preserve the native modeling core
2. move UI semantics behind explicit backend contracts
3. build a TypeScript shell with screenshot-verified visual parity
4. migrate workbench surfaces incrementally
5. cut over only after the TypeScript shell is genuinely usable
6. remove Qt last, not first

That sequence gives the best chance of keeping FreeCAD recognizable while replacing its frontend stack without destabilizing the product.