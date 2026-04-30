# FreeCAD GUI Ownership Table

Status: first-pass ownership map for Qt-to-TypeScript migration

## 1. Purpose

This document assigns migration-oriented ownership buckets across the current GUI codebase.

It is intended to answer two questions:

1. which parts of `src/Gui` and `src/Mod/*/Gui` belong to which migration stream
2. which files should move together when replacing Qt surfaces with TypeScript equivalents

## 2. `src/Gui` Ownership Buckets

### Bucket 1. Shell Startup and Main Window

Representative files:

- `src/Gui/Application.cpp`
- `src/Gui/Application.h`
- `src/Gui/GuiApplication.cpp`
- `src/Gui/GuiApplication.h`
- `src/Gui/MainWindow.cpp`
- `src/Gui/MainWindow.h`
- `src/Gui/StartupProcess.cpp`
- `src/Gui/StartupProcess.h`

Owns:

- GUI startup lifecycle
- main window shell
- startup handoff from process boot into the GUI layer

Target migration stream:

- shell and startup decoupling

### Bucket 2. Command and Action Infrastructure

Representative files:

- `src/Gui/Action.cpp`
- `src/Gui/Action.h`
- `src/Gui/Command.cpp`
- `src/Gui/Command.h`
- `src/Gui/CommandDispatcher.cpp`
- `src/Gui/CommandDispatcher.h`
- `src/Gui/MenuManager.cpp`
- `src/Gui/MenuManager.h`
- `src/Gui/ToolBarManager.cpp`
- `src/Gui/ToolBarManager.h`
- `src/Gui/ShortcutManager.cpp`
- `src/Gui/ShortcutManager.h`

Owns:

- command state, dispatch, menu composition, toolbar composition, shortcut behavior

Target migration stream:

- backend command and workbench semantics extraction

### Bucket 3. Workbench System

Representative files:

- `src/Gui/Workbench.cpp`
- `src/Gui/Workbench.h`
- `src/Gui/WorkbenchFactory.cpp`
- `src/Gui/WorkbenchFactory.h`
- `src/Gui/WorkbenchManager.cpp`
- `src/Gui/WorkbenchManager.h`
- `src/Gui/WorkbenchSelector.cpp`
- `src/Gui/WorkbenchSelector.h`
- `src/Gui/WorkbenchManipulator.cpp`

Owns:

- workbench registration, activation, selector UI, and workbench-driven shell state

Target migration stream:

- workbench protocol and shell composition

### Bucket 4. Docking, Layout, and Multi-View Shell

Representative files:

- `src/Gui/DockWindow.cpp`
- `src/Gui/DockWindow.h`
- `src/Gui/DockWindowManager.cpp`
- `src/Gui/DockWindowManager.h`
- `src/Gui/ComboView.cpp`
- `src/Gui/ComboView.h`
- `src/Gui/SplitView3DInventor.cpp`
- `src/Gui/SplitView3DInventor.h`
- `src/Gui/ToolBox.cpp`
- `src/Gui/ToolBoxManager.cpp`
- `src/Gui/RollbackBar.cpp`

Owns:

- dock regions, layout persistence assumptions, view composition, combo view shell

Target migration stream:

- TypeScript shell layout and docking

### Bucket 5. Tree, Document Browser, and Selection Shell

Representative files:

- `src/Gui/Tree.cpp`
- `src/Gui/Tree.h`
- `src/Gui/TreeView.cpp`
- `src/Gui/TreeView.h`
- `src/Gui/Document.cpp`
- `src/Gui/Document.h`
- `src/Gui/DocumentModel.cpp`
- `src/Gui/DocumentModel.h`
- `src/Gui/Selection/**`

Owns:

- object tree rendering, document browser behavior, selection-linked tree interactions

Target migration stream:

- editing surfaces and selection sync

### Bucket 6. Property and Inspector Surfaces

Representative files:

- `src/Gui/PropertyView.cpp`
- `src/Gui/PropertyView.h`
- `src/Gui/propertyeditor/**`
- `src/Gui/PropertyPage.cpp`
- `src/Gui/PropertyPage.h`

Owns:

- property grid rendering and editing controls

Target migration stream:

- schema-driven TS property editor

### Bucket 7. Task Panels and Dialog Runtime

Representative files:

- `src/Gui/TaskView/**`
- `src/Gui/TaskCommandLink.cpp`
- `src/Gui/TaskElementColors.cpp`
- `src/Gui/TaskTransform.cpp`
- `src/Gui/Dialogs/**`

Owns:

- shell-level task runtime patterns and reusable Qt dialog flows

Target migration stream:

- task panel runtime and general dialog replacement

### Bucket 8. Viewport Host and Scene Runtime

Representative files:

- `src/Gui/View3DInventor.cpp`
- `src/Gui/View3DInventor.h`
- `src/Gui/View3DInventorViewer.cpp`
- `src/Gui/View3DInventorViewer.h`
- `src/Gui/ViewProviderDocumentObject.cpp`
- `src/Gui/ViewProviderDocumentObject.h`
- `src/Gui/ViewProviderLink.cpp`
- `src/Gui/ViewProviderPart.cpp`
- `src/Gui/Quarter/**`
- `src/Gui/Inventor/**`

