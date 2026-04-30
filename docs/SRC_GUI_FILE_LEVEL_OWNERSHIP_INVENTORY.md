# FreeCAD src/Gui File-Level Ownership Inventory

Status: second-pass `src/Gui` ownership inventory

## 1. Purpose

This document refines the broader GUI ownership map into a `src/Gui`-specific inventory that is detailed enough for staffing and migration sequencing.

It is not intended to list every file. It groups the code by ownership-worthy technical islands and shell surfaces.

## 2. Summary

`src/Gui` is not one migration unit. It is a mix of:

- shell infrastructure and startup code
- dock, tree, property, and task surfaces
- viewport hosting and rendering bridges
- selection and navigation systems
- vendored or isolated technical islands

The highest-risk separation is between:

- shell-facing UI surfaces that can be replatformed behind protocols
- viewport and rendering islands that are tightly coupled to Qt and Coin3D ownership

## 3. Directory Weight Snapshot

Approximate high-weight subdirectories under `src/Gui` by source and UI footprint:

| Rank | Directory | Approximate Weight | Migration Meaning |
|---|---|---:|---|
| 1 | `Dialogs` | about 100 files | Largest modal dialog cluster |
| 2 | `PreferencePages` | about 45 files | Settings and preference-page system |
| 3 | `Quarter` | about 35 files | Qt and Coin3D viewport bridge |
| 4 | `TaskView` | about 23 files | Task panel runtime |
| 5 | `Inventor` | about 23 files | Custom scene and render nodes |
| 6 | `Selection` | about 20 files | Selection and filter system |
| 7 | `Navigation` | about 18 files | Camera and interaction styles |
| 8 | `3Dconnexion` | about 11 files | 3D mouse and native event handling |
| 9 | `DAGView` | about 9 files | Dependency graph UI |
| 10 | `propertyeditor` | about 8 files | Property-grid subsystem |

Important additional root-level surface:

- the `src/Gui` root itself contains the main shell, workbench, command, document, and view host files that define most of the product architecture

## 4. Ownership Buckets

### Bucket 1. Startup and Shell Root

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

- GUI process lifecycle
- shell instantiation
- startup handoff and main window ownership

Migration note:

- this bucket has to be decoupled early, otherwise the TypeScript shell remains secondary

### Bucket 2. Command, Menu, Toolbar, and Workbench Infrastructure

Representative files:

- `src/Gui/Action.cpp`
- `src/Gui/Action.h`
- `src/Gui/Command.cpp`
- `src/Gui/Command.h`
- `src/Gui/CommandDispatcher.cpp`
- `src/Gui/MenuManager.cpp`
- `src/Gui/ToolBarManager.cpp`
- `src/Gui/Workbench.cpp`
- `src/Gui/WorkbenchFactory.cpp`
- `src/Gui/WorkbenchManager.cpp`
- `src/Gui/WorkbenchSelector.cpp`

Owns:

- command semantics
- workbench switching
- toolbar and menu state
- shortcut-linked shell behavior

Migration note:

- this is the main backend protocol extraction zone for command and workbench state

### Bucket 3. Docking and Multi-Panel Shell

Representative files:

- `src/Gui/DockWindow.cpp`
- `src/Gui/DockWindowManager.cpp`
- `src/Gui/ComboView.cpp`
- `src/Gui/ToolBox.cpp`
- `src/Gui/ToolBoxManager.cpp`
- `src/Gui/RollbackBar.cpp`
- `src/Gui/SplitView3DInventor.cpp`

Owns:

- dock regions
- combo view shell composition
- panel persistence assumptions
- split and multi-view layout behavior

Migration note:

- this bucket must move with a shell-neutral layout state model, not a direct widget clone

### Bucket 4. Document, Tree, and Selection Shell

Representative files:

- `src/Gui/Document.cpp`
- `src/Gui/DocumentModel.cpp`
- `src/Gui/Tree.cpp`
- `src/Gui/TreeView.cpp`
- `src/Gui/Selection/Selection.cpp`
- `src/Gui/Selection/SelectionFilter.cpp`
- `src/Gui/Selection/SelectionView.cpp`
- `src/Gui/Selection/SoFCSelection.cpp`

Owns:

- object tree rendering
- document view binding
- selection model propagation
- selection filtering rules

Migration note:

- this bucket is one of the most important editing-surface migration streams because it touches almost every workflow

### Bucket 5. Property and Inspector Surfaces

Representative files:

- `src/Gui/PropertyView.cpp`
- `src/Gui/PropertyPage.cpp`
- `src/Gui/propertyeditor/PropertyEditor.cpp`
- `src/Gui/propertyeditor/PropertyModel.cpp`
- `src/Gui/propertyeditor/PropertyItem.cpp`
- `src/Gui/propertyeditor/PropertyItemDelegate.cpp`

Owns:

- property grid rendering
- property editing delegates
- property model-view separation

Migration note:

- this bucket is relatively self-contained and is a strong candidate for schema-first TS replacement

### Bucket 6. Task Runtime and Shell-Level Operation Panels

Representative files:

