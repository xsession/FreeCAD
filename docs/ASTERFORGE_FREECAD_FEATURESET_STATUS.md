# AsterForge FreeCAD Featureset Status

Status: actual repository-state audit for the TypeScript and Rust migration surface

Last reviewed: 2026-05-04

## Purpose

This document records what the AsterForge migration is actually covering today, compared with the broader FreeCAD featureset named in the migration plans.

It is intentionally narrower and stricter than a roadmap. It distinguishes between:

- implemented and test-backed migration surface
- partially migrated or staging-only surface
- clearly missing FreeCAD parity

Use this file together with:

- `docs/QT_TO_TYPESCRIPT_FRONTEND_MIGRATION_PLAN.md`
- `docs/architecture/qt-to-typescript-migration-checklist.md`
- `docs/FREECAD_RUST_BACKEND_MIGRATION_PLAN.md`

## Current Bottom Line

The current AsterForge variant is a real shell-migration prototype with a meaningful backend-owned UI contract and a substantial STEP inspection vertical slice.

It is not yet a broad FreeCAD replacement.

The repo currently migrates these areas the furthest:

- shell chrome and shell-state ownership
- backend-owned command, layout, and session surfaces
- STEP document inspection, viewport interaction, PMI, measurement, and visibility workflows
- extension and macro compatibility staging surfaces

The repo is still missing these areas for actual FreeCAD parity:

- end-to-end Start, Part, PartDesign, Sketcher, and Assembly workflows in the TS shell
- mature FreeCAD-native modeling and recompute behavior behind Rust-owned services
- full plugin and PySide replacement
- packaged product cutover away from Qt

## Featureset Status Table

| Feature family | Current state | What exists now | Main missing pieces |
| --- | --- | --- | --- |
| Shell platform and chrome | Implemented but incomplete | React shell, menu bar, toolbar bands, workbench selector, tree, property, task panel, report, diagnostics, history, jobs, status bar, backend-owned layout state, shell snapshot contract | visual parity baselines, final theme-token pipeline, packaged shell ownership, full shell polish |
| Command and layout state | Implemented but incomplete | backend-owned command catalog, workbench activation, dock visibility and tabs, workspace-session restore, status-bar contract, command palette and in-canvas command access | broader command parity with FreeCAD workbenches, shortcut customization, final preference migration |
| STEP and AP242 inspection slice | Strongest implemented vertical slice | parser-backed STEP open flow, typed scene/index responses, synthetic model tree, property groups, selection, diagnostics, task panel, viewport drawables, HUD view controls, focus, reset, fit-all, standard views, PMI inspection, measurement, visibility controls | write workflows, broader import and export parity, real large-assembly acceptance validation, broader standards transport |
| Extension and macro compatibility | Staging only | Extensions dock path, backend-owned extension compatibility lanes, reviewed-entry actions, launcher-backed fixture execution, trust and run-result staging, addon provenance and blocker review inventory | real addon lifecycle parity, backend plugin API, frontend contribution API, de-Qt compatibility path for PySide-heavy extensions |
| FCStd and native document bridge | Partial | document open, shell snapshot, tree, properties, command flow, undo and redo framing, workspace persistence, bridge-backed shell composition | full document ownership in Rust, save and recompute authority, wider native execution coverage, mature bridge boundary |
| Viewport parity | Partial | selectable STEP viewport, orientation readout, shell-local wheel zoom, in-canvas controls, backend selection linkage, backend viewport state for STEP interactions | FreeCAD-compatible navigation feel, broader native-document viewport parity, validation on real assemblies, richer picking and overlay parity |
| Core workbenches | Mostly missing | some bridge-aware and PartDesign-oriented command flow exists in backend tests and shell metadata | no end-to-end Start, Part, PartDesign, Sketcher, or Assembly workflow family usable in the TS shell |
| Preferences and persistence | Partial | layout persistence moved behind backend state, shell launcher supports `qt`, `asterforge`, and `dual` modes | preferences schema, shortcut customization, theming, and full shell memory are not migrated end to end |
| Dual-shell and cutover | Early | repo-level launcher, runtime-only GUI bootstrap path, side-by-side shell startup support | default startup is still Qt-oriented, product packaging is not TS-shell-owned, Qt retirement has not started |

## Implemented Migration Surface

### 1. Shell surfaces already migrated into AsterForge

The TypeScript shell and Rust gateway already cover a meaningful desktop-shell slice:

- backend-owned shell snapshot, boot payload, and protocol contracts
- backend-owned menu bar, toolbar bands, workbench selector metadata, and layout state
- tree, property, task panel, report, diagnostics, history, jobs, and status regions rendered in the TS shell
- backend-owned workspace-session restore and recent-document state
- backend-owned shell status bar items for workbench, save state, selection mode, selection summary, diagnostics, dock context, worker mode, jobs, and panel visibility
- shared icon metadata flowing through the protocol instead of frontend-only placeholders

