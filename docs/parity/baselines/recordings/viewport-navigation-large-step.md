# Recording Step Log

Status: scaffolded step log awaiting reviewer execution

## Capture Summary

- recording id: viewport-navigation-large-step
- capture date: 2026-05-02
- reviewer: GitHub Copilot
- launcher command: set `PARITY_BASELINE_ID=import-step-large-light`, `PARITY_THEME=light`, `PARITY_FIXTURE_DOCUMENT=step-large-assembly`, `PARITY_STEP_FILE=tests/models/cn-06-13-00_asm.stp`, and `PARITY_CAPTURE_VIEWPORT=1`, then run `./run_freecad.bat --safe-mode tools/profile/capture_qt_shell_parity.py`
- start state or fixture: import-step-large-light
- supporting screenshots: `docs/parity/baselines/screenshots/import-step-large-light.png`; `docs/parity/baselines/screenshots/import-step-large-light-viewport.png`
- supporting metadata: `docs/parity/baselines/metadata/import-step-large-light.json`

## Steps

| Step | User Action | Observed Result |
|---|---|---|
| 1 | Launch the large STEP assembly baseline state and confirm the imported assembly is visible. | Pending reviewer capture. |
| 2 | Run fit-all, then orbit and pan the assembly in the active 3D view. | Pending reviewer capture. |
| 3 | Select a visible assembly element and confirm the shell and viewport remain stable. | Pending reviewer capture. |

## Review Checks

- expected flow outcome: navigation and selection stay responsive on the large STEP document with no blank redraw, broken shading, or lost selection context
- shell or dock regressions observed: pending reviewer capture
- viewport or redraw regressions observed: pending reviewer capture
- approved deviation reference: none recorded yet

## Decision

- accepted: pending reviewer capture
- needs recapture: pending reviewer capture
- follow-up notes: cite the viewport threshold in `docs/parity/acceptance/thresholds.md` if redraw variance or overlay drift is observed