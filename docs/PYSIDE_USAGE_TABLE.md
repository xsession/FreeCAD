# FreeCAD PySide Usage Table

Status: frozen planning baseline for PySide and PySideWrapper inventory

## 1. Purpose

This document identifies the major PySide and PySideWrapper usage hotspots under `src/Mod` to support the Qt retirement program.

It focuses on bundled modules and migration risk, not external addons.

## 2. Search Markers Used

This inventory is based on first-pass matching of files containing markers such as:

- `from PySide`
- `from PySide2`
- `from PySide6`
- `from PySideWrapper`
- `import PySide`
- `PySideUic`

## 3. Top Module Hotspots

### 1. `AddonManager`

Approximate files matched: 43

Representative files:

- `src/Mod/AddonManager/AddonManager.py`
- `src/Mod/AddonManager/AddonManagerOptions.py`
- `src/Mod/AddonManager/addonmanager_connection_checker.py`
- `src/Mod/AddonManager/Widgets/addonmanager_widget_view_selector.py`
- `src/Mod/AddonManager/Widgets/addonmanager_widget_progress_bar.py`

Usage pattern:

- extensive `PySideWrapper` abstraction
- custom widget classes
- dialogs, message boxes, repository management, installer flows, progress UI

Migration assessment:

- high UI volume but structurally more modern than older direct `PySide` code because it already uses a wrapper layer

### 2. `BIM`

Approximate files matched: 35 or more

Representative files:

- `src/Mod/BIM/ArchComponent.py`
- `src/Mod/BIM/ArchCommands.py`
- `src/Mod/BIM/ArchAxis.py`
- `src/Mod/BIM/ArchGrid.py`
- `src/Mod/BIM/ArchFloor.py`

Usage pattern:

- direct legacy `PySide` imports
- many dialog and task-panel style workflows
- `FreeCADGui.PySideUic.loadUi(...)` in multiple flows

Migration assessment:

- one of the highest-risk migration hotspots due to breadth plus legacy patterns

### 3. `Assembly`

Approximate files matched: about 12

Representative files:

- `src/Mod/Assembly/CommandCreateBom.py`
- `src/Mod/Assembly/CommandInsertLink.py`
- `src/Mod/Assembly/CommandCreateView.py`
- `src/Mod/Assembly/CommandCreateSimulation.py`
- `src/Mod/Assembly/JointObject.py`

Usage pattern:

- direct `PySide` imports with `QtCore`, `QtGui`, `QtWidgets`
- `Gui.PySideUic.loadUi(...)` task panels
- dialogs, menus, list widgets, help dialogs, interactive editors

Migration assessment:

- moderate to high risk because Assembly is a strategic workflow and still has active PySide growth

### 4. `TechDraw`

Approximate files matched: about 10

Representative files:

- task and helper tools under `src/Mod/TechDraw/Gui`

Usage pattern:

- task-oriented dialogs and helpers
- drawing interaction support

Migration assessment:

- medium to high risk because TechDraw is workflow-critical and dialog-heavy

### 5. `PartDesign`

Approximate files matched: about 5

Representative files:

- `src/Mod/PartDesign/WizardShaft/WizardShaft.py`
- `src/Mod/PartDesign/WizardShaft/ShaftDiagram.py`

Usage pattern:

- wizard dialogs and specialized editors

Migration assessment:

- narrower surface than BIM or AddonManager, but still user-visible in important flows

### 6. `Material`

Representative pattern:

- mixed `PySideWrapper` and direct imports in editor and property flows

Migration assessment:

- moderate risk; good candidate for later structured schema-driven migration

### 7. `Spreadsheet`

Representative files:

- `src/Mod/Spreadsheet/TestSpreadsheetGui.py`

Usage pattern:

- GUI testing and support utilities rather than broad production PySide ownership

Migration assessment:

- lower production risk than the modules above, but test migration will still matter

### 8. `Import`

Representative files:

- `src/Mod/Import/stepZ.py`

Usage pattern:

- import dialogs and UI helpers

Migration assessment:

- limited footprint but relevant to onboarding and file workflows

## 4. Migration Heatmap

### P0 Hotspots

- `BIM`
- `AddonManager`
- `Assembly`

Reason:

- broad PySide ownership in bundled workflows, many interactive dialogs, and visible user-facing flows

### P1 Hotspots

- `TechDraw`
- `PartDesign`
- `Material`

Reason:

- meaningful user-facing PySide usage but less breadth than the P0 group

### P2 Hotspots

- `Import`
- `Spreadsheet` GUI tests and helpers
- template and test modules

Reason:

- narrower or less central to daily workflow migration sequencing

## 5. Pattern Observations

### Pattern A. Legacy Direct `PySide`

Common in `BIM` and older Python workbench flows.

Traits:

- direct `QtCore`, `QtGui`, `QtWidgets` imports
- dialog creation inline in command files
- `PySideUic.loadUi(...)` task panels

Migration impact:

- hardest class of Python UI to retire cleanly

### Pattern B. Wrapper-Based `PySideWrapper`

Common in `AddonManager`.

Traits:

- version abstraction around Qt5 and Qt6
- more modular widget files
- explicit widget classes

Migration impact:

- easier to isolate behind a compatibility layer during transition

### Pattern C. UI Loaded from `.ui` Resources

Common in `Assembly`, `BIM`, and `AddonManager`.

Traits:

- task panels and dialogs defined in `.ui`
- runtime loading through `FreeCADGui.PySideUic`

Migration impact:

- must be replaced with TS component trees and backend-described form schemas

## 6. Recommendations

1. treat `BIM`, `AddonManager`, and `Assembly` as dedicated Python UI migration streams
2. define a temporary Python UI compatibility lane instead of trying to rewrite all PySide flows immediately
3. prohibit new bundled PySide UI growth once the TypeScript shell program formally starts
4. prioritize Python UI schemas for dialogs and task panels that are already backed by `.ui` resources