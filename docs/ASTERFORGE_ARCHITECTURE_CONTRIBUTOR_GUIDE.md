# AsterForge Architecture Contributor Guide

Status: contributor-oriented architecture overview for the current Rust-backed AsterForge prototype as of 2026-05-04

## Audience

This document is for contributors who need to modify or extend AsterForge at the developer level.

It is not a product pitch and it is not a high-level migration manifesto. The goal is to explain how the current code is actually organized, where ownership lives today, and how to make changes without pushing logic back into the wrong layer.

## What AsterForge Is

AsterForge is the Rust-first backend variant inside the FreeCAD repository.

Today, its role is to act as a product control plane around a native FreeCAD bridge contract. The backend is responsible for:

- command definition and validation
- document interpretation and state projection
- API transport and protocol translation
- shell-oriented composition of history, properties, task panels, viewport state, and diagnostics
- bridge-backed execution and mock-native session handling
- STEP-specific inspection workflows

It is not yet a full native CAD kernel rewrite. The current design deliberately separates:

- transport and orchestration
- shared backend semantics
- native bridge interaction
- STEP inspection helpers

## Workspace Layout

The AsterForge Rust workspace lives under `variants/asterforge`.

Current workspace members:

- `backend/crates/api-gateway`
- `backend/crates/command-core`
- `backend/crates/document-core`
- `backend/crates/step-core`
- `backend/crates/protocol-types`
- `native/freecad-bridge`

At a glance:

```text
frontend / client
    |
    v
api-gateway
    |
    +--> command-core
    +--> document-core
    +--> step-core
    +--> protocol-types
    |
    v
freecad-bridge
    |
    v
native / mock FreeCAD session behavior
```

## Architectural Intent

The main architectural direction is to reduce `api-gateway` into a transport and composition layer, while pushing durable backend semantics into smaller ownership crates.

The practical rule is:

- if logic defines command behavior or validation, it should usually live in `command-core`
- if logic defines document interpretation, feature history, graph state, session bookkeeping, or selection semantics, it should usually live in `document-core`
- if logic defines STEP-specific shell behavior, message semantics, or preset decoding, it should usually live in `step-core`
- if logic defines native contract types or bridge execution behavior, it should usually live in `freecad-bridge`
- if logic only exists to translate HTTP or protocol requests into these services and assemble response payloads, it belongs in `api-gateway`

## Crate Ownership

### `api-gateway`

Purpose:

- owns HTTP routing, protocol translation, stateful app composition, and shell-facing response assembly

Important paths:

- `src/app.rs`: gateway bootstrap, tracing initialization, service-container wiring
- `src/app/routes.rs`: Axum routes and HTTP entrypoints
- `src/app/state.rs`: central application state and async API surface
- `src/app/services.rs`: explicit service container for bridge, command-core, and document-core access

Key submodules inside `src/app/`:

- `command_runtime.rs`: top-level command orchestration, job/event creation, runtime dispatch
- `bridge_command_runtime.rs`: thin bridge-backed snapshot-apply layer over the shared `command-core` bridge adapter seam plus the shared history adapter seam for undo/redo execution
- `step_runtime.rs`: STEP-specific command execution
- `extension_runtime.rs`: extension inventory and reviewed launcher flow
- `state_bootstrap.rs`: startup `AppModel` assembly for initial bridge snapshot, projection, and persisted-workspace restore
- `state_open.rs`: document-open reset and activity bootstrap for cache clearing, resync, jobs, and events
- `state_query.rs`: snapshot, boot payload, and document-scoped read-query builders for the shell-facing read side
- `state_selection.rs`: preselection, selection, and selection-mode mutation flow for validation, resync, and event emission
- `state_shell.rs`: workbench activation plus shell panel and shell session mutation flow for shell-facing layout and session state updates
- `state_views.rs`: top-level response assembly for viewport, shell, selection, diagnostics, and task panel
- `state_workspace.rs`: persistence and workspace session bookkeeping
- `state_properties.rs`: property projection and STEP property shaping
- `state_step_cache.rs`: STEP source resolution, parsed file loading, and active cache management
- `state_step_tools.rs`: STEP visibility, PMI, measurement, and camera helpers
- `state_step_views.rs`: STEP-specific response builders
- `state_sync.rs`: bridge snapshot synchronization and selection normalization helpers

Design note:

`state.rs` is still the central state owner, but much less logic should be added there directly than earlier in the project. Startup assembly and document-open mutation flow already moved into focused sibling modules; prefer extending those or adding another sibling helper before growing `state.rs` again.

### `command-core`

Purpose:

- authoritative home for command definitions, command argument metadata, validation, dispatch classification, job planning, event planning, and the shared bridge-command adapter seam

Examples of responsibility:

- command ids and metadata
- validation error kinds
- transaction mode and job kind classification
- shared runtime planning
- bridge-command adapter traits and shared bridge request or failure normalization
- extension inventory policy and reviewed launcher messaging

Use `command-core` when a change answers questions like:

- what commands exist?
- when is a command valid?
- what job or event plan should a command produce?
- how should commands be grouped or routed?

### `document-core`

Purpose:

- authoritative home for bridge-to-document projection and shared document semantics

Examples of responsibility:

- `DocumentState`, `DocumentSummary`, `FeatureHistoryResponse`, and related state structures
- workspace recent-document and session entries
- bridge snapshot projection into document summary, history, evaluation, and graph state
- shared selection-mode filtering
- sketch readiness helpers
- feature dependency interpretation

Use `document-core` when a change answers questions like:

- how do we interpret a bridge snapshot as document state?
- what objects are selectable in a given mode?
- what does feature history mean?
- what is shared document logic independent of HTTP or UI transport?

### `step-core`

Purpose:

- shared STEP shell semantics that are not specific to HTTP transport

Examples of responsibility:

- STEP command message text
- view preset decoding
- STEP-specific message helpers used by gateway STEP handlers

Use `step-core` when the logic is STEP-specific but reusable across gateway code.

### `protocol-types`

Purpose:

- transport-facing typed protocol definitions

Use this crate when you need durable protocol messages shared between layers rather than gateway-only DTOs.

### `freecad-bridge`

Purpose:

- explicit native adapter contract and mock-native session behavior

Current internal modules:

- `contract.rs`: protocol and contract types
- `session_store.rs`: mock session persistence
- `model.rs`: snapshot loading and document mutation helpers
- `prototype.rs`: `FreecadBridgeContract` implementation for the prototype bridge
- `runtime.rs`: runtime metadata helpers
- `undo.rs`: undo stack and undo/redo actions
- `viewport.rs`: viewport diff logic
- `workflow.rs`: workflow text helpers for shell/task panel composition

Use `freecad-bridge` when the change is about:

- bridge request and response shapes
- command execution against a native or mock bridge session
- runtime metadata and capabilities
- undo stack behavior tied to bridge snapshots
- native-facing error boundaries

## Request and Data Flow

### Command Flow

The current command path looks like this:

```text
HTTP route
  -> api-gateway routes
  -> AppState::run_command
  -> command-core validation
  -> api-gateway command_runtime
  -> dispatch route selection
      -> step_runtime
      -> extension_runtime
      -> bridge_command_runtime
  -> AppModel update + view/state refresh
  -> response payload + jobs + events
```

Important details:

- `AppServices` now generates a correlation id for each request path
- the same correlation id is threaded through validation, document projection, and bridge command execution
- bridge-backed commands populate `BridgeRequestOptions.correlation_id`
- request shaping and bridge failure normalization for bridge-backed commands now flow through the shared `command-core` adapter helper instead of being rebuilt inline in the gateway
- document-open flows now go through the explicit bridge session contract before the gateway resolves the working snapshot
- command jobs and event plans are built from `command-core`, not invented ad hoc in routes

### Document Open Flow

The current document-open path looks like this:

```text
AppState::open_document
  -> services.bridge.open_document_snapshot
  -> services.document.project_document_state
  -> AppModel::sync_from_snapshot
  -> optional STEP projection via state_step_cache
  -> workspace/session bookkeeping
  -> jobs/events for document.open
```

Key split:

- bridge snapshot acquisition is bridge-owned
- document interpretation is document-core-owned
- response composition remains gateway-owned

### STEP Flow

STEP is currently a distinct vertical slice inside the backend.

Typical path:

```text
open STEP document
  -> state_step_cache resolves and parses STEP payload
  -> state_properties shapes STEP property map
  -> state_step_views builds STEP-specific response content
  -> step_runtime handles STEP interaction commands
  -> state_step_tools updates visibility, PMI, measurement, and camera state
```

This is intentionally separate from the regular PartDesign bridge flow because STEP inspection is read-heavy and shell-composition heavy.

## Service Container

`api-gateway/src/app/services.rs` is the current service boundary.

It is intentionally thin.

Current service groups:

- `BridgeServices`
- `CommandCoreServices`
- `DocumentCoreServices`

What it does today:

- creates production wiring
- generates correlation ids
- logs boundary transitions
- centralizes calls from gateway into the ownership crates

What it should not become:

- a second monolithic application layer
- a hidden replacement for crate ownership
- a place where core semantics are silently reimplemented

Rule of thumb:

- if the code in `services.rs` starts making product decisions instead of delegating and tracing, that is a smell

## State Model

`AppState` owns async access and persistence-facing entrypoints.

`AppModel` owns the in-memory shell/backend state for the active document context.

Key state categories inside `AppModel`:

- current bridge snapshot
- projected `DocumentState`
- object tree
- selection and preselection
- jobs and event stream
- property groups by object
- recent documents and workspace sessions
- extension compatibility state
- STEP caches, measurement summaries, PMI summaries, and viewport camera overrides

Contributors should treat `AppModel` as a composition root for current backend state, not as the default home for every new algorithm.

## Where To Put New Code

### Adding a New Command

Typical sequence:

1. define metadata and validation behavior in `command-core`
2. decide whether the command routes to STEP, extension, bridge vertical slice, or another backend dispatch path
3. if the command is bridge-backed, prefer extending the shared `command-core` bridge adapter seam instead of rebuilding bridge request shaping in the gateway
4. if the command is undo or redo behavior, prefer extending the shared `command-core` history adapter seam instead of calling bridge undo helpers directly from gateway runtime code
4. implement execution in the appropriate runtime module inside `api-gateway`
5. update response composition only where necessary
6. add tests at the right level

