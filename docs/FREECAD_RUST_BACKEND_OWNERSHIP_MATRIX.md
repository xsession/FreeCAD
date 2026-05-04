# FreeCAD Rust Backend Ownership Matrix

Status: working execution matrix as of 2026-05-04

## Purpose

This matrix turns the Rust backend migration strategy into a domain-by-domain ownership decision.

Use these values consistently:

- `Rust-own`: Rust should become the primary authority in the near term
- `Bridge-now`: native C++ or Python remains the execution path, but only behind a Rust-owned bridge
- `Later-candidate`: a Rust rewrite may make sense later, but not before boundaries and tests mature
- `Compatibility-only`: preserve via compatibility lane, not by first-wave rewrite

## Core Platform Matrix

| Domain | Current Baseline | Near-Term Decision | Target Authority | Migration Mode | Priority | Current State | Notes |
|---|---|---|---|---|---|---|---|
| Session lifecycle | Mixed GUI + app startup paths | Rust-own | Rust | C | P0 | Partial in AsterForge | Move boot, active session, recent docs, recovery policy into backend service ownership |
| Document lifecycle | `src/App` plus native persistence | Bridge-now | Rust over native bridge | B | P0 | Not migrated | Rust owns new/open/save/close/recover orchestration; native path preserves FCStd compatibility |
| Command registry | Qt and legacy command routing | Rust-own | Rust | C | P0 | Partial in AsterForge | `command-core` should own taxonomy, enablement, arguments, and execution framing |
| Undo/redo framing | Native document transactions | Bridge-now | Rust over native bridge | B | P0 | Partial in AsterForge | Rust owns transaction boundaries and user-facing history semantics |
| Selection/preselection | Legacy GUI + shell snapshot state | Rust-own | Rust | C | P0 | Partial in AsterForge | Make selection state backend-canonical for all migrated flows |
| Jobs/progress/events | Mixed ad hoc status flows | Rust-own | Rust | C | P0 | Partial in AsterForge | Move worker supervision, job stages, diagnostics, and event feeds out of `api-gateway` monoliths |
| Protocol/API versioning | Variant-local contracts | Rust-own | Rust | C | P0 | Partial in AsterForge | Version the backend surface before expanding workbench coverage |
| Preferences/layout policy | GUI-heavy today | Rust-own | Rust | C | P1 | Partial in AsterForge | UI renders settings; Rust owns durable state and compatibility migrations |
| Crash recovery | Legacy process-bound behavior | Rust-own | Rust | C | P1 | Not migrated | Worker restart, autosave, and post-failure diagnostics belong in Rust |
| FCStd migration bookkeeping | Native serializer only | Rust-own | Rust over native bridge | B | P1 | Not migrated | Add schema bookkeeping and migration metadata around native persistence |

## Geometry And Modeling Matrix

| Domain | Current Baseline | Near-Term Decision | Target Authority | Migration Mode | Priority | Current State | Notes |
|---|---|---|---|---|---|---|---|
| Part geometry operations | `src/Mod/Part` + OCCT | Bridge-now | Rust orchestration, native execution | B | P0 | Not migrated | Keep booleans, fillet, chamfer, loft, sweep, and offset native until proven replacements exist |
| PartDesign feature execution | `src/Mod/PartDesign` | Bridge-now | Rust orchestration, native execution | B | P0 | Partial vertical slice only | Rust owns workflow, task state, and command framing; native keeps feature execution |
| Sketcher solve engine | `src/Mod/Sketcher` | Bridge-now | Rust orchestration, native solve bridge | B | P0 | Not migrated | Solver rewrite is too risky as a first-wave goal |
| Recompute planning | Implicit native behavior | Rust-own | Rust | B | P0 | Not migrated | Rust should own invalidation and recompute scheduling even while execution remains native |
| Topology naming compatibility | Native implementation | Bridge-now | Native behind Rust | B | P0 | Not migrated | Preserve working native behavior first; do not trigger a topology rewrite program prematurely |
| Tessellation generation | Native view and shape paths | Bridge-now | Rust orchestration, native extraction | B | P0 | Partial in AsterForge | Contract should carry versioned viewport payloads and diffs |
| Picking and subelement mapping | GUI-driven today | Bridge-now | Rust over native bridge | B | P0 | Not migrated | Backend owns mapping authority; native provides geometry lookup where needed |
| STEP and AP242 data services | Mixed import stack, early Rust STEP | Rust-own | Rust | C/B | P0 | Early implementation exists | Extend `step-core` and standards services in Rust |
| Native import/export codecs | OCCT and legacy libraries | Bridge-now | Rust orchestration, native codecs | B | P0 | Not migrated | Coordinate through Rust, preserve mature codec paths |

## Workbench Matrix

