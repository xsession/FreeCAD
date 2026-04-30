# FreeCAD Qt-to-TypeScript Repo Execution Plan

Status: repo-specific execution plan

## Related Documents

- `docs/QT_TO_TYPESCRIPT_FRONTEND_MIGRATION_PLAN.md`
- `docs/QT_SURFACE_INVENTORY.md`
- `docs/QT_UI_FORM_INVENTORY.md`
- `docs/PYSIDE_USAGE_TABLE.md`
- `docs/GUI_OWNERSHIP_TABLE.md`
- `docs/SRC_GUI_FILE_LEVEL_OWNERSHIP_INVENTORY.md`
- `docs/FRONTEND_PARITY_BASELINE_SPEC.md`
- `docs/architecture/ADR-0010-typescript-shell-and-qt-retirement.md`
- `docs/architecture/qt-to-typescript-migration-checklist.md`
- `docs/architecture/qt-to-typescript-milestone-issues.md`

## 1. Purpose

This document converts the generic Qt removal strategy into a repo-specific execution plan for the current FreeCAD tree.

It assumes the migration target is:

- TypeScript frontend shell
- Rust application layer
- native FreeCAD and OCCT retained as backend and bridge code during the transition
- convergence toward the existing `variants/asterforge` architecture instead of inventing a second migration target

## 2. Current Repo Anchors

The migration has to account for these concrete ownership points in the repository.

### 2.1 Startup and Runtime Shell

- `src/Main/MainGui.cpp` creates the Qt application and handles GUI-mode startup.
- `src/Main/FreeCADGuiPy.cpp` exposes GUI startup assumptions into Python-facing flows.
- `src/Gui/MainWindow.cpp` and `src/Gui/MainWindow.h` anchor the current Qt main window shell.

### 2.2 Core GUI Library

- `src/Gui/CMakeLists.txt` links the entire `FreeCADGui` shared library against Qt modules including `QtCore`, `QtWidgets`, `QtOpenGL`, `QtOpenGLWidgets`, `QtPrintSupport`, `QtSvg`, `QtNetwork`, `QtUiTools`, and `QtXml`.
- `src/Gui` contains the current shell primitives: actions, menus, toolbars, docks, tree, property editor, task panels, workbench switching, notifications, Python console, and 3D viewer hosting.

### 2.3 App-Layer Qt Usage Outside `src/Gui`

- `src/App/Application.cpp`
- `src/App/ApplicationDirectories.cpp`
- `src/App/Application.h`

These files show that even application bootstrap and environment handling currently depend on Qt types such as `QCoreApplication`, `QDir`, `QSettings`, and `QStandardPaths`.

### 2.4 Module GUI Entry Points

The tree currently contains at least these GUI module roots:

- `src/Mod/Assembly/Gui`
- `src/Mod/CAM/Gui`
- `src/Mod/Cloud/Gui`
- `src/Mod/Fem/Gui`
- `src/Mod/Import/Gui`
- `src/Mod/Inspection/Gui`
- `src/Mod/Material/Gui`
- `src/Mod/Measure/Gui`
- `src/Mod/Mesh/Gui`
- `src/Mod/MeshPart/Gui`
- `src/Mod/Part/Gui`
- `src/Mod/PartDesign/Gui`
- `src/Mod/Points/Gui`
- `src/Mod/ReverseEngineering/Gui`
- `src/Mod/Robot/Gui`
- `src/Mod/SheetMetal/Gui`
- `src/Mod/Sketcher/Gui`
- `src/Mod/Spreadsheet/Gui`
- `src/Mod/Start/Gui`
- `src/Mod/Surface/Gui`
- `src/Mod/TechDraw/Gui`
- `src/Mod/Test/Gui`

There are also PySide-heavy Python workbench surfaces outside those C++ GUI folders, especially under:

- `src/Mod/AddonManager`
- `src/Mod/BIM`
- `src/Mod/CAM`
- `src/Mod/Import`
- `src/Mod/Spreadsheet`

### 2.5 Existing Migration Target Scaffold

The repository already contains a future-facing architecture under:

- `variants/asterforge/frontend/app`
- `variants/asterforge/backend/crates`
- `variants/asterforge/native/freecad-bridge`
- `variants/asterforge/protocol`

This should become the canonical shell direction.

## 3. Workstreams

The migration should be executed through eight parallel workstreams.

### Workstream A. Shell and Startup Decoupling

Scope:

- `src/Main/MainGui.cpp`
- `src/Main/FreeCADGuiPy.cpp`
- `src/Gui/Application*`
- `src/Gui/MainWindow*`

Objective:

- separate GUI-independent startup from Qt shell startup
- allow a second desktop shell to boot against the same backend services

Key outputs:

- shell-neutral startup contract
- backend boot service
- TypeScript shell launch path

### Workstream B. Command and Workbench Semantics Extraction

Scope:

- `src/Gui/Action*`
- `src/Gui/Command*`
- `src/Gui/MenuManager*`
- `src/Gui/ToolBarManager*`
- `src/Gui/Workbench*`
- `src/Gui/WorkbenchSelector*`

Objective:

- move command metadata and workbench state behind protocol services
- stop using Qt action objects as the canonical command state container

Key outputs:

- command schema
- workbench schema
- backend command service

### Workstream C. Layout, Docking, and Panel Persistence

Scope:

