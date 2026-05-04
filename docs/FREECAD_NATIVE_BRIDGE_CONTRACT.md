# FreeCAD Native Bridge Contract

Status: first working contract for the Rust-authoritative backend program as of 2026-05-04

## 1. Purpose

This document defines the first explicit contract between the Rust backend and native FreeCAD or OCCT-backed execution layers.

It is the required contract boundary for:

- `variants/asterforge/backend/crates/api-gateway`
- `variants/asterforge/backend/crates/command-core`
- `variants/asterforge/backend/crates/document-core`
- `variants/asterforge/native/freecad-bridge`

The contract exists to prevent the backend from drifting into one of two failure modes:

- Rust becomes a thin pass-through wrapper over arbitrary native calls
- frontend and backend work continue depending on undocumented legacy native behavior

## 2. Contract Principles

1. Rust is the caller of record for all migrated workflows.
2. Native code must expose explicit capability contracts, not ambient runtime behavior.
3. Each bridge call must be bounded by timeout, cancellation, and structured error reporting.
4. Bridge payloads must be versioned and serializable.
5. Bridge responses must not leak raw Qt or GUI-layer objects.
6. Native workers may fail; the app session must survive that failure.
7. The contract optimizes for correctness and containment first, then performance.

## 3. Execution Topology

### 3.1 Required Runtime Shape

The bridge contract assumes this topology:

```text
React shell
  -> Rust backend
      -> command-core / document-core
          -> native bridge host
              -> FreeCAD / OCCT / Python worker processes or libraries
```

### 3.2 In-Process Versus Worker Process Rules

In-process native execution is acceptable only when all of these are true:

- the operation is read-mostly or low-risk
- failure will not corrupt active session ownership in Rust
- restart isolation is not required
- latency benefit is material

Out-of-process worker execution is required when any of these are true:

- the operation can crash due to OCCT or legacy runtime instability
- the operation may hang or run for long periods
- Python or plugin execution is involved
- import/export depends on unstable or third-party native stacks
- parallel worker scaling is needed later

Default rule:

- document extraction, geometry mutation, import/export, and Python execution should be treated as worker-oriented operations unless proven safe otherwise

## 4. Contract Surface

The first bridge version must support six service families.

### 4.1 Capability Handshake

Purpose:

- determine what the native side can actually do at runtime

Required response fields:

- bridge protocol version
- worker mode
- detected FreeCAD runtime version
- detected OCCT version if available
- capability flags
- supported file families
- known limitations

Current repository anchor:

- `variants/asterforge/native/freecad-bridge/src/lib.rs`

Current gap:

- the bridge exposes `BridgeStatus` and `BridgeCapabilities`, but not yet a sufficiently explicit negotiated contract

### 4.2 Document Session Service

Purpose:

- open, inspect, save, close, and recover native-backed documents through Rust-owned session identifiers

Required operations:

- `open_document`
- `save_document`
- `save_document_as`
- `close_document`
- `recover_document`
- `fetch_document_summary`
- `fetch_document_graph_snapshot`

Required request shape:

- Rust-generated `session_id`
- source path or recovery token
- requested workbench or import context if relevant
- timeout budget

Required response shape:

- `document_id`
- display name
- file path
- dirty state
- workbench hint
- native document token opaque to Rust callers beyond the bridge host

Rules:

- Rust owns session ids and lifecycle
- native document pointers or handles must never leave the bridge boundary in raw form

### 4.3 Object Graph And Property Service

Purpose:

- fetch the native-backed object graph and property projection needed to build Rust-owned document state

Required operations:

- `fetch_object_tree`
- `fetch_feature_history`
- `fetch_dependency_edges`
- `fetch_property_groups`
- `fetch_selection_snapshot`

Required response shape:

- stable object ids
- parent-child relationships
- source and dependency references where available
- property groups with typed values and editability metadata
- history marker and suppression state

Rules:

- this is a projection surface, not permission for the frontend to rely on native internals
- Rust reconstructs canonical state from these payloads

Current repository anchors:

- `variants/asterforge/backend/crates/document-core/src/lib.rs`
- `variants/asterforge/backend/crates/api-gateway/src/app/state.rs`

Current gap:

- graph and property logic still lives mostly in gateway and bridge snapshot shaping instead of a clean bridge service contract

### 4.4 Command Execution Service

Purpose:

- allow Rust-owned commands to request native execution without surrendering ownership of validation or workflow semantics

Required operations:

- `execute_native_command`
- `recompute_document`
- `undo_native`
- `redo_native`

Required request shape:

- `command_id`
- `session_id`
- target object ids or subelement refs
- typed arguments
- transaction mode
- timeout budget
- tracing or correlation id

Required response shape:

