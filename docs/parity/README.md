# FreeCAD Parity Artifacts

Status: baseline capture workspace for Qt-to-TypeScript migration

## Purpose

This directory holds the concrete artifacts used to measure shell, editing-surface, and viewport parity between the current Qt shell and the target TypeScript shell.

It is the execution companion to `docs/FRONTEND_PARITY_BASELINE_SPEC.md`.

## Directory Layout

- `baselines/screenshots/`: approved screenshot baselines
- `baselines/recordings/`: interaction recordings, step logs, and the recording manifest
- `baselines/metadata/`: machine-readable metadata per baseline state
- `fixtures/`: fixture manifest and capture guidance
- `acceptance/`: parity thresholds, review logs, and gate decisions

## Required Starting Artifacts

1. baseline manifest
2. metadata template
3. acceptance thresholds
4. fixture manifest

## Initial Capture Order

1. shell startup and empty document states
2. Part, PartDesign, and Sketcher shell states
3. tree, property, and task-panel crops
4. large STEP assembly viewport state
5. interaction recordings for workbench switch, preferences, and viewport navigation

## Capture Workflow

Use the repository launcher to run the parity capture helper inside FreeCAD GUI:

```powershell
$env:PARITY_BASELINE_ID = 'shell-empty-light'
.\run_freecad.bat --safe-mode tools\profile\capture_qt_shell_parity.py
```

Optional environment variables:

- `PARITY_THEME`
- `PARITY_FIXTURE_DOCUMENT`
- `PARITY_STEP_FILE`
- `PARITY_CAPTURE_VIEWPORT=1`
- `PARITY_CAPTURE_TREE_PROPERTY=1`
- `PARITY_CAPTURE_TASK_PANEL=1`
- `PARITY_CAPTURE_DOCK_TARGET=model|property`
- `PARITY_SELECT_OBJECT=<object-name>`
- `PARITY_RUN_COMMAND=<command-id>`

For repeatable batches, use the capture matrix runner:

```powershell
.\tools\profile\capture_qt_shell_matrix.ps1 -DryRun
```

The default manifest lives at `docs/parity/fixtures/qt-shell-capture-matrix.json` and now enables the full required baseline set using committed in-repo fixtures and deterministic helper-driven setup.

The helper writes screenshots into `docs/parity/baselines/screenshots` and metadata into `docs/parity/baselines/metadata`.

Current startup-shell captures are recorded with the actual active workbench reported by FreeCAD. On the current Windows runtime that startup shell resolves to `PartDesignWorkbench`, so metadata reflects that value instead of a legacy `StartWorkbench` label.

`PARITY_THEME=light|dark` now switches the built-in FreeCAD theme pack before capture by pairing `FreeCAD.qss` with the corresponding `FreeCAD Light` or `FreeCAD Dark` style-parameter set.

For full instructions and examples, see `docs/parity/CAPTURE_WORKFLOW.md`.

## Current Status

- artifact scaffolding, metadata templates, and the capture helper are in place
- `shell-startup-light` now emits a full-window screenshot plus metadata
- `shell-empty-light` now emits a full-window screenshot, a tree/property crop, and metadata
- `shell-empty-dark` now emits a full-window screenshot, a tree/property crop, and metadata
- `part-default-light` now emits a full-window screenshot, a viewport crop, a tree/property crop, and metadata
- `partdesign-default-light` now emits a full-window screenshot, a viewport crop, a tree/property crop, and metadata
- `sketcher-task-light` now emits a full-window screenshot, a task-panel crop, and metadata
- `techdraw-default-light` now emits a full-window screenshot and metadata
- `import-step-large-light` now emits a full-window screenshot, a viewport crop, and metadata using the committed assembly at `tests/models/cn-06-13-00_asm.stp`
- `tree-expanded-light` now emits an expanded model-tree crop and metadata
- `property-grouped-light` now emits a grouped property-editor crop and metadata
- `task-panel-modeling-light` now emits a PartDesign modeling task-panel crop and metadata
- `viewport-selection-light` now emits a selected-state viewport crop and metadata
- the required recording set now has a manifest, a reusable step-log template, and five prefilled step-log stubs under `docs/parity/baselines/recordings/`

## Related Documents

- `docs/FRONTEND_PARITY_BASELINE_SPEC.md`
- `docs/QT_TO_TYPESCRIPT_FRONTEND_MIGRATION_PLAN.md`
- `docs/architecture/qt-to-typescript-migration-checklist.md`