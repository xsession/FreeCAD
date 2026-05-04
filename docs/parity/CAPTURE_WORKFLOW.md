# Parity Capture Workflow

Status: executable workflow for collecting Qt-shell baseline artifacts

## Purpose

This workflow turns the parity plan into repeatable capture steps using the current Qt runtime.

It is intentionally narrow: collect stable baseline evidence first, then review it, then compare later TypeScript renders against the same artifact set.

## Script Entry Point

Run the helper through the repository launcher:

```powershell
.\run_freecad.bat tools\profile\capture_qt_shell_parity.py
```

The script runs inside FreeCAD GUI and writes screenshots plus metadata under `docs/parity/baselines`.

For repeatable capture batches, use the matrix runner:

```powershell
.\tools\profile\capture_qt_shell_matrix.ps1 -DryRun
```

The runner reads `docs/parity/fixtures/qt-shell-capture-matrix.json`, applies the required parity environment variables per entry, and invokes `run_freecad.bat` for each enabled baseline.

## Required Environment Variables

- `PARITY_BASELINE_ID`: unique baseline identifier such as `shell-empty-light`

## Optional Environment Variables

- `PARITY_WORKBENCH`: workbench id to activate before capture, such as `PartWorkbench` or `PartDesignWorkbench`. Leave unset for startup-shell baselines.
- `PARITY_THEME`: `light` or `dark` switches the built-in FreeCAD theme pack before capture; other values are stored in metadata only
- `PARITY_FIXTURE_DOCUMENT`: fixture id stored in metadata
- `PARITY_EDIT_OBJECT`: document object name to enter edit mode on before capture
- `PARITY_SELECT_OBJECT`: document object name to select before capture
- `PARITY_SELECT_SUBELEMENT`: optional subelement name such as `Face1` to select on the target object
- `PARITY_STEP_FILE`: STEP file to open before capture
- `PARITY_RUN_COMMAND`: command id to invoke after fixture preparation, such as `PartDesign_CompSketches`
- `PARITY_CAPTURE_VIEWPORT`: set to `1` to export a viewport image via the active 3D view
- `PARITY_CAPTURE_TREE_PROPERTY`: set to `1` to crop the first dock matching tree or property keywords
- `PARITY_CAPTURE_TASK_PANEL`: set to `1` to crop the Tasks dock when an active task or edit workflow is visible
- `PARITY_CAPTURE_DOCK_TARGET`: optionally target a specific dock tab such as `model` or `property`
- `PARITY_EXPAND_TREE`: set to `1` to expand visible tree views before capture
- `PARITY_SELECTION_EMPHASIS`: set to `1` to apply a persistent selected-state emphasis when offscreen viewport capture omits transient selection overlays
- `PARITY_AUTO_ACCEPT_MODAL`: set to `1` to auto-accept a blocking modal dialog before capturing a command-driven task workflow
- `PARITY_NOTES`: optional note string stored in metadata

## Example Commands

Startup shell baseline:

```powershell
$env:PARITY_BASELINE_ID = 'shell-startup-light'
$env:PARITY_THEME = 'light'
$env:PARITY_FIXTURE_DOCUMENT = 'startup-shell'
.\run_freecad.bat --safe-mode tools\profile\capture_qt_shell_parity.py
```

Empty shell baseline:

```powershell
$env:PARITY_BASELINE_ID = 'shell-empty-light'
$env:PARITY_THEME = 'light'
$env:PARITY_FIXTURE_DOCUMENT = 'empty-document'
.\run_freecad.bat --safe-mode tools\profile\capture_qt_shell_parity.py
```

Dark empty shell baseline:

```powershell
$env:PARITY_BASELINE_ID = 'shell-empty-dark'
$env:PARITY_THEME = 'dark'
$env:PARITY_FIXTURE_DOCUMENT = 'empty-document'
$env:PARITY_CAPTURE_TREE_PROPERTY = '1'
.\run_freecad.bat --safe-mode tools\profile\capture_qt_shell_parity.py
```

