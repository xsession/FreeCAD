# FreeCAD Full Parity Matrix

## Purpose

This document is the execution companion to [FREECAD_REACT_RUST_VARIANT_PLAN.md](E:/GIT/FreeCAD/FREECAD_REACT_RUST_VARIANT_PLAN.md).

Its purpose is to track feature parity for a Rust + React variant that aims to clone:

- the complete core FreeCAD feature set
- bundled workbenches
- strategic third-party plugins
- Python automation and macro workflows

This is a management artifact, not a prose vision document. Every row should eventually map to owners, fixtures, and acceptance tests.

---

## Status Legend

Use these values consistently:

- `not_started`
- `inventorying`
- `planned`
- `in_progress`
- `compat_mode`
- `partial`
- `feature_complete`
- `workflow_complete`
- `accepted`
- `blocked`
- `deferred`

## Migration Mode Legend

- `A`: Native compatibility hosted behind Rust
- `B`: Rust orchestration with native kernel operations
- `C`: Full Rust/React reimplementation
- `D`: Sunset/replace with new extension API

## Compatibility Tier Legend

- `Tier 1`: Full supported parity
- `Tier 2`: Supported with migration/adaptation
- `Tier 3`: Best-effort legacy mode
- `Tier 4`: Unsupported or deferred

---

## Core Platform Matrix

| Domain | Subsystem | User Workflow | Current FreeCAD Baseline | Target Ownership | Migration Mode | Priority | Status | Acceptance Criteria |
|---|---|---|---|---|---|---|---|---|
| Application | Startup/Start WB | Launch, recent files, templates, onboarding | Present | React + Rust | C | P0 | planned | All startup actions available without Qt UI |
| Application | Document lifecycle | New/open/save/save as/close/recover | Present | Rust + native bridge | B | P0 | planned | FCStd open/save/recover parity for supported release |
| Application | Command system | Command registration, invocation, shortcuts | Present | Rust | C | P0 | planned | Command registry/versioning works across all migrated workbenches |
| Application | Undo/redo | Transaction boundaries and history | Present | Rust + native bridge | B | P0 | planned | Deterministic undo/redo across top workflows |
| Application | Selection | Object/subelement/preselection | Present | Rust + React + native worker | B | P0 | planned | Backend-canonical selection model with viewport parity |
| Application | Properties | Property editor, units, expressions | Present | Rust + React | B | P0 | planned | Property editing and expression evaluation parity for major types |
| Application | Preferences | App/workbench settings | Present | Rust + React | C | P1 | planned | All critical preferences editable in new shell |
| Application | Notifications/logging | Console, warnings, progress, errors | Present | Rust + React | C | P1 | planned | Structured logs and user-safe notifications |
| Application | Addon management | Discover/install/update/remove addons | Present | Rust + React | C | P1 | planned | Tiered addon support with signed manifest model |
| Application | Macro tools | Run/edit/record macros | Present | Rust + Python worker + React | B | P1 | planned | Macro execution works without legacy GUI dependency |

---

## Bundled Workbench Matrix

