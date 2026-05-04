# Parity Review Log 2026-05-02

Status: provisional acceptance record for the current required screenshot baseline set

## Capture Summary

- capture date: 2026-05-02
- reviewer: GitHub Copilot
- shell runtime: Windows debug build launched through `run_freecad.bat --safe-mode`
- matrix status: `tools/profile/capture_qt_shell_matrix.ps1 -DryRun` enumerates every baseline in `docs/parity/baselines/baseline-manifest.md` without skips
- artifact root: `docs/parity/baselines/screenshots`
- metadata root: `docs/parity/baselines/metadata`

## Reviewed Baselines

| Baseline ID | Theme | Workbench | Fixture | Acceptance Notes |
|---|---|---|---|---|
| `shell-startup-light` | light | PartDesignWorkbench | startup shell | Accepted as startup shell reference with full-window artifact and metadata. |
| `shell-empty-light` | light | PartDesignWorkbench | empty document | Accepted as empty shell reference with tree or property crop output. |
| `shell-empty-dark` | dark | PartDesignWorkbench | empty document | Accepted as dark-theme shell reference with deterministic runtime theme switching. |
| `part-default-light` | light | Part | primitive document | Accepted with viewport and tree or property crop outputs. |
| `partdesign-default-light` | light | PartDesign | body with sketch and pad | Accepted with deterministic pad fixture, viewport crop, and tree or property crop outputs. |
| `sketcher-task-light` | light | Sketcher | constraint-rich sketch | Accepted with task-panel crop and full-window artifact. |
| `import-step-large-light` | light | PartDesignWorkbench | large STEP assembly | Accepted using committed repo asset resolved from repo-relative input path. |
| `techdraw-default-light` | light | TechDraw | techdraw example | Accepted with deterministic page, template, and view fixture. |
| `tree-expanded-light` | light | Part | multi-body tree | Accepted as model-tree crop baseline with expanded tree state. |
| `property-grouped-light` | light | PartDesign | editable body feature | Accepted as property-editor crop baseline for selected `Pad`. |
| `task-panel-modeling-light` | light | PartDesign | active task workflow | Accepted after refresh through `PartDesign_CompSketches`; metadata now shows `visible_panels` containing `Tasks` and emits a task-panel crop. |
| `viewport-selection-light` | light | Part | selected object state | Accepted with documented persisted selection emphasis because offscreen viewport export does not preserve transient selection overlay reliably. |

## Artifact Review

- metadata completeness: every required baseline has a committed metadata file under `docs/parity/baselines/metadata`
- crop completeness: tree, property, viewport, and task-specific baselines emit the expected secondary artifact type for the reviewed state
- shell coverage: shell baselines cover startup, empty light, empty dark, Part, PartDesign, Sketcher, TechDraw, and STEP import shell states
- matrix coverage: the canonical matrix entry set now reproduces every required baseline through helper-generated fixtures or committed repo assets

## Observations

- runtime theme switching is now real rather than metadata-only; `shell-empty-dark` depends on the helper applying and restoring the FreeCAD dark theme at capture time
- `viewport-selection-light` is truthful but uses a pragmatic workaround: persistent view-provider emphasis makes the selected state visible in the saved viewport crop because transient selection overlay is absent in the current offscreen renderer path
- `task-panel-modeling-light` is visually valid and now records the Tasks dock in `visible_panels`, but `active_task` remains `null`; the task crop itself is the more reliable acceptance signal on the current runtime
- unresolved editor imports for `FreeCAD`, `FreeCADGui`, `ImportGui`, and `PySide` remain expected because those modules are injected by the FreeCAD runtime rather than normal source discovery

## Decision

- accepted: yes, provisionally, for the required screenshot baseline set in `docs/parity/baselines/baseline-manifest.md`
- needs recapture: no immediate recapture required for the reviewed baseline set
- follow-up notes: diff-based gating can now use the active threshold set in `docs/parity/acceptance/thresholds.md`; any deviation from those values should be logged explicitly in future review entries
- follow-up notes: the recording set is now scaffolded under `docs/parity/baselines/recordings/`, but the logs still require reviewer execution and are not covered by this review entry