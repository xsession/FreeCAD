# Baseline Manifest

Status: initial capture manifest

## Required Baselines

| Baseline ID | Theme | Workbench | Fixture | Primary Outputs |
|---|---|---|---|---|
| `shell-startup-light` | light | Start | startup shell | full window, metadata |
| `shell-empty-light` | light | Start | empty document | full window, tree/property crop, metadata |
| `shell-empty-dark` | dark | Start | empty document | full window, metadata |
| `part-default-light` | light | Part | primitive document | full window, viewport crop, metadata |
| `partdesign-default-light` | light | PartDesign | body with sketch and pad | full window, viewport crop, metadata |
| `sketcher-task-light` | light | Sketcher | constraint-rich sketch | full window, task crop, metadata |
| `import-step-large-light` | light | Import | large STEP assembly | full window, viewport crop, metadata |
| `techdraw-default-light` | light | TechDraw | techdraw example | full window, metadata |
| `tree-expanded-light` | light | Part | assembly or multi-body tree | tree crop, metadata |
| `property-grouped-light` | light | PartDesign | editable body feature | property crop, metadata |
| `task-panel-modeling-light` | light | PartDesign | active task workflow | task crop, metadata |
| `viewport-selection-light` | light | Part | selected object state | viewport crop, metadata |

## Recording Set

1. `switch-workbench`
2. `open-preferences`
3. `partdesign-task-flow`
4. `viewport-navigation-large-step`
5. `dock-resize-panels`