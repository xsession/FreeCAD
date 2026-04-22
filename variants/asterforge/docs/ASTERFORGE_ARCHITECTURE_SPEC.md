# AsterForge Architecture Specification

Status: draft baseline for implementation planning

## 1. Purpose

This document translates the AsterForge master prompt into an implementation-oriented architecture for the FreeCAD React and Rust variant under `variants/asterforge`.

It defines:

- runtime topology
- layer ownership
- document and recompute semantics
- workbench and plugin contracts
- rendering and geometry boundaries
- transport and protocol shape
- phased roadmap from the current bridge-backed state toward a stronger native geometry platform

This specification assumes the current AsterForge codebase already provides:

- a React and TypeScript frontend shell
- a Rust backend gateway
- explicit protocol schemas
- a native `freecad-bridge` boundary
- FreeCAD-style shell parity in the UI

It does not assume a production-ready parametric core already exists.

## 2. Product Boundary

### 2.1 Primary Goal

Build a production-grade parametric CAD platform that preserves FreeCAD-class workflows while moving application semantics, orchestration, and extension boundaries into Rust and presenting them through a React desktop shell.

### 2.2 Immediate Product Shape

The first serious AsterForge releases should be:

- desktop-first
- React-rendered
- Rust-controlled
- bridge-backed for core document extraction and modeling execution where required
- structured so geometry and solver subsystems can be replaced incrementally without breaking the UI or plugin surface

### 2.3 Non-Goals For Early Milestones

- full replacement of FreeCAD and OCCT geometry internals in phase 1
- browser-only deployment as the primary target
- total feature parity with every legacy workbench before the document core is stable
- frontend-owned command semantics or recompute logic

## 3. Architectural Principles

1. Rust owns domain truth.
2. React owns presentation, interaction composition, and local UI state only.
3. Native bridge code is isolated behind explicit services.
4. Document recompute is a first-class subsystem, not an implementation detail.
5. Workbench logic must be versioned and extensible.
6. Rendering state is derived from backend-owned scene payloads, not handcrafted frontend-only model state.
7. Large-model handling and long-running jobs must be designed in from the start.
8. Migration safety matters more than novelty.

## 4. High-Level Runtime Topology

```text
+---------------------------------------------------------------+
|                        React Desktop Shell                    |
|  menu bar | toolbars | combo view | viewport | utility dock   |
|  document tabs | task panels | property editor | status bar   |
+------------------------------+--------------------------------+
                               |
                    HTTP now, streaming later
                               |
+------------------------------v--------------------------------+
|                     Rust Application Platform                  |
|  api gateway | session service | document service | command bus|
|  recompute engine | job service | plugin manager | event stream|
+-------------+------------------+-------------------+-----------+
              |                  |                   |
              |                  |                   |
+-------------v----+   +---------v----------+   +---v----------+
| Native Bridge    |   | Geometry Services  |   | Import/Export|
| FreeCAD workers  |   | mesh, picking,     |   | adapters      |
| document access  |   | caches, diff prep  |   | STEP STL DXF |
+-------------+----+   +---------+----------+   +--------------+
              |                    |
              |                    |
+-------------v--------------------v----------------------------+
|            FreeCAD / OCCT / solver / future Rust kernel       |
+---------------------------------------------------------------+
```

## 5. Layer Ownership

### 5.1 Frontend Layer

The frontend in `frontend/app` owns:

- application chrome and layout composition
- view-local state such as dock visibility and active tabs
- user interaction capture for selection, hover, shortcuts, and forms
- rendering of backend payloads for tree, properties, tasks, diagnostics, jobs, and history
- command palette presentation
- viewport presentation and interaction adapters

The frontend does not own:

- command enablement rules
- document mutation semantics
- recompute decisions
- durable object identity
- authoritative feature definitions

### 5.2 Rust Application Layer

The Rust backend in `backend/crates/api-gateway` evolves into the authoritative application platform and owns:

- session lifecycle
- document registry
- command registry and dispatch
- undo and redo transaction boundaries
- recompute scheduling
- dependency analysis
- selection and preselection authority
- jobs, progress, and event stream emission
- plugin discovery and version negotiation
- adapter orchestration for native bridge and future geometry services

### 5.3 Native Bridge Layer

The native layer in `native/freecad-bridge` owns compatibility-facing operations that still rely on FreeCAD internals, including:

- document opening and extraction
- bridge-backed topology and scene payload generation
- access to legacy feature recompute behavior where still required
- import and export pathways that remain better served by FreeCAD and OCCT

The bridge must not leak ad hoc internal structures directly to the frontend.

## 6. Core Subsystems

### 6.1 Document Model

The document model is the primary product core.

Each open document should be represented as:

- `DocumentId`
- stable object graph
- feature timeline
- dependency DAG
- evaluation state
- selection state
- scene projection state
- undo and redo history
- dirty and persistence state

Recommended logical model:

```text
Document
  metadata
  roots[]
  objects: Map<ObjectId, ObjectRecord>
  features: Map<FeatureId, FeatureRecord>
  dependencies: Dag<Edge>
  history: TimelineEntry[]
  evaluation: EvaluationState
  selection: SelectionState
  scene: SceneProjectionState
```

Each object record should include:

- stable id
- display metadata
- workbench domain type
- property groups
- upstream references
- downstream dependents
- suppression and inactive status
- scene projection handles

### 6.2 Recompute Engine

The recompute engine is responsible for determining what must be reevaluated when a document mutation occurs.

Capabilities required:

- mark changed nodes dirty
- walk downstream dependencies
- determine minimal recompute slice
- schedule bridge or geometry execution tasks
- publish evaluation results and failures
- maintain rollback and resume markers

Early implementation can be bridge-backed but the invalidation graph must be Rust-owned.

### 6.3 Command System

Commands are the only legal way to mutate documents.

Each command definition requires:

- stable `command_id`
- workbench ownership
- selection requirements
- argument schema
- execution handler
- undo behavior
- side-effect summary
- job classification for long-running operations

Recommended Rust shape:

```text
CommandDefinition {
  id,
  workbench,
  label,
  enablement,
  argument_schema,
  transaction_mode,
  execution_kind,
  ui_hints,
}
```

Execution flow:

1. frontend requests command execution
2. backend validates selection and arguments
3. backend opens transaction boundary
4. backend performs bridge or native operation
5. backend updates document graph and evaluation state
6. backend emits tree, property, task, job, and viewport deltas

### 6.4 Workbench System

Workbench modules are backend-first domain packages with frontend presentation extensions.

Each workbench contributes:

- command groups
- object and feature types
- property schemas
- task-panel builders
- validation rules
- toolbar and menu taxonomy
- optional import, export, or simulation adapters

Initial workbench targets:

- Part Design
- Sketcher
- Assembly
- Mesh
- TechDraw
- CFD

### 6.5 Plugin System

Plugins must extend the application through versioned contracts rather than deep runtime patching.

Plugin contribution categories:

- workbench contributions
- command packs
- panel or dock contributions
- import and export adapters
- simulation and solver adapters
- property inspectors and validators

Minimum plugin contract requirements:

- semantic version range
- declared capabilities
- contribution manifests
- sandbox or isolation strategy
- migration rules for persisted plugin-owned document data

## 7. Parametric Modeling Model

### 7.1 Modeling Strategy

Parametric modeling must be represented as explicit features with stable references, not as opaque scene edits.

Initial feature classes:

- body
- sketch
- pad
- pocket
- revolve
- loft
- sweep
- fillet
- chamfer

Each feature should carry:

- feature id
- parent container
- defining arguments
- reference selectors
- generated result handles
- dependency edges
- suppression flag
- evaluation status

### 7.2 Selector Stability

The architecture must account for selector stability and topology drift.

Near-term strategy:

- use bridge-backed selectors where existing FreeCAD logic is more reliable
- preserve selector metadata in Rust document records
- expose selector diagnostics in history and properties

Medium-term strategy:

- introduce Rust-owned selector abstraction
- measure breakage classes under editing operations
- formalize repair and fallback behavior

## 8. Sketcher Architecture

The Sketcher workbench is a primary subsystem, not an optional feature.

### 8.1 Sketch Model

Each sketch contains:

- sketch plane or support reference
- 2D geometry primitives
- construction flags
- constraints
- solver state
- profile readiness state
- downstream feature consumers

### 8.2 Constraint Graph

Represent constraints as a graph over geometric entities.

Support at minimum:

- coincident
- parallel
- perpendicular
- tangent
- horizontal
- vertical
- distance
- angle
- radius
- diameter
- symmetry
- equality

### 8.3 Solver Ownership

Solver orchestration belongs in Rust even if the earliest solving path is still adapter-backed.

Roadmap:

- phase 1: bridge-backed or embedded compatibility solving
- phase 2: Rust-native constraint graph representation
- phase 3: optional WASM packaging for shared solver logic and tests

### 8.4 Sketch Failure Surface

The backend must expose diagnostic states for:

- under-constrained sketches
- over-constrained sketches
- conflicting constraints
- unsupported geometry combinations
- invalid downstream profile consumption

## 9. Rendering Architecture

### 9.1 Scene Ownership

The backend owns scene payload semantics. The frontend owns GPU resource management and interaction mapping.

Scene payloads should distinguish between:

- document object identity
- render node identity
- selectable entity identity
- material and state overlays
- visibility and suppression state
- hover and selection state

### 9.2 Viewer Pipeline

Recommended viewer flow:

1. backend emits scene snapshot or delta
2. frontend normalizes payload into viewer store
3. renderer updates GPU buffers and scene graph incrementally
4. picking maps back to backend entity ids
5. hover and selection events are posted back to backend authority

### 9.3 Large-Model Strategy

The viewer must support:

- progressive loading
- culling and scene partitioning
- mesh and material deduplication
- worker-assisted parse and prep steps
- fallback display modes for extremely large assemblies

### 9.4 Selection System

Selection authority remains backend-owned.

Selection categories should include:

- object
- body
- sketch
- feature
- face
- edge
- vertex

Preselection must follow the same identity model so task guidance and command previews stay consistent.

## 10. Shell And Interaction Model

The desktop shell already exists conceptually and must be preserved as an interaction contract.

Required shell regions:

- classic menu bar
- dense toolbar deck
- top document tabs
- left combo view with model and tasks tabs
- dominant central viewport
- bottom utility dock with report, Python console, jobs, diagnostics, history, and commands
- bottom status bar

The shell should remain backend-driven where possible:

- menus derived from command taxonomy
- toolbars derived from workbench definitions
- task panel derived from workflow metadata
- command palette derived from command registry

## 11. Transport And Protocol

### 11.1 Near-Term Shape

The current HTTP JSON surface is sufficient for bootstrapping, but it should be treated as a temporary transport envelope around stronger domain contracts.

### 11.2 Target Shape

Move toward:

- protobuf-defined contracts in `protocol/proto`
- generated Rust and TypeScript types
- request and stream interfaces for viewport, jobs, events, and recompute updates
- backward-compatible versioning rules

### 11.3 Payload Families

Core payload groups should include:

- bootstrap and session
- document summary and tabs
- object tree
- properties and property groups
- command catalog
- task panel
- selection and preselection state
- viewport scene snapshot and deltas
- jobs and diagnostics
- history and evaluation markers

## 12. Persistence Model

Document persistence must cover both CAD data and application state.

Persisted categories:

- underlying CAD document representation
- AsterForge-side document metadata
- command history markers where safe
- dock and layout preferences
- active workbench and recent documents
- plugin compatibility metadata

The architecture should separate:

- CAD document save format
- UI session persistence
- diagnostic and job history retention

## 13. Import And Export

