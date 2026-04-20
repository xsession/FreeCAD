# FreeCAD React/Rust Variant Execution Roadmap

## Purpose

This document turns the strategy in [FREECAD_REACT_RUST_VARIANT_PLAN.md](E:/GIT/FreeCAD/FREECAD_REACT_RUST_VARIANT_PLAN.md) into a delivery roadmap for a full FreeCAD + plugin clone effort.

This is intentionally operational:

- milestone-based
- owner-friendly
- test-driven
- parity-aware

---

## 1. Program Outcome

Build a production-grade Rust + React FreeCAD variant that:

- replaces the legacy Qt GUI for all supported end-user workflows
- preserves FreeCAD document value and automation power
- supports bundled workbenches through migration waves
- supports strategic plugins via compatibility tiers
- gradually reduces hard dependence on legacy GUI internals

---

## 2. Delivery Principles

- Ship by workflow, not by widget.
- Keep native geometry logic where rewrite cost is unjustified.
- Make Rust authoritative for commands, sessions, events, and extension policy.
- Make React authoritative for user experience and workbench interaction surfaces.
- Tie every milestone to golden workflows and parity dashboards.
- Do not mark a workbench complete without plugin and automation implications reviewed.

---

## 3. Workstreams

### WS1 Platform and Protocol

- API schema
- command taxonomy
- event streams
- session lifecycle
- worker supervision

### WS2 Native Integration

- FreeCAD/OCCT worker host
- document bridge
- recompute bridge
- tessellation bridge
- import/export bridge

### WS3 Frontend Shell and UX

- app shell
- document tabs
- tree/properties/task panels
- command palette
- notifications

### WS4 Viewport and Interaction

- rendering
- selection
- preselection/highlighting
- sketch overlays
- large-model performance

### WS5 Workbench Migration

- Start
- Part
- PartDesign
- Sketcher
- Draft
- Spreadsheet
- TechDraw
- remaining workbenches by wave

### WS6 Plugin and Python Compatibility

- Python worker
- macro tooling
- plugin manifests
- compatibility host
- extension APIs

### WS7 Quality and Parity

- golden workflows
- fixture management
- parity dashboards
- regression tracking
- performance labs

---

## 4. Milestone Roadmap

## Milestone 0: Program Setup

Target: 4-8 weeks

Deliverables:

- parity matrix created
- workbench inventory completed
- plugin tiering completed
- ADR set created
- golden workflow list agreed
- baseline release target chosen

Exit criteria:

- scope is frozen for the target FreeCAD baseline
- architecture governance exists
- top 20 workflows are named and testable

## Milestone 1: Architecture Vertical Slice

Target: 8-12 weeks

Deliverables:

- React shell boots in desktop container
- Rust backend boots and exposes versioned protocol
- native worker opens document
- object tree loads in UI
- viewport renders backend tessellation
- one property update recomputes end-to-end

Exit criteria:

- create/open/save roundtrip works
- one command executes through Rust, not legacy GUI routing
- worker crash can be observed and reported cleanly

## Milestone 2: Core Modeling Slice

Target: 12-20 weeks

Deliverables:

- document tree
- property editor
- selection sync
- undo/redo
- create body
- create sketch on plane
- sketch edit basics
- pad and pocket workflows

Exit criteria:

- GW-001, GW-002, GW-003 pass
- no Qt GUI dependency for the vertical slice

## Milestone 3: Core Workbench Baseline

Target: 16-24 weeks

Deliverables:

- Part major workflows
- PartDesign daily-use workflows
- Sketcher daily-use workflows
- import/export baseline
- expression and units parity
- startup/preferences/addon-manager baseline

Exit criteria:

- daily-use mechanical part workflow is dogfood-capable
- FCStd roundtrip trusted for supported fixtures

## Milestone 4: Workbench Expansion Wave 1

Target: 20-32 weeks

Deliverables:

- Draft baseline
- Spreadsheet baseline
- TechDraw baseline
- Material and Measure parity
- plugin manifest system
- macro execution service

Exit criteria:

- GW-004 through GW-010 coverage substantially in place
- Tier A plugin migration plans approved

## Milestone 5: Ecosystem Compatibility

Target: 20-28 weeks

Deliverables:

- Python automation host stable
- Tier A plugin support in progress
- compatibility adapters for legacy GUI-bound plugin behaviors
- extension API alpha

Exit criteria:

- at least 3-5 strategic plugins run in supported or adapted mode

## Milestone 6: Advanced Engineering Wave

Target: 24-40 weeks

Deliverables:

- FEM workflows baseline
- CAM/Path workflows baseline
- Mesh/Surface/Inspection/RE baselines
- large-model performance improvements
- assembly workflow stabilization

Exit criteria:

- advanced workbench parity reaches agreed threshold for internal users

## Milestone 7: Product Hardening

Target: ongoing after milestone 6

Deliverables:

- parity dashboard in CI
- crash/recovery hardening
- performance budgets
- plugin certification process
- release notes and migration docs

Exit criteria:

- release candidate suitable for external evaluation

---

## 5. Ownership Model

| Area | Primary Roles | Secondary Roles |
|---|---|---|
| Platform/API | Rust backend, architect | QA, native bridge |
| Native bridge | C++/OCCT bridge | Rust backend |
| Frontend shell | React/frontend | UX |
| Viewport | Rendering engineer, frontend | native bridge |
| Part/PartDesign/Sketcher | CAD domain + native bridge + frontend | Rust backend |
| Draft/Spreadsheet/TechDraw | frontend + Rust + CAD domain | QA |
| FEM/CAM/Mesh/Surface | CAD domain + native bridge | frontend |
| Plugin compatibility | Python/plugin engineer + Rust | frontend |
| QA/parity | QA automation | all teams |

---

## 6. Release Gates

### Gate A: Architectural viability

- backend protocol stable enough for vertical slice
- frontend does not call legacy GUI directly
- worker isolation works

### Gate B: Core modeling viability

- core parametric workflow complete
- selection/property/recompute model stable
- save/open roundtrip proven

### Gate C: Product viability

- multiple workbenches usable daily
- performance acceptable for target fixtures
- addon and macro story credible

### Gate D: Ecosystem viability

- Tier A plugin plan materially executed
- migration path for Python and plugins documented
- parity dashboard shows sustained improvement

---

## 7. Major Risks and Active Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Hidden GUI coupling in legacy features | High | feature inventory, adapter boundaries, golden workflows |
| Plugin breakage from Qt assumptions | High | compatibility tiers, plugin host, migration shims |
| Viewport parity gaps | High | dedicated rendering workstream, canonical selection model |
| Over-broad rewrite scope | High | wave-based delivery, migration modes |
| Rust backend becoming thin RPC wrapper | Medium/High | own commands, transactions, sessions, extensions in Rust |
| Team underestimates CAD complexity | High | dedicated CAD domain owners, fixture-driven validation |

---

## 8. Immediate 12-Week Backlog

### Weeks 1-4

- create parity source files
- freeze target FreeCAD release baseline
- define command taxonomy
- define plugin tiering
- scaffold protocol and roadmap dashboards

### Weeks 5-8

- wire document open/tree/properties through Rust
- build viewport proof with tessellation
- create golden workflows for top 10 core paths
- define extension API alpha

### Weeks 9-12

- implement body/sketch/pad vertical slice
- enable save/reopen
- produce first internal parity scorecard
- begin Start/Part/PartDesign/Sketcher wave ownership

---

## 9. Reporting

Weekly reporting should include:

- parity score change by workbench
- blocked workflows
- plugin compatibility movement
- top crash/perf issues
- golden workflow pass rate
- next two-week risk outlook

Monthly reporting should include:

- milestone status
- architecture deviations
- staffing/capacity risks
- plugin ecosystem support status
- release readiness estimate