- `src/Gui/DockWindow*`
- `src/Gui/DockWindowManager*`
- `src/Gui/ComboView*`
- `src/Gui/ToolBox*`
- `src/Gui/ToolBoxManager*`
- `src/Gui/StatusBarLabel*`

Objective:

- replace Qt docking and window-state persistence with backend-described layout state and TS shell persistence

Key outputs:

- shell layout schema
- saved layout format
- TS docking framework

### Workstream D. Editing Surfaces

Scope:

- `src/Gui/Tree*`
- `src/Gui/TreeView*`
- `src/Gui/PropertyView*`
- `src/Gui/propertyeditor/**`
- `src/Gui/TaskView/**`
- `src/Gui/ReportView*`

Objective:

- replace the tree, property panel, task panel, and report view with protocol-driven TS components

Key outputs:

- document tree API
- property schema renderer
- task schema renderer
- diagnostics stream

### Workstream E. Viewport and Scene Presentation

Scope:

- `src/Gui/View3DInventor*`
- `src/Gui/ViewProvider*`
- `src/Gui/Inventor/**`
- `src/Gui/Quarter/**`
- `src/Gui/NaviCube*`
- `src/Gui/Overlay*`

Objective:

- replace Qt-hosted Coin3D widget ownership with backend scene extraction and TS rendering

Key outputs:

- scene payload protocol
- TypeScript viewport renderer
- camera and selection compatibility rules

### Workstream F. Preferences, Themes, and Assets

Scope:

- `src/Gui/PreferencePages/**`
- `src/Gui/Stylesheets/**`
- `src/Gui/ThemeTokens*`
- `src/Gui/Icons/**`
- `src/Gui/resource.cpp`

Objective:

- define explicit design tokens and replace Qt resource and preference-page assumptions with shell-neutral services and TS UIs

Key outputs:

- design token package
- frontend asset pipeline
- backend preference schema

### Workstream G. PySide and Python UI Compatibility

Scope:

- `src/Mod/AddonManager/**`
- `src/Mod/BIM/**`
- Python workbench UI scripts under `src/Mod/**`
- `src/Ext/freecad/UiTools.py`

Objective:

- define how Python-facing UI contributions survive the transition without keeping Qt as a permanent runtime requirement

Key outputs:

- compatibility adapter policy
- deprecation tiers
- plugin and macro migration guidance

### Workstream H. Build and Packaging Cutover

Scope:

- CMake entry points
- packaging scripts
- pixi environment definitions
- runtime launchers

Objective:

- support a dual-shell transition and later produce a shipping package without Qt runtime UI dependencies

Key outputs:

- dual-shell packaging
- TS shell default launch option
- Qt-free production packaging criteria

## 4. Recommended Sequence

### Phase 1. Discovery and Stabilization

Deliver first:

- Qt surface inventory
- visual parity baseline
- shell-neutral protocol skeleton
- repo decision ADR

### Phase 2. Shell Extraction

Deliver next:

- TypeScript shell in `variants/asterforge/frontend/app`
- Rust shell services in `variants/asterforge/backend/crates`
- shell-neutral startup path that can coexist with `MainGui.cpp`

### Phase 3. Static Parity

Deliver next:

- menu bar parity
- toolbar parity
- docking shell parity
- status bar parity
- theme token parity

### Phase 4. Behavioral Parity

Deliver next:

- command execution
- workbench switching
- tree and property surfaces
- task panel runtime

### Phase 5. Viewport Parity

Deliver next:

- scene extraction bridge
- TS viewport integration
- selection and navigation parity

### Phase 6. Workbench Migration

Suggested order for bundled primary workflows:

1. `src/Mod/Start`
2. `src/Mod/Part`
3. `src/Mod/PartDesign`
4. `src/Mod/Sketcher`
5. `src/Mod/Import`
6. `src/Mod/Spreadsheet`
7. `src/Mod/TechDraw`
8. `src/Mod/Fem`
9. specialist workbenches

### Phase 7. Dual-Shell Operation

Run both:

- current Qt shell
- new TypeScript shell

against the same backend semantics until the TypeScript shell is proven for daily use.

### Phase 8. Qt Retirement

Only after the above phases succeed:

- stop defaulting to Qt shell launch
- remove Qt-only runtime UI code paths
- remove PySide from bundled production UI flows
- retire Qt from shipping UI dependencies

## 5. First Implementation Backlog

The first concrete coding backlog should be:

1. create a shell-neutral command and workbench protocol under `variants/asterforge/protocol`
2. expose command and workbench state from current FreeCAD into that protocol
3. build a static shell parity prototype in `variants/asterforge/frontend/app`
4. create screenshot parity fixtures for current FreeCAD shell
5. replace tree and property panel rendering through protocol payloads
6. prototype viewport scene extraction from native code into frontend payloads

## 6. Definition of Done for Repo Cutover

The repository is ready for Qt runtime removal only when all of the following are true:

- startup no longer requires `MainGui.cpp` to create the shipping shell
- `src/Gui` is no longer the source of truth for commands, layout, and workbench state
- primary workflows run from the TypeScript shell
- bundled PySide UI dependencies are either removed or isolated in non-shipping compatibility lanes
- the packaged product can run without Qt UI libraries

## 7. Recommendation

Treat `variants/asterforge` as the future shell root.

Do not attempt to transplant TypeScript directly into `src/Gui`. Instead:

- extract semantics from `src/Gui`
- render those semantics in the TypeScript shell
- migrate workbench surfaces incrementally
- delete Qt only after the new shell is feature-proven