# ADR-0008: React + Rust Architecture for a Full FreeCAD Variant

## Status

Proposed

## Context

The project direction is to build a FreeCAD-derived product that eventually clones:

- the complete bundled workbench feature set
- core document and automation behaviors
- strategic plugin ecosystem workflows

The legacy Qt GUI architecture is not an acceptable long-term foundation for that outcome because:

- UI and core behavior are too tightly coupled
- plugin behaviors often depend on GUI internals
- testability and API clarity are limited
- remote-capable or service-oriented evolution is difficult

At the same time, a full rewrite of geometry, OCCT integration, and mature CAD kernel behavior is too risky as an initial move.

## Decision

Adopt this target architecture:

- React owns the frontend and all shipping end-user workflow surfaces
- Rust owns application orchestration, sessions, commands, transactions, events, plugin policy, and external APIs
- native FreeCAD/OCCT/C++ logic is isolated behind explicit worker or bridge boundaries
- Python remains supported in backend-hosted worker form for compatibility and extensibility

This is a staged architecture:

1. Separate UI from core behavior
2. Move orchestration and application semantics into Rust
3. Rebuild workbench UX in React
4. Maintain or wrap native geometry behavior where justified
5. Reimplement selected legacy subsystems in Rust only when boundaries and tests are mature

## Consequences

### Positive

- clear frontend/backend separation
- modern UI iteration speed
- better backend testability and crash containment
- strong foundation for plugin APIs and future remote execution
- gradual migration path instead of all-at-once rewrite

### Negative

- the system becomes more distributed and operationally complex
- protocol/versioning design becomes critical early
- plugin compatibility needs deliberate migration layers
- some duplication of concepts exists during transition

### Neutral / Tradeoff

- C++ and Python remain part of the product longer than a purity-focused rewrite would prefer
- full parity takes longer but has a much higher chance of success

## Rejected Alternatives

### 1. Continue evolving the Qt GUI directly

Rejected because it does not create the architectural separation required for a long-term Rust/React platform.

### 2. Full rewrite of FreeCAD core in Rust first

Rejected because it is too risky, too slow, and likely to stall before feature parity.

### 3. React frontend as a thin remote-control for legacy GUI commands

Rejected because it would preserve hidden coupling and produce an unstable API surface.

### 4. Browser-only first implementation

Rejected as the initial product mode because desktop CAD requirements, filesystem integration, native worker concerns, and plugin compatibility all favor desktop-first delivery.

## Follow-Up Decisions Required

- transport choice and protocol constraints
- worker isolation topology
- viewport rendering authority model
- plugin compatibility tiers and extension API
- FCStd compatibility boundaries
- Python automation surface

## Notes

This ADR is the umbrella architecture decision. More specific ADRs should refine:

- plugin API design
- compatibility model
- viewport design
- persistence strategy
- command/event taxonomy
