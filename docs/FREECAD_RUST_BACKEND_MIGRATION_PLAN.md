# FreeCAD Rust Backend Migration Plan

Status: proposed execution plan grounded in the repository state as of 2026-05-04

## Companion Documents

- `docs/FREECAD_RUST_BACKEND_OWNERSHIP_MATRIX.md`
- `docs/FREECAD_NATIVE_BRIDGE_CONTRACT.md`
- `docs/FREECAD_RUST_PHASE1_EXECUTION_BACKLOG.md`

## 1. Executive Position

The current repository is not in a state where a literal full rewrite of the entire backend into Rust is the correct next move.

That approach would force the project to replace, in one program, all of the following at once:

- the `src/App` document and property model
- the `src/Mod/Part`, `src/Mod/PartDesign`, and `src/Mod/Sketcher` geometry and parametric execution layers
- the Python automation and plugin surface
- large parts of import and export compatibility
- Qt-era GUI coupling that still leaks into backend behavior

That is not a modernization program. It is a multi-year kernel rewrite with a high probability of stalling before product parity.

The viable path is stricter and more realistic:

- make Rust the authoritative application backend and orchestration layer
- isolate existing C++ and Python logic behind explicit worker and bridge boundaries
- reimplement selected backend subsystems in Rust where the payoff is high and the compatibility risk is acceptable
- keep OCCT-heavy and solver-heavy native logic until replacement candidates are proven by tests and benchmarks

If the product goal is to become a robust modern CAD and CAM platform that can compete with commercial incumbents, the success criteria are not language purity. The success criteria are:

- deterministic workflows
- reliable crash containment
- strong large-model performance
- standards-aware import, export, PMI, and manufacturing data paths
- testable command, document, and recompute behavior
- disciplined extension and automation boundaries

Rust is the right control plane for that. It is not the right first target for rewriting every native modeling subsystem.

## 2. Actual Repository State

### 2.1 Legacy Production Backend Still Dominates

The main product backend remains mostly C++ and Python under `src`.

Primary backend-heavy surfaces still live here:

- `src/App`
- `src/Base`
- `src/Gui`
- `src/Mod/Part`
- `src/Mod/PartDesign`
- `src/Mod/Sketcher`
- `src/Mod/Assembly`
- `src/Mod/Draft`
- `src/Mod/TechDraw`
- `src/Mod/Fem`
- `src/Mod/CAM`
- `src/Mod/Spreadsheet`
- `src/Mod/Material`
- `src/Mod/Import`
- `src/Mod/AddonManager`

This means the shipping backend is still coupled to:

- OCCT-backed native geometry execution
- FreeCAD document and property semantics in C++
- Python macro, plugin, and workbench conventions
- Qt-era behavior assumptions, especially around selection, tasks, and command routing

### 2.2 Rust Exists, But In A Focused Variant Lane

There is already a Rust workspace in `variants/asterforge`.

Current workspace members:

- `variants/asterforge/backend/crates/api-gateway`
- `variants/asterforge/backend/crates/command-core`
- `variants/asterforge/backend/crates/document-core`
- `variants/asterforge/backend/crates/step-core`
- `variants/asterforge/backend/crates/protocol-types`
- `variants/asterforge/native/freecad-bridge`

This is important because it proves the repository has already chosen a Rust-first backend direction for the new shell architecture.

### 2.3 What The Existing Rust Code Actually Does

The current Rust implementation is real, but still partial.

Observed backend capabilities:

- `api-gateway` boots an Axum service and exposes routes for bootstrap, open document, selection, shell snapshot, tree, properties, commands, history, diagnostics, jobs, events, task panel, and STEP scene data
- `command_runtime` already owns a backend command execution path for shell and STEP-oriented actions, feature-history actions, undo and redo framing, and extension inventory staging
- `step-core` is a substantive early subsystem with memory-mapped access and STEP-oriented parsing support
- `protocol-types` provides the shared contract shape between frontend and backend

Observed backend gaps:

