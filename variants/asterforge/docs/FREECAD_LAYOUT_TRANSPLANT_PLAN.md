# AsterForge FreeCAD React Variant Master Prompt

Status: layout parity is already established in the React shell as of 2026-04-20. The next step is no longer a shell-only transplant. The next step is to drive AsterForge as a production-grade, parametric FreeCAD reimplementation with Rust-owned semantics, a React desktop shell, and a native FreeCAD bridge that can later evolve toward a dedicated kernel.

## Purpose

Use the following prompt when generating architecture, implementation slices, or planning documents for the AsterForge variant. It is tailored to the code already present under `variants/asterforge` and is intentionally stricter than a generic React CAD prompt.

This prompt assumes:

- React plus TypeScript frontend in `frontend/app`
- Rust backend and service ownership in `backend/crates/api-gateway`
- explicit protocol contracts in `protocol/proto` and `protocol/schemas`
- native integration boundary in `native/freecad-bridge`
- FreeCAD-style desktop shell parity as a requirement, not the end goal
- long-term migration path from bridge-backed geometry toward a stronger Rust and WASM geometry core

## Master Prompt

Act as a senior CAD software architect, computational geometry engineer, Rust systems engineer, and React frontend systems engineer.

Your task is to design and generate a production-grade, web-first and desktop-packaged CAD system for the AsterForge FreeCAD variant. The system is inspired by FreeCAD, but reimplemented with a modern React plus Rust architecture, backend-owned semantics, protocol-driven boundaries, and an extensible multi-backend system.

Do not design a toy viewer. Design a long-lived parametric CAD platform with workbench extensibility, native bridge integration, and a migration path from FreeCAD-backed services toward dedicated geometry infrastructure.

### Goal

Create a parametric CAD application with:

- feature-based modeling similar to FreeCAD, Fusion 360, and Onshape
- multi-workbench architecture
- real-time, high-performance 3D rendering
- Rust-owned document and command semantics
- protocol-driven frontend and backend boundaries
- extensible plugin and workbench model for CAD, CAM, CFD, electronics, and digital-twin workflows

### Target AsterForge Stack

Frontend:

- React plus TypeScript
- Zustand for state management
- Vite for build and development workflow
- Tailwind for styling
- Three.js for current rendering, with scene abstraction that could support Babylon.js later if required
- WebGL required, WebGPU optional
- desktop shell compatibility with the current Tauri target

Core application and service layer:

- Rust as the authoritative domain and command layer
- `backend/crates/api-gateway` as the initial service boundary
- explicit document, selection, property, command, job, and viewport payload contracts
- streaming-friendly architecture for future gRPC or websocket transport

Native and geometry layer:

- near-term native FreeCAD bridge in `native/freecad-bridge`
- near-term geometry authority may remain bridge-backed for document extraction and scene generation
- medium-term geometry acceleration in Rust for meshing, constraint solving, and selective recompute
- long-term option for WASM or Rust-native geometry kernels, including OpenCascade-backed services or a dedicated Rust kernel

Backend and compute execution:

- local Rust service layer first
- websocket or streaming transport for heavy updates and long operations
- worker-based job supervision for expensive recompute, import, meshing, and simulation steps
- clear separation between UI orchestration, document semantics, geometry execution, and native bridge operations

### Architecture Requirements

Design a layered system with strict ownership boundaries.

1. Document model layer

- parametric feature tree
- dependency graph as a DAG
- recompute engine with invalidation tracking
- undo and redo model
- rollback, suppression, and dependency-aware inactive states
- stable object identity and reference model across edits

2. Command and workflow layer

- backend-owned command registry
- argument schemas and task-panel metadata
- workbench-aware enablement rules
- selection-sensitive command resolution
- transaction boundaries for document mutation

3. Geometry layer

- solid modeling and B-Rep ownership model
- sketch entities and constraint graph
- boolean operations
- meshing pipeline for viewport and export
- bridge-backed extraction now, kernel abstraction preserved for future replacement

4. Rendering layer

- scene graph abstraction independent from raw Three.js component trees
- selection and preselection system for faces, edges, vertices, sketches, bodies, and features
- GPU-aware large-model rendering
- incremental scene updates instead of full reloads
- support strategy for large assemblies and large STEP or STL imports

5. UI layer

- FreeCAD-style desktop shell with menu bar, toolbar deck, document tabs, combo view, dominant central viewport, bottom utility dock, and status bar
- workbench-scoped panels and tool groups
- property editor and model tree
- task panel and workflow guidance
- command palette driven by backend metadata

### Workbench System

Implement modular workbenches similar to FreeCAD, but backed by versioned Rust and protocol contracts.

Initial workbench targets:

- Part Design
- Sketcher
- Assembly
- Mesh
- TechDraw
- CFD with multi-solver readiness for OpenFOAM, FluidX3D, Elmer, and future external engines

Each workbench must be able to:

- register tools and command groups
- extend menus, toolbars, task panels, and dock content
- add domain data types and property groups
- contribute validation rules and workflow stages
- expose job types and simulation hooks where needed

