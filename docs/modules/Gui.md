# Gui Module (FreeCADGui)

> **Library**: `FreeCADGui.dll` / `libFreeCADGui.so`  
> **Source**: `src/Gui/`  
> **Files**: ~365 .cpp · ~347 .h  
> **Dependencies**: FreeCADApp, FreeCADBase, Qt6, Coin3D/Quarter, OpenGL  
> **Architecture SVG**: [gui_architecture.svg](../svg/gui_architecture.svg)

---

## 📋 Overview

The **Gui** module is FreeCAD's largest single library (~712 source files). It provides the complete graphical user interface:

- **3D viewer** — Coin3D/OpenInventor-based scene graph renderer
- **Navigation** — multiple mouse/keyboard styles (CAD, Blender, Gesture, etc.)
- **Command system** — action framework for menus, toolbars, keyboard shortcuts
- **Selection framework** — pre-selection (hover) + selection (click) + sub-elements
- **ViewProviders** — visual representation of DocumentObjects
- **Workbench system** — switchable tool/menu configurations per module
- **UI components** — tree view, task panels, property editor, python console
- **Coin3D layer** — custom scene graph nodes (SoFC* classes)

---

## 🏗️ Architecture

### 3D Viewer Stack

```
Qt Widget Layer
  └── View3DInventor (MDI window)
       └── View3DInventorViewer (Coin3D context)
            ├── SoFCDB (scene graph database)
            ├── SoFCUnifiedSelection (selection highlighting)
            ├── NaviCube (corner navigation widget)
            └── Clipping planes
```

The viewer uses **Coin3D** (Open Inventor implementation) for scene graph management:
- Scene graph nodes define 3D geometry, materials, transformations
- Coin3D handles rendering, picking, event dispatch
- **Quarter** bridges Qt and Coin3D event loops

### Navigation Styles

| Style | Origin |
|---|---|
| `CADNavigationStyle` | Default — middle-button orbit |
| `BlenderNavigationStyle` | Matches Blender controls |
| `GestureNavigationStyle` | Touchpad-friendly |
| `OpenInventorNavigationStyle` | Classic Inventor |
| `MayaGestureNavigationStyle` | Matches Maya |
| `OpenCascadeNavigationStyle` | Matches OCCT viewer |
| `TouchpadNavigationStyle` | Pure touchpad |
| `RevitNavigationStyle` | Matches Revit |

All inherit from `NavigationStyle` base class.

### Command System

```
Command (C++ or Python)
  ├── triggered by menu/toolbar/shortcut
  ├── checks isActive() preconditions
  └── executes activated() action
       └── often creates/modifies DocumentObjects

CommandManager
  ├── registers all commands
  ├── creates QAction bindings
  └── manages shortcut conflicts
```

Types:
- **C++ Command** — compiled actions (e.g., `StdCmdNew`, `StdCmdSave`)
- **PythonCommand** — scripted actions (workbench-specific)
- **MacroCommand** — user-recorded macros

### Selection Framework

```
SelectionSingleton (global)
  ├── addSelection(doc, obj, sub, pos)     // click
  ├── setPreselection(doc, obj, sub, pos)  // hover
  ├── SelectionObserver (callback interface)
  ├── SelectionFilter (pattern matching)
  └── SelectionGate (restricts allowed selections)
```

Selection supports:
- **Pre-selection** — hover highlighting (yellow by default)
- **Selection** — click selection (green by default)
- **Sub-element** — edge, face, vertex selection (TNP-aware)
- **Box/Lasso selection** — area selection modes

### ViewProvider System

Every `DocumentObject` has a corresponding `ViewProvider` in the GUI:

```
ViewProvider (base)
  └── ViewProviderDocumentObject
       ├── ViewProviderGeometryObject (has placement display)
       │    ├── ViewProviderPart (Part shapes)
       │    ├── ViewProviderMesh (mesh display)
       │    └── ViewProviderFemMesh (FEM meshes)
       ├── ViewProviderAnnotation (dimensions, labels)
       └── ViewProviderPythonFeature (Python-defined)
```

ViewProviders manage:
- Coin3D scene graph nodes for 3D display
- Display modes (shaded, wireframe, points)
- Drag & drop behavior
- Context menus
- Task panel launching

