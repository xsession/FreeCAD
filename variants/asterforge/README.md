# AsterForge

AsterForge is the first implementation workspace for the React + Rust FreeCAD variant described in [`FREECAD_REACT_RUST_VARIANT_PLAN.md`](/C:/GIT/FreeCAD/FREECAD_REACT_RUST_VARIANT_PLAN.md).

This folder intentionally starts as a standalone workspace so we can iterate on the new architecture without destabilizing the existing C++/Qt application.

## Windows Entry Point

- `build.bat` builds the Rust workspace and the React frontend from the AsterForge root.
- `build.bat run` builds first, then starts the backend and frontend dev servers in separate Windows terminals.

## Week 1 Scope

- protocol package with document, selection, property, and command schemas
- Rust backend `api-gateway` skeleton
- native `freecad-bridge` placeholder crate
- React app shell prototype
- initial object tree and property metadata payload definitions

## Layout

```text
variants/asterforge/
  backend/
    crates/
      api-gateway/
  frontend/
    app/
  native/
    freecad-bridge/
  protocol/
    proto/
    schemas/
  docs/
    adr/
```

## Current State

The code here is now a runnable separate-program slice, not just a static scaffold.

- The Rust backend exposes live HTTP endpoints for boot payloads, object trees, property fetches, events, and command execution.
- The Rust backend now also exposes a bridge-backed viewport payload so the UI renders backend-owned scene data.
- The backend also serves workbench command metadata and a task-panel payload so the UI can drive workflows from backend-owned semantics.
- The mock `partdesign.pad` command now performs a real backend state mutation against the bridge snapshot and refreshes the tree, viewport, properties, and workflow panels.
- Sketch-driven pad creation now accepts explicit length input from the task panel instead of always using the default mock extrusion depth.
- The mock `partdesign.edit_pad` flow now updates pad length through the backend and reflects the change in the viewport, property panel, and task panel.
- The mock `partdesign.new_sketch` flow now creates a sketch inside the selected body and advances the workflow toward pad creation.
- The mock `partdesign.pocket` and `partdesign.edit_pocket` flows now support subtractive feature creation and depth editing from the selected sketch or pocket.
- The backend now exposes explicit feature-history data so the shell can show sequence order and sketch-to-feature relationships as a timeline.
- Timeline entries can now suppress and unsuppress features through backend-owned history state, and suppressed features drop out of the viewport.
- Dependency-aware history state now marks downstream features inactive when an upstream sketch or feature is suppressed, and the command/task surfaces react to that model state.
- The property panel now includes dependency-state metadata and pocket depth values instead of falling back to generic placeholders.
- The timeline now supports rollback-to-here and full-history resume, with backend-owned model evaluation markers reflected in the viewport and dependency state.
- The command catalog now exposes backend-owned argument metadata, action labels, and undo/redo availability so the shell can render suggested actions without hardcoded React-only modeling forms.
- Sketch creation, pad creation/editing, and pocket creation/editing now persist richer mock definition data such as reference plane, symmetric-pad mode, and pocket extent mode through backend-owned command arguments, property groups, and task-panel actions.
- Sketch workflow surfaces now use bridge-backed metadata for constraint count, profile readiness, and solver state instead of hardcoded placeholder text.
- The task panel now derives its primary workflow guidance for sketch, pad, pocket, and body states from bridge-owned helpers rather than route-layer prose templates.
- Dependency and inactive-state task-panel guidance now also routes through bridge-owned helpers, so the main workflow prose no longer depends on `domain.rs` string templates.
- The React shell now promotes backend-owned quick actions such as undo, redo, recompute, save, focus, and resume-history directly into the viewport workspace chrome.
- The React shell now presents a FreeCAD-style desktop frame with classic menubar and toolbar rows, top document tabs, a left combo view, a dominant central viewport, a bottom utility dock, and a live status bar instead of the earlier dashboard-first composition.
- The combo view now mirrors FreeCAD more closely by keeping the model tree and data/property surfaces together in the Model tab, while the Tasks tab hosts the active task workflow and selection guidance.
- The shell also maintains a lightweight recent-document strip and a notice rail that surfaces the latest backend events and command outcomes without forcing users to scan the full activity feed.
- The shell now also keeps a tab-style session rail for recently opened documents, giving the workspace a more document-centric desktop feel even while the backend still exposes a single active document session.
- The shell now includes a searchable command palette opened from the chrome or with `Ctrl+K`, driven entirely by backend command definitions rather than a separate frontend-only registry.
- The backend now owns an explicit selection-state payload, including selectable mode groups for objects, bodies, sketches, and downstream features.
- The backend now also owns a lightweight preselection-state payload so hover candidates are tracked through the same service boundary as committed selection.
- Preselection payloads now also include backend-derived model state, dependency notes, and suggested command ids, so hover can preview workflow intent instead of only object identity.
- The frontend shell now includes a dedicated selection inspector that consolidates the selected object, model-state status, viewport presence, focused properties, and currently enabled commands into a single backend-driven context panel.
- The viewport lane now includes a backend-driven selection-mode rail that can retarget the current focus when users switch between body, sketch, feature, and full-object selection contexts.
- Tree and viewport hover now publish backend-owned preselection candidates and surface them in the workspace chrome, giving the shell a first explicit hover/preselection event loop.
- The viewport overlay and selection inspector now translate those backend hover hints into immediate guidance chips and candidate action previews.
- Those hover guidance chips can now also promote directly into backend commands by selecting the hovered candidate and executing the requested action.
- Hovered candidates can now also open inline backend-driven argument forms for parameterized actions such as sketch-to-pad or sketch-to-pocket promotion, instead of always relying on command defaults.
- Command execution now also feeds a backend-owned jobs slice, so the shell can show recent task outcomes and progress-like status through a dedicated jobs panel instead of only notice text.
- Jobs now also carry stage histories such as queueing, bridge mutation, viewport sync, and completion so the shell can present a first real progress model instead of only flat completed/failed rows.
- Document open now also enters that same backend-owned jobs model with staged lifecycle markers, so opening a file participates in the same supervision surface as modeling commands.
- The tree and viewport now render that backend selection mode directly by dimming incompatible objects and only exposing live hit targets for selectable items, so the shell’s affordances stay aligned with backend selection authority.
- The shell now also includes a diagnostics panel that summarizes timeline health, viewport state, event-stream status, last-command outcome, and selection dependency state in one place.
- Diagnostics are now served as a dedicated backend payload and route, so the shell reads health summaries, selection state, and recent signals from backend-owned semantics rather than inferring them entirely in React.
- The command palette can now execute parameterized backend commands directly, including argument entry for quantity, enum, boolean, and text inputs, rather than being limited to zero-argument actions.
- The protocol package defines the first payloads and event/service shapes.
- The React frontend fetches live backend state instead of importing static mock data.
- The native bridge crate establishes the Rust-side boundary for future FreeCAD/OCCT worker integration.

