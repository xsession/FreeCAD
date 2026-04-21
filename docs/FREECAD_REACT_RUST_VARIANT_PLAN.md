# FreeCAD React/Rust Variant Plan

## 1. Executive Summary

This document proposes a practical plan for building a new FreeCAD-derived variant with a strict frontend/backend separation and an eventual mandate to clone the complete FreeCAD feature set, bundled workbenches, and strategically important plugin ecosystem:

- Frontend: React
- Backend: Rust
- Native CAD/geometry bridge: FreeCAD/OCCT/C++ retained behind a stable service boundary

The critical design choice is this:

Do not rewrite FreeCAD's geometric and parametric core first.

A full rewrite of OCCT-facing modeling, PartDesign, Sketcher solving, topology naming, file compatibility, import/export, and Python extensibility in Rust would turn the project into a multi-year research program with very high failure risk. The viable path is:

1. Separate UI from core behavior.
2. Move orchestration, sessions, commands, persistence coordination, job execution, plugin management, and API boundaries into Rust.
3. Keep existing C++ FreeCAD/OCCT logic accessible through a controlled native bridge.
4. Build a modern React client on top of explicit backend APIs.
5. Replace or reimplement selected subsystems in Rust only after boundaries and tests are stable.

The end state is not "React calling legacy C++ directly." The end state is:

- React owns presentation and interaction.
- Rust owns application orchestration and external API surface.
- Native C++ libraries are isolated workers/adapters invoked by Rust.

For the full-clone version of the program, the long-term destination is even stronger:

- every major FreeCAD user workflow is available through the React UI
- every core document, property, command, recompute, and automation concept is backend-owned by Rust
- every bundled workbench is either fully reimplemented in Rust/React or hosted through a compatibility layer
- major third-party plugins/workbenches are brought forward through compatibility adapters, then migrated to explicit frontend/backend extension APIs
- native C++ remains only where it is the most practical implementation of geometry kernels, solver logic, or legacy compatibility

---

## 2. Product Vision

### 2.1 Goal

Create a modern engineering desktop application derived from FreeCAD with:

- a responsive React-based interface
- a service-oriented Rust backend
- explicit APIs between UI and modeling core
- improved reliability, testability, and future extensibility
- a path toward cloud, remote, and collaborative use later

### 2.2 What This Variant Should Improve

Compared with current FreeCAD, the variant should improve:

- UI consistency
- startup and interaction architecture
- separation of concerns
- backend testability
- command and workflow determinism
- plugin isolation
- remote automation potential
- crash containment around native CAD kernels

### 2.3 What This Variant Must Preserve

The variant must preserve:

- parametric document workflows
- Part / PartDesign / Sketcher capability
- FreeCAD document compatibility where practical
- Python automation compatibility in some form
- access to OCCT-based import/export and modeling
- extensibility for engineering modules

### 2.4 Non-Goals

Not in the initial program:

- rewriting OCCT in Rust
- rewriting all FreeCAD workbenches at once as a single first milestone
- browser-only CAD as the first milestone
- replacing all Python support in phase 1
- full cloud collaboration in MVP
- complete feature parity with every FreeCAD workbench before first release

---

## 3. Strategic Architecture Decision

### 3.1 Required Separation

The application will be split into three major layers:

1. React frontend
2. Rust backend platform
3. Native geometry/modeling bridge

### 3.2 Recommended Runtime Topology

Use a desktop shell with separate frontend and backend processes.

Recommended structure:

- React SPA for UI
- Tauri shell for desktop packaging and native desktop integration
- Rust backend service running as a separate local process or embedded managed service
- Native bridge workers for FreeCAD/OCCT operations

This gives you:

- true frontend/backend separation
- a modern web UI stack
- native desktop capabilities without Electron overhead
- Rust as the control layer
- future ability to move backend remote without rewriting UI

### 3.3 Why Not a Pure Browser App First

A pure browser app is attractive but premature because:

- desktop CAD needs filesystem integration
- large mesh/model transfer needs local performance tuning
- native kernel failures need containment
- plugin and Python compatibility are simpler in desktop-first mode
- 3D interaction, drag/drop, and window integration are easier to stabilize in a desktop shell first

Desktop-first, remote-capable later is the correct sequence.

---

## 4. Target System Architecture

## 4.1 High-Level Diagram

```text
+---------------------------------------------------------+
|                     React Frontend                       |
|  - App shell                                             |
|  - Workbench UI                                          |
|  - Tree, property panel, task panels                     |
|  - 3D viewport controls                                  |
|  - command palette, notifications, settings              |
+-----------------------------+---------------------------+
                              |
                     gRPC / WebSocket / IPC
                              |
+-----------------------------v---------------------------+
|                     Rust Backend Core                    |
|  - session manager                                       |
|  - document service                                      |
|  - command bus                                           |
|  - transaction/undo orchestration                        |
|  - workspace/project service                             |
|  - plugin manager                                        |
|  - job scheduler                                          |
|  - auth/collab stubs for future remote mode              |
|  - API gateway                                           |
+------------------+------------------+-------------------+
                   |                  | 
                   |                  |
     +-------------v----+   +--------v----------------+
     | Native CAD Bridge |   | Rendering/Geometry     |
     | C ABI / FFI       |   | Translation Services   |
     | FreeCAD/OCCT      |   | tessellation, picking  |
     +-------------+----+   +-------------------------+
                   |
         +---------v----------------------------------+
         | Existing FreeCAD / OCCT / Python modules   |
         | Sketcher, PartDesign, Part, import/export  |
         +--------------------------------------------+
```