| Workbench | Main User Value | Key Workflows | Target Ownership | Migration Mode | Priority | Status | Parity Target |
|---|---|---|---|---|---|---|---|
| Start | App entrypoint | New/open/recent/start content | React + Rust | C | P0 | planned | Workflow-complete |
| Part | B-Rep solid/surface ops | primitives, booleans, fillet, chamfer, import-based edits | Rust + native bridge + React | B | P0 | planned | Workflow-complete |
| PartDesign | Parametric part modeling | body, sketch, pad, pocket, pattern, datum workflows | Rust + native bridge + React | B | P0 | planned | Workflow-complete |
| Sketcher | Constraint-based 2D modeling | geometry creation, constraints, dimensions, solve/edit | Rust + native solver bridge + React | B | P0 | planned | Workflow-complete |
| Draft | 2D/3D drafting tools | lines, wires, snaps, annotations, transforms | Rust + native bridge + React | B | P1 | planned | Workflow-complete |
| BIM/Arch | Building workflows | walls, windows, structure, spaces, BIM objects | Mixed | A/B | P1 | planned | Major workflows complete |
| Assembly | Multi-part relationships | placement, constraints/joints, large model workflows | Mixed | A/B | P1 | planned | Daily-use workflows complete |
| Spreadsheet | Parametric tabular data | aliases, expressions, document binding | Rust + React | C | P1 | planned | Workflow-complete |
| TechDraw | 2D drawing generation | page creation, views, dimensions, export | Rust + native bridge + React | B | P1 | planned | Major workflows complete |
| Material | Material assignment | libraries, assignment, metadata | Rust + React | C | P1 | planned | Feature-complete |
| Measure | Inspection/measurement | dimensions, distance, angle, area | Rust + React + native bridge | B | P1 | planned | Feature-complete |
| FEM | Simulation prep and orchestration | materials, meshes, constraints, solver setup | Mixed | A/B | P2 | planned | Major workflows complete |
| CAM/Path | Manufacturing workflows | toolpaths, operations, post-processing | Mixed | A/B | P2 | planned | Major workflows complete |
| Mesh | Mesh inspection/edit | import, repair, selection, conversion | Mixed | B | P2 | planned | Major workflows complete |
| MeshPart | Mesh/B-Rep bridge workflows | shape-to-mesh, mesh-to-shape support | Mixed | B | P2 | planned | Feature-complete |
| Surface | Advanced surfacing | fillings, ruled surfaces, curves | Mixed | B | P2 | planned | Major workflows complete |
| Points | Point cloud/basic points | import, display, transform | Mixed | B | P2 | planned | Feature-complete |
| ReverseEngineering | RE workflows | scan-to-geometry support | Mixed | A/B | P2 | planned | Major workflows complete |
| Inspection | Compare/analyze workflows | deviation and inspection tooling | Mixed | A/B | P2 | planned | Feature-complete |
| Import | File exchange operations | import format handling | Rust + native bridge | B | P0 | planned | Supported formats parity |
| OpenSCAD | OpenSCAD integration | script-driven geometry exchange | Mixed | A/B | P3 | planned | Feature-complete |
| Robot | Kinematics/robot tools | model setup and simulation support | Mixed | A/B | P3 | planned | Major workflows complete |
| Plot | Plotting/data views | plotting and chart workflows | React + Rust | C | P3 | planned | Feature-complete |
| Web | Web/document helpers | embedded web-related utilities | React + Rust | C | P3 | planned | Feature-complete |
| Utilities | Misc support tools | preferences, diagnostics, helpers | Rust + React | C | P1 | planned | Workflow-complete |
| FlowStudio | CFD/custom module in this fork | solver setup, workflows, adapters | Mixed | B | P1 | planned | Major workflows complete |

---

## Core Cross-Cutting Capability Matrix

| Capability | Description | Priority | Status | Acceptance Criteria |
|---|---|---|---|---|
| FCStd compatibility | Open/save/recover target document set | P0 | planned | Golden fixture roundtrip passes |
| Import/export | STEP, IGES, STL, OBJ, DXF, SVG, PDF and others as scoped | P0 | planned | Format matrix with pass/fail coverage |
| Expressions/units | Expressions, unit parsing, aliases | P0 | planned | Expression-driven models behave identically for target fixtures |
| Recompute engine | Deterministic recompute and dependency propagation | P0 | planned | Golden workflows recompute without semantic drift |
| Tessellation | Backend-generated render payloads | P0 | planned | Stable viewport rendering with diff-based updates |
| Selection semantics | Canonical object/subelement mapping | P0 | planned | Selection parity across Part/PartDesign/Sketcher |
| Python automation | Macro/script execution and APIs | P1 | planned | Tier 1 and Tier 2 automation flows pass |
| Plugin system | Install/load/update/disable/report compatibility | P1 | planned | Tier A plugins work through declared extension APIs |
| Crash recovery | Worker isolation, autosave, restart flows | P1 | planned | Native worker crashes do not kill whole shell |
| Performance | Large document and assembly usability | P1 | planned | Target metrics agreed and tracked in CI/perf lab |

