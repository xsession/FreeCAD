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

## Required Environment Variables

- `PARITY_BASELINE_ID`: unique baseline identifier such as `shell-empty-light`

## Optional Environment Variables

- `PARITY_WORKBENCH`: workbench id to activate before capture, such as `StartWorkbench` or `PartWorkbench`
- `PARITY_THEME`: freeform theme label stored in metadata
- `PARITY_FIXTURE_DOCUMENT`: fixture id stored in metadata
- `PARITY_STEP_FILE`: STEP file to open before capture
- `PARITY_CAPTURE_VIEWPORT`: set to `1` to export a viewport image via the active 3D view
- `PARITY_CAPTURE_TREE_PROPERTY`: set to `1` to crop the first dock matching tree or property keywords
- `PARITY_NOTES`: optional note string stored in metadata

## Example Commands

Empty shell baseline:

```powershell
$env:PARITY_BASELINE_ID = 'shell-empty-light'
$env:PARITY_WORKBENCH = 'StartWorkbench'
$env:PARITY_THEME = 'light'
$env:PARITY_FIXTURE_DOCUMENT = 'empty-document'
.\run_freecad.bat tools\profile\capture_qt_shell_parity.py
```

Large STEP viewport baseline:

```powershell
$env:PARITY_BASELINE_ID = 'import-step-large-light'
$env:PARITY_WORKBENCH = 'StartWorkbench'
$env:PARITY_THEME = 'light'
$env:PARITY_FIXTURE_DOCUMENT = 'step-large-assembly'
$env:PARITY_STEP_FILE = 'E:\WORK\flow_studio_sims\cn-06-13-00_asm_simplified.stp'
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
- no baseline screenshots have been produced yet in this session
- repeated launcher attempts from the current automated tool path produced no screenshots, metadata capture files, or launcher log output
- treat the first real baseline capture as a local follow-up run outside this automation path until the launcher behavior is understood

## Review Flow

1. run the script for the target baseline
2. inspect the generated screenshots for clipping, loading artifacts, or transient UI noise
3. add review notes using `docs/parity/acceptance/review-log-template.md`
4. if acceptable, keep the artifacts and register the capture in `docs/parity/baselines/baseline-manifest.md`
5. if not acceptable, rerun after correcting the shell state or fixture preparation

## Current Limits

- tree or property crop detection is heuristic and based on dock titles
- interaction recordings are not automated yet
- the script captures the current Qt runtime only; later TS captures should match the same metadata model
- automated GUI-script launch from this session was not reliable enough to generate the first baselines