## 4.2 Separation of Responsibilities

### React frontend owns

- layout
- visual components
- state presentation
- viewport interaction model
- keyboard/mouse binding presentation layer
- tree and property rendering
- task/workflow wizards
- notifications and progress UI
- local UI cache
- optimistic interaction where safe

### Rust backend owns

- source of truth for active session state
- document lifecycle
- command validation and dispatch
- undo/redo boundaries
- long-running job coordination
- API versioning
- persistence orchestration
- plugin loading policy
- Python execution policy
- native process supervision
- crash recovery and restart

### Native bridge owns

- geometry creation and mutation
- topological naming logic already implemented in FreeCAD
- feature recompute execution
- document serialization compatibility hooks
- import/export to CAD formats
- OCCT and solver-specific behavior

---

## 5. Technology Stack

## 5.1 Frontend

Recommended stack:

- React 19+
- TypeScript
- Vite
- Zustand or Redux Toolkit for client state slices
- React Query or TanStack Query for backend data synchronization
- react-three-fiber for viewport integration if custom WebGL path is chosen
- three.js for scene rendering and interaction helpers
- Radix UI or Ariakit for primitives
- Tailwind or CSS Modules with design tokens
- Tauri frontend bridge for desktop shell integration

### Why React

React gives:

- strong component reuse
- ecosystem maturity
- fast UI iteration
- rich developer tooling
- compatibility with Tauri
- clear separation between local UI state and backend state

## 5.2 Backend

Recommended Rust stack:

- Rust stable
- Tokio async runtime
- tonic for gRPC
- axum for internal admin/debug HTTP if needed
- serde for JSON/proto conversion helpers
- prost for protobuf generation
- tracing for structured logs
- sqlx or rusqlite if local metadata DB is needed
- thiserror / anyhow for error propagation
- parking_lot for concurrency primitives where necessary

## 5.3 Native Bridge

Recommended approach:

- define a thin C ABI around selected FreeCAD capabilities
- load bridge from Rust using FFI or run it as a worker process
- prefer worker process for crash isolation

Preferred long-term pattern:

- Rust backend talks to native worker over IPC/gRPC/shared memory
- not direct in-process FFI for everything

Reason:

OCCT and legacy C++ paths can crash. If they live in-process with Rust backend, the whole app dies. Worker isolation is safer.

## 5.4 Desktop Shell

Recommended:

- Tauri for production shell

Reason:

- Rust-native ecosystem
- lower memory overhead than Electron
- good OS integration
- aligns with Rust backend direction

---

## 6. Product Modes

## 6.1 MVP Mode

Single-user desktop app.

- local backend process
- local native worker process
- local project files
- no collaboration
- no remote compute

## 6.2 Phase 2 Mode

Local-first with optional remote backend.

- UI unchanged
- backend can run out-of-process locally or remotely
- rendering remains local
- background compute can be offloaded

## 6.3 Phase 3 Mode

Multi-user or service-backed engineering platform.

- versioned backend APIs
- session persistence service
- collaboration/event streaming
- shared model review mode

---

## 7. Recommended Repository Structure

Use a mono-repo with explicit subprojects.

```text
freecad-variant/
  frontend/
    app/
    packages/
      ui/
      viewport/
      cad-client/
  backend/
    crates/
      api-gateway/
      session-core/
      document-service/
      command-service/
      plugin-service/
      worker-supervisor/
      fcstd-service/
      geometry-cache/
  native/
    freecad-bridge/
    occt-worker/
    python-worker/
  protocol/
    proto/
    schemas/
  docs/
    adr/
    api/
    migration/
  tools/
  fixtures/
  integration-tests/
```

If staying inside current FreeCAD repo initially, use:

```text
FreeCAD/
  frontend/
  backend/
  native/
  protocol/
  docs/variant/
```

---

## 8. Domain Model Boundaries

## 8.1 Backend Domain Concepts

Rust backend should define stable application concepts independent of legacy GUI classes.

Core domains:

- Session
- Workspace
- Document
- Object
- Feature
- Sketch
- Body
- Part
- Assembly
- ViewState
- Selection
- Command
- Transaction
- Job
- Resource
- Plugin

## 8.2 Important Rule

Do not expose raw FreeCAD GUI concepts as your public API.

Avoid APIs like:

- "activateViewProviderX"
- "callWorkbenchCommandByString"
- "runGuiTaskPanel"

Instead expose domain commands like:

- CreateDocument
- CreateBody
- CreateSketchOnPlane
- RecomputeDocument
- UpdateProperty
- StartEditSession
- GenerateMeshPreview
- ExportStep

This prevents the React UI from becoming a thin remote-control for legacy GUI internals.

---

## 9. Communication Protocol

## 9.1 Recommended Protocol Mix

Use:

- gRPC for structured request/response and streaming events
- WebSocket only if needed for browser transport later
- shared-memory or file-backed transfer for huge mesh payloads if performance requires it

## 9.2 Protocol Domains

Separate APIs into services:

- SessionService
- DocumentService
- CommandService
- ViewportService
- PropertyService
- SelectionService
- JobService
- PluginService
- ImportExportService

## 9.3 Event Streams

Frontend should subscribe to backend events rather than polling.

Required streams:

- document changed
- object added/removed
- recompute started/progress/completed
- selection changed
- property changed
- task started/completed/failed
- backend warnings/errors
- worker crash/restart events

---

## 10. Frontend Architecture Plan

## 10.1 Frontend Modules

### Shell

- app window
- docking layout
- menus and command palette
- tabbed documents
- global notifications
- settings and theme

### Modeling Workspace UI

