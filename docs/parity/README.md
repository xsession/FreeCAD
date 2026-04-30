# FreeCAD Parity Artifacts

Status: baseline capture workspace for Qt-to-TypeScript migration

## Purpose

This directory holds the concrete artifacts used to measure shell, editing-surface, and viewport parity between the current Qt shell and the target TypeScript shell.

It is the execution companion to `docs/FRONTEND_PARITY_BASELINE_SPEC.md`.

## Directory Layout

- `baselines/screenshots/`: approved screenshot baselines
- `baselines/recordings/`: interaction recordings or step logs
- `baselines/metadata/`: machine-readable metadata per baseline state
- `fixtures/`: fixture manifest and capture guidance
- `acceptance/`: parity thresholds, review logs, and gate decisions

## Required Starting Artifacts

1. baseline manifest
2. metadata template
3. acceptance threshold template
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
$env:PARITY_WORKBENCH = 'StartWorkbench'
.\run_freecad.bat tools\profile\capture_qt_shell_parity.py
```

Optional environment variables:

- `PARITY_THEME`
- `PARITY_FIXTURE_DOCUMENT`
- `PARITY_STEP_FILE`
- `PARITY_CAPTURE_VIEWPORT=1`
- `PARITY_CAPTURE_TREE_PROPERTY=1`

The helper writes screenshots into `docs/parity/baselines/screenshots` and metadata into `docs/parity/baselines/metadata`.

For full instructions and examples, see `docs/parity/CAPTURE_WORKFLOW.md`.

## Current Status

- artifact scaffolding, metadata templates, and the capture helper are in place
- no approved screenshot baselines are committed yet
- first capture runs should be executed locally because automated launcher runs in this session did not emit output artifacts

## Related Documents

- `docs/FRONTEND_PARITY_BASELINE_SPEC.md`
- `docs/QT_TO_TYPESCRIPT_FRONTEND_MIGRATION_PLAN.md`
- `docs/architecture/qt-to-typescript-migration-checklist.md`