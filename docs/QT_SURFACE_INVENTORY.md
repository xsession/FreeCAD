# FreeCAD Qt Surface Inventory

Status: frozen planning baseline for migration inventory

## Related Documents

- `docs/QT_UI_FORM_INVENTORY.md`
- `docs/PYSIDE_USAGE_TABLE.md`
- `docs/GUI_OWNERSHIP_TABLE.md`
- `docs/SRC_GUI_FILE_LEVEL_OWNERSHIP_INVENTORY.md`
- `docs/FRONTEND_PARITY_BASELINE_SPEC.md`
- `docs/QT_TO_TYPESCRIPT_FRONTEND_MIGRATION_PLAN.md`
- `docs/QT_TO_TYPESCRIPT_REPO_EXECUTION_PLAN.md`
- `docs/architecture/ADR-0010-typescript-shell-and-qt-retirement.md`
- `docs/architecture/qt-to-typescript-migration-checklist.md`
- `docs/architecture/qt-to-typescript-milestone-issues.md`

## 1. Purpose

This document is a first-pass inventory of where Qt and PySide currently participate in the FreeCAD product. It is intended to support the Qt removal and TypeScript shell migration effort.

It is not a complete grep dump. It is a migration-oriented map of the highest-value ownership boundaries.

## 2. Inventory Summary

Qt currently appears in five major layers:

1. process startup and application bootstrap
2. core GUI shell and shell services
3. viewport hosting and view providers
4. C++ workbench GUI modules
5. Python and PySide workbench UI code

Qt also leaks into:

- app-layer filesystem and config handling
- tools and resource pipelines
- tests and packaging

## 3. Highest-Priority Migration Buckets

### Bucket A. Startup-Critical Qt

These files are product boot blockers because they shape GUI runtime initialization.

- `src/Main/MainGui.cpp`
- `src/Main/FreeCADGuiPy.cpp`
- `src/Gui/GuiApplication.cpp`
- `src/Gui/Application.cpp`
- `src/Gui/MainWindow.cpp`

Observed Qt usage includes:

- `QApplication`
- `QMessageBox`
- `QLocale`
- window boot and GUI-mode control flow

Migration consequence:

- a replacement shell cannot launch cleanly until startup is split into shell-neutral and shell-specific layers

### Bucket B. Core Shell Framework in `src/Gui`

This is the largest concentration of Qt UI ownership.

Representative files:

- `src/Gui/Action.cpp`
- `src/Gui/Action.h`
- `src/Gui/MenuManager.cpp`
- `src/Gui/ToolBarManager.cpp`
- `src/Gui/DockWindow.cpp`
- `src/Gui/DockWindowManager.cpp`
- `src/Gui/ComboView.cpp`
- `src/Gui/TreeView.cpp`
- `src/Gui/PropertyView.cpp`
- `src/Gui/ReportView.cpp`
- `src/Gui/Workbench.cpp`
- `src/Gui/WorkbenchSelector.cpp`
- `src/Gui/NotificationArea.cpp`
- `src/Gui/PythonConsole.cpp`

Observed Qt primitives include:

- `QAction`
- `QActionGroup`
- `QMenu`
- `QToolBar`
- `QToolButton`
- `QWidget`
- `QDockWidget`
- `QMainWindow`
- `QTimer`
- `QToolTip`

Migration consequence:

- command semantics, menu composition, workbench switching, docking, and shell persistence are all currently coupled to Qt widgets

### Bucket C. Viewport Host and Scene Presentation

Representative files:

- `src/Gui/View3DInventor.cpp`
- `src/Gui/View3DInventorViewer.cpp`
- `src/Gui/ViewProviderDocumentObject.cpp`
- `src/Gui/ViewProviderLink.cpp`
- `src/Gui/ViewProviderPart.cpp`
- `src/Gui/NaviCube.cpp`
- `src/Gui/OverlayManager.cpp`
- `src/Gui/Quarter/**`
- `src/Gui/Inventor/**`

Observed coupling:

- Qt window hosting plus Coin3D viewer ownership
- view lifecycle and MDI interactions
- overlays and navigation aids bound to GUI widget behavior

Migration consequence:

- Qt removal requires a full replacement for viewport hosting, not just panel migration

### Bucket D. App-Layer Qt Usage

Representative files:

- `src/App/Application.cpp`
- `src/App/Application.h`
- `src/App/ApplicationDirectories.cpp`
- `src/App/ApplicationDirectories.h`

Observed Qt usage includes:

- `QCoreApplication`
- `QDir`
- `QFileInfo`
- `QSettings`
- `QStandardPaths`
- `QProcessEnvironment`

Migration consequence:

- even after UI replacement, some app services still depend on Qt utility types and must be decoupled before a true Qt-free product is possible

### Bucket E. Workbench GUI Modules in C++

The repository currently contains at least 22 GUI module roots under `src/Mod/*/Gui`.

Primary bundled GUI module roots:

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

Observed patterns in these modules include:

- `.ui` forms
- `QDialog`-based workflows
- task widgets
- Qt-owned workbench-specific settings pages

Migration consequence:

- each of these folders needs a de-Qt plan or an explicit compatibility strategy

### Bucket F. PySide-Heavy Python UI Workbenches

Highest-risk Python UI areas identified from first-pass search:

- `src/Mod/AddonManager/**`
- `src/Mod/BIM/**`
- `src/Mod/CAM/PathCommands.py`
- `src/Mod/Import/stepZ.py`
- `src/Mod/Spreadsheet/TestSpreadsheetGui.py`
- `src/Ext/freecad/UiTools.py`

Representative usage patterns include:

- `from PySide import QtCore, QtGui`
- `from PySideWrapper import QtCore, QtGui, QtWidgets`
- `FreeCADGui.PySideUic.loadUi(...)`
- `QMessageBox`, `QDialog`, `QWidget`, `QTreeWidgetItem`, `QDialogButtonBox`

Migration consequence:

- Python UI compatibility will be one of the largest non-C++ blockers to full Qt retirement

## 4. Structural Hotspots

### Hotspot 1. `src/Gui/CMakeLists.txt`

This file currently wires `FreeCADGui` to Qt modules directly:

- `QtCore`
- `QtWidgets`
- `QtOpenGL`
- `QtOpenGLWidgets`
- `QtPrintSupport`
- `QtSvg`
- `QtSvgWidgets`
- `QtNetwork`
- `QtUiTools`
- `QtXml`

Migration meaning:

- the GUI library cannot remain the production shell root if the goal is a Qt-free product

### Hotspot 2. `src/Main/MainGui.cpp`

This file proves that GUI process startup is Qt-owned today.

Migration meaning:

- startup must be split before the TypeScript shell can be first-class

### Hotspot 3. `src/Gui/Action.*`

`Action` and `ActionGroup` bridge FreeCAD command semantics to Qt `QAction` objects.

Migration meaning:

- command state extraction is a prerequisite for menu and toolbar migration

### Hotspot 4. `src/Gui/MainWindow.*`

The shell hierarchy, docks, menus, toolbars, and overall layout are rooted here.

Migration meaning:

- no meaningful Qt retirement can happen until the shell is re-owned elsewhere

### Hotspot 5. `src/Gui/View3DInventor*` and `src/Gui/ViewProvider*`

The current 3D user experience is deeply integrated into Qt-hosted viewer objects.

Migration meaning:

- viewport replacement is one of the critical path items

## 5. Migration Difficulty Tiers

### Tier 1. Straightforward to Replatform

- shell chrome rendering
- menu and toolbar presentation after protocol extraction
- status bar rendering
- notification rendering
- preferences UI rendering once schema-backed

### Tier 2. Medium Difficulty

- tree view
- property editor
- task panels
- docking behavior
- shortcut customization

### Tier 3. High Difficulty

- command system extraction from `QAction`
- workbench switching semantics
- Python UI compatibility
- viewport hosting and scene interaction
- startup and lifecycle decoupling

### Tier 4. Hard Blockers for Full Qt Removal

- `MainGui.cpp` startup path
- `FreeCADGui` library root depending on Qt modules
- Coin3D and Qt viewer hosting in `src/Gui`
- PySide-bound bundled workflows
- app-layer Qt utilities in `src/App`

## 6. Recommended Inventory Follow-Ups

The next inventory passes should add:

1. file-level ownership for `src/Gui`
2. per-workbench Qt and PySide usage tables
3. `.ui` form inventory
4. Qt resource inventory including icons and translations
5. startup dependency graph
6. viewport dependency graph

## 7. Recommended Immediate Actions

1. treat `src/Main/MainGui.cpp`, `src/Gui/CMakeLists.txt`, and `src/Gui/Action.*` as P0 migration anchors
2. create a protocol model for commands, workbench state, layout, tree, properties, and tasks
3. begin static shell reproduction in `variants/asterforge/frontend/app`
4. create a dedicated PySide compatibility workstream for `AddonManager` and `BIM`
5. separate viewport migration into its own program, not a late incidental task