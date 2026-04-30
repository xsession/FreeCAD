# Qt-to-TypeScript Milestone Issue Pack

Status: issue-style planning pack

## 1. Purpose

This document turns the migration strategy into issue-style milestone slices grouped by subsystem.

Each issue is written as a planning unit that can later become a real tracker item.

## 2. Milestone Group A: Shell Foundation

### Issue A1. Split GUI Startup from Qt Shell Startup

Goal:

- make startup shell-neutral so the TypeScript shell can boot without `MainGui.cpp` owning the application lifecycle

Primary scope:

- `src/Main/MainGui.cpp`
- `src/Main/FreeCADGuiPy.cpp`
- `src/Gui/Application*`
- `src/Gui/MainWindow*`

Dependencies:

- ADR-0010 accepted

Done when:

- a second shell can start against backend services without inheriting the current Qt main window path

### Issue A2. Establish TypeScript Desktop Shell Skeleton

Goal:

- stand up the production shell root in `variants/asterforge/frontend/app`

Primary scope:

- `variants/asterforge/frontend/app`
- `variants/asterforge/backend/crates`

Dependencies:

- Issue A1

Done when:

- the TypeScript shell launches with shell chrome scaffolding and backend connectivity

## 3. Milestone Group B: Commands and Workbenches

### Issue B1. Extract Command Metadata from Qt Actions

Goal:

- stop using `QAction` as the source of truth for command state

Primary scope:

- `src/Gui/Action*`
- `src/Gui/Command*`
- `src/Gui/MenuManager*`
- `src/Gui/ToolBarManager*`

Dependencies:

- shell protocol design

Done when:

- menus and toolbars can be rendered from backend-owned command descriptors

### Issue B2. Extract Workbench State and Selector Semantics

Goal:

- move workbench registration and active-workbench state behind backend services

Primary scope:

- `src/Gui/Workbench*`
- `src/Gui/WorkbenchSelector*`

Dependencies:

- Issue B1

Done when:

- the TypeScript shell can switch workbenches without Qt shell mediation

## 4. Milestone Group C: Shell Layout and Parity

### Issue C1. Recreate Static Shell Chrome with Screenshot Parity

Goal:

- reproduce menu bar, toolbars, combo view shell, report view shell, and status bar visually in TypeScript

Primary scope:

- `variants/asterforge/frontend/app`
- parity baselines under `docs`

Dependencies:

- shell skeleton

Done when:

- shell parity screenshots meet the agreed tolerance

### Issue C2. Replace Docking and Layout Persistence

Goal:

- replace Qt docking and layout persistence with shell-neutral layout state

Primary scope:

- `src/Gui/DockWindow*`
- `src/Gui/DockWindowManager*`
- `src/Gui/ComboView*`
- `src/Gui/ToolBox*`

Dependencies:

- Issue C1

Done when:

- the TypeScript shell can persist and restore the major panel layout states

## 5. Milestone Group D: Editing Surfaces

### Issue D1. Replace Tree and Document Browser Surfaces

Goal:

- move tree rendering and document browsing into protocol-driven TS components

Primary scope:

- `src/Gui/Tree*`
- `src/Gui/TreeView*`
- `src/Gui/Document*`
- `src/Gui/DocumentModel*`

Dependencies:

- command and layout protocols

Done when:

- the document tree works in the TypeScript shell with correct selection and update behavior

### Issue D2. Replace Property Editor and Inspector Panels

Goal:

- render properties from backend schemas instead of Qt editor widgets

Primary scope:

- `src/Gui/PropertyView*`
- `src/Gui/propertyeditor/**`

Dependencies:

- Issue D1

Done when:

- primary property editing flows preserve undo and recompute behavior

### Issue D3. Replace Task Panel Runtime

Goal:

- replace task panels and shell-level task dialogs with TS task runtime backed by protocol schemas

Primary scope:

