# Parity Fixture Manifest

Status: active fixture inventory for helper-driven parity capture

## Core Fixtures

| Fixture ID | Type | Purpose |
|---|---|---|
| `startup-shell` | runtime state | startup shell baseline before document creation |
| `empty-document` | in-app | shell baseline without model state noise |
| `primitive-document` | helper-generated | simple Part shell, viewport, and selection baseline |
| `partdesign-pad-example` | helper-generated | PartDesign body, sketch, and pad baseline |
| `sketcher-constraint-example` | helper-generated | Sketcher editing and task-panel baseline |
| `techdraw-example` | helper-generated | TechDraw page, template, and view baseline |
| `multi-body-tree` | helper-generated | expanded model-tree and hierarchy baseline |
| `partdesign-editable-feature` | helper-generated | editable PartDesign feature baseline for property capture |
| `partdesign-movefeature-example` | helper-generated | auxiliary PartDesign move-feature workflow fixture |
| `partdesign-taskpanel-example` | helper-generated | minimal PartDesign task-panel workflow fixture |
| `step-large-assembly` | repo asset | large-model viewport and shell stress baseline |

## Current Fixture Coverage

- all required screenshot baselines in `docs/parity/baselines/baseline-manifest.md` now resolve to either a helper-generated fixture or a committed repo asset
- `step-large-assembly` is satisfied by the committed STEP asset used by `import-step-large-light`
- `partdesign-movefeature-example` remains available for auxiliary investigation even though the accepted task-panel baseline uses `partdesign-taskpanel-example`

## Fixture Rules

1. each fixture must have a stable identifier
2. each fixture should have a repeatable creation or retrieval path
3. large external models should have size and provenance notes
4. parity captures should avoid ad hoc documents created differently between runs