| Workbench Or Domain | Current Baseline | Near-Term Decision | Target Authority | Migration Mode | Priority | Current State | Notes |
|---|---|---|---|---|---|---|---|
| Start | GUI + Python helpers | Rust-own | React + Rust | C | P0 | Not migrated | Good candidate for clean reimplementation |
| Part | Native C++ | Bridge-now | Rust + native bridge | B | P0 | Not migrated | Keep execution native, move orchestration and state into Rust |
| PartDesign | Native C++ | Bridge-now | Rust + native bridge | B | P0 | Partial prototype | Prioritize daily-use workflows before expansion |
| Sketcher | Native C++ | Bridge-now | Rust + native bridge | B | P0 | Not migrated | Rust owns command workflow, not first-wave solver rewrite |
| Import | Native/import stack | Bridge-now | Rust + native bridge | B | P0 | Partial STEP lane | Rust should own format orchestration and diagnostics |
| Assembly | Mixed, Python-heavy | Later-candidate | Rust eventually | A/B then C | P1 | Not migrated | Strong Rust rewrite candidate after platform hardening |
| Draft | Mixed C++ and Python | Bridge-now | Rust + native bridge | B | P1 | Not migrated | Move workflow state into Rust, preserve geometry paths initially |
| Spreadsheet | Native module | Later-candidate | Rust eventually | C | P1 | Not migrated | High-value rewrite candidate because it is not OCCT-heavy |
| TechDraw | Native C++ | Bridge-now | Rust + native bridge | B | P1 | Not migrated | Keep drawing generation native first |
| Material | Mixed UI/data | Rust-own | Rust | C | P1 | Not migrated | Strong early rewrite candidate |
| Measure | Mixed | Bridge-now | Rust + native bridge | B | P1 | Not migrated | Rust owns workflow and reporting, native can provide geometry measurements initially |
| CAM/Path | Mixed Python/native | Later-candidate | Rust eventually | A/B then C | P1 | Not migrated | Good candidate for Rust orchestration of jobs, tools, and posts |
| FEM | Mixed C++/Python | Bridge-now | Rust orchestration, native and solver workers | A/B | P2 | Not migrated | Rust should own job supervision before deeper rewrites |
| BIM | Mixed Python/native | Compatibility-only | Compatibility lane first | A | P2 | Not migrated | Heavy interoperability surface; preserve via compatibility first |
| Mesh/MeshPart | Mixed native | Bridge-now | Rust + native bridge | B | P2 | Not migrated | Defer until P0 modeling path is stable |
| Surface | Native | Bridge-now | Rust + native bridge | B | P2 | Not migrated | Defer until core modeling parity exists |
| ReverseEngineering | Mixed | Compatibility-only | Compatibility first | A | P2 | Not migrated | Specialist lane, not first-wave rewrite material |
| Robot | Mixed legacy | Compatibility-only | Compatibility first | A | P3 | Not migrated | Preserve only after core platform is stable |
| FlowStudio | Mixed fork-specific | Bridge-now | Rust + native bridge | B | P1 | Active fork lane | Candidate for strong Rust orchestration because jobs and workflows matter more than kernel rewrites |

## Extension And Automation Matrix

| Domain | Current Baseline | Near-Term Decision | Target Authority | Migration Mode | Priority | Current State | Notes |
|---|---|---|---|---|---|---|---|
| Addon inventory and trust | AddonManager and GUI flows | Rust-own | Rust | C | P0 | Partial in AsterForge | Move inventory, trust, compatibility state, and policy into Rust |
| Macro execution | Python and GUI-bound assumptions | Bridge-now | Rust + Python worker | B | P1 | Early inventory surface only | Supervise Python execution explicitly |
| Python automation APIs | Broad ambient runtime access | Bridge-now | Rust + Python worker | B | P1 | Not migrated | Preserve essential automation through explicit bindings |
| Legacy GUI-heavy plugins | Direct Qt and PySide access | Compatibility-only | Compatibility lane | A | P2 | Not migrated | Do not promise first-wave rewrite parity |
| External workbench registration | Python and package discovery | Rust-own | Rust | C/B | P1 | Partial in AsterForge | Rust should own manifests, discovery metadata, and policy |

## Decision Rules

Use these rules when new subsystems are proposed:

1. If the subsystem is primarily orchestration, state, policy, or transport, default to `Rust-own`.
2. If the subsystem is heavily OCCT-dependent and already works well enough, default to `Bridge-now`.
3. If the subsystem is Python-heavy but strategically important, default to `Bridge-now` with a supervised worker.
4. If the subsystem is specialist, legacy, or low-value relative to migration cost, default to `Compatibility-only`.
5. Promote a `Later-candidate` lane to a rewrite only after tests, benchmarks, and bridge behavior are stable.

## Immediate Use

This matrix should drive:

- bridge contract scope
- Phase 1 ticket ordering
- parity acceptance decisions
- plugin support promises
- staffing and ownership splits across Rust, native bridge, and frontend work