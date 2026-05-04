# Recording Step Log

Status: scaffolded step log awaiting reviewer execution

## Capture Summary

- recording id: dock-resize-panels
- capture date: 2026-05-02
- reviewer: GitHub Copilot
- launcher command: set `PARITY_BASELINE_ID=shell-empty-light`, `PARITY_THEME=light`, and `PARITY_FIXTURE_DOCUMENT=empty-document`, then run `./run_freecad.bat --safe-mode tools/profile/capture_qt_shell_parity.py`
- start state or fixture: shell-empty-light
- supporting screenshots: `docs/parity/baselines/screenshots/shell-empty-light.png`; `docs/parity/baselines/screenshots/shell-empty-light-tree-property.png`
- supporting metadata: `docs/parity/baselines/metadata/shell-empty-light.json`

## Steps

| Step | User Action | Observed Result |
|---|---|---|
| 1 | Launch the shell-empty-light baseline state and confirm the combo view and report-dock areas are visible. | Pending reviewer capture. |
| 2 | Resize the model or property side of the combo view to a narrower and then wider state. | Pending reviewer capture. |
| 3 | Resize the lower dock region and confirm the shell returns to a usable default layout. | Pending reviewer capture. |

## Review Checks

- expected flow outcome: dock resizing preserves panel ordering, visible content, and usable shell proportions without layout corruption
- shell or dock regressions observed: pending reviewer capture
- viewport or redraw regressions observed: pending reviewer capture
- approved deviation reference: none recorded yet

## Decision

- accepted: pending reviewer capture
- needs recapture: pending reviewer capture
- follow-up notes: note any minimum-width clipping or panel reorder against the structural thresholds in `docs/parity/acceptance/thresholds.md`