- model tree
- property inspector
- selection inspector
- task pane
- history/timeline panel
- constraints panel
- diagnostics panel

### Viewport UI Layer

- camera controls
- selection overlays
- transform gizmos
- sketch drawing interactions
- measurement overlay
- section cut overlay
- highlight and hover feedback

### Data/Command Client

- protobuf/gRPC client
- local cache of document tree and property state
- command queue
- event subscription manager

## 10.2 Frontend State Strategy

Split state into:

- server-sourced canonical state
- local UI interaction state
- viewport transient state

Canonical state examples:

- open documents
- objects
- properties
- backend task status
- selection model

Local state examples:

- panel open/closed state
- current tool widget settings
- viewport camera mode
- hover state
- drag gesture state

Do not mirror entire backend document state in ad hoc React component state.

## 10.3 Frontend Rendering Strategy

Use a client-rendered scene graph based on backend-provided tessellation and selection metadata.

The backend provides:

- tessellated meshes
- edge overlays
- B-Rep identifiers
- selection maps
- visibility layers
- material/color metadata
- exploded/section representations where needed

The frontend renders:

- shaded faces
- wire overlays
- highlights
- preselection state
- measurement/annotation UI

Important:

The frontend does not evaluate CAD topology rules. It renders what the backend publishes.

## 10.4 Sketcher UI Strategy

Do not attempt to reimplement all solver behavior in frontend.

Frontend responsibilities:

- gesture capture
- sketch tool modes
- live cursor previews
- constraint handles and visual guides
- dimension input UI

Backend responsibilities:

- actual sketch object mutation
- solver invocation
- final constraint state
- geometry consistency rules

For low-latency interaction, backend should support incremental preview commands.

---

## 11. Backend Architecture Plan

## 11.1 Core Rust Services

### Session Manager

Responsibilities:

- lifecycle of application sessions
- open documents registry
- worker allocation
- crash recovery state
- active document and context

### Document Service

Responsibilities:

- create/open/close documents
- object graph retrieval
- tree snapshots and diffs
- persistence orchestration
- import/export initiation

### Command Service

Responsibilities:

- validate commands
- route commands to workers
- create undoable transactions
- enforce preconditions
- emit domain events

### Property Service

Responsibilities:

- fetch property metadata
- update property values
- unit conversion and validation
- expression binding hooks

### Viewport Service

Responsibilities:

- tessellation requests
- visibility state
- section planes
- camera presets
- selection hit-test mediation

### Job Service

Responsibilities:

- recompute
- meshing
- export
- analysis preparation
- long-running task progress and cancellation

### Plugin Service

Responsibilities:

- plugin discovery
- version compatibility checks
- sandbox policy
- Python plugin host coordination

## 11.2 Worker Topology

Recommended workers:

- modeling worker
- import/export worker
n- python automation worker
- mesh/tessellation worker

Potential deployment:

- one worker per document session for isolation
- or pooled workers for stateless tasks like import/export

## 11.3 Error Model

All backend APIs should return structured errors with:

- code
- message
- user-safe message
- details
- retryability
- originating subsystem
- correlation ID

Example categories:

- invalid command
- invalid selection
- geometry failure
- import failure
- worker crash
- unsupported plugin
- persistence error

---

## 12. Native Bridge Strategy

## 12.1 Bridge Principles

The bridge must be:

- narrow
- explicit
- versioned
- testable
- isolated from UI

## 12.2 What Goes Through the Bridge First

Phase 1 bridge capabilities:

- open/save document
- list objects and metadata
- create basic objects
- create body/sketch/feature via stable commands
- update property values
- recompute document
- tessellate visible geometry
- run selection queries
- import/export standard formats

## 12.3 What Should Not Go Through the Bridge Initially

Avoid exposing:

- ad hoc GUI-only FreeCAD commands
- raw GUI selection objects
- widget-specific behaviors
- arbitrary Python execution without sandboxing
- unrestricted pointer-like handles

## 12.4 Worker Isolation Model

Preferred model:

- Rust launches native worker process
- worker loads FreeCAD native libraries
- communication over IPC
- worker can crash and be restarted without killing app shell

This is safer than direct FFI for a CAD system built on legacy native dependencies.

---

## 13. Rendering and Viewport Plan

## 13.1 Viewport Requirements

The React UI needs a serious viewport strategy. This is not a normal dashboard.

Requirements:

- million-triangle scale support
- edge + face rendering
- preselection highlight
- precise selection mapping
- sectioning
- transparency
- measurement overlay
- sketch edit overlay
- datum visibility control
- exploded views later

## 13.2 Recommended Rendering Approach

Phase 1:

- three.js / react-three-fiber
- backend tessellates shapes
- frontend renders meshes and polylines
- selection uses backend element IDs mapped into GPU pick buffers or CPU raycast metadata

Phase 2:

- optimize with binary mesh streams
- partial scene updates
- instancing for repeated parts
- LOD and streaming for large assemblies

## 13.3 Selection Model

Selection should be backend-canonical.

Flow:

1. frontend raycasts or GPU-picks approximate candidate
2. frontend sends candidate hit data to backend
3. backend resolves actual object/subelement identity
4. backend broadcasts canonical selection event
5. frontend renders highlight

This avoids diverging frontend selection logic from backend topology naming.

---

## 14. File Format and Persistence Plan

## 14.1 Initial Compatibility Strategy

Preserve FCStd compatibility initially.

Rust backend should not invent a new file format for MVP.

Instead:

- use native bridge for FCStd read/write
- add Rust-side metadata caches if useful
- build migration/versioning around the backend API, not an immediate format fork