- `src/Gui/TaskView/TaskView.cpp`
- `src/Gui/TaskView/TaskDialog.cpp`
- `src/Gui/TaskView/TaskDialogPython.cpp`
- `src/Gui/TaskView/TaskAppearance.cpp`
- `src/Gui/TaskView/TaskEditControl.cpp`
- `src/Gui/TaskTransform.cpp`
- `src/Gui/TaskElementColors.cpp`
- `src/Gui/TaskCommandLink.cpp`

Owns:

- task panel lifecycle
- shell-level operation panels
- some Python-linked task behaviors

Migration note:

- this bucket defines a core UX contract and should migrate as a platform service, not as isolated dialogs

### Bucket 7. Dialogs and Preferences

Representative files:

- `src/Gui/Dialogs/DlgPreferencesImp.cpp`
- `src/Gui/Dialogs/DlgCustomizeImp.cpp`
- `src/Gui/Dialogs/DlgMaterialPropertiesImp.cpp`
- `src/Gui/Dialogs/DlgKeyboardImp.cpp`
- `src/Gui/PreferencePages/DlgSettingsGeneral.cpp`
- `src/Gui/PreferencePages/DlgSettings3DViewImp.cpp`
- `src/Gui/PreferencePages/DlgSettingsNavigation.cpp`
- `src/Gui/PreferencePages/DlgSettingsPythonConsole.cpp`

Owns:

- general-purpose shell dialogs
- settings page hierarchy
- customization and preference UI

Migration note:

- this is large but structurally straightforward if preferences become schema-backed

### Bucket 8. Viewport Host and 3D Scene Runtime

Representative files:

- `src/Gui/View3DInventor.cpp`
- `src/Gui/View3DInventorViewer.cpp`
- `src/Gui/View3DInventorSelection.cpp`
- `src/Gui/View3DSettings.cpp`
- `src/Gui/ViewProviderDocumentObject.cpp`
- `src/Gui/ViewProviderLink.cpp`
- `src/Gui/ViewProviderPart.cpp`
- `src/Gui/Quarter/QuarterWidget.cpp`
- `src/Gui/Quarter/SoQTQuarterAdaptor.cpp`
- `src/Gui/Inventor/SoFCDB.cpp`

Owns:

- Qt-owned viewport lifecycle
- viewer event bridging
- scene presentation
- view-provider side of presentation and interaction

Migration note:

- this is one of the main hard blockers for Qt retirement

### Bucket 9. Navigation and Overlay Systems

Representative files:

- `src/Gui/Navigation/NavigationStyle.cpp`
- `src/Gui/Navigation/InventorNavigationStyle.cpp`
- `src/Gui/Navigation/CADNavigationStyle.cpp`
- `src/Gui/NaviCube.cpp`
- `src/Gui/OverlayManager.cpp`
- `src/Gui/OverlayWidgets.cpp`
- `src/Gui/MouseSelection.cpp`

Owns:

- camera interaction styles
- overlays and helpers
- viewport interaction affordances

Migration note:

- much of this can migrate after the scene protocol exists, but it should remain a dedicated ownership stream

### Bucket 10. Python Console and Developer Tooling

Representative files:

- `src/Gui/PythonConsole.cpp`
- `src/Gui/PythonEditor.cpp`
- `src/Gui/PythonDebugger.cpp`
- `src/Gui/RemoteDebugger.py`
- `src/Gui/CallTips.cpp`

Owns:

- Python REPL and editor tooling
- developer-oriented debugging surfaces

Migration note:

- this bucket can move later or run through an explicit compatibility lane

## 5. Special Technical Islands

### `Quarter`

Representative files:

- `src/Gui/Quarter/QuarterWidget.cpp`
- `src/Gui/Quarter/Quarter.cpp`
- `src/Gui/Quarter/InteractionMode.cpp`
- `src/Gui/Quarter/ContextMenu.cpp`

Why separate:

- it is the critical bridge between Qt event handling and Coin3D viewer ownership

### `Inventor`

Representative files:

- `src/Gui/Inventor/SoFCDB.cpp`
- `src/Gui/Inventor/SoFCBackgroundGradient.cpp`
- `src/Gui/Inventor/SoAxisCrossKit.cpp`
- `src/Gui/Inventor/Draggers/Gizmo.cpp`

Why separate:

- it represents engine-bound scene node and interaction logic rather than ordinary shell UI

### `Selection`

Representative files:

- `src/Gui/Selection/Selection.cpp`
- `src/Gui/Selection/SelectionFilter.cpp`
- `src/Gui/Selection/SoFCUnifiedSelection.cpp`

Why separate:

- selection is cross-cutting enough to deserve its own API and migration contract

### `Dialogs`

Representative files:

- `src/Gui/Dialogs/DlgPreferencesImp.cpp`
- `src/Gui/Dialogs/DlgCustomizeImp.cpp`
- `src/Gui/Dialogs/DlgActionsImp.cpp`

Why separate:

- it is the largest UI form island and should likely be migrated via consolidation patterns instead of individual one-off rewrites

## 6. Recommended Staffing Model

Use ownership leads for:

1. shell and startup
2. commands and workbenches
3. layout and docks
4. tree and selection
5. properties and tasks
6. viewport and scene runtime
7. preferences and dialogs
8. Python tooling and compatibility

## 7. Recommendation

Do not assign `src/Gui` to a single migration owner. The directory already contains multiple architectural seams, and the migration will move faster if these seams become explicit workstreams.