- `src/Gui/TaskView/**`
- shell-level task `.ui` assets

Dependencies:

- Issue D2

Done when:

- primary task workflows can run without Qt task widgets

## 6. Milestone Group E: Viewport and Interaction

### Issue E1. Define Scene Extraction and Viewport Protocol

Goal:

- establish the payload boundary between native geometry and TS viewport rendering

Primary scope:

- `variants/asterforge/protocol`
- `variants/asterforge/native/freecad-bridge`
- viewport extraction points in `src/Gui/ViewProvider*`

Dependencies:

- ADR-0010 follow-on decision for viewport transport

Done when:

- the scene protocol can carry visible geometry, transforms, visibility, and selection identifiers

### Issue E2. Build TypeScript Viewport Renderer

Goal:

- replace Qt-hosted Coin3D view ownership with a TypeScript-rendered viewport

Primary scope:

- `src/Gui/View3DInventor*`
- `src/Gui/Quarter/**`
- `variants/asterforge/frontend/app`

Dependencies:

- Issue E1

Done when:

- open, navigate, select, hide/show, and fit-all work in the TypeScript shell on real models

## 7. Milestone Group F: Primary Workflow Modules

### Issue F1. Migrate Start, Part, PartDesign, and Sketcher Workflows

Goal:

- make the core modeling workflows usable in the TypeScript shell

Primary scope:

- `src/Mod/Start`
- `src/Mod/Part`
- `src/Mod/PartDesign`
- `src/Mod/Sketcher`

Dependencies:

- command, tree, property, task, and viewport issues

Done when:

- a user can perform primary modeling workflows without using the Qt shell

### Issue F2. Migrate Support Workflows: Import, Spreadsheet, Measure, Material

Goal:

- complete support flows needed for normal document work in the new shell

Primary scope:

- `src/Mod/Import`
- `src/Mod/Spreadsheet`
- `src/Mod/Measure`
- `src/Mod/Material`

Dependencies:

- Issue F1

Done when:

- imported documents and document support surfaces behave acceptably in the TypeScript shell

## 8. Milestone Group G: Compatibility-Heavy Modules

### Issue G1. Define PySide Compatibility Lane

Goal:

- prevent PySide-heavy modules from blocking the initial shell cutover

Primary scope:

- `src/Mod/AddonManager/**`
- `src/Mod/BIM/**`
- Python UI helpers using `FreeCADGui.PySideUic`

Dependencies:

- plugin and compatibility policy definition

Done when:

- there is a written, supported transition strategy for PySide-heavy bundled modules

### Issue G2. Migrate Assembly and TechDraw to Protocol-Driven UI

Goal:

- bring two strategically important but dialog-heavy workflows into the new shell

Primary scope:

- `src/Mod/Assembly/**`
- `src/Mod/TechDraw/**`

Dependencies:

- task runtime and viewport parity

Done when:

- assembly task flows and technical drawing task flows are usable without Qt widgets

## 9. Milestone Group H: Cutover and Retirement

### Issue H1. Run Dual-Shell Validation Program

Goal:

- validate the TypeScript shell against the Qt shell in real workflows before cutover

Primary scope:

- packaging, launchers, parity dashboards, workflow validation

Dependencies:

- core workflows usable in TS shell

Done when:

- the remaining Qt-only blockers are enumerated and acceptable for cutover

### Issue H2. Remove Qt from Production Runtime Paths

Goal:

- stop shipping the product with Qt as the UI runtime dependency

Primary scope:

- startup path
- shell modules
- bundled PySide UI dependencies
- packaging requirements

Dependencies:

- Issue H1

Done when:

- the packaged product launches and operates without Qt UI runtime libraries

## 10. Recommended Execution Order

1. A1
2. A2
3. B1
4. B2
5. C1
6. C2
7. D1
8. D2
9. D3
10. E1
11. E2
12. F1
13. F2
14. G1
15. G2
16. H1
17. H2