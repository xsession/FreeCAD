# FreeCAD Chat Summary - 2026-05-04

## Scope
This session continued the Rust backend migration work inside `variants/asterforge` with the standing goal of turning the AsterForge prototype into a clearer Rust-owned control plane. The work moved beyond planning and documentation into repeated ownership extractions across the native bridge, gateway runtime, gateway domain shaping, and gateway state response projection.

## Outcomes

### 1. Bridge crate decomposition advanced materially
- `variants/asterforge/native/freecad-bridge/src/lib.rs` was reduced to a facade with module declarations, re-exports, and the bridge ABI version function.
- Protocol and contract types were extracted into `contract.rs`.
- model and snapshot mutation logic moved into `model.rs`.
- viewport diff logic moved into `viewport.rs`.
- bridge service areas now live in dedicated modules including `session_store.rs`, `undo.rs`, `workflow.rs`, `runtime.rs`, and `prototype.rs`.

### 2. Gateway command runtime stopped being one large file
- `variants/asterforge/backend/crates/api-gateway/src/app/command_runtime.rs` was slimmed down into orchestration and dispatch.
- STEP command handling moved into `app/step_runtime.rs`.
- extension launcher and inventory flows moved into `app/extension_runtime.rs`.
- bridge vertical-slice and undo or redo command execution moved into `app/bridge_command_runtime.rs`.

### 3. Shared document semantics moved out of gateway
- selection-mode filtering, sketch constraint summary, sketch profile readiness, pad length lookup, and related bridge helpers moved from gateway-owned logic into `variants/asterforge/backend/crates/document-core/src/lib.rs`.
- `document-core` test coverage was extended for those shared helpers.

### 4. Gateway domain shaping was split into focused submodules
- bridge-derived command catalog, task panel, diagnostics, selection, and preselection builders moved into `variants/asterforge/backend/crates/api-gateway/src/domain/bridge_views.rs`.
- shell snapshot, extension compatibility, workbench catalog, menu, toolbar, and layout builders moved into `variants/asterforge/backend/crates/api-gateway/src/domain/shell_views.rs`.
- viewport, viewport diff, and object-tree projection builders moved into `variants/asterforge/backend/crates/api-gateway/src/domain/viewport_views.rs`.
- parsed STEP document-index and scene-bundle translation moved into `variants/asterforge/backend/crates/api-gateway/src/domain/step_views.rs`.
- `variants/asterforge/backend/crates/api-gateway/src/domain.rs` is now primarily DTO definitions, small shared helpers, sample fixtures, and submodule re-exports instead of the previous monolith.

### 5. Gateway state response projection started to split as well
- the `AppModel` response projection entrypoints for viewport, command catalog, shell snapshot, task panel, diagnostics, selection state, and preselection state moved into `variants/asterforge/backend/crates/api-gateway/src/app/state_views.rs`.
- `variants/asterforge/backend/crates/api-gateway/src/app/state.rs` now delegates those view-composition entrypoints instead of owning the full branch logic inline.

### 6. Gateway workspace persistence and property projection also started to split
- workspace persistence, session namespace generation, persisted shell-state load or save, active session id composition, and recent-document bookkeeping moved into `variants/asterforge/backend/crates/api-gateway/src/app/state_workspace.rs`.
- bridge property projection plus STEP object-tree and STEP property-map shaping moved into `variants/asterforge/backend/crates/api-gateway/src/app/state_properties.rs`.
- `variants/asterforge/backend/crates/api-gateway/src/app/state.rs` now delegates those areas instead of owning all workspace and property shaping directly.

### 7. STEP cache and STEP interaction helpers split out of gateway state
- STEP source-path detection, STEP cache resolution, STEP file loading, and active STEP projection moved into `variants/asterforge/backend/crates/api-gateway/src/app/state_step_cache.rs`.
- STEP visibility filtering, PMI inspection, measurement summaries, camera framing, viewport preset helpers, and related STEP-tree traversal helpers moved into `variants/asterforge/backend/crates/api-gateway/src/app/state_step_tools.rs`.
- `variants/asterforge/backend/crates/api-gateway/src/app/state.rs` is now more focused on shared state shape and remaining orchestration instead of owning the full STEP helper surface.

