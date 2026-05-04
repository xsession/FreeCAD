# FreeCAD Rust Phase 1 Execution Backlog

Status: implementation backlog for Phase 1 of the Rust backend migration as of 2026-05-04

## Scope

This backlog covers Phase 1 from [docs/FREECAD_RUST_BACKEND_MIGRATION_PLAN.md](docs/FREECAD_RUST_BACKEND_MIGRATION_PLAN.md): make Rust the product control plane.

The goal is not broad feature parity. The goal is to convert the current AsterForge prototype into a backend with clear crate ownership and a path to production hardening.

## Current Reality

Phase 1 work is primarily about extracting ownership out of:

- `variants/asterforge/backend/crates/api-gateway/src/app/state.rs`
- `variants/asterforge/backend/crates/api-gateway/src/app/command_runtime.rs`
- `variants/asterforge/backend/crates/api-gateway/src/domain.rs`

And moving it into:

- `variants/asterforge/backend/crates/command-core/src/lib.rs`
- `variants/asterforge/backend/crates/document-core/src/lib.rs`
- `variants/asterforge/native/freecad-bridge/src/lib.rs`

## Execution Status Snapshot

Completed or materially landed in code:

- `P1-001`: shared command definition generation moved into `command-core`
- `P1-002`: shared command validation API added in `command-core` and used by gateway execution entrypoints
- `P1-003`: command runtime job and event planning plus shared command-family routing are now bundled in `command-core` and consumed by gateway command execution
- `P1-004`: `command-core` now owns an explicit bridge command adapter trait plus bridge-dispatch request shaping, accepted-snapshot reload orchestration, and bridge error normalization so gateway bridge execution no longer hard-codes those details inline
- `P1-004`: `command-core` now also owns an explicit history command adapter trait plus undo or redo dispatch shaping so gateway undo or redo execution no longer calls bridge undo helpers directly from runtime code
- `P1-005`: `document-core` now owns shared workspace and recent-document session types, synchronization helper logic, and shared bridge selection or sketch-profile helper semantics
- `P1-007`: gateway recent-document and workspace-session bookkeeping now flows through `document-core`, and gateway selection-mode filtering now consumes shared `document-core` bridge helper functions
- `P1-009`: explicit bridge protocol types now exist for runtime metadata, document sessions, command execution, and viewport requests, and now live behind a dedicated `freecad-bridge` contract module instead of sitting inline in the crate root
- `P1-011`: structured bridge error categories and request options now exist for bounded failure reporting
- `P1-012`: bridge session responses now return opaque native tokens rather than exposing native pointer concepts
- `P1-015`: gateway now exposes bridge runtime metadata through `/api/runtime/bridge`
- `P1-016`: unit coverage exists for command validation, document session bookkeeping, shared bridge selection and sketch helper semantics, bridge helper execution, session-backed bridge contract behavior, and shared undo or redo action handling
- `P1-017`: `step-core` now owns shared STEP shell preset decoding and STEP command message semantics used by gateway handlers
- `P1-018`: `command-core` now owns extension inventory lane planning and reviewed-entry execution policy messaging consumed by gateway handlers
- `P1-010`: `freecad-bridge` now has distinct session-store, undo, workflow, runtime, prototype-command, model, and viewport modules instead of keeping those service areas embedded in one monolithic `lib.rs`
- `P1-010`: gateway document-open flows now use the explicit bridge session contract through `BridgeServices` before resolving snapshots, instead of bypassing the contract and calling the snapshot helper directly
- `P1-010`: bridge runtime descriptor fallback now lives behind `BridgeServices` instead of being reimplemented separately in gateway bootstrap and app state
- `P1-013`: `api-gateway` now splits STEP handlers, extension launcher flow, bridge or undo execution, STEP parsed-scene or index projection, bridge-derived command or task or diagnostics or selection view builders, shell or workbench chrome builders, viewport or object-tree projections, state-level response composition, workspace persistence bookkeeping, property projection, STEP cache handling, STEP interaction helpers, STEP response builders, and bridge-sync selection transitions across dedicated runtime and domain or state submodules instead of keeping them embedded in `command_runtime.rs`, `domain.rs`, and one large `state.rs` cluster
- `P1-013`: workbench activation plus shell panel and shell session mutation flows now live in a dedicated `api-gateway/src/app/state_shell.rs` helper instead of remaining embedded inline inside `state.rs`
- `P1-013`: preselection, selection, and selection-mode mutation flows now live in a dedicated `api-gateway/src/app/state_selection.rs` helper instead of remaining embedded inline inside `state.rs`
- `P1-013`: document-open state reset, job bootstrap, and open-event emission now live in a dedicated `api-gateway/src/app/state_open.rs` helper instead of remaining embedded inline inside `state.rs`
- `P1-013`: startup `AppModel` assembly now lives in a dedicated `api-gateway/src/app/state_bootstrap.rs` helper instead of remaining embedded inline inside `state.rs`
- `P1-013`: snapshot, boot payload, and document-scoped read-query builders now live in a dedicated `api-gateway/src/app/state_query.rs` helper instead of remaining embedded inline inside `state.rs`