Initial supported formats:

- STEP
- STL
- OBJ
- DXF 2D

Import and export operations must run through the jobs subsystem and expose:

- queued state
- running stage
- progress text
- success or failure outcome
- resulting object bindings into the document graph

## 14. Performance Strategy

### 14.1 Performance Priorities

- avoid full-document recompute on every edit
- avoid full-scene rebuild on every viewport update
- keep interaction latency acceptable during large imports
- isolate expensive geometry and meshing work from UI responsiveness

### 14.2 Techniques

- dirty-set recompute
- scene diff emission
- geometry and tessellation caches
- workerized import and mesh preparation
- batched protocol updates
- backend-side throttling for noisy event surfaces

### 14.3 Large Assembly Targets

The system should be planned for:

- very large object counts
- high triangle counts
- 500MB-class source files
- partial visibility workflows
- selective property and tree hydration when full document expansion is too expensive

## 15. Testing Strategy

### 15.1 Backend Tests

- document DAG tests
- recompute invalidation tests
- command validation tests
- selection mode tests
- plugin contract tests
- import and export adapter tests

### 15.2 Frontend Tests

- shell composition tests
- task-panel workflow tests
- command palette interaction tests
- selection and hover state tests
- property and history rendering tests

### 15.3 Integration Tests

- Rust and TypeScript protocol compatibility tests
- bridge-backed document open and mutation flows
- rendering snapshot or golden-image tests
- regression tests for pad, pocket, suppression, rollback, and resume-history flows

## 16. Recommended Folder Evolution

```text
variants/asterforge/
  backend/
    crates/
      api-gateway/
      document-core/
      command-core/
      workbench-partdesign/
      workbench-sketcher/
      jobs-core/
      plugin-host/
  frontend/
    app/
      src/
        shell/
        workbenches/
        viewer/
        panels/
        protocol/
        stores/
  native/
    freecad-bridge/
  protocol/
    proto/
    schemas/
  docs/
    adr/
    ASTERFORGE_ARCHITECTURE_SPEC.md
```

The important structural change is the separation of reusable backend domain crates from the gateway transport crate.

## 17. Phased Roadmap

### Phase 1: Domain Ownership Baseline

- generate types from protocol definitions
- split document and command logic out of the gateway
- formalize document graph and history state
- replace route-level heuristics with backend domain services

### Phase 2: Recompute And Sketcher Core

- implement Rust-owned invalidation and recompute scheduling
- formalize sketch data model and constraint graph
- improve feature definitions for pad, pocket, revolve, and sweep readiness

### Phase 3: Viewer And Large-Model Pipeline

- move from coarse snapshots to scene deltas
- add geometry and tessellation caching
- add progressive import and viewer hydration

### Phase 4: Plugin And Workbench Contracts

- publish versioned workbench manifest format
- support plugin-loaded commands and panels
- add adapter interfaces for simulation and external solvers

### Phase 5: Geometry Migration Options

- measure which bridge-backed responsibilities should remain native
- move mesh prep, selectors, or solver layers into Rust where beneficial
- evaluate WASM packaging for shared geometry and solver modules

## 18. Immediate Next Implementation Slices

The next engineering slices should be tackled in this order:

1. extract a `document-core` crate with document graph, history, and evaluation state
2. extract a `command-core` crate with registry, validation, and transaction boundaries
3. formalize protocol-generated types in Rust and TypeScript
4. define a `workbench-sketcher` domain model and constraint graph
5. define scene snapshot and scene-delta contracts for the viewer

## 19. Acceptance Criteria For This Spec

This architecture is being followed correctly when:

1. document and recompute semantics are converging into Rust-owned crates
2. frontend logic is mostly rendering and interaction composition rather than hidden business logic
3. bridge-backed operations are exposed through explicit service boundaries
4. new workbench behavior is added through versioned domain and protocol contracts
5. performance work targets recompute slicing, scene deltas, and job isolation instead of ad hoc UI patching