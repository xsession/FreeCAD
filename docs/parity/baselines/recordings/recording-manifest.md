# Recording Manifest

Status: executable checklist for the required parity interaction set

## Purpose

This manifest turns the recording set in `docs/parity/baselines/baseline-manifest.md` into concrete capture instructions.

Each recording may be satisfied by either:

- a screen recording under `docs/parity/baselines/recordings/`
- a reviewer-authored step log under `docs/parity/baselines/recordings/` when recording automation is unavailable on the current runtime

Until native recording automation exists, step logs are the default required artifact.

## Required Recording Set

| Recording ID | Fixture or Start State | Required Evidence | Reviewer Checks |
|---|---|---|---|
| `switch-workbench` | `shell-empty-light` shell state | `switch-workbench.md` step log plus optional `switch-workbench.mp4` | workbench selector changes shell chrome without blank intermediate shell or missing menus |
| `open-preferences` | `shell-empty-light` shell state | `open-preferences.md` step log plus optional `open-preferences.mp4` | preferences dialog opens from the expected command path and can be dismissed without shell corruption |
| `partdesign-task-flow` | `task-panel-modeling-light` fixture path | `partdesign-task-flow.md` step log plus optional `partdesign-task-flow.mp4` | task workflow stays in managed task-panel state from invocation through accept or cancel |
| `viewport-navigation-large-step` | `import-step-large-light` shell state | `viewport-navigation-large-step.md` step log plus optional `viewport-navigation-large-step.mp4` | fit-all, orbit, pan, and selection succeed on the large STEP assembly without broken redraw |
| `dock-resize-panels` | `shell-empty-light` shell state | `dock-resize-panels.md` step log plus optional `dock-resize-panels.mp4` | combo-view and report-dock resizing preserves usable layout and correct dock ordering |

## Step Log Template

Each step log should record:

1. capture date
2. reviewer
3. runtime and launcher command
4. starting baseline or fixture
5. exact user actions in order
6. observed result after each action
7. acceptance decision and any deviation note

Start from `docs/parity/baselines/recordings/step-log-template.md` when creating a new recording log.

## Recording Notes

- when a screen recording is unavailable, the step log is the gate artifact and should link any supporting screenshots already committed under `docs/parity/baselines/screenshots`
- if a flow depends on one of the required screenshot baselines, reference the corresponding metadata file under `docs/parity/baselines/metadata`
- any deviation from `docs/parity/acceptance/thresholds.md` or the review log must be called out in the step log explicitly