Partially landed and still in flight:

- `P1-003`: command validation, definition, runtime planning, shared dispatch routing, shared undo or redo action handling, and extension command semantics moved, but gateway still owns step or extension state mutations and snapshot-to-UI synchronization
- `P1-004`: explicit adapter seams now exist in `command-core` for both bridge-backed commands and history undo or redo execution, but more hard-coded bridge behavior still needs to move behind explicit adapters over time
- `P1-010`: bridge service areas are continuing to split into modules, and document-open now uses the explicit bridge session contract, but protocol types and the remaining contract surface still share `freecad-bridge/src/lib.rs`
- `P1-010`: bridge service areas are continuing to split into modules, document-open now uses the explicit bridge session contract, and runtime-descriptor fallback now goes through a shared bridge service helper, but protocol types and the remaining contract surface still share `freecad-bridge/src/lib.rs`
- `P1-013`: gateway business logic volume is reduced for the document or history or model or PartDesign mutation slice, STEP shell messaging, STEP parsed-scene or index projection, extension inventory command semantics, bridge or undo execution paths, selection-mode helper semantics, bridge-derived view shaping, shell chrome composition, viewport or object-tree projection logic, top-level state response composition, workspace persistence bookkeeping, property projection, STEP cache loading, STEP viewport or PMI or measurement helpers, STEP response builders, and bridge-sync selection transitions, leaving `state.rs` mostly as a thinner facade plus residual command-state wiring
- `P1-013`: gateway startup assembly is thinner now that initial `AppModel` construction moved into `state_bootstrap.rs`, document-open reset or activity bootstrap moved into `state_open.rs`, preselection or selection or selection-mode mutation flow moved into `state_selection.rs`, shell or workbench mutation flow moved into `state_shell.rs`, and read-side snapshot or boot or document query builders moved into `state_query.rs`, but `state.rs` is still the central composition surface for many flows
- `P1-014`: app bootstrap and gateway state now wire an explicit `app/services.rs` container for bridge, command-core, and document-core interactions, but the container is still a thin production wiring layer rather than the final long-term dependency boundary
- `P1-017`: gateway state tests now include broader FCStd and STEP vertical-slice coverage that boots through the explicit service container and exercises open, tree, properties, command flow, undo or redo, save, and STEP extraction seams end to end
- `P1-018`: gateway services now generate correlation ids, bridge requests now carry those ids through `BridgeRequestOptions`, gateway persistence warnings now log with those ids, and gateway, command-core, document-core, and freecad-bridge now emit structured tracing events at the active service boundaries with integration-style assertions covering bridge-session failure and persistence warning flows

Validated on 2026-05-04:

- Rust editor diagnostics are clean for the touched files
- `C:\Users\livanyi\.cargo\bin\cargo.exe test -p asterforge-command-core -p asterforge-document-core -p asterforge-step-core -p asterforge-freecad-bridge -p asterforge-api-gateway` passes in `variants/asterforge`
- `C:\Users\livanyi\.cargo\bin\cargo.exe test -p asterforge-freecad-bridge -p asterforge-api-gateway` passes after the `freecad-bridge/src/model.rs`, `freecad-bridge/src/viewport.rs`, `freecad-bridge/src/contract.rs`, `api-gateway/src/app/step_runtime.rs`, `api-gateway/src/app/extension_runtime.rs`, and `api-gateway/src/app/bridge_command_runtime.rs` extractions
- `C:\Users\livanyi\.cargo\bin\cargo.exe test -p asterforge-document-core -p asterforge-api-gateway -p asterforge-freecad-bridge` passes after moving bridge selection-mode and sketch-profile helper functions into `document-core`
- `C:\Users\livanyi\.cargo\bin\cargo.exe test -p asterforge-document-core -p asterforge-api-gateway -p asterforge-freecad-bridge` passes after extracting bridge-derived command catalog, task panel, diagnostics, and selection or preselection builders into `api-gateway/src/domain/bridge_views.rs`
- `C:\Users\livanyi\.cargo\bin\cargo.exe test -p asterforge-document-core -p asterforge-api-gateway -p asterforge-freecad-bridge` passes after extracting shell snapshot, extension compatibility, workbench catalog, menu, toolbar, and layout builders into `api-gateway/src/domain/shell_views.rs`
- `C:\Users\livanyi\.cargo\bin\cargo.exe test -p asterforge-document-core -p asterforge-api-gateway -p asterforge-freecad-bridge` passes after extracting viewport, viewport diff, and object-tree projection builders into `api-gateway/src/domain/viewport_views.rs`
- `C:\Users\livanyi\.cargo\bin\cargo.exe test -p asterforge-document-core -p asterforge-api-gateway -p asterforge-freecad-bridge` passes after extracting STEP parsed document-index and scene-bundle projection builders into `api-gateway/src/domain/step_views.rs`
- `C:\Users\livanyi\.cargo\bin\cargo.exe test -p asterforge-document-core -p asterforge-api-gateway -p asterforge-freecad-bridge` passes after extracting `AppModel` response projection entrypoints into `api-gateway/src/app/state_views.rs`
- `C:\Users\livanyi\.cargo\bin\cargo.exe test -p asterforge-document-core -p asterforge-api-gateway -p asterforge-freecad-bridge` passes after extracting workspace persistence and session bookkeeping into `api-gateway/src/app/state_workspace.rs`
- `C:\Users\livanyi\.cargo\bin\cargo.exe test -p asterforge-document-core -p asterforge-api-gateway -p asterforge-freecad-bridge` passes after extracting bridge property projection plus STEP object-tree and STEP property-map shaping into `api-gateway/src/app/state_properties.rs`
- `C:\Users\livanyi\.cargo\bin\cargo.exe test -p asterforge-document-core -p asterforge-api-gateway -p asterforge-freecad-bridge` passes after extracting STEP source-path detection, cache resolution, and STEP file loading into `api-gateway/src/app/state_step_cache.rs`
- `C:\Users\livanyi\.cargo\bin\cargo.exe test -p asterforge-document-core -p asterforge-api-gateway -p asterforge-freecad-bridge` passes after extracting STEP visibility, PMI, measurement, and camera helpers into `api-gateway/src/app/state_step_tools.rs`
- `C:\Users\livanyi\.cargo\bin\cargo.exe test -p asterforge-document-core -p asterforge-api-gateway -p asterforge-freecad-bridge` passes after extracting STEP selection, viewport, task-panel, catalog, diagnostics, and shell inspection builders into `api-gateway/src/app/state_step_views.rs`
- `C:\Users\livanyi\.cargo\bin\cargo.exe test -p asterforge-document-core -p asterforge-api-gateway -p asterforge-freecad-bridge` passes after extracting bridge snapshot sync and selection-target orchestration into `api-gateway/src/app/state_sync.rs`
- `C:\Users\livanyi\.cargo\bin\cargo.exe test -p asterforge-document-core -p asterforge-api-gateway -p asterforge-freecad-bridge` passes after introducing explicit gateway service-container wiring in `api-gateway/src/app/services.rs` and threading it through app bootstrap, state entrypoints, and command execution
- `C:\Users\livanyi\.cargo\bin\cargo.exe test -p asterforge-document-core -p asterforge-api-gateway -p asterforge-freecad-bridge` passes after adding service-backed FCStd and STEP vertical-slice workflow tests in `api-gateway/src/app/state.rs`
- `C:\Users\livanyi\.cargo\bin\cargo.exe test -p asterforge-document-core -p asterforge-api-gateway -p asterforge-freecad-bridge` passes after extending correlation ids into bridge-session failure and persistence warning flows and adding integration-style log assertions in `api-gateway/src/app/state.rs`
- `C:\Users\livanyi\.cargo\bin\cargo.exe test -p asterforge-command-core -p asterforge-api-gateway -p asterforge-document-core -p asterforge-freecad-bridge` passes after introducing the `command-core` bridge adapter seam and routing gateway bridge execution through it
- `C:\Users\livanyi\.cargo\bin\cargo.exe test -p asterforge-command-core -p asterforge-api-gateway -p asterforge-document-core -p asterforge-freecad-bridge` passes after routing gateway document-open flows through the explicit bridge session contract and adding a correlation-id assertion for the bridge session-open path
- `C:\Users\livanyi\.cargo\bin\cargo.exe test -p asterforge-command-core -p asterforge-api-gateway -p asterforge-document-core -p asterforge-freecad-bridge` passes after extracting the document-open contract fallback logic into a testable helper and adding direct coverage for contract success, session-open failure fallback, and missing-session-snapshot fallback in `api-gateway/src/app/services.rs`
- `C:\Users\livanyi\.cargo\bin\cargo.exe test -p asterforge-command-core -p asterforge-api-gateway -p asterforge-document-core -p asterforge-freecad-bridge` passes after extracting bridge runtime-descriptor fallback into a shared bridge service helper and adding direct coverage for runtime-descriptor success and fallback in `api-gateway/src/app/services.rs`
- `C:\Users\livanyi\.cargo\bin\cargo.exe test -p asterforge-command-core -p asterforge-api-gateway -p asterforge-document-core -p asterforge-freecad-bridge` passes after extracting startup `AppModel` assembly into `api-gateway/src/app/state_bootstrap.rs`, adding persisted-workspace bootstrap coverage, and restoring an explicit gateway-side bridge failure log for correlation assertions
- `C:\Users\livanyi\.cargo\bin\cargo.exe test -p asterforge-command-core -p asterforge-api-gateway -p asterforge-document-core -p asterforge-freecad-bridge` passes after extracting document-open reset and activity bootstrap into `api-gateway/src/app/state_open.rs` and adding focused stage-label coverage for FCStd and STEP open flows
- `C:\Users\livanyi\.cargo\bin\cargo.exe test -p asterforge-command-core -p asterforge-api-gateway -p asterforge-document-core -p asterforge-freecad-bridge` passes after extracting preselection plus selection and selection-mode mutation flow into `api-gateway/src/app/state_selection.rs` while keeping the focused suites green at 58 `api-gateway` tests
- `C:\Users\livanyi\.cargo\bin\cargo.exe test -p asterforge-command-core -p asterforge-api-gateway -p asterforge-document-core -p asterforge-freecad-bridge` passes after extracting workbench activation plus shell panel and shell session mutation flow into `api-gateway/src/app/state_shell.rs` while keeping the focused suites green at 58 `api-gateway` tests
- `C:\Users\livanyi\.cargo\bin\cargo.exe test -p asterforge-command-core -p asterforge-api-gateway -p asterforge-document-core -p asterforge-freecad-bridge` passes after introducing a shared `command-core` history adapter seam and routing gateway undo or redo execution through `app/services.rs` instead of calling bridge undo helpers directly from `bridge_command_runtime.rs`
- `C:\Users\livanyi\.cargo\bin\cargo.exe test -p asterforge-command-core -p asterforge-api-gateway -p asterforge-document-core -p asterforge-freecad-bridge` passes after extracting snapshot, boot payload, and document-scoped read-query builders into `api-gateway/src/app/state_query.rs` while keeping the focused suites green at 58 `api-gateway` tests and 24 `command-core` tests