- `command-core` is still essentially a placeholder crate
- `document-core` is still essentially a placeholder crate
- `native/freecad-bridge` is present, but not yet a mature bridge to the full FreeCAD and OCCT execution surface
- the Rust backend is not yet the production owner of document persistence, recompute scheduling, geometry execution, plugin compatibility, or Python automation

### 2.4 Existing Repository Strategy Already Points In The Right Direction

The existing architecture documents already reject a full Rust rewrite first.

That position is consistent across:

- `docs/FREECAD_REACT_RUST_VARIANT_PLAN.md`
- `docs/FREECAD_EXECUTION_ROADMAP.md`
- `docs/architecture/ADR-0008-react-rust-freecad-variant-architecture.md`
- `variants/asterforge/docs/ASTERFORGE_ARCHITECTURE_SPEC.md`
- `docs/QT_TO_TYPESCRIPT_FRONTEND_MIGRATION_PLAN.md`

The repo is therefore not missing strategy. It is missing a sharper backend execution plan that converts that strategy into a bounded Rust migration program.

## 3. Required Architecture Boundary

The backend target should be this:

- Rust owns application semantics, orchestration, command validation, sessions, jobs, events, persistence coordination, recompute scheduling, extension policy, and transport contracts
- native C++ owns OCCT-heavy geometry execution, legacy document compatibility hooks, mature solver pathways, and import and export paths that are still cheaper to preserve than to rewrite
- Python remains available through controlled backend-hosted workers for compatibility, but not as the primary authority for core product workflows

In practical terms, that means:

- React or TypeScript never talks directly to legacy native code
- all frontend mutations must go through Rust commands
- native operations must be wrapped behind explicit bridge contracts
- bridge contracts must be narrow, versioned, and testable
- Rust must own the canonical document session model even when underlying geometry execution is still delegated

## 4. Backend Ownership Model

### 4.1 Rust Must Own Early

These lanes are good Rust targets in the near term because they improve reliability and architecture without forcing a kernel rewrite.

- application boot and session lifecycle
- command registry, enablement, validation, and dispatch
- event stream, logging, diagnostics, and audit history
- background jobs and worker supervision
- selection, preselection, and shell-state authority
- document registry and document metadata indexing
- persistence coordination and recovery policy
- extension inventory, trust policy, and compatibility tiering
- API gateway and protocol versioning
- FCStd packaging coordination and migration bookkeeping around native serialization
- import and export orchestration pipelines around native or external codecs
- standards-first data services such as STEP, AP242, EXPRESS, PMI, and future manufacturing interchange control planes
- spreadsheet, materials, preferences, and similar non-geometry-heavy product services

### 4.2 Keep Native Behind The Bridge For Now

These lanes should remain native until bridge contracts, benchmarks, and regression suites are mature.

- OCCT shape creation and mutation
- Part booleans, fillet, chamfer, loft, sweep, and offset operations
- PartDesign feature execution for the current production path
- Sketcher constraint solving and mature geometry solving behavior
- tessellation derived directly from native shape state where compatibility matters
- legacy file import and export that already depends on existing native libraries

### 4.3 Rewrite In Rust Only After Boundaries Stabilize

These lanes are plausible future Rust rewrite candidates, but only after the backend platform is already authoritative.

- assembly orchestration and constraint-state management
- spreadsheet engine and expression evaluation surface that is independent of legacy document internals
- material library, catalog, and assignment services
- CAM job planning, tool library management, and post-processing orchestration
- workflow-level manufacturing state and standards adapters
- selective document graph and recompute services where Rust can own invalidation even if execution remains bridge-backed

## 5. Migration Principles

1. Migrate by authority, not by source line count.
2. Make Rust authoritative before making Rust complete.
3. Do not rewrite geometry code just because it is old C++.
4. Move non-geometry application services first.
5. Force every backend mutation through versioned Rust commands.
6. Turn Python from an ambient dependency into a supervised compatibility lane.
7. Treat crash containment as a product feature.
8. Tie every migration slice to workflow, compatibility, and performance gates.