### 8. STEP response builders and bridge-sync transitions were separated further
- STEP selection-state, preselection-state, viewport, task-panel, shell inspection, command-catalog, and diagnostics builders moved into `variants/asterforge/backend/crates/api-gateway/src/app/state_step_views.rs`.
- bridge snapshot synchronization, active-mode selectable object derivation, target selection application, and selection normalization moved into `variants/asterforge/backend/crates/api-gateway/src/app/state_sync.rs`.
- `variants/asterforge/backend/crates/api-gateway/src/app/state.rs` now acts mainly as the central state type plus a thinner facade over focused sibling modules.

### 9. Explicit gateway service wiring is now in code
- a new `variants/asterforge/backend/crates/api-gateway/src/app/services.rs` module now owns the production wiring for bridge, command-core, and document-core service access.
- `variants/asterforge/backend/crates/api-gateway/src/app.rs` now bootstraps `AppState` with an explicit service container instead of relying only on implicit crate-level construction.
- `variants/asterforge/backend/crates/api-gateway/src/app/state.rs`, `command_runtime.rs`, `bridge_command_runtime.rs`, and `state_sync.rs` now consume the service container for bridge runtime access, command validation and planning, and document projection or selection helpers.

### 10. Vertical-slice coverage now crosses the new service boundary
- `variants/asterforge/backend/crates/api-gateway/src/app/state.rs` now includes a broader FCStd workflow test that opens a document, inspects tree and properties, creates a sketch and pad, runs undo or redo, saves, and verifies jobs or events while booted through the explicit service container.
- the same test module now includes a broader STEP workflow test that opens a STEP fixture, resolves the parsed index and scene bundle, inspects tree and properties, and executes focus, measurement, and PMI commands while booted through the explicit service container.
- this is the first concrete landing for `P1-017` against the new `P1-014` seam rather than only relying on narrower unit-style command tests.

### 11. Correlation ids and tracing now cross the service boundary
- `variants/asterforge/backend/crates/api-gateway/src/app/services.rs` now generates per-request correlation ids and uses them when logging bridge access, command validation or planning, and document projection calls.
- gateway command and document entrypoints in `variants/asterforge/backend/crates/api-gateway/src/app/state.rs`, `command_runtime.rs`, `bridge_command_runtime.rs`, and `state_sync.rs` now thread a single correlation id through validation, command dispatch, bridge requests, and state synchronization.
- `variants/asterforge/backend/crates/command-core/src/lib.rs`, `variants/asterforge/backend/crates/document-core/src/lib.rs`, and `variants/asterforge/native/freecad-bridge/src/prototype.rs` now emit structured tracing events so the correlation path is visible beyond the gateway crate itself.
- the default gateway tracing filter in `variants/asterforge/backend/crates/api-gateway/src/app.rs` now enables debug visibility for `asterforge_command_core`, `asterforge_document_core`, and `asterforge_freecad_bridge` in addition to the gateway target.

### 12. Failure-path tracing now has end-to-end assertions
- persistence load and save warnings in `variants/asterforge/backend/crates/api-gateway/src/app/state_workspace.rs` now log with the active request correlation id instead of emitting disconnected warnings.
- `variants/asterforge/backend/crates/api-gateway/src/app/bridge_command_runtime.rs` now emits an explicit gateway-side warning when bridge execution fails, and `variants/asterforge/native/freecad-bridge/src/prototype.rs` now emits a bridge-side warning when command execution hits a missing-session failure.
- `variants/asterforge/backend/crates/api-gateway/src/app/state.rs` now includes integration-style tracing assertions proving the same correlation id survives a bridge-session failure flow and a persistence warning flow.