## 14.2 Long-Term Persistence Strategy

Long-term, consider a layered persistence model:

- canonical engineering document persisted in compatible FCStd form
- derived caches stored separately
- UI layout/workspace state in Rust-managed JSON/SQLite metadata
- asset cache for tessellation and thumbnails

## 14.3 Save Semantics

Implement:

- explicit save transactions
- autosave snapshots
- crash recovery journals
- backend-level dirty state
- background thumbnail generation

---

## 15. Plugin and Python Compatibility Plan

## 15.1 Why Python Must Stay

FreeCAD’s Python ecosystem is strategic.

Removing it early would destroy one of the main reasons to build on FreeCAD instead of starting fresh.

## 15.2 Recommended Model

Keep Python in the backend only.

- React never runs Python directly.
- Rust manages Python worker lifecycle.
- Python plugins communicate through backend APIs.
- existing macro and workbench logic can be adapted gradually.

## 15.3 Plugin Layers

Define three extension layers:

### Frontend extensions

- add panels
- add commands
- add workspace tools
- add inspectors

### Backend Rust extensions

- add services
- add job types
- add import/export processors
- add workflow automation

### Python/native extensions

- adapt legacy FreeCAD automation
- feature generation
- advanced engineering module logic

## 15.4 Compatibility Strategy

Phase 1:

- compatibility subset for macros and scripts
- backend-hosted Python execution service

Phase 2:

- compatibility adapter for selected workbench logic
- event-based API instead of GUI-bound scripting

Phase 3:

- encourage migration from direct GUI automation to backend commands

---

## 16. Security and Stability Model

## 16.1 Crash Containment

Use process isolation for:

- native geometry worker
- Python automation worker
- potentially import/export worker

## 16.2 Trust Boundaries

Trusted:

- Rust backend core
- signed internal plugins

Less trusted:

- third-party Python macros/plugins
- imported geometry files
- custom script execution

## 16.3 Required Safeguards

- worker watchdogs
- structured crash dumps
- autosave before dangerous jobs
- timeouts and cancellation
- plugin capability declarations
- optional safe mode startup

---

## 17. UX and Workflow Migration Plan

## 17.1 First Workflows to Rebuild in React

Build these first:

1. open/save/start page
2. document tree and selection
3. property editor
4. PartDesign basic flow
5. sketch create/edit flow
6. viewport navigation and selection
7. undo/redo feedback

## 17.2 Workflows to Delay

Delay until backend boundaries stabilize:

- full Assembly UX redesign
- advanced FEM UI
- TechDraw redesign
- Python macro IDE
- PDM/collaboration

## 17.3 UI Architecture Rule

Do not copy current Qt screens one-to-one.

Use the separation to redesign flows around:

- explicit task state
- narrower side panels
- better property search/filtering
- command palette
- discoverable empty states
- consistent notifications/progress

---

## 18. Incremental Delivery Plan

## 18.1 Phase 0 - Architecture and Proofs

Duration: 6-10 weeks

Deliverables:

- protocol definitions
- Rust session skeleton
- native worker spike
- React shell spike
- document tree + property fetch prototype
- viewport prototype with backend-provided test meshes

Exit criteria:

- open a FreeCAD document via backend
- list objects in React UI
- render at least one model in React viewport
- update one property and recompute through backend

## 18.2 Phase 1 - Vertical Slice MVP

Duration: 3-5 months

Scope:

- desktop shell
- document open/save
- model tree
- property editor
- selection sync
- viewport render/highlight
- create body
- create sketch on plane
- basic PartDesign feature flow
- recompute and undo/redo

Exit criteria:

- user can create a simple parametric part end-to-end without Qt UI
- FCStd roundtrip works for supported feature subset
- crash in native worker does not kill whole app shell

## 18.3 Phase 2 - Modeling Expansion

Duration: 4-8 months

Scope:

- more sketch tools
- more Part / PartDesign features
- import/export workflows
- job progress UI
- richer property typing
- plugin host baseline
- Python automation service

Exit criteria:

- common mechanical part workflows are usable daily
- command/event model is stable
- integration tests cover main workflows

## 18.4 Phase 3 - Performance and Scale

Duration: 4-6 months

Scope:

- incremental scene updates
- mesh cache
- assembly scene instancing
- worker pooling
- partial recompute orchestration where safe
- diagnostics tooling

Exit criteria:

- large assemblies open and navigate better than stock FreeCAD
- backend profiling and scene profiling are mature

## 18.5 Phase 4 - Advanced Modules

Scope:

- Assembly UX
- TechDraw UI
- FEM orchestration UI
- remote execution support
- collaboration foundations

---

## 19. Work Breakdown Structure

## 19.1 Frontend Track

### Foundation

- React app bootstrap
- design system and tokens
- routing/layout shell
- command palette
- document tabs
- global event bus

### Viewport

- 3D scene setup
- camera/navigation
- selection rendering
- hover/preselection
- overlay system
- sketch edit overlay

### Workbench UI

- tree panel
- property panel
- task panel engine
- notifications/progress
- history panel

## 19.2 Backend Track

### Core

- protocol design
- service bootstrapping
- session manager
- logging and tracing
- config handling
- settings service

### Documents

- document open/save
- object graph snapshots
- change events
- transaction boundaries
- undo/redo orchestration

### Commands

- command registry
- validation layer
- execution layer
- error mapping
- job tracking

## 19.3 Native Integration Track

- worker bootstrap
- command adapter to FreeCAD native functions
- document bridge
- tessellation bridge
- import/export bridge
- Python worker bridge