- accepted or rejected status
- structured warning or error details
- dirty-state change
- changed object ids
- recompute summary
- updated history marker state

Rules:

- enablement and argument validation are owned by Rust before the bridge call
- native execution may reject invalid context, but must return structured failure data
- Rust translates bridge results into canonical events, jobs, and document deltas

Current repository anchors:

- `variants/asterforge/backend/crates/command-core/src/lib.rs`
- `variants/asterforge/backend/crates/api-gateway/src/app/command_runtime.rs`

Current gap:

- command runtime logic is still implemented directly inside `api-gateway` instead of through a dedicated bridge execution interface

### 4.5 Viewport And Tessellation Service

Purpose:

- return backend-owned scene payloads and incremental viewport diffs without exposing legacy viewer objects

Required operations:

- `fetch_viewport_snapshot`
- `fetch_viewport_diff`
- `fetch_drawable_subset`
- `focus_object`
- `fit_all`

Required response shape:

- camera state
- drawable ids
- stable object references
- bounds
- topology or selection hooks where available
- diff payloads for add, remove, modify, and camera changes

Rules:

- the bridge owns extraction from native geometry or view state
- the frontend never depends on native scene graph semantics directly

Current repository anchor:

- `variants/asterforge/native/freecad-bridge/src/lib.rs`

Current gap:

- the current bridge payloads are still prototype-oriented and 2D-ish compared with a production CAD viewport contract

### 4.6 Import, Export, And Exchange Service

Purpose:

- wrap legacy format handling and future standards services behind one Rust-facing gateway

Required operations:

- `import_file`
- `export_file`
- `inspect_exchange_capabilities`
- `validate_exchange_result`

Required response shape:

- format family
- import or export result summary
- diagnostics and warnings
- created or modified document ids
- roundtrip metadata if available

Rules:

- Rust owns orchestration, policy, auditing, and user-facing diagnostics
- native or external codecs remain behind the bridge until replacement value is proven

## 5. Error Model

Every bridge response must resolve into one of these categories:

- `ok`
- `validation_error`
- `native_error`
- `timeout`
- `cancelled`
- `worker_crashed`
- `unsupported`

Minimum error payload:

- category
- stable error code
- user-safe summary
- technical detail
- correlation id
- session id if applicable
- command id or operation id

Rules:

- `panic`, exceptions, raw tracebacks, and OCCT diagnostics must be normalized before they leave the bridge boundary

## 6. Timeout And Cancellation Policy

All bridge operations require:

- default timeout budget
- optional caller override within safe limits
- cancellation token or equivalent cancellation path
- clear statement on whether the operation is retry-safe

Baseline defaults:

- document metadata fetch: 2 to 5 seconds
- object tree and properties: 2 to 10 seconds depending on document size
- command execution and recompute: 10 to 120 seconds depending on command class
- import and export: workflow-specific, but always bounded and cancellable

## 7. Security And Trust Boundaries

The bridge contract is also a trust boundary.

Required rules:

- plugin and macro execution must not share the same trust tier as core document inspection
- reviewed and trusted execution lanes must be explicit
- bridge host must record execution provenance for extension-triggered operations
- Rust must be able to deny execution before the bridge is invoked

## 8. First Version Scope

Version 1 of the bridge contract should support only the P0 workflow set:

- open document
- save document
- fetch object tree
- fetch properties
- fetch feature history
- run PartDesign vertical-slice commands already exercised in AsterForge
- recompute
- undo and redo
- fetch viewport snapshot and diff
- STEP document and scene extraction already present in the prototype

Everything else is deferred until V1 is stable.

## 9. Required Refactors In Current Tree

To align the repository with this contract, the following refactors should happen first:

1. move command execution semantics out of `variants/asterforge/backend/crates/api-gateway/src/app/command_runtime.rs` into `command-core` plus a bridge adapter layer
2. move document-state shaping and graph ownership out of `variants/asterforge/backend/crates/api-gateway/src/app/state.rs` into `document-core`
3. turn `variants/asterforge/native/freecad-bridge/src/lib.rs` from a snapshot helper crate into an explicit bridge service surface
4. define protocol-versioned bridge DTOs that are not coupled to current shell-only HTTP shapes

## 10. Acceptance Tests

The bridge contract is not accepted until these tests exist:

- capability handshake test
- open or save roundtrip test for FCStd fixtures
- command execution test for PartDesign sketch, pad, and pocket vertical slice
- undo or redo consistency test
- viewport diff correctness test
- worker crash containment test
- timeout and cancellation test
- STEP extraction contract test

## 11. Non-Goals

This contract does not attempt to:

- redesign OCCT
- rewrite FreeCAD geometry internals
- expose raw GUI internals to the frontend
- promise blanket compatibility for all existing Python and Qt extensions in V1