PartDesign shell baseline:

```powershell
$env:PARITY_BASELINE_ID = 'partdesign-default-light'
$env:PARITY_WORKBENCH = 'PartDesignWorkbench'
$env:PARITY_THEME = 'light'
$env:PARITY_FIXTURE_DOCUMENT = 'partdesign-pad-example'
$env:PARITY_CAPTURE_VIEWPORT = '1'
$env:PARITY_CAPTURE_TREE_PROPERTY = '1'
.\run_freecad.bat --safe-mode tools\profile\capture_qt_shell_parity.py
```

Sketcher task baseline:

```powershell
$env:PARITY_BASELINE_ID = 'sketcher-task-light'
$env:PARITY_WORKBENCH = 'SketcherWorkbench'
$env:PARITY_THEME = 'light'
$env:PARITY_FIXTURE_DOCUMENT = 'sketcher-constraint-example'
$env:PARITY_EDIT_OBJECT = 'Sketch'
$env:PARITY_CAPTURE_TASK_PANEL = '1'
.\run_freecad.bat --safe-mode tools\profile\capture_qt_shell_parity.py
```

TechDraw shell baseline:

```powershell
$env:PARITY_BASELINE_ID = 'techdraw-default-light'
$env:PARITY_WORKBENCH = 'TechDrawWorkbench'
$env:PARITY_THEME = 'light'
$env:PARITY_FIXTURE_DOCUMENT = 'techdraw-example'
.\run_freecad.bat --safe-mode tools\profile\capture_qt_shell_parity.py
```

Expanded tree baseline:

```powershell
$env:PARITY_BASELINE_ID = 'tree-expanded-light'
$env:PARITY_WORKBENCH = 'PartWorkbench'
$env:PARITY_THEME = 'light'
$env:PARITY_FIXTURE_DOCUMENT = 'multi-body-tree'
$env:PARITY_CAPTURE_TREE_PROPERTY = '1'
$env:PARITY_CAPTURE_DOCK_TARGET = 'model'
$env:PARITY_EXPAND_TREE = '1'
.\run_freecad.bat --safe-mode tools\profile\capture_qt_shell_parity.py
```

Property editor baseline:

```powershell
$env:PARITY_BASELINE_ID = 'property-grouped-light'
$env:PARITY_WORKBENCH = 'PartDesignWorkbench'
$env:PARITY_THEME = 'light'
$env:PARITY_FIXTURE_DOCUMENT = 'partdesign-editable-feature'
$env:PARITY_SELECT_OBJECT = 'Pad'
$env:PARITY_CAPTURE_TREE_PROPERTY = '1'
$env:PARITY_CAPTURE_DOCK_TARGET = 'property'
.\run_freecad.bat --safe-mode tools\profile\capture_qt_shell_parity.py
```

PartDesign modeling task-panel baseline:

```powershell
$env:PARITY_BASELINE_ID = 'task-panel-modeling-light'
$env:PARITY_WORKBENCH = 'PartDesignWorkbench'
$env:PARITY_THEME = 'light'
$env:PARITY_FIXTURE_DOCUMENT = 'partdesign-taskpanel-example'
$env:PARITY_SELECT_OBJECT = 'Body'
$env:PARITY_RUN_COMMAND = 'PartDesign_CompSketches'
$env:PARITY_CAPTURE_TASK_PANEL = '1'
$env:PARITY_AUTO_ACCEPT_MODAL = '1'
.\run_freecad.bat --safe-mode tools\profile\capture_qt_shell_parity.py
```

Viewport selection baseline:

```powershell
$env:PARITY_BASELINE_ID = 'viewport-selection-light'
$env:PARITY_WORKBENCH = 'PartWorkbench'
$env:PARITY_THEME = 'light'
$env:PARITY_FIXTURE_DOCUMENT = 'primitive-document'
$env:PARITY_SELECT_OBJECT = 'Box'
$env:PARITY_SELECT_SUBELEMENT = 'Face1'
$env:PARITY_SELECTION_EMPHASIS = '1'
$env:PARITY_CAPTURE_VIEWPORT = '1'
.\run_freecad.bat --safe-mode tools\profile\capture_qt_shell_parity.py
```

Large STEP viewport baseline:

```powershell
$env:PARITY_BASELINE_ID = 'import-step-large-light'
$env:PARITY_THEME = 'light'
$env:PARITY_FIXTURE_DOCUMENT = 'step-large-assembly'
$env:PARITY_STEP_FILE = 'tests/models/cn-06-13-00_asm.stp'
$env:PARITY_CAPTURE_VIEWPORT = '1'
.\run_freecad.bat tools\profile\capture_qt_shell_parity.py
```

## Expected Outputs

For each capture the script writes:

- `docs/parity/baselines/screenshots/<baseline-id>.png`
- optional viewport or dock crop screenshots with suffixes
- `docs/parity/baselines/metadata/<baseline-id>.json`

## Current Execution Status

- the helper script and supporting metadata assets are validated in-repo
- a matrix runner now exists at `tools/profile/capture_qt_shell_matrix.ps1` for repeatable local capture batches
- `shell-startup-light` now emits a full-window screenshot and metadata on the current Windows runtime
- `shell-empty-light` now emits a full-window screenshot, a tree/property crop, and metadata on the current Windows runtime
- `shell-empty-dark` now emits a full-window screenshot, a tree/property crop, and metadata on the current Windows runtime
- `part-default-light` now emits a full-window screenshot, a viewport crop, a tree/property crop, and metadata on the current Windows runtime
- `partdesign-default-light` now emits a full-window screenshot, a viewport crop, a tree/property crop, and metadata on the current Windows runtime
- `sketcher-task-light` now emits a full-window screenshot, a task-panel crop, and metadata on the current Windows runtime
- `techdraw-default-light` now emits a full-window screenshot and metadata on the current Windows runtime
- `import-step-large-light` now emits a full-window screenshot, a viewport crop, and metadata on the current Windows runtime using the committed assembly at `tests/models/cn-06-13-00_asm.stp`
- `tree-expanded-light` now emits an expanded model-tree crop and metadata on the current Windows runtime
- `property-grouped-light` now emits a grouped property-editor crop and metadata on the current Windows runtime
- `task-panel-modeling-light` now emits a PartDesign modeling task-panel crop and metadata on the current Windows runtime
- `viewport-selection-light` now emits a selected-state viewport crop and metadata on the current Windows runtime
- startup-shell captures currently report `PartDesignWorkbench` as the active workbench in metadata because that is the runtime-selected startup workbench
- `PARITY_THEME=light|dark` now switches the live FreeCAD theme pack before capture instead of only labeling metadata

## Review Flow

1. run the script for the target baseline
2. inspect the generated screenshots for clipping, loading artifacts, or transient UI noise
3. add review notes using `docs/parity/acceptance/review-log-template.md`
4. if acceptable, keep the artifacts and register the capture in `docs/parity/baselines/baseline-manifest.md`
5. if not acceptable, rerun after correcting the shell state or fixture preparation

## Recording Flow

1. choose the required interaction from `docs/parity/baselines/recordings/recording-manifest.md`
2. start from the referenced baseline or fixture state
3. record the interaction or write the required step log under `docs/parity/baselines/recordings/`
4. note any deviation against `docs/parity/acceptance/thresholds.md` or the current dated review log
5. keep the step log even when a screen recording is also captured; the written log is the review anchor

## Current Limits

- tree or property crop detection is heuristic and based on dock titles
- interaction recordings are still manual on the current runtime, but the required set now has an executable manifest and step-log path under `docs/parity/baselines/recordings/`
- the script captures the current Qt runtime only; later TS captures should match the same metadata model