## 19.4 QA Track

- protocol contract tests
- backend unit tests
- worker integration tests
- UI integration tests
- golden-model comparison fixtures
- performance baselines

---

## 20. API Design Principles

## 20.1 Public Command Style

Commands should be explicit and versioned.

Examples:

- `document.open`
- `document.save`
- `object.set_property`
- `body.create`
- `sketch.create_on_plane`
- `feature.pad.create`
- `document.recompute`
- `selection.set`

## 20.2 Response Style

Return:

- updated IDs
- transaction ID
- affected objects
- async job reference if long-running
- structured warnings

## 20.3 Event Style

Events should carry:

- event type
- session ID
- document ID
- correlation ID
- object IDs affected
- minimal payload diff

---

## 21. Testing Strategy

## 21.1 Required Test Layers

### Rust backend unit tests

- command validation
- state transitions
- event emission
- transaction logic

### Native worker integration tests

- open/save
- recompute
- property updates
- geometry generation
- import/export

### Frontend integration tests

- tree updates
- property edit flows
- selection sync
- task panel workflows

### End-to-end tests

- create document -> body -> sketch -> pad -> save -> reopen
- import STEP -> inspect -> export
- native worker crash -> recovery flow

## 21.2 Golden Model Fixtures

Create reference models for:

- simple parts
- PartDesign chains
- sketch constraints
- TechDraw fixtures later
- assembly subsets later

Compare:

- document structure
- property values
- export output metadata
- tessellation checksums where stable

---

## 22. Performance Strategy

## 22.1 Primary Performance Risks

- excessive mesh transfer between backend and frontend
- full scene rebuilds on small model edits
- too-chatty event protocol
- synchronous recompute blocking interaction
- copying huge geometry buffers repeatedly

## 22.2 Mitigations

- binary payloads for meshes
- object-level diffs
- background tessellation jobs
- cache invalidation by object ID/revision
- scene chunking and LOD
- instancing for linked/repeated parts

## 22.3 Metrics to Track

- cold start time
- document open time
- property edit latency
- recompute latency
- viewport FPS
- event throughput
- mesh generation time
- worker crash count

---

## 23. Migration Strategy from Current FreeCAD

## 23.1 Migration Philosophy

Do not fork blindly and start rewriting everything.

Use a strangler pattern.

### Stage A

Use existing FreeCAD modeling core through a controlled bridge.

### Stage B

Move application orchestration and state semantics into Rust.

### Stage C

Move selected stable subsystems out of legacy native code when justified.

## 23.2 First Subsystems That Can Be Owned by Rust

Reasonable early Rust ownership:

- session management
- workspace/project metadata
- command registry
- event streaming
- job management
- plugin manifest handling
- autosave/journaling
- UI settings and layout persistence

## 23.3 Subsystems That Should Stay Native Longer

Keep native for longer:

- Part/PartDesign execution
- Sketcher solver integration
- TNP-critical feature logic
- import/export using OCCT stack
- FCStd-native compatibility details

---

## 24. Staffing Plan

## 24.1 Minimum Credible Team

For a serious effort:

- 2 frontend engineers
- 2 Rust/backend engineers
- 1 native/C++ bridge engineer
- 1 CAD domain engineer familiar with FreeCAD/OCCT
- 1 QA/automation engineer
- 1 product/UX lead

Minimum: 7 people.

## 24.2 Faster Team

Recommended:

- 3 frontend
- 3 Rust/backend
- 2 C++/OCCT/FreeCAD bridge
- 1 rendering engineer
- 1 QA automation
- 1 product/UX

Recommended: 11 people.

---

## 25. Timeline Estimate

## 25.1 Conservative Schedule

- Phase 0: 2 months
- Phase 1: 4 months
- Phase 2: 6 months
- Phase 3: 4 months
- Phase 4: 6+ months

Total to strong product baseline: about 22 months.

## 25.2 Aggressive MVP Schedule

If scope is restricted to Part + PartDesign basics:

- proof of architecture: 6 weeks
- usable vertical slice: 4 months
- dogfood-capable internal release: 6-8 months

---

## 26. Risk Register

## 26.1 Major Risks

### Risk 1: Hidden FreeCAD GUI coupling

Problem:

Core workflows may depend on GUI assumptions more than expected.

Mitigation:

- inventory command paths early
- move to domain commands rather than replaying GUI commands
- isolate Qt-only logic fast

### Risk 2: Native worker bridge becomes too thin or too thick

Problem:

Too thin means chatty unstable APIs. Too thick means backend becomes a legacy RPC wrapper.

Mitigation:

- bridge at domain command level
- keep native API explicit and versioned
- review every bridge addition with ADRs

### Risk 3: Viewport parity is harder than expected

Problem:

CAD viewport behavior is much more demanding than standard 3D apps.

Mitigation:

- dedicated rendering track
- start with simple robust selection/highlight loops
- avoid overpromising early sketch editing fidelity

### Risk 4: Plugin ecosystem breakage

Problem:

Existing Python workbenches may depend heavily on Qt GUI classes.

Mitigation:

- define compatibility tiers
- support backend Python first
- provide migration docs and adapter APIs

### Risk 5: Team underestimates CAD domain complexity

Problem:

A generic web/backend team will not automatically succeed in CAD.

Mitigation:

- dedicate CAD domain owners
- preserve existing native logic initially
- make golden workflow fixtures mandatory

---

## 27. First 90 Days Plan

## 27.1 Month 1

- define protocol and domain model
- create Rust backend skeleton
- create React shell
- build native worker spike
- open document and read object tree