## 6. Program Phases

### Phase 0: Freeze The Boundary

Objective:

- define the target Rust authority boundary and stop new frontend or GUI work from bypassing it

Work:

- publish bridge contract rules for document, geometry, import/export, and solver calls
- inventory native entry points required for P0 workflows: open, save, recompute, Part, PartDesign, Sketcher, Import, Measure, and STEP
- classify all backend modules as `Rust-own`, `Bridge-now`, or `Later-candidate`
- define canonical command and event taxonomies
- define failure domains for in-process versus worker-process native execution

Exit criteria:

- the team can point to one approved backend boundary document and one approved bridge contract list
- no new migrated UI surface mutates product state without a Rust command path

### Phase 1: Make Rust The Product Control Plane

Objective:

- promote Rust from a shell-support prototype into the authoritative application backend for supported workflows

Work:

- harden `api-gateway` into a production service boundary
- implement real `command-core` and `document-core`
- move session lifecycle, document registry, selection state, command dispatch, and event delivery into Rust-owned crates
- add structured job supervision and worker lifecycle control
- add persistent crash-safe logs and command audit trails
- add protocol compatibility tests between Rust and TypeScript

Exit criteria:

- open, save, selection, command execution, history, diagnostics, and shell-state flows are Rust-authoritative for supported workflows
- the frontend no longer depends on legacy GUI routing for those flows

### Phase 2: Workerize Native Execution

Objective:

- isolate the unstable and expensive native pathways so backend failures are containable

Work:

- evolve `native/freecad-bridge` into explicit worker-facing bridge contracts
- decide where in-process FFI is acceptable and where out-of-process workers are mandatory
- add timeout, cancellation, and restart policy for native operations
- separate document extraction, geometry execution, tessellation, and import/export worker roles where needed
- add bridge integration tests against golden FCStd and STEP fixtures

Exit criteria:

- the backend can survive a native worker failure without corrupting the full app session
- native execution paths have measurable latency, retry, and crash-reporting behavior

### Phase 3: Rust Owns Document Semantics Above Native Execution

Objective:

- move the document model, transaction framing, and recompute planning into Rust even while native execution still performs many operations

Work:

- implement a Rust document graph and stable object identity model
- make Rust the owner of transaction boundaries, undo/redo framing, and dirty-state policy
- implement dependency tracking and invalidation planning in Rust
- translate native results back into Rust-owned state deltas instead of leaking native document mutations directly upward
- introduce FCStd metadata versioning and migration bookkeeping around the native serializer

Exit criteria:

- Rust is the canonical owner of document session state for supported workflows
- recompute planning is no longer an implicit side effect of GUI or native entry points

### Phase 4: Migrate High-Leverage Non-Geometry Subsystems

Objective:

- replace backend areas where Rust gives immediate product value without destabilizing the geometry kernel

Priority targets:

- material and catalog services
- spreadsheet and expression-authoring services where legacy coupling can be narrowed
- preferences, settings, and policy services
- addon inventory, trust, compatibility, and installation orchestration
- macro execution brokerage and compatibility reporting
- CAM orchestration services around jobs, tools, setups, posts, and machine metadata
- standards services for STEP, AP242, PMI, GD&T, drawing profiles, and manufacturing handoff

Exit criteria:

- these services are backend-owned by Rust and no longer depend on Qt-era state assumptions

### Phase 5: Rebuild Plugin And Python Compatibility On Purpose

Objective:

- stop treating Python and plugins as ambient runtime behavior and start treating them as explicit compatibility products

Work:

- create plugin manifest and capability metadata
- build a Python worker host with controlled API exposure
- define supported compatibility tiers for macros, legacy workbenches, and trusted extensions
- surface compatibility health, trust, and failures through backend-owned diagnostics
- replace direct Qt or PySide assumptions with backend or web-safe compatibility contracts

Exit criteria:

- strategic automation and plugin workflows operate through supervised compatibility lanes instead of direct legacy GUI coupling