## Local Run Shape

- backend address: `http://127.0.0.1:4180`
- frontend dev address: `http://127.0.0.1:4173`
- Vite proxies `/api/*` to the Rust backend during local development

## Current HTTP Surface

- `GET /api/bootstrap`
- `POST /api/documents/open`
- `GET /api/documents/:document_id/tree`
- `GET /api/documents/:document_id/properties/:object_id`
- `GET /api/documents/:document_id/commands`
- `GET /api/documents/:document_id/task-panel`
- `GET /api/documents/:document_id/selection-state`
- `GET /api/documents/:document_id/preselection-state`
- `GET /api/documents/:document_id/jobs`
- `GET /api/documents/:document_id/viewport`
- `GET /api/documents/:document_id/events`
- `POST /api/selection`
- `POST /api/selection/mode`
- `POST /api/preselection`
- `POST /api/commands/run`

## Next Recommended Steps

1. Generate Rust/TypeScript types from `protocol/proto`.
2. Move the current HTTP JSON routes behind the gRPC/domain boundary from the plan.
3. Replace the bridge mock snapshot with real document open/tree/property/scene extraction from FreeCAD workers.
4. Push viewport diffs through the eventual gRPC or streaming boundary instead of only the current HTTP command response path.
5. Replace the remaining static command/task heuristics with bridge- or worker-derived workbench logic.
6. Extend backend-owned command definitions to cover richer PartDesign and Sketcher dialogs beyond the current mock mutation set.
7. Decide whether the first desktop packaging step lands as Tauri immediately or after one more backend milestone.
