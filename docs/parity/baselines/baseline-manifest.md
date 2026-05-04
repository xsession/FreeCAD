# Baseline Manifest

Status: active capture and recording manifest for the current Qt parity lane

## Required Baselines

| Baseline ID | Theme | Workbench | Fixture | Primary Outputs |
|---|---|---|---|---|
| `shell-startup-light` | light | PartDesignWorkbench startup shell | startup shell | full window, metadata |
| `shell-empty-light` | light | PartDesignWorkbench empty shell | empty document | full window, tree/property crop, metadata |
| `shell-empty-dark` | dark | PartDesignWorkbench empty shell | empty document | full window, tree/property crop, metadata |
| `part-default-light` | light | Part | primitive document | full window, viewport crop, tree/property crop, metadata |
| `partdesign-default-light` | light | PartDesign | body with sketch and pad | full window, viewport crop, tree/property crop, metadata |
| `sketcher-task-light` | light | Sketcher | constraint-rich sketch | full window, task crop, metadata |
| `import-step-large-light` | light | PartDesignWorkbench after STEP import | large STEP assembly | full window, viewport crop, metadata |
| `techdraw-default-light` | light | TechDraw | techdraw example | full window, metadata |
| `tree-expanded-light` | light | Part | assembly or multi-body tree | tree crop, metadata |
| `property-grouped-light` | light | PartDesign | editable body feature | property crop, metadata |
| `task-panel-modeling-light` | light | PartDesign | active task workflow | task crop, metadata |
| `viewport-selection-light` | light | Part | selected object state | viewport crop, metadata |

## Recording Set

| Recording ID | Start State | Required Outputs |
|---|---|---|
| `switch-workbench` | `shell-empty-light` | step log, optional screen recording |
| `open-preferences` | `shell-empty-light` | step log, optional screen recording |
| `partdesign-task-flow` | `task-panel-modeling-light` | step log, optional screen recording |
| `viewport-navigation-large-step` | `import-step-large-light` | step log, optional screen recording |
| `dock-resize-panels` | `shell-empty-light` | step log, optional screen recording |

See `docs/parity/baselines/recordings/recording-manifest.md` for the executable checklist and review expectations for each flow.