Do not start by editing routes unless the transport surface actually changes.

### Adding Shared Document Semantics

If a new rule affects document meaning rather than HTTP representation, prefer `document-core`.

Examples:

- feature dependency interpretation
- selection-mode filtering
- graph and history shaping
- document/session bookkeeping semantics

### Adding STEP Shell Behavior

If the logic is STEP-only:

- message semantics or preset decoding usually belong in `step-core`
- cache resolution, view composition, and gateway-specific orchestration usually belong in `api-gateway/src/app/state_step_*`

### Adding Native Bridge Capability

If the change is about a bridge request, response, error, or session behavior, it belongs in `freecad-bridge`.

That includes:

- new bridge commands
- new bridge request options
- error category expansion
- session lifecycle behavior

## Tracing and Correlation Ids

The system now supports per-request correlation ids through the gateway service boundary.

Current behavior:

- `AppServices` creates a new correlation id for request flows
- gateway services log boundary calls using that id
- bridge-backed commands pass the id through `BridgeRequestOptions.correlation_id`
- `command-core`, `document-core`, and `freecad-bridge` emit tracing events at important boundaries

This means contributors should prefer extending the existing correlation path rather than inventing local request ids in random modules.

If you add a new bridge-backed path, thread the existing correlation id through it.

## Testing Strategy

Current validated test emphasis is:

- unit coverage inside ownership crates
- gateway-focused workflow tests that cross the explicit service boundary

Notable current coverage areas:

- command validation and runtime planning
- document projection and selection-mode semantics
- bridge execution and undo/redo behavior
- FCStd vertical-slice workflow
- STEP vertical-slice workflow

When adding a feature, choose the narrowest test that proves the ownership boundary:

- crate-local semantic rule: test in the ownership crate
- gateway composition or cross-service flow: test in `api-gateway`
- native/session contract behavior: test in `freecad-bridge`

## Contributor Rules Of Thumb

### 1. Do not put new durable semantics into routes

Routes should translate protocol and call state entrypoints.

### 2. Do not put reusable semantics into `state.rs` by default

Try a focused sibling module, `command-core`, `document-core`, `step-core`, or `freecad-bridge` first.

### 3. Keep the service container explicit and thin

It should wire, trace, and delegate. It should not become a secret business-logic layer.

### 4. Prefer ownership clarity over short-term convenience

Adding one more helper to the wrong file is often faster in the moment and more expensive later.

### 5. Preserve the current separation between PartDesign flow and STEP inspection flow

They share infrastructure, but they are different vertical slices with different constraints.

## Common Contributor Workflows

### Modify command behavior

- start in `command-core`
- then check `command_runtime.rs`
- then update `bridge_command_runtime.rs`, `step_runtime.rs`, or `extension_runtime.rs` as appropriate

### Modify document interpretation

- start in `document-core`
- then update gateway response composition only where projections are consumed

### Modify STEP behavior

- start in `step-core` for shared messages or preset semantics
- start in `api-gateway/src/app/state_step_*` for cache, tool, or response composition behavior

### Modify bridge behavior

- start in `freecad-bridge/contract.rs` for type changes
- then `prototype.rs`, `model.rs`, `session_store.rs`, or `undo.rs` depending on the behavior

## Current Weak Spots

Contributors should be aware of the current in-flight edges:

- `api-gateway/src/app/state.rs` is much thinner than before, but still the central composition surface
- the service container is real, but still early-stage and intentionally minimal
- bridge behavior is still mock/prototype-oriented in important areas
- failure-path tracing and failure-path integration coverage still need deeper work

## Practical Contribution Checklist

Before opening a PR for AsterForge backend work, verify:

1. the new logic lives in the narrowest correct crate or module
2. any bridge-backed path preserves the existing correlation-id flow
3. tests cover the ownership boundary you changed
4. the change does not move semantics back into routes or inflate `state.rs` unnecessarily
5. documentation or backlog notes are updated when the architecture changes materially

## Related Files

Useful companion documents:

- `docs/FREECAD_RUST_PHASE1_EXECUTION_BACKLOG.md`
- `docs/CHAT_SUMMARY_2026-05-04.md`

Useful code entrypoints:

- `variants/asterforge/backend/crates/api-gateway/src/app.rs`
- `variants/asterforge/backend/crates/api-gateway/src/app/services.rs`
- `variants/asterforge/backend/crates/api-gateway/src/app/state.rs`
- `variants/asterforge/backend/crates/command-core/src/lib.rs`
- `variants/asterforge/backend/crates/document-core/src/lib.rs`
- `variants/asterforge/backend/crates/step-core/src/lib.rs`
- `variants/asterforge/native/freecad-bridge/src/lib.rs`

## Short Version

If you only remember one thing, remember this:

AsterForge is being built by moving durable semantics out of the gateway and into smaller ownership crates, while the gateway becomes a thin composition and transport layer over an explicit bridge contract.