### Sketcher System

Define a fully parametric sketch system as a first-class subsystem, not a drawing overlay.

Geometry primitives:

- line
- arc
- circle
- spline
- point and construction geometry support

Constraints:

- coincident
- parallel
- perpendicular
- tangent
- horizontal and vertical
- distance
- angle
- radius and diameter
- symmetry and equality

Solver requirements:

- incremental solving
- conflict detection and diagnosis
- under-constrained and over-constrained state reporting
- editable constraint graph
- migration path to Rust-native solving with optional WASM packaging later

### Parametric Modeling

Implement feature-based modeling with explicit dependency tracking.

Initial feature set:

- extrude or pad
- pocket
- revolve
- loft
- sweep
- fillet
- chamfer
- pattern and mirror readiness

Each feature must:

- reference prior geometry through stable selectors
- remain editable through command arguments and property metadata
- trigger partial recompute where possible
- expose suppression, rollback, and dependency diagnostics

### Performance Requirements

- handle large assemblies and high-object-count scenes
- prefer lazy recomputation over eager full-document rebuilds
- support incremental updates for tree, properties, viewport, and task panels
- use worker threads, Rust concurrency, and future WASM parallelism where appropriate
- cache geometry, tessellation, and selection acceleration structures
- define a strategy for 500MB-class import scenarios without freezing the UI

### Extensibility

Design a plugin and extension system with stable versioned contracts.

The API surface must cover:

- workbench registration
- command registration
- task-panel contributions
- property and document type extensions
- geometry and simulation service hooks
- import and export adapters

Plugins must be dynamically loadable where safe, versioned, and isolated from core document corruption risks.

### Data Interchange

Support at least:

- STEP
- STL
- OBJ
- DXF for 2D

Include:

- import pipeline
- export pipeline
- conversion into internal document and geometry representations
- background job execution for heavy imports and exports

### Advanced Features

- future-ready multi-user collaboration model
- digital-twin integration hooks for live telemetry and embedded systems
- live data overlays on geometry and assemblies
- solver and simulation integration points
- enterprise-ready supervision for long-running jobs and external compute adapters

### Testing Strategy

Use a deterministic, professional CAD-style testing strategy.

Include:

- deterministic geometry tests
- document recompute and dependency tests
- protocol compatibility tests between Rust and TypeScript layers
- UI automation tests for workflow-critical panels
- rendering snapshot or golden-image tests
- import and export regression tests

### Output Format

Return a highly structured, implementation-ready response with:

1. full system architecture with clear layer boundaries
2. folder structure aligned to the current AsterForge workspace
3. key module definitions with code for document model, feature system, sketcher base, command registry, and 3D viewer boundary
4. example workbench implementation using the current Rust-owned command model
5. example plugin or extension contract
6. performance strategy for large models and long-running jobs
7. staged roadmap from current bridge-backed implementation to a stronger native geometry platform

### Important Constraints

- do not produce a toy CAD viewer
- do not frontload cosmetic UI work ahead of document and geometry correctness
- keep Rust as the authority for domain semantics, command enablement, workflow state, and recompute triggers
- preserve protocol boundaries so frontend code does not become the hidden domain layer
- keep FreeCAD desktop shell parity, but treat it as an interaction requirement rather than the whole architecture
- design for maintainability over a ten-year horizon
- favor correctness, stable ownership, and migration safety over novelty

### Inspiration

Take conceptual inspiration from:

- FreeCAD
- Autodesk Fusion 360
- Onshape
- Siemens NX

Do not copy their architecture blindly. Modernize it for AsterForge's Rust-first, protocol-driven, React-shell design.

## What This Replaces

The older shell-transplant framing is now a subproblem inside the UI layer. The shell still needs to preserve these FreeCAD interaction patterns:

- classic menu bar structure
- dense toolbar rows
- top document tabs
- left combo view with model and tasks
- central viewport dominance
- bottom utility dock with report, Python console, jobs, diagnostics, history, and commands
- live status bar feedback

Those requirements remain valid, but they are no longer the primary architecture target.

## Recommended Prompt Chain

Do not ask for the entire system implementation in one step. Use this prompt first for architecture, then split implementation by subsystem.

Recommended sequence:

1. architecture and folder plan for the full AsterForge variant
2. document DAG plus recompute and undo model
3. command registry plus workbench extension contracts
4. sketch constraint graph and solver strategy
5. viewport scene graph and large-model rendering path
6. bridge-backed geometry extraction to protocol payload pipeline
7. import, export, and simulation adapter surfaces

## Immediate Acceptance Criteria

This document is correctly applied when future design and generation work for AsterForge:

1. treats parametric modeling and document recompute as the core problem
2. keeps Rust as the authoritative domain layer
3. preserves protocol and bridge boundaries
4. treats the FreeCAD shell as a required interaction surface, not the product definition
5. plans for workbench extensibility, solver integration, and large-model handling from the start
