# Parity Fixture Manifest

Status: initial fixture list

## Core Fixtures

| Fixture ID | Type | Purpose |
|---|---|---|
| `empty-document` | in-app | shell baseline without model state noise |
| `primitive-document` | in-app | simple Part and viewport baseline |
| `part-boolean-example` | repo or generated | Part workflow baseline |
| `partdesign-pad-example` | repo or generated | PartDesign workflow baseline |
| `sketcher-constraints-example` | repo or generated | Sketcher editing and task-panel baseline |
| `techdraw-example` | repo or generated | TechDraw shell baseline |
| `step-large-assembly` | external or repo | large-model viewport and shell stress baseline |

## Fixture Rules

1. each fixture must have a stable identifier
2. each fixture should have a repeatable creation or retrieval path
3. large external models should have size and provenance notes
4. parity captures should avoid ad hoc documents created differently between runs