## 27.2 Month 2

- render tessellated geometry in React viewport
- property panel bound to backend object metadata
- selection event loop working
- recompute command working end-to-end

## 27.3 Month 3

- create body and sketch on plane
- update sketch-related properties
- basic PartDesign pad workflow working
- save/reopen supported models
- basic end-to-end tests running in CI

---

## 28. MVP Definition

The MVP is successful if a user can:

1. launch the app
2. create a document
3. create a body
4. create a sketch on XY/XZ/YZ or planar face
5. draw basic sketch geometry
6. constrain/edit dimensions
7. create a pad or pocket
8. edit properties and recompute
9. save and reopen the file
10. navigate the model reliably in the React viewport

If these are not solid, the product is not ready regardless of architecture elegance.

---

## 29. ADRs You Should Write Immediately

Create architecture decision records for:

1. desktop shell choice: Tauri vs Electron
2. transport choice: gRPC vs IPC-only
3. worker isolation model: process vs in-process FFI
4. viewport stack: three.js vs vtk.js vs custom native bridge
5. document compatibility strategy: FCStd-first vs new format
6. plugin compatibility strategy
7. tessellation ownership and caching strategy
8. selection/picking authority model

---

## 30. Recommended Final Direction

The recommended implementation path is:

- React frontend in a Tauri shell
- Rust backend as the authoritative application platform
- native FreeCAD/OCCT worker process behind explicit domain APIs
- FCStd compatibility retained initially
- Python preserved in backend worker form
- gradual subsystem replacement, not full rewrite

This gives you the best balance of:

- engineering realism
- delivery speed
- reuse of FreeCAD strengths
- modern UI architecture
- long-term maintainability
- future remote/multi-user potential

## 31. Concrete Starting Backlog

### Week 1 backlog

- create `protocol/` package with document, selection, property, and command schemas
- scaffold `backend/crates/api-gateway`
- scaffold `frontend/app`
- scaffold `native/freecad-bridge`
- define object tree payload
- define property metadata payload

### Week 2 backlog

- open document command
- object tree fetch
- property fetch
- event subscription plumbing
- React tree panel prototype

### Week 3 backlog

- tessellation fetch for visible objects
- viewport mesh rendering
- camera controls
- object selection sync

### Week 4 backlog

- property update command
- recompute command
- transaction event stream
- simple error surface in UI

---

## 32. Bottom Line

A React frontend plus Rust backend FreeCAD variant is viable only if it is treated as an architectural extraction project first, and only then as a full-clone reimplementation program.

The correct strategy is:

- split UI and backend cleanly
- make Rust the orchestration and API layer
- isolate native CAD logic behind a controlled bridge
- ship a narrow vertical slice early
- replace legacy internals selectively, only where justified by data

---

## 33. Complete FreeCAD Clone Objective

### 33.1 Expanded Product Mandate

If the explicit goal is to clone the complete feature set of FreeCAD and its plugin ecosystem using a Rust + React stack, the program must be framed as a multi-track platform reimplementation rather than only a UI modernization effort.

That means the target scope is:

- core application shell and document model
- all major bundled workbenches
- all standard file import/export pathways
- Python macro and automation behavior
- workbench/plugin loading and extension surfaces
- task panels, tree, properties, selections, expressions, units, preferences, and command system
- technical workflows like Path, FEM, TechDraw, Spreadsheet, Assembly, Surface, Reverse Engineering, and addon management

### 33.2 Definition of "Complete Feature Clone"

For this initiative, "complete feature clone" should mean:

- workflow parity for all bundled workbenches shipped in the targeted FreeCAD baseline
- document compatibility for the supported release family
- command parity for end-user operations, not merely object/model parity
- automation parity for the practical subset used by macros and plugin workbenches
- extension parity for user-installed addons, with a documented compatibility classification
- no hard dependency on the legacy Qt GUI for any shipping end-user workflow

### 33.3 Scope Rule

The clone objective should be measured at four levels:

1. Document parity
2. Workflow parity
3. Automation parity
4. Extension parity

Only cloning the data model is not enough. Only cloning the visual layout is not enough. The program succeeds only when users can perform the same meaningful engineering jobs in the new stack.

---

## 34. Full Feature Inventory Program

### 34.1 Required Baseline Audit

Before implementation planning is considered complete, create a machine-readable inventory of:

- all bundled workbenches
- all commands
- all document object types
- all view providers
- all import/export formats
- all task panels
- all property types
- all preference panels
- all Python-exposed modules, classes, and commands
- all addon-manager discoverable first-party and high-value third-party plugins

Store this inventory as versioned source data, not prose only.

Recommended artifacts:

- `docs/variant/parity/workbenches.yaml`
- `docs/variant/parity/commands.yaml`
- `docs/variant/parity/object_types.yaml`
- `docs/variant/parity/import_export.yaml`
- `docs/variant/parity/plugins.yaml`
- `docs/variant/parity/python_api_surface.yaml`

### 34.2 Core Built-In Workbench Families to Inventory

At minimum, the parity matrix must cover:

- Start
- Part
- PartDesign
- Sketcher
- Draft
- Arch or BIM-related modules in the target baseline
- Assembly
- TechDraw
- Spreadsheet
- FEM
- Path or CAM
- Mesh
- MeshPart
- Surface
- Points
- Material
- Measure
- Inspection
- ReverseEngineering
- Import/export utilities
- Robot
- Plot
- Web
- OpenSCAD integration
- FlowStudio or other custom bundled modules in this fork

### 34.3 Plugin Ecosystem Classes

Third-party addons should be classified into:

- Tier A: strategic high-adoption plugins that must work near launch
- Tier B: important engineering plugins supported through compatibility mode
- Tier C: legacy or low-usage plugins supported later or only via adapters

Examples of plugin categories to inventory:

- Sheet metal
- Fasteners
- Assembly-related addons
- BIM/architecture addons
- CFD/CAE addons
- electronics or PCB integrations
- rendering and visualization addons
- manufacturing/post-processing addons
- data exchange or PLM connectors

### 34.4 Parity Matrix Fields

Each feature row in the inventory should include:

- feature ID
- workbench
- command name
- user-facing workflow description
- required object types
- dependency on OCCT/native worker
- dependency on Python
- dependency on Qt-only behavior
- migration strategy
- parity tier
- test fixture
- acceptance criteria
- status

---

## 35. Full Workbench and Plugin Reimplementation Strategy

### 35.1 Migration Modes

Every workbench and plugin should be assigned one of four migration modes:

#### Mode A: Native compatibility hosted behind Rust

Use this when:

- the subsystem is large
- native logic is already stable
- UI can be replaced without immediately rewriting core behavior

Examples:

- Part
- PartDesign
- Sketcher solver integration
- import/export pipelines

#### Mode B: Rust orchestration with native kernel operations

Use this when:

- command semantics can be Rust-owned
- geometry execution can remain native
- the UI can be fully React-based

Examples:

- document recompute orchestration
- property editing
- task workflows
- selection and viewport state

#### Mode C: Full Rust/React reimplementation

Use this when:

- the subsystem is mostly orchestration or application logic
- native GUI coupling is high but domain complexity is moderate
- ownership by Rust gives large long-term benefits

Examples:

- addon manager
- preferences and settings
- startup flows
- project/workspace handling
- task/job scheduler
- plugin manager
- notifications and logging UI

#### Mode D: Sunset or replace with a modern extension API

Use this when:

- the original subsystem is tightly bound to Qt internals
- direct compatibility is expensive and low value
- a migration shim plus new extension API is better

Examples:

- some GUI-heavy macro helpers
- highly coupled custom dialogs
- legacy view-provider-only plugins

### 35.2 Full Clone Waves

The complete clone should be split into implementation waves:

#### Wave 1: Core shell and modeling essentials

- Start
- document management
- tree, properties, selection, undo/redo
- Part
- PartDesign
- Sketcher
- viewport
- expressions and units
- save/open/import/export basics

#### Wave 2: production engineering workflows

- Draft
- Arch/BIM target workflows
- Spreadsheet
- TechDraw
- Material
- Measure
- addon management
- plugin compatibility host

#### Wave 3: advanced engineering and manufacturing

- FEM
- Path/CAM
- Mesh and mesh-part tooling
- Surface
- Points
- inspection workflows
- reverse engineering

#### Wave 4: specialist and ecosystem completion

- Robot
- Plot
- Web
- OpenSCAD integration
- assembly ecosystem refinement
- strategic third-party plugins
- deep automation compatibility

### 35.3 Plugin Forward-Porting Strategy

Each supported plugin should have one of these forward paths:

- run unchanged in Python compatibility mode
- run with a Qt-to-React adapter shim for command and panel registration
- be partially ported to Rust backend plus React frontend
- be fully rewritten as a first-class Rust/React extension

---

## 36. React + Rust Ownership Model for Full Parity

### 36.1 What Must Eventually Move to Rust

For a true platform clone, Rust should become authoritative for:

- command registry and dispatch
- transaction and undo/redo semantics
- document/session lifecycle
- plugin manifests and capability policies
- job scheduling and recompute orchestration
- selection model
- workspace/project metadata
- settings and preferences
- API versioning and remote automation
- test harnesses and parity validation

### 36.2 What Must Eventually Move to React

For the frontend to count as a real reimplementation, React should own:

- all top-level shell navigation
- workbench chrome and panels
- document tabs
- tree views
- property editors
- task panels
- sketch editing UI layer
- TechDraw UI workflows
- FEM/Path/Spreadsheet interaction surfaces
- plugin panels and frontend extension surfaces

### 36.3 What May Remain Native Long-Term

Even in the full-clone target, it is reasonable for these to remain native for years:

- OCCT-heavy geometry operations
- topology naming and B-Rep details
- deep solver internals
- some import/export codecs
- parts of mesh generation/tessellation
- specialized legacy algorithms where rewrite ROI is poor

The goal is not ideological purity. The goal is complete user-facing parity with a maintainable architecture.

---

## 37. Python and Plugin Compatibility for a Full Clone

### 37.1 Compatibility Tiers

Define explicit compatibility tiers for Python and plugin support:

#### Tier 1: Full supported compatibility

- supported without code changes
- tested in CI
- documented as release-blocking

#### Tier 2: Supported with adaptation

- minor migration changes required
- stable backend APIs provided
- documented upgrade path

#### Tier 3: Best-effort legacy mode

- may run under compatibility host
- not guaranteed for all GUI behaviors
- not release-blocking

#### Tier 4: Not supported

- legacy or unsafe behavior
- direct Qt widget assumptions
- unsupported hacks or brittle internals

### 37.2 New Extension API Surface

To make a complete ecosystem sustainable, define new extension APIs for:

- registering commands
- declaring backend jobs
- adding tree/property/task UI contributions
- contributing import/export handlers
- adding analysis or manufacturing pipelines
- listening to document, selection, and recompute events

### 37.3 Qt Plugin Migration

Many plugins will be coupled to:

- `Gui.runCommand`
- Qt task panels
- dock widgets
- view providers
- direct selection observers

Provide migration layers for:

- command registration adapters
- task-panel-to-schema conversion
- property panel schema rendering
- selection event subscriptions
- backend-executed Python command hosts

### 37.4 Macro and Console Parity

If full FreeCAD cloning is the goal, include:

- Python console equivalent
- macro recorder/player
- macro management UI
- script execution with document/session bindings
- backend-safe automation API

---

## 38. Acceptance Criteria for Complete Feature Parity

### 38.1 Workbench-Level Acceptance

Each workbench is only considered complete when:

- major user workflows are executable in React UI
- command coverage reaches agreed parity threshold
- core fixtures load and roundtrip successfully
- automated tests cover creation, edit, recompute, save, reopen
- user docs exist for migrated workflows
- required plugins for that workbench tier are classified and supported

### 38.2 Plugin-Level Acceptance

A plugin is only considered supported when:

- it installs through the new addon/plugin system
- commands load without legacy GUI dependency failures
- panels or workflows render in React or via sanctioned adapters
- automation hooks function through the backend API
- failures are isolated and diagnosable

### 38.3 Product-Level Acceptance

The full-clone program reaches success when:

1. all bundled workbenches in scope have accepted parity plans
2. all Tier A plugins are supported or replaced
3. common daily workflows no longer require launching legacy Qt FreeCAD
4. document roundtrips are trusted by internal power users
5. automation/macro users can migrate without losing critical productivity
6. major regressions are tracked by a continuously updated parity dashboard

---

## 39. Expanded Delivery Program for a Complete Clone

### 39.1 Program Phases

The original MVP phases are still valid, but a true full-clone program needs additional program-level phases:

#### Program Phase A: Inventory and baseline capture

Duration: 2-4 months

Deliverables:

- complete feature inventory
- plugin ecosystem inventory
- parity matrix
- golden workflow suite
- baseline performance and compatibility measurements

#### Program Phase B: platform extraction

Duration: 4-8 months

Deliverables:

- Rust backend foundation
- React shell and viewport base
- native worker isolation
- protocol definitions
- command/event model

#### Program Phase C: core modeling parity

Duration: 8-14 months

Deliverables:

- Part/PartDesign/Sketcher daily-use parity
- document lifecycle parity
- property/expression/unit parity
- FCStd roundtrip confidence

#### Program Phase D: workbench expansion

Duration: 10-18 months

Deliverables:

- Draft, Spreadsheet, TechDraw, Material, Measure, addon workflows
- Arch/BIM strategy implemented
- plugin host stable

#### Program Phase E: advanced engineering parity

Duration: 10-18 months

Deliverables:

- FEM, Path, Mesh, Surface, ReverseEngineering, Inspection
- deeper plugin ecosystem support
- performance hardening for large documents and assemblies

#### Program Phase F: ecosystem and de-legacy

Duration: 6-12 months

Deliverables:

- Tier A plugin support complete
- legacy GUI dependencies removed from core release path
- migration tooling and docs published
- optional remote/service-backed backend mode stabilized

### 39.2 Realistic Timeline

For a complete FreeCAD + plugin clone, a more realistic schedule is:

- narrow vertical slice: 6-10 months
- strong internal dogfood release: 12-18 months
- broad bundled-workbench parity: 24-36 months
- serious plugin ecosystem parity: 30-42 months

This assumes a dedicated, experienced team and stable funding.

### 39.3 Team Size for Full Clone

The earlier team estimates are too small for the complete-clone goal.

More realistic team for sustained execution:

- 4 React/frontend engineers
- 4 Rust/backend engineers
- 3 C++/OCCT/FreeCAD bridge engineers
- 2 rendering/viewport engineers
- 2 CAD domain engineers
- 2 QA/automation engineers
- 1 product lead
- 1 UX/design lead
- 1 developer relations or plugin migration engineer

Total: about 20 people.

### 39.4 Program Governance

For a project this large, add:

- architecture review board
- parity dashboard reviewed every sprint
- ADRs for every extension-surface decision
- plugin compatibility board
- golden workflow signoff from domain owners
- release gates tied to parity categories, not just code completion

---

## 40. Recommended Next Documents

To make this expanded plan actionable, create these follow-on documents immediately:

1. `FREECAD_FULL_PARITY_MATRIX.md`
2. `FREECAD_PLUGIN_COMPATIBILITY_STRATEGY.md`
3. `FREECAD_WORKBENCH_MIGRATION_WAVES.md`
4. `FREECAD_PYTHON_AUTOMATION_COMPATIBILITY.md`
5. `FREECAD_VIEWPORT_AND_SELECTION_ARCHITECTURE.md`
6. `FREECAD_EXTENSION_API_DESIGN.md`
7. `FREECAD_GOLDEN_WORKFLOW_TEST_PLAN.md`
8. `FREECAD_DATA_MODEL_AND_COMMAND_TAXONOMY.md`

### 40.1 Suggested Immediate Backlog for the Full-Clone Goal

#### Next 30 days

- generate feature inventory from source tree
- classify workbenches and plugins by migration mode
- define parity matrix schema
- identify Tier A plugins
- define command taxonomy and document object taxonomy

#### Next 60 days

- build golden workflow fixtures for top 20 workflows
- define frontend extension APIs
- define backend plugin APIs
- define Python compatibility service boundaries
- map every Qt-only workflow hotspot

#### Next 90 days

- freeze baseline feature scope for target FreeCAD release
- publish bundle and plugin compatibility roadmap
- begin Wave 1 implementation with explicit parity dashboards
- start workbench-by-workbench migration tracking