Owns:

- 3D view hosting, scene presentation, and Qt-linked viewer lifecycle

Target migration stream:

- viewport and scene presentation replacement

### Bucket 9. Navigation, Overlays, and Visualization Helpers

Representative files:

- `src/Gui/NaviCube.cpp`
- `src/Gui/NaviCube.h`
- `src/Gui/OverlayManager.cpp`
- `src/Gui/OverlayManager.h`
- `src/Gui/OverlayWidgets.cpp`
- `src/Gui/MouseSelection.cpp`
- `src/Gui/ViewParams.cpp`
- `src/Gui/TreeParams.cpp`

Owns:

- overlays, navigation affordances, viewport helper visuals, and selection interaction modes

Target migration stream:

- viewport parity and interaction parity

### Bucket 10. Preferences, Themes, Notifications, and Utility Shell Widgets

Representative files:

- `src/Gui/PreferencePages/**`
- `src/Gui/ThemeTokens.cpp`
- `src/Gui/ThemeTokens.h`
- `src/Gui/NotificationArea.cpp`
- `src/Gui/NotificationArea.h`
- `src/Gui/ProgressDialog.cpp`
- `src/Gui/InputField.cpp`
- `src/Gui/Placement.cpp`

Owns:

- shell utility widgets, settings pages, notifications, theme tokens, and reusable input widgets

Target migration stream:

- preferences and design token extraction

### Bucket 11. Python Console and Editor Tooling

Representative files:

- `src/Gui/PythonConsole.cpp`
- `src/Gui/PythonEditor.cpp`
- `src/Gui/PythonDebugger.cpp`
- `src/Gui/RemoteDebugger.py`
- `src/Gui/CallTips.cpp`

Owns:

- Python REPL, editor, call tips, debugger surfaces

Target migration stream:

- specialized tooling migration or explicit compatibility lane

## 3. `src/Mod/*/Gui` Ownership Table

| Module | Gui Surface Size | Representative Areas | Migration Priority |
|---|---|---|---|
| `Fem` | Very large | constraints, meshing, solver setup, post-processing | P1 after core shell |
| `CAM` | Very large | tool editors, operation panels, simulator, setup | P1 after core shell |
| `TechDraw` | Large | drawing tasks, annotations, dimensions, views | P1 for engineering workflows |
| `Part` | Large | geometry and operation dialogs | P0 primary workflow |
| `PartDesign` | Large | feature editing dialogs and tasks | P0 primary workflow |
| `Sketcher` | Medium | constraints, validation, arrays, settings | P0 primary workflow |
| `BIM` | Large UI but partly outside `Gui` | IFC, project dialogs, architecture workflows | compatibility-heavy P1 |
| `Draft` | Medium | arrays, layers, preferences | P1 |
| `Material` | Medium | material editor and properties | P1 |
| `AddonManager` | Medium, mostly Python UI | installer, repository, package details | compatibility-heavy P1 |
| `Assembly` | Medium | joint/task panels, BOM, view creation | P0 or P1 depending on product priority |
| `Spreadsheet` | Small to medium | sheet dialogs and settings | P1 or P2 |
| `Import` | Small | import preferences and helpers | P0 support workflow |
| `Start` | Small | startup preferences | P0 shell onboarding |
| `Surface` | Small | filling and section tasks | P2 |
| `Robot` | Small | trajectory and control tasks | P2 |
| `ReverseEngineering` | Small | segmentation dialogs | P2 |
| `Mesh` | Small to medium | mesh tools and segmentation | P2 |
| `MeshPart` | Small | conversion helpers | P2 |
| `Measure` | Small | measurement dialogs | P1 support workflow |
| `Inspection` | Small | visual inspection | P2 |
| `Cloud` | C++ GUI but no `.ui` weight | cloud integration shell | P2 |

## 4. Primary Daily-Use Migration Set

The first ownership set that should be staffed as a coherent product slice is:

- `src/Gui` buckets 1 through 8
- `src/Mod/Start`
- `src/Mod/Part`
- `src/Mod/PartDesign`
- `src/Mod/Sketcher`
- `src/Mod/Import`

## 5. Secondary Ownership Set

The second ownership set should cover:

- `src/Mod/Assembly`
- `src/Mod/Spreadsheet`
- `src/Mod/TechDraw`
- `src/Mod/Material`
- `src/Mod/Measure`

## 6. Compatibility-Lane Ownership Set

These areas should likely run with a temporary compatibility plan during early migration:

- `src/Mod/AddonManager`
- `src/Mod/BIM`
- Python-heavy dialogs and task flows outside C++ `Gui` directories

## 7. Recommendation

Use this ownership table to assign engineering leads by bucket, not by individual file. The Qt retirement program will move faster if ownership follows product surfaces and protocol boundaries instead of mirroring the current widget-level fragmentation.