### Workbench System

```
Workbench (base)
  ├── setupMenuBar() → menu configuration
  ├── setupToolBars() → toolbar configuration  
  └── setupContextMenu() → right-click menus

PythonWorkbench
  └── defined in module's InitGui.py

WorkbenchManager
  └── handles activation/deactivation
```

Each module defines its workbench in `InitGui.py`:
```python
class MyWorkbench(Gui.Workbench):
    MenuText = "My Module"
    ToolTip = "My module description"
    def Initialize(self):
        self.appendToolbar("Tools", ["Cmd1", "Cmd2"])
        self.appendMenu("My Menu", ["Cmd1", "Cmd2"])
```

### UI Components

| Component | Class | Purpose |
|---|---|---|
| Main Window | `MainWindow` | Top-level Qt window |
| 3D View | `View3DInventor` | Coin3D-based viewport |
| Tree View | `TreeWidget` | Object hierarchy browser |
| DAG View | `DAGView` | Dependency graph visualization |
| Property Editor | `PropertyEditor` | Object property editing |
| Task Panel | `TaskView` | Context-sensitive tool panels |
| Python Console | `PythonConsole` | Interactive Python shell |
| Report View | `ReportView` | Console log display |
| Preferences | `DlgPreferences` | Settings dialog |
| Overlay | `OverlayManager` | Transparent dock panels |

### Coin3D Custom Nodes (SoFC*)

FreeCAD extends Coin3D with custom scene graph nodes:

| Node | Purpose |
|---|---|
| `SoFCSelection` | Per-object selection highlighting |
| `SoFCUnifiedSelection` | Global selection manager |
| `SoFCBoundingBox` | Bounding box display |
| `SoFCColorBar` | Color legend bar |
| `SoFCColorGradient` | Gradient color mapping |
| `SoNavigationDragger` | Interactive manipulation |
| `SoAxisCrossKit` | Axis cross display |
| `SoAutoZoomTranslation` | Scale-independent labels |

---

## 📅 Historical Timeline

| Year | Milestone |
|---|---|
| 2002 | Initial GUI — Qt3 + Coin3D |
| 2008 | Qt4 migration |
| 2012 | NaviCube added |
| 2015 | TaskView system |
| 2018 | OverlayManager (transparent docks) |
| 2020 | DAGView, improved tree |
| 2023 | TNP-aware selection, unified highlighting |
| 2024–25 | Qt6 port, PySide6 migration |

---

## 📂 Key Files

| File | Purpose |
|---|---|
| `Application.h/cpp` | GUI application singleton |
| `MainWindow.h/cpp` | Top-level window |
| `View3DInventor.h/cpp` | 3D viewport MDI window |
| `View3DInventorViewer.h/cpp` | Coin3D viewer widget |
| `Command.h/cpp` | Command base classes |
| `CommandStd.cpp` | Standard commands (New, Open, Save) |
| `Selection.h/cpp` | Selection singleton |
| `SelectionFilter.h/cpp` | Selection pattern matching |
| `ViewProvider.h/cpp` | VP base class |
| `ViewProviderDocumentObject.h/cpp` | VP for doc objects |
| `Workbench.h/cpp` | Workbench base |
| `Tree.h/cpp` | Object tree widget |
| `TaskView/TaskView.h/cpp` | Task panel framework |
| `NavigationStyle.h/cpp` | Navigation base |
| `NaviCube.h/cpp` | Navigation cube |
| `OverlayManager.h/cpp` | Transparent overlays |
| `PropertyEditor/` | Property editing widgets |
| `Quarter/` | Qt-Coin3D bridge |
| `QSint/` | Ribbon/action panel widgets |

---

## 🔗 Dependency Graph

```
Gui depends on:
  ├── App (documents, objects, properties)
  ├── Base (everything)
  ├── Qt6 (widgets, core, OpenGL)
  ├── Coin3D (3D scene graph)
  ├── Quarter (Qt+Coin3D bridge)
  └── OpenGL (rendering)

Used by:
  └── All Mod/*/Gui/ libraries (module-specific VP and commands)
```

---

*Part of the [FreeCAD Documentation Hub](../README.md)*