### 13. The first explicit P1-004 bridge adapter seam is now in code
- `variants/asterforge/backend/crates/command-core/src/lib.rs` now owns a bridge command adapter trait and a shared bridge-dispatch helper that shapes adapter requests, normalizes bridge failures, and decides when an accepted command should reload session state.
- `variants/asterforge/backend/crates/api-gateway/src/app/services.rs` now implements that adapter trait over the existing bridge service wiring instead of forcing the gateway runtime to construct bridge requests by hand.
- `variants/asterforge/backend/crates/api-gateway/src/app/bridge_command_runtime.rs` is now thinner again and mainly applies updated snapshots back into `AppModel` before running the existing gateway sync path.

### 14. Document open now uses the explicit bridge session contract
- `variants/asterforge/backend/crates/api-gateway/src/app/services.rs` now opens document sessions through `FreecadBridgeContract::open_document_session`, then resolves the stored snapshot from the bridge session store instead of bypassing the contract and calling the direct snapshot helper on the main path.
- `variants/asterforge/backend/crates/api-gateway/src/app/state.rs` now uses a pending session id during bootstrap and document-open flows so the explicit contract path can be exercised before the final active session id is known.
- `variants/asterforge/backend/crates/api-gateway/src/app/state.rs` now includes an integration-style tracing assertion proving the same correlation id appears in both the gateway document-open log and the bridge-side session-open log.

### 15. The document-open fallback path is now directly unit tested
- `variants/asterforge/backend/crates/api-gateway/src/app/services.rs` now extracts the contract-open plus fallback behavior into a testable helper instead of leaving that logic embedded only inside the production bridge service method.
- the same module now includes direct tests covering contract success, fallback when session open fails, and fallback when the session opens but no retrievable snapshot is available.

### 16. Runtime descriptor fallback now uses the same service-seam pattern
- `variants/asterforge/backend/crates/api-gateway/src/app/services.rs` now owns bridge runtime-descriptor fallback policy instead of leaving that behavior duplicated between gateway bootstrap and `AppState::bridge_runtime_descriptor`.
- the same module now includes direct tests covering both successful runtime descriptor lookup and fallback to the default descriptor when the bridge contract reports a failure.
- `variants/asterforge/backend/crates/api-gateway/src/app.rs` and `variants/asterforge/backend/crates/api-gateway/src/app/state.rs` now both consume the shared bridge service helper instead of reimplementing fallback behavior inline.

### 17. Startup model assembly is now split out of `state.rs`
- `variants/asterforge/backend/crates/api-gateway/src/app/state_bootstrap.rs` now owns the initial `AppModel` assembly path, including bridge snapshot acquisition, document projection, object-tree and property bootstrap, default shell state, and persisted-workspace application.
- `variants/asterforge/backend/crates/api-gateway/src/app/state.rs` now delegates startup assembly to that helper instead of constructing the initial model inline.
- the new bootstrap module includes focused coverage proving persisted workspace state is applied during startup bootstrap.

### 18. Document-open reset and activity bootstrap are now split out of `state.rs`
- `variants/asterforge/backend/crates/api-gateway/src/app/state_open.rs` now owns the document-open reset path, including cache clearing, extension-compatibility reset, snapshot resynchronization, active STEP projection, open-job creation, and open-event emission.
- `variants/asterforge/backend/crates/api-gateway/src/app/state.rs` now keeps only the async document-open entrypoint, bridge snapshot acquisition, and persistence boundary while delegating the mutation-heavy model update path to that sibling helper.
- the new module includes focused tests proving the open-document stage labels stay correct for both FCStd and STEP document flows.

### 19. Selection mutation flow is now split out of `state.rs`
- `variants/asterforge/backend/crates/api-gateway/src/app/state_selection.rs` now owns the preselection, selection, and selection-mode mutation paths, including validation, step-aware selection constraints, snapshot synchronization, and event emission.
- `variants/asterforge/backend/crates/api-gateway/src/app/state.rs` now keeps the async selection entrypoints and persistence boundary while delegating the mutation-heavy selection flow to that sibling helper.
- the focused suites stayed green after this extraction without changing the current test count.

