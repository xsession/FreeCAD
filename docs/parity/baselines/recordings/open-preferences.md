# Recording Step Log

Status: scaffolded step log awaiting reviewer execution

## Capture Summary

- recording id: open-preferences
- capture date: 2026-05-02
- reviewer: GitHub Copilot
- launcher command: set `PARITY_BASELINE_ID=shell-empty-light`, `PARITY_THEME=light`, and `PARITY_FIXTURE_DOCUMENT=empty-document`, then run `./run_freecad.bat --safe-mode tools/profile/capture_qt_shell_parity.py`
- start state or fixture: shell-empty-light
- supporting screenshots: `docs/parity/baselines/screenshots/shell-empty-light.png`
- supporting metadata: `docs/parity/baselines/metadata/shell-empty-light.json`

## Steps

| Step | User Action | Observed Result |
|---|---|---|
| 1 | Launch the shell-empty-light baseline state and confirm the main shell is responsive. | Pending reviewer capture. |
| 2 | Open Preferences from the standard menu path used in the current Qt shell. | Pending reviewer capture. |
| 3 | Dismiss Preferences with Cancel and confirm the original shell state is restored. | Pending reviewer capture. |

## Review Checks

- expected flow outcome: preferences opens on the expected command path and closes without corrupting menus, toolbars, or docks
- shell or dock regressions observed: pending reviewer capture
- viewport or redraw regressions observed: pending reviewer capture
- approved deviation reference: none recorded yet

## Decision

- accepted: pending reviewer capture
- needs recapture: pending reviewer capture
- follow-up notes: capture the dialog entry path used during review if it differs from the expected menu route