---

## Strategic Plugin Matrix

| Plugin / Addon Category | Example Scope | Business Importance | Compatibility Tier Target | Migration Strategy | Priority | Status |
|---|---|---|---|---|---|---|
| Sheet metal | folded part workflows | High | Tier 1 | Adapter first, selective rewrite later | P1 | planned |
| Fasteners | hardware libraries and insertion workflows | High | Tier 1 | Backend/plugin API support | P1 | planned |
| Assembly addons | alternative assembly workflows | High | Tier 2 | Compatibility host then converge | P1 | planned |
| BIM addons | architecture/construction extensions | High | Tier 2 | Mixed compatibility and targeted rewrite | P2 | planned |
| CFD/CAE addons | engineering analysis and setup | High | Tier 2 | Backend job/plugin APIs | P2 | planned |
| Rendering/visualization | render/export pipelines | Medium | Tier 2 | Worker-based integrations | P3 | planned |
| Electronics/PCB | ECAD/MCAD workflows | Medium | Tier 2 | Plugin APIs + compatibility host | P3 | planned |
| PLM/PDM connectors | enterprise/project integrations | Medium | Tier 2 | Rust backend integrations | P3 | planned |
| Legacy GUI-heavy macros | Qt-bound workflow helpers | Low/Variable | Tier 3 | Compatibility mode only | P3 | planned |

---

## Python Automation Matrix

| Surface | Examples | Target Tier | Migration Path | Status |
|---|---|---|---|---|
| Basic macro execution | run/save/manage macros | Tier 1 | Python worker + backend command context | planned |
| Scripting against documents | create/update/recompute objects | Tier 1 | Backend-owned API bindings | planned |
| GUI automation shims | legacy `Gui.runCommand` style flows | Tier 2 | Command adapters and warnings | planned |
| Qt widget direct access | custom dialogs, widget poking | Tier 3 | Legacy compatibility only | planned |
| Unsupported internal hacks | monkey-patching GUI internals | Tier 4 | Explicitly not guaranteed | planned |

---

## Golden Workflow Matrix

| Workflow ID | Domain | Workflow Summary | Fixture Required | Priority | Status | Acceptance |
|---|---|---|---|---|---|---|
| GW-001 | Core | New document -> save -> reopen | Yes | P0 | planned | Document roundtrip intact |
| GW-002 | PartDesign | Body -> sketch on XY -> pad -> save -> reopen | Yes | P0 | planned | Full parity |
| GW-003 | Sketcher | Create and constrain parametric sketch | Yes | P0 | planned | Solver and edit parity |
| GW-004 | Part | Primitive -> boolean -> fillet/chamfer | Yes | P0 | planned | Feature parity |
| GW-005 | Draft | Drafting and transform workflow | Yes | P1 | planned | Workflow parity |
| GW-006 | Spreadsheet | Spreadsheet-driven model dimensions | Yes | P1 | planned | Expression parity |
| GW-007 | TechDraw | Drawing page from part -> export | Yes | P1 | planned | Workflow parity |
| GW-008 | Import/Export | STEP import -> inspect -> STEP export | Yes | P0 | planned | Format parity |
| GW-009 | Addons | Install supported addon -> run workflow | Yes | P1 | planned | Plugin parity |
| GW-010 | Macro | Run automation script against document | Yes | P1 | planned | Automation parity |

---

## Execution Notes

- This matrix should become machine-readable over time.
- Each row should gain owners, milestones, and linked test assets.
- Parity claims should not be accepted without fixture-backed proof.
- "Feature complete" is weaker than "workflow complete".
- "Workflow complete" is weaker than "accepted".