### 20. Shell and workbench mutation flow is now split out of `state.rs`
- `variants/asterforge/backend/crates/api-gateway/src/app/state_shell.rs` now owns workbench activation plus shell panel and shell session mutation paths, including workbench validation, panel tab or visibility or size updates, inactive session cleanup, and shell-facing event emission.
- `variants/asterforge/backend/crates/api-gateway/src/app/state.rs` now keeps the async shell or workbench entrypoints and persistence boundary while delegating those mutation-heavy updates to the sibling helper.
- the focused suites stayed green after this extraction without changing the current test count.

### 21. Undo or redo now uses an explicit history adapter seam
- `variants/asterforge/backend/crates/command-core/src/lib.rs` now owns a shared history-command adapter trait and execution helper alongside the earlier bridge-command adapter seam.
- `variants/asterforge/backend/crates/api-gateway/src/app/services.rs` now exposes a dedicated history adapter service that translates the shared history action into the concrete `freecad-bridge` undo helper.
- `variants/asterforge/backend/crates/api-gateway/src/app/bridge_command_runtime.rs` no longer calls bridge undo helpers directly and now routes undo or redo through the shared `command-core` helper.

### 22. Read-side snapshot and query builders are now split out of `state.rs`
- `variants/asterforge/backend/crates/api-gateway/src/app/state_query.rs` now owns snapshot shaping, boot-payload shaping, and the document-scoped read-query builders for object tree, properties, events, viewport, shell snapshot, command catalog, history, diagnostics, selection, preselection, and jobs.
- `variants/asterforge/backend/crates/api-gateway/src/app/state.rs` now keeps the async read entrypoints and protocol conversions while delegating the actual read-side payload shaping to that sibling helper.
- the focused suites stayed green after this extraction without changing the current test count.

### 23. HTTP-facing request DTOs moved out of `state.rs`
- `variants/asterforge/backend/crates/api-gateway/src/app/state_requests.rs` now owns the HTTP-facing request DTOs for document open, selection, selection mode, workbench activation, preselection, and shell mutations, plus the small `SelectionResponse` DTO.
- `variants/asterforge/backend/crates/api-gateway/src/app/routes.rs`, `state_proto.rs`, `state_mutations.rs`, `state_selection.rs`, `state_shell.rs`, `protocol.rs`, and the `state.rs` integration tests now consume that dedicated DTO module directly.
- the focused suites stayed green after this extraction while keeping 58 `api-gateway` tests, 24 `command-core` tests, 7 `document-core` tests, and 14 `freecad-bridge` tests passing.

### 24. Top-level snapshot payload DTOs moved out of `state.rs`
- `variants/asterforge/backend/crates/api-gateway/src/app/state_payloads.rs` now owns the top-level `AppSnapshot` and `BootPayload` DTOs used by state reads, routes, and protocol conversion.
- `variants/asterforge/backend/crates/api-gateway/src/app/state_query.rs`, `state_reads.rs`, `routes.rs`, and `protocol.rs` now consume that dedicated payload module directly.
- the focused suites stayed green after this extraction while keeping 58 `api-gateway` tests, 24 `command-core` tests, 7 `document-core` tests, and 14 `freecad-bridge` tests passing.

### 25. Shared gateway state structs moved out of `state.rs`
- `variants/asterforge/backend/crates/api-gateway/src/app/state_types.rs` now owns `AppModel`, `PersistedWorkspaceState`, and the shared STEP cache or measurement or PMI or camera structs used across the gateway state helpers.
- the runtime, STEP, read, bootstrap, workspace, and model helper modules now import those types directly from `state_types.rs` instead of routing them back through `state.rs`.
- the focused suites stayed green after this extraction while keeping 58 `api-gateway` tests, 24 `command-core` tests, 7 `document-core` tests, and 14 `freecad-bridge` tests passing.