This means the migration is already past static mockups. The shell is reading and rendering real backend state.

### 2. STEP inspection is the most complete migrated workflow family

The current implementation is strongest around imported STEP or Part 21 inspection:

- STEP parsing and typed transport through `step-core` and `api-gateway`
- parser-backed document open bound to the active file instead of a global fixture-only response
- backend-owned STEP tree, property, diagnostics, task-panel, and viewport projections
- frontend STEP scene loading and selectable rendering
- in-canvas viewport HUD actions including focus, fit-all, reset, and standard view presets
- STEP-specific workbench chrome, command deck, inspection state, PMI inspection, measurement, and visibility controls
- executable frontend and backend tests covering this workflow slice

This is real migration progress, but it is inspection-heavy and mostly read-oriented. It is not a full modeling or editing parity story yet.

### 3. Extension compatibility is present as a migration lane, not as final parity

The repo now includes a first backend-owned compatibility surface for:

- macros
- AddonManager-related flows
- external workbench registration review

What exists today is a shell staging surface:

- compatibility inventory lanes
- backend action ids
- trust and provenance metadata
- addon provenance and blocker review inventory
- reviewed-entry execution path and dock-visible run results

What does not exist yet is full FreeCAD extension parity. There is still no final addon lifecycle, no shipped plugin API replacement, and no complete PySide compatibility story.

### 4. Backend ownership has started, but is not complete

The Rust side already owns:

- API gateway routes for shell, tree, properties, commands, diagnostics, jobs, events, task panel, and STEP scene data
- command dispatch for shell and STEP-oriented actions
- session and shell-state shaping
- startup restore, tracing, persistence warnings, and correlation-aware observability

But the backend still does not fully own:

- document persistence as the production authority
- recompute scheduling
- geometry execution
- full native workflow orchestration
- plugin compatibility as a production subsystem

`command-core` and `document-core` still remain much thinner than the eventual target architecture implies.

## Missing Or Incomplete FreeCAD Parity

### 1. Core workbench workflows are still missing

The main gap is still the actual FreeCAD workflow surface.

Not yet end to end in the TS shell:

- Start
- Part
- PartDesign
- Sketcher
- Assembly
- Draft
- TechDraw
- BIM
- CAM
- FEM
- Spreadsheet
- Material
- Mesh
- Surface
- ReverseEngineering
- Robot

The current repo has some command metadata, bridge-aware flows, and tests around PartDesign-oriented behavior, but that is not the same as workbench parity.

### 2. Viewport parity remains partial

The TS shell has meaningful viewport work, but full FreeCAD behavior is still missing:

- FreeCAD-compatible camera feel
- native-document viewport parity beyond the STEP-heavy slice
- richer preselection and picking parity
- broader isolate, hide, show, and fit workflows across all document families
- validated large-assembly behavior under real workloads

### 3. Preferences, theming, accessibility, and localization are not finished

Still missing or incomplete:

- shared theme-token pipeline
- preferences schema migration out of Qt pages
- shortcut customization migration
- localization-ready string externalization across the shell
- accessibility conformance work needed for enterprise or procurement-grade rollout

### 4. Plugin and PySide retirement is still ahead

The migration acknowledges this problem, but does not solve it yet.

Still missing:

- legacy compatibility lane for PySide-heavy plugins
- new backend plugin API
- new frontend contribution API
- deprecation schedule and retirement path for Qt-bound extension APIs
- removal of PySide from bundled primary workflows

### 5. Qt cutover is not close yet

The current repo supports dual-shell and runtime-only bootstrap paths, but the product is still Qt-dependent:

- Qt is still the production runtime default
- packaged startup is not owned end to end by the TS shell
- production runtime still depends on Qt libraries and Qt-originated workflows

## Evidence Summary

This status is based on the current repository state reflected in:

- `docs/QT_TO_TYPESCRIPT_FRONTEND_MIGRATION_PLAN.md`
- `docs/architecture/qt-to-typescript-migration-checklist.md`
- `docs/FREECAD_RUST_BACKEND_MIGRATION_PLAN.md`
- `docs/FREECAD_RUST_PHASE1_EXECUTION_BACKLOG.md`
- `docs/ASTERFORGE_ARCHITECTURE_CONTRIBUTOR_GUIDE.md`
- `variants/asterforge/frontend/app/src/App.integration.test.tsx`

Recent validated checks include:

- `npm test -- App.integration.test.tsx`
- `npm run build`
- `C:\Users\livanyi\.cargo\bin\cargo.exe test -p asterforge-api-gateway`

## Recommended Interpretation

If this migration is evaluated honestly, the current AsterForge featureset should be described as:

- a credible backend-owned shell migration
- a meaningful STEP inspection and standards-foundation slice
- an early extension-compatibility staging surface
- not yet a usable replacement for the main bundled FreeCAD workbench families

That distinction matters because the shell and STEP work are real progress, but they should not be mistaken for full Part, PartDesign, Sketcher, or Assembly migration.