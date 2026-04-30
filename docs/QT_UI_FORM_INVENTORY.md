# FreeCAD Qt UI Form Inventory

Status: frozen planning baseline for UI form inventory

## 1. Purpose

This document inventories `.ui` form usage in the FreeCAD repository to support the Qt-to-TypeScript frontend migration.

It focuses on migration planning, not exhaustive form semantics.

## 2. Summary

Approximate `.ui` distribution across the current tree:

- `src/Gui` total: about 71 `.ui` files
- `src/App` total: 0 `.ui` files
- `src/Mod` total: about 527 `.ui` files

`src/Gui` is shell-critical, but the heaviest raw `.ui` volume lives in workbench modules.

## 3. `src/Gui` Inventory Breakdown

### `src/Gui/Dialogs`

Approximate count: 35 `.ui` files

Representative forms:

- `src/Gui/Dialogs/AboutApplication.ui`
- `src/Gui/Dialogs/DlgPreferences.ui`
- `src/Gui/Dialogs/DlgKeyboard.ui`
- `src/Gui/Dialogs/DlgMacroExecute.ui`
- `src/Gui/Dialogs/DlgUnitsCalculator.ui`
- `src/Gui/Dialogs/DlgThemeEditor.ui`

Migration meaning:

- preferences, macros, keyboard shortcuts, themes, and general shell dialogs all need TS replacements or protocol-backed equivalents

### `src/Gui/PreferencePages`

Approximate count: 16 `.ui` files

Representative forms:

- `src/Gui/PreferencePages/DlgSettings3DView.ui`
- `src/Gui/PreferencePages/DlgSettingsGeneral.ui`
- `src/Gui/PreferencePages/DlgSettingsNavigation.ui`
- `src/Gui/PreferencePages/DlgSettingsPythonConsole.ui`
- `src/Gui/PreferencePages/DlgSettingsUI.ui`

Migration meaning:

- preference pages must become schema-driven backend settings plus TS rendering, not one-off Qt forms

### `src/Gui/TaskView`

Approximate count: 5 `.ui` files

Representative forms:

- `src/Gui/TaskView/TaskAppearance.ui`
- `src/Gui/TaskView/TaskEditControl.ui`
- `src/Gui/TaskView/TaskImage.ui`
- `src/Gui/TaskView/TaskOrientation.ui`
- `src/Gui/TaskView/TaskSelectLinkProperty.ui`

Migration meaning:

- these are shell-level task runtime patterns that should inform the generic TS task panel system

### `src/Gui` root forms

Approximate count: 15 `.ui` files

Representative forms:

- `src/Gui/Clipping.ui`
- `src/Gui/DocumentRecovery.ui`
- `src/Gui/DownloadManager.ui`
- `src/Gui/Placement.ui`
- `src/Gui/SceneInspector.ui`
- `src/Gui/TaskTransform.ui`

Migration meaning:

- several shell utilities, recovery flows, and common transformation workflows still depend on Qt form definitions

## 4. Top `src/Mod` Modules by `.ui` Count

Top workbench and module areas by approximate `.ui` volume:

| Rank | Module | Approximate `.ui` Count | Notes |
|---|---|---:|---|
| 1 | `Fem` | 97 | Constraints, meshing, solver config, post-processing |
| 2 | `CAM` | 61 | Tooling, operations, simulators, setup and dressups |
| 3 | `BIM` | 49 | IFC dialogs, project tools, architectural workflows |
| 4 | `TechDraw` | 38 | Drawing tasks, views, dimensions, annotations |
| 5 | `Part` | 31 | Feature and geometry dialogs |
| 6 | `PartDesign` | 25 | Feature task dialogs and parametric editors |
| 7 | `Draft` | 19 | Arrays, layers, annotations, preferences |
| 8 | `Material` | 17 | Material editor and material properties |
| 9 | `AddonManager` | 16 | Installer, package, progress, repository dialogs |
| 10 | `Sketcher` | 15 | Constraint panels, validation, settings, arrays |

## 5. Large UI Migration Zones

### FEM

Approximate count: 97 `.ui` files

Representative paths:

- `src/Mod/Fem/Gui/TaskFemConstraint*.ui`
- `src/Mod/Fem/Gui/TaskPost*.ui`
- `src/Mod/Fem/Gui/Resources/ui/Solver*.ui`
- `src/Mod/Fem/Gui/Resources/ui/Mesh*.ui`

Migration implication:

- FEM is one of the largest Qt form retirement programs in the repo and should be treated as a dedicated workstream

### CAM

Approximate count: 61 `.ui` files

Representative paths:

- `src/Mod/CAM/Gui/Resources/panels/PageOp*.ui`
- `src/Mod/CAM/Gui/Resources/panels/Tool*.ui`
- `src/Mod/CAM/Gui/Resources/panels/Dlg*.ui`
- `src/Mod/CAM/Gui/Resources/preferences/*.ui`

Migration implication:

- CAM has a large task-panel and editor surface with many specialized forms that should likely migrate after shell and primary CAD workflows are stable

### BIM

Approximate count: 49 `.ui` files

Representative paths:

- `src/Mod/BIM/Resources/ui/dialog*.ui`
- `src/Mod/BIM/Resources/ui/preferences*.ui`
- `src/Mod/BIM/Resources/ui/*TaskPanel.ui`

Migration implication:

- BIM combines large Qt form volume with heavy PySide usage, making it one of the highest-risk de-Qt areas

### TechDraw

Approximate count: 38 `.ui` files

Representative paths:

- `src/Mod/TechDraw/Gui/Task*.ui`
- `src/Mod/TechDraw/Gui/DlgPrefsTechDraw*.ui`
- `src/Mod/TechDraw/Gui/SymbolChooser.ui`

Migration implication:

- TechDraw’s workflow is dialog and task heavy, so parity testing must include technical drawing authoring sequences

## 6. Primary Workflow Modules with Significant `.ui` Weight

Modules most likely to define the main migration burden for daily-use workflows:

- `Part`
- `PartDesign`
- `Sketcher`
- `Import`
- `Spreadsheet`
- `TechDraw`
- `Fem`

## 7. Recommended Follow-Up Inventory Passes

1. add a file-by-file mapping for all `.ui` forms in `src/Gui`
2. classify each `.ui` form as shell, preferences, task, dialog, or utility
3. classify each workbench `.ui` form as P0, P1, P2, or compatibility-lane migration priority
4. link each `.ui` family to a target TypeScript component or protocol schema