### 26. Gateway bootstrap no longer bypasses the bridge runtime seam
- `variants/asterforge/backend/crates/api-gateway/src/app.rs` now reads the bridge runtime descriptor through `AppState::bridge_runtime_descriptor()` instead of calling `services.bridge.describe_runtime(...)` directly during bootstrap.
- this keeps the bootstrap path aligned with the existing read-side bridge seam in `state_reads.rs` and `bridge_services.rs` instead of leaving a top-level one-off runtime lookup in the composition root.
- the focused suites stayed green after this tightening while keeping 58 `api-gateway` tests, 24 `command-core` tests, 7 `document-core` tests, and 14 `freecad-bridge` tests passing.

### 27. The large AppState test host moved out of `state.rs`
- `variants/asterforge/backend/crates/api-gateway/src/app/state_tests.rs` now owns the broad integration-style `AppState` test host that previously lived at the bottom of `state.rs`.
- `variants/asterforge/backend/crates/api-gateway/src/app.rs` now wires that test module at the app level, and `state.rs` is now production-only facade code plus constants instead of mixing production surface and long test bodies.
- the focused suites stayed green after this extraction while keeping 58 `api-gateway` tests, 24 `command-core` tests, 7 `document-core` tests, and 14 `freecad-bridge` tests passing.

### 28. Bridge snapshot projection now goes through the service container
- `variants/asterforge/backend/crates/api-gateway/src/app/services.rs` now owns a shared `project_bridge_snapshot(...)` helper that shapes gateway-facing document state, object tree, selected object, and property map from a bridge snapshot.
- `variants/asterforge/backend/crates/api-gateway/src/app/state_bootstrap.rs` and `variants/asterforge/backend/crates/api-gateway/src/app/state_sync.rs` now both use that shared projection helper instead of hand-assembling the same bridge-derived state in multiple places.
- the focused suites stayed green after this tightening while keeping 58 `api-gateway` tests, 24 `command-core` tests, 7 `document-core` tests, and 14 `freecad-bridge` tests passing.

### 29. Startup restore warnings now have explicit bootstrap tracing coverage
- `variants/asterforge/backend/crates/api-gateway/src/app/state_lifecycle.rs` now emits an explicit `bootstrapping app state` trace with the startup correlation id before persisted shell-state restore and bootstrap assembly run.
- `variants/asterforge/backend/crates/api-gateway/src/app/state_tests.rs` now includes a bootstrap-time integration-style assertion proving an invalid persisted shell-state parse warning preserves that same correlation id through the surrounding startup flow.
- the focused suites stayed green after this hardening while keeping 59 `api-gateway` tests, 24 `command-core` tests, 7 `document-core` tests, and 14 `freecad-bridge` tests passing.

### 30. Startup restore read failures now use the same correlation contract
- `variants/asterforge/backend/crates/api-gateway/src/app/state_tests.rs` now also includes a bootstrap-time integration-style assertion proving an unreadable persisted shell-state path preserves the same startup correlation id.
- this closes the immediate gap between persisted-state parse warnings and persisted-state read warnings, so both startup restore warning classes now sit on the same observable bootstrap trace chain.
- the focused suites stayed green after this hardening while keeping 60 `api-gateway` tests, 24 `command-core` tests, 7 `document-core` tests, and 14 `freecad-bridge` tests passing.

## Validation
- Focused validation remained green throughout the latest extractions with:
  - `C:\Users\livanyi\.cargo\bin\cargo.exe test -p asterforge-document-core -p asterforge-api-gateway -p asterforge-freecad-bridge`
- At the end of the session, the focused suites passed cleanly with:
  - 50 `api-gateway` tests passing
  - 22 `command-core` tests passing
  - 7 `document-core` tests passing
  - 14 `freecad-bridge` tests passing

- After adding direct fallback coverage for document-open through the bridge service seam, the focused suites passed with:
  - 53 `api-gateway` tests passing
  - 22 `command-core` tests passing
  - 7 `document-core` tests passing
  - 14 `freecad-bridge` tests passing

- After extracting runtime-descriptor fallback into the bridge service seam, the focused suites passed with:
  - 55 `api-gateway` tests passing
  - 22 `command-core` tests passing
  - 7 `document-core` tests passing
  - 14 `freecad-bridge` tests passing

