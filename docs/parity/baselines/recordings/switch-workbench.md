# Recording Step Log

Status: scaffolded step log awaiting reviewer execution

## Capture Summary

- recording id: switch-workbench
- capture date: 2026-05-02
- reviewer: GitHub Copilot
- launcher command: set `PARITY_BASELINE_ID=shell-empty-light`, `PARITY_THEME=light`, and `PARITY_FIXTURE_DOCUMENT=empty-document`, then run `./run_freecad.bat --safe-mode tools/profile/capture_qt_shell_parity.py`
- start state or fixture: shell-empty-light
- supporting screenshots: `docs/parity/baselines/screenshots/shell-empty-light.png`
- supporting metadata: `docs/parity/baselines/metadata/shell-empty-light.json`

## Steps

| Step | User Action | Observed Result |
|---|---|---|
| 1 | Launch the shell-empty-light baseline state and confirm the default startup shell is visible. | Pending reviewer capture. |
| 2 | Switch the active workbench from PartDesign to Part using the workbench selector. | Pending reviewer capture. |
| 3 | Switch from Part to Sketcher, then back to PartDesign. | Pending reviewer capture. |

## Review Checks

- expected flow outcome: workbench changes update menus, toolbars, and panel labels without a blank shell, missing chrome, or stale command sets
- shell or dock regressions observed: pending reviewer capture
- viewport or redraw regressions observed: pending reviewer capture
- approved deviation reference: none recorded yet

## Decision

- accepted: pending reviewer capture
- needs recapture: pending reviewer capture
- follow-up notes: compare against the shell and structural thresholds in `docs/parity/acceptance/thresholds.md`