### Phase 6: Selective Rust Reimplementation Of Chosen Domains

Objective:

- rewrite only the backend domains where the architecture, tests, and benchmarks prove the rewrite is worth it

Good candidates:

- assembly state and constraint orchestration
- spreadsheet-like data systems
- materials and engineering data catalogs
- manufacturing planning and post workflow services
- import and standards adapters that do not require OCCT to remain authoritative
- future recompute and dependency services beyond the native graph

Conditional candidates only after heavy evidence:

- sketch solving
- selected PartDesign features
- selected geometry-preparation or meshing pipelines

Exit criteria:

- each rewrite candidate demonstrates better correctness, observability, or performance than the bridge-backed version on agreed benchmarks

## 7. Workbench And Domain Priority

### P0 Product Backbone

- document lifecycle
- command system
- Part and PartDesign workflow orchestration
- Sketcher editing loop coordination
- selection, history, diagnostics, jobs
- import and export baseline
- AddonManager and macro compatibility foundation

### P1 Competitive Workflow Expansion

- Assembly
- Draft
- TechDraw
- Spreadsheet
- Material
- Measure
- CAM workflow orchestration

### P2 Specialist And Enterprise Expansion

- FEM orchestration and solver management
- BIM and IFC-facing services
- Mesh, Surface, ReverseEngineering, Robot, and specialist tools
- PDM and regulated-traceability services

## 8. Performance Program

If the goal is to compete with strong commercial CAD and CAM tools, performance work must be a first-class backend stream, not a cleanup step.

Backend performance priorities:

- worker-process isolation for unstable native code
- background recompute scheduling and dependency slicing
- selective parallelism in Rust-owned planning and parsing layers
- lazy document and scene projection
- streaming scene and diagnostic payloads instead of full refresh churn
- STEP and standards parsing that scales with memory-mapped and incremental access patterns
- measurable large-assembly budgets for open, recompute, selection, and view updates

Required performance gates:

- cold start budget
- open-document budget by file type and model size
- recompute budget by representative part history depth
- assembly interaction budget
- import and export roundtrip budget
- worker crash recovery budget

## 9. Quality Gates

Every phase should ship only behind explicit verification.

Required test families:

- Rust unit tests for command, document, and event logic
- bridge integration tests against native workers
- protocol compatibility tests between Rust and TypeScript
- golden workflow tests for Part, PartDesign, Sketcher, import/export, and plugin compatibility
- regression fixtures for FCStd and STEP roundtrips
- performance labs for large-model and repeated-command workloads
- fault-injection tests for worker crash, timeout, bad geometry, and Python failure cases

## 10. Business Reality Check

Rust alone will not make the product beat commercial competitors.

To become a credible superior alternative, the program must also deliver:

- a tighter daily-use workflow than current FreeCAD
- robust assembly and manufacturing flows
- predictable standards support
- reliable plugin and automation compatibility
- strong documentation and onboarding
- measurable quality and performance discipline

The correct message for the program is therefore not:

- rewrite the whole backend into Rust

The correct message is:

- build a Rust-authoritative backend platform, isolate native compatibility aggressively, and selectively replace the legacy backend where the evidence shows real product advantage

## 11. Immediate Next Steps

1. turn `command-core` and `document-core` into real ownership crates rather than placeholders
2. define the first production bridge contract for document lifecycle, recompute, geometry execution, and tessellation
3. make `api-gateway` the required authority for all migrated shell mutations
4. publish a workbench-by-workbench `Rust-own` versus `Bridge-now` matrix
5. establish benchmark fixtures for P0 workflows before selecting any large rewrite candidate

Execution status:

- item 2 is now captured in `docs/FREECAD_NATIVE_BRIDGE_CONTRACT.md`
- item 4 is now captured in `docs/FREECAD_RUST_BACKEND_OWNERSHIP_MATRIX.md`
- item 1 is now broken into actionable work in `docs/FREECAD_RUST_PHASE1_EXECUTION_BACKLOG.md`