- After extracting startup model assembly into `state_bootstrap.rs`, the focused suites passed with:
  - 56 `api-gateway` tests passing
  - 22 `command-core` tests passing
  - 7 `document-core` tests passing
  - 14 `freecad-bridge` tests passing

- After extracting document-open reset and activity bootstrap into `state_open.rs`, the focused suites passed with:
  - 58 `api-gateway` tests passing
  - 22 `command-core` tests passing
  - 7 `document-core` tests passing
  - 14 `freecad-bridge` tests passing

- After introducing the shared history adapter seam for undo or redo execution, the focused suites passed with:
  - 58 `api-gateway` tests passing
  - 24 `command-core` tests passing
  - 7 `document-core` tests passing
  - 14 `freecad-bridge` tests passing

- After extracting snapshot, boot payload, and document-scoped read-query builders into `state_query.rs`, the focused suites still passed with:
  - 58 `api-gateway` tests passing
  - 24 `command-core` tests passing
  - 7 `document-core` tests passing
  - 14 `freecad-bridge` tests passing

- After moving viewport diff computation behind `bridge_services.rs`, the focused suites still passed with:
  - 58 `api-gateway` tests passing
  - 24 `command-core` tests passing
  - 7 `document-core` tests passing
  - 14 `freecad-bridge` tests passing

- After moving workspace-session snapshot sync behind `bridge_services.rs`, the focused suites still passed with:
  - 58 `api-gateway` tests passing
  - 24 `command-core` tests passing
  - 7 `document-core` tests passing
  - 14 `freecad-bridge` tests passing

- After extracting HTTP-facing request DTOs and the selection response DTO into `state_requests.rs`, the focused suites still passed with:
  - 58 `api-gateway` tests passing
  - 24 `command-core` tests passing
  - 7 `document-core` tests passing
  - 14 `freecad-bridge` tests passing

- After extracting `AppSnapshot` and `BootPayload` into `state_payloads.rs`, the focused suites still passed with:
  - 58 `api-gateway` tests passing
  - 24 `command-core` tests passing
  - 7 `document-core` tests passing
  - 14 `freecad-bridge` tests passing

- After extracting `AppModel`, `PersistedWorkspaceState`, and the shared STEP state structs into `state_types.rs`, the focused suites still passed with:
  - 58 `api-gateway` tests passing
  - 24 `command-core` tests passing
  - 7 `document-core` tests passing
  - 14 `freecad-bridge` tests passing

- After routing gateway bootstrap runtime descriptor lookup through `AppState`, the focused suites still passed with:
  - 58 `api-gateway` tests passing
  - 24 `command-core` tests passing
  - 7 `document-core` tests passing
  - 14 `freecad-bridge` tests passing

- After moving the `AppState` integration-style test host into `state_tests.rs`, the focused suites still passed with:
  - 58 `api-gateway` tests passing
  - 24 `command-core` tests passing
  - 7 `document-core` tests passing
  - 14 `freecad-bridge` tests passing

- After centralizing bridge snapshot projection through `app/services.rs`, the focused suites still passed with:
  - 58 `api-gateway` tests passing
  - 24 `command-core` tests passing
  - 7 `document-core` tests passing
  - 14 `freecad-bridge` tests passing

- After adding explicit startup bootstrap tracing and persisted-state restore warning correlation coverage, the focused suites still passed with:
  - 59 `api-gateway` tests passing
  - 24 `command-core` tests passing
  - 7 `document-core` tests passing
  - 14 `freecad-bridge` tests passing

- After extending startup restore correlation coverage to unreadable persisted-state paths, the focused suites still passed with:
  - 60 `api-gateway` tests passing
  - 24 `command-core` tests passing
  - 7 `document-core` tests passing
  - 14 `freecad-bridge` tests passing

## Current Status
- `freecad-bridge` is no longer a single-file prototype surface.
- `api-gateway` command family handling is split into dedicated runtime modules.
- `api-gateway` domain shaping is split across dedicated submodules instead of a monolithic `domain.rs`.
- `api-gateway` state response projection, workspace persistence, property projection, STEP cache handling, STEP interaction helpers, STEP response builders, and bridge-sync transitions have started to split through `app/state_views.rs`, `app/state_workspace.rs`, `app/state_properties.rs`, `app/state_step_cache.rs`, `app/state_step_tools.rs`, `app/state_step_views.rs`, and `app/state_sync.rs`, leaving `app/state.rs` much thinner than at the start of the session.
- `api-gateway` command runtime now routes viewport diff computation through `app/bridge_services.rs`, and workspace bookkeeping routes remembered-document session snapshot sync through the same seam, reducing two more direct dependencies on bridge helper internals from gateway orchestration.
- `api-gateway` now also isolates the HTTP-facing request DTO block in `app/state_requests.rs`, leaving `app/state.rs` closer to state definitions, core boot payloads, thin delegating methods, and integration-style tests.
- `api-gateway` now also isolates the top-level snapshot and boot payload DTOs in `app/state_payloads.rs`, leaving `app/state.rs` closer to state definitions, thin delegating methods, and integration-style tests.
- `api-gateway` now also isolates the shared gateway state structs in `app/state_types.rs`, leaving `app/state.rs` closer to constants, thin delegating methods, and integration-style tests.
- `api-gateway` now also isolates the large `AppState` integration-style test host in `app/state_tests.rs`, leaving `app/state.rs` closer to constants and thin delegating methods.
- `api-gateway` now also centralizes bridge snapshot projection in `app/services.rs`, so bootstrap and bridge resync no longer separately rebuild the same gateway-facing projection state.
- `api-gateway` now also emits an explicit bootstrap trace from `app/state_lifecycle.rs`, making startup restore warnings part of the observable correlation contract instead of opaque one-off warnings.
- `api-gateway` now also covers both persisted-state parse failures and persisted-state read failures with startup correlation assertions, so restore warnings no longer have a blind spot between malformed and unreadable state files.
- `api-gateway` now also has an explicit service composition layer in `app/services.rs`, which is the first real landing for `P1-014` rather than only a backlog target.
- `document-core` owns more genuine shared semantics than it did at the start of the session, especially around bridge document interpretation.

## Continuation Plan

### 32. Viewport diff computation now goes through the bridge seam
- `variants/asterforge/backend/crates/api-gateway/src/app/bridge_services.rs` now owns `diff_viewport(...)` so the gateway command runtime no longer imports the bridge viewport helper directly.
- `variants/asterforge/backend/crates/api-gateway/src/app/command_runtime.rs` now computes mutating-command viewport diffs through the shared bridge service seam instead of calling `freecad-bridge` helpers inline.
- the focused suites stayed green after this extraction while keeping 58 `api-gateway` tests, 24 `command-core` tests, 7 `document-core` tests, and 14 `freecad-bridge` tests passing.

### 33. Workspace bridge-session sync now goes through the bridge seam
- `variants/asterforge/backend/crates/api-gateway/src/app/bridge_services.rs` now owns `sync_session_snapshot(...)` so gateway workspace bookkeeping no longer calls prototype bridge helpers directly.
- `variants/asterforge/backend/crates/api-gateway/src/app/state_workspace.rs`, `state_sync.rs`, `state_selection.rs`, `state_shell.rs`, `state_open.rs`, `state_bootstrap.rs`, and `state_model.rs` now thread `AppServices` through remembered-document updates so the bridge session snapshot sync stays behind the shared bridge service seam.
- the focused suites stayed green after this extraction while keeping 58 `api-gateway` tests, 24 `command-core` tests, 7 `document-core` tests, and 14 `freecad-bridge` tests passing.

### Priority 1: Harden the new service boundary
- decide which remaining gateway-owned transitions should move behind `app/services.rs` or `app/bridge_services.rs` versus remain transport-layer facade logic.
- keep the container thin and explicit rather than letting it become a second monolith.

### Priority 2: Add vertical-slice coverage across the new seams
- extend the new `P1-017` coverage beyond the landed bridge-session failure and persistence warning cases into more mixed command families, startup restore failures, and deeper STEP failure edges.

### Priority 3: Deepen the tracing contract
- push the new `P1-018` correlation path past the newly covered bridge-session and persistence warning flows into more bridge error categories, startup restore warnings, and failure paths that span multiple backend services.

### Priority 4: Revisit explicit bridge adapters
- continue `P1-004` by replacing more hard-coded bridge behavior with explicit adapters now that the first command-core bridge seam is in place and covered by unit plus integration tests.

### Priority 5: Keep converting bridge flows onto the explicit contract
- remove more remaining direct helper usage in favor of session or runtime operations that go through `FreecadBridgeContract` and the service-container seam first.

### Priority 6: Reassess what still belongs in `document-core`
- identify any remaining gateway-owned logic that is actually shared document semantics rather than transport or shell composition.
- move only the genuinely reusable pieces into `variants/asterforge/backend/crates/document-core/src/lib.rs`.

## Files Changed In This Session
- `docs/FREECAD_RUST_PHASE1_EXECUTION_BACKLOG.md`
- `variants/asterforge/backend/crates/api-gateway/src/app/state_requests.rs`
- `variants/asterforge/backend/crates/api-gateway/src/app/state_payloads.rs`
- `variants/asterforge/backend/crates/api-gateway/src/app/state_types.rs`
- `variants/asterforge/backend/crates/api-gateway/src/app/state_tests.rs`
- `variants/asterforge/native/freecad-bridge/src/lib.rs`
- `variants/asterforge/native/freecad-bridge/src/contract.rs`
- `variants/asterforge/native/freecad-bridge/src/model.rs`
- `variants/asterforge/native/freecad-bridge/src/viewport.rs`
- `variants/asterforge/native/freecad-bridge/src/session_store.rs`
- `variants/asterforge/native/freecad-bridge/src/undo.rs`
- `variants/asterforge/native/freecad-bridge/src/workflow.rs`
- `variants/asterforge/native/freecad-bridge/src/runtime.rs`
- `variants/asterforge/native/freecad-bridge/src/prototype.rs`
- `variants/asterforge/backend/crates/api-gateway/src/app.rs`
- `variants/asterforge/backend/crates/api-gateway/src/app/command_runtime.rs`
- `variants/asterforge/backend/crates/api-gateway/src/app/step_runtime.rs`
- `variants/asterforge/backend/crates/api-gateway/src/app/extension_runtime.rs`
- `variants/asterforge/backend/crates/api-gateway/src/app/bridge_command_runtime.rs`
- `variants/asterforge/backend/crates/api-gateway/src/app/state.rs`
- `variants/asterforge/backend/crates/api-gateway/src/app/state_views.rs`
- `variants/asterforge/backend/crates/api-gateway/src/app/state_workspace.rs`
- `variants/asterforge/backend/crates/api-gateway/src/app/state_properties.rs`
- `variants/asterforge/backend/crates/api-gateway/src/app/state_step_cache.rs`
- `variants/asterforge/backend/crates/api-gateway/src/app/state_step_tools.rs`
- `variants/asterforge/backend/crates/api-gateway/src/app/state_step_views.rs`
- `variants/asterforge/backend/crates/api-gateway/src/app/state_sync.rs`
- `variants/asterforge/backend/crates/api-gateway/src/app/services.rs`
- `variants/asterforge/backend/crates/api-gateway/src/domain.rs`
- `variants/asterforge/backend/crates/api-gateway/src/domain/bridge_views.rs`
- `variants/asterforge/backend/crates/api-gateway/src/domain/shell_views.rs`
- `variants/asterforge/backend/crates/api-gateway/src/domain/viewport_views.rs`
- `variants/asterforge/backend/crates/api-gateway/src/domain/step_views.rs`
- `variants/asterforge/backend/crates/document-core/src/lib.rs`

## Practical Next Step
Use the new `variants/asterforge/backend/crates/api-gateway/src/app/services.rs` boundary to drive the next phase: add integration-style coverage across the composed services and only keep shrinking `state.rs` where a remaining cluster still has clear ownership value.