## Epics

### Epic P1-A: Command Core Ownership

Outcome:

- `command-core` becomes the authoritative home for command metadata, validation, transaction behavior, job classification, and execution planning

### Epic P1-B: Document Core Ownership

Outcome:

- `document-core` becomes the authoritative home for document session state, graph state, history state, and state synchronization rules

### Epic P1-C: Bridge Contract Extraction

Outcome:

- `freecad-bridge` becomes an explicit native adapter contract instead of a snapshot helper

### Epic P1-D: Gateway Hardening

Outcome:

- `api-gateway` becomes a thin transport and composition layer instead of the long-term owner of backend semantics

### Epic P1-E: Tests, Telemetry, And Safety

Outcome:

- protocol, integration, and failure behavior become measurable and enforceable

## Ticket List

| ID | Epic | Task | Primary Paths | Depends On | Acceptance Criteria |
|---|---|---|---|---|---|
| P1-001 | P1-A | Define `CommandDefinition` registry shape with stable ids, argument schemas, and enablement metadata for all currently shipped AsterForge commands | `variants/asterforge/backend/crates/command-core/src/lib.rs` | None | All commands currently surfaced through gateway routes are defined in `command-core` and covered by unit tests |
| P1-002 | P1-A | Add command validation API that accepts document context, selection context, and arguments and returns structured validation errors | `variants/asterforge/backend/crates/command-core/src/lib.rs` | P1-001 | Invalid command requests fail before execution with stable error categories |
| P1-003 | P1-A | Extract command execution planning from gateway into `command-core`, including transaction mode, job kind, and expected side effects | `variants/asterforge/backend/crates/command-core/src/lib.rs`, `variants/asterforge/backend/crates/api-gateway/src/app/command_runtime.rs` | P1-002 | Gateway no longer owns command planning logic |
| P1-004 | P1-A | Introduce bridge command adapter interface so native execution is a dependency of command-core rather than hard-coded gateway logic | `variants/asterforge/backend/crates/command-core/src/lib.rs`, `variants/asterforge/native/freecad-bridge/src/lib.rs` | P1-003 | Command-core can execute through an adapter trait or equivalent abstraction; revisit after the current service-container and tracing seams by replacing more hard-coded bridge behavior with explicit adapters |
| P1-005 | P1-B | Expand document-core with session identity, dirty-state policy, graph ownership, and synchronization APIs | `variants/asterforge/backend/crates/document-core/src/lib.rs` | None | `DocumentState` is not limited to summary and history containers |
| P1-006 | P1-B | Extract document graph creation and bridge-to-document translation out of gateway | `variants/asterforge/backend/crates/document-core/src/lib.rs`, `variants/asterforge/backend/crates/api-gateway/src/domain.rs`, `variants/asterforge/backend/crates/api-gateway/src/app/state.rs` | P1-005 | Graph and evaluation shaping logic lives in document-core |
| P1-007 | P1-B | Add document session store abstraction for open documents, recent documents, workspace sessions, and active selection state | `variants/asterforge/backend/crates/document-core/src/lib.rs`, `variants/asterforge/backend/crates/api-gateway/src/app/state.rs` | P1-005 | Gateway state becomes a client of document-core session store APIs |
| P1-008 | P1-B | Define Rust-owned state delta types for document summary, object tree, history, diagnostics, jobs, and viewport invalidation | `variants/asterforge/backend/crates/document-core/src/lib.rs`, `variants/asterforge/backend/crates/protocol-types/**` | P1-006 | Backend can emit explicit state deltas instead of ad hoc full snapshot mutation rules |
| P1-009 | P1-C | Introduce explicit bridge protocol types for capabilities, document sessions, command execution, and viewport payloads | `variants/asterforge/native/freecad-bridge/src/lib.rs` | None | Bridge API no longer centers on `open_document_snapshot` alone |
| P1-010 | P1-C | Split bridge status and snapshot helpers into service-oriented modules or traits aligned to the bridge contract | `variants/asterforge/native/freecad-bridge/src/lib.rs` | P1-009 | Distinct service groups exist for session, command, and viewport operations |
| P1-011 | P1-C | Add timeout, cancellation, and structured error types to bridge operations | `variants/asterforge/native/freecad-bridge/src/lib.rs` | P1-009 | Every bridge call has bounded failure semantics |
| P1-012 | P1-C | Add opaque native handle strategy so Rust never depends on raw native document pointers | `variants/asterforge/native/freecad-bridge/src/lib.rs` | P1-009 | Bridge responses return stable opaque tokens only |
| P1-013 | P1-D | Reduce `api-gateway` to routing, protocol translation, and service composition | `variants/asterforge/backend/crates/api-gateway/src/app/routes.rs`, `variants/asterforge/backend/crates/api-gateway/src/app/state.rs` | P1-004, P1-007, P1-010 | Business logic volume in gateway drops materially and ownership boundaries are visible in code |
| P1-014 | P1-D | Introduce backend service container wiring for command-core, document-core, and bridge services | `variants/asterforge/backend/crates/api-gateway/src/app/state.rs`, `variants/asterforge/backend/crates/api-gateway/src/app.rs` | P1-004, P1-007, P1-010 | Gateway app boot wires explicit services instead of constructing behavior implicitly |
| P1-015 | P1-D | Add protocol version handshake route and backend capability reporting route | `variants/asterforge/backend/crates/api-gateway/src/app/routes.rs`, `variants/asterforge/backend/crates/api-gateway/src/app/protocol.rs` | P1-009 | Frontend can verify backend and bridge contract versions before using advanced features |
| P1-016 | P1-E | Add unit tests for command validation, document sync rules, and bridge error normalization | `variants/asterforge/backend/crates/command-core/src/lib.rs`, `variants/asterforge/backend/crates/document-core/src/lib.rs`, `variants/asterforge/native/freecad-bridge/src/lib.rs` | P1-002, P1-005, P1-011 | New unit coverage exists around extracted ownership logic |
| P1-017 | P1-E | Add integration tests for open, save, tree, properties, PartDesign command flow, undo/redo, and STEP extraction | `variants/asterforge/backend/crates/api-gateway/src/app/state.rs`, test fixtures under `variants/asterforge` | P1-013, P1-014 | P0 vertical-slice workflows pass through the refactored service boundaries |
| P1-018 | P1-E | Add structured tracing and correlation ids across gateway, command-core, document-core, and bridge calls | `variants/asterforge/backend/crates/api-gateway/**`, `variants/asterforge/backend/crates/command-core/**`, `variants/asterforge/backend/crates/document-core/**`, `variants/asterforge/native/freecad-bridge/**` | P1-014 | A single command can be traced end to end in logs |
| P1-019 | P1-E | Add worker failure and timeout simulation tests for the bridge contract | `variants/asterforge/native/freecad-bridge/src/lib.rs`, `variants/asterforge/backend/crates/api-gateway/**` | P1-011 | Backend survives simulated native failure without losing process integrity |

## Recommended Order

The minimum sensible implementation order is:

1. P1-001 through P1-003
2. P1-005 through P1-007
3. P1-009 through P1-012
4. P1-013 through P1-015
5. P1-016 through P1-019

## Two-Week Execution Slice

If the team needs a short first sprint, use this cut:

- P1-001
- P1-002
- P1-005
- P1-006
- P1-009
- P1-013

That sprint should end with one visible architectural improvement:

- gateway code is no longer the default home for new command and document semantics

## Done Definition For Phase 1

Phase 1 is complete only when all of the following are true:

- `command-core` owns command registry, validation, and execution planning
- `document-core` owns document session and graph shaping rules
- `freecad-bridge` exposes an explicit contract surface aligned to the bridge contract document
- `api-gateway` acts mainly as routing and protocol composition
- integration tests cover the P0 vertical slice through these boundaries
- backend logs can correlate one request across gateway, command-core, document-core, and bridge layers