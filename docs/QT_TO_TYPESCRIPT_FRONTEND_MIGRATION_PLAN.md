# FreeCAD Qt Removal and TypeScript Frontend Migration Plan

Status: active implementation plan with AsterForge shell in progress

## Progress Snapshot

Estimated overall progress against the milestone plan: `█████░░░░░ 51%`

| Milestone | Status | Notes |
| --- | --- | --- |
| A. Discovery and Baselines | In progress | Inventory and ownership artifacts exist, the Qt screenshot baseline set is captured, and the manual interaction recording lane is scaffolded; final recording review remains open. |
| B. Static TS Shell Parity | Largely complete | The TypeScript shell, chrome, and shell scaffolding are present and actively used, and the viewport now carries an in-canvas quick-access strip, a backend-driven command shelf, and a denser, more restrained shell treatment that keeps attention on the model area. |
| C. Command and Layout Parity | Largely complete | Menus, toolbars, workbench-specific chrome, command palette and in-canvas command access, a viewport-anchored quick-access rail plus backend-driven command shelf with inline argument editing for suggested commands, keyboard-first quick open plus numeric selection-mode shortcuts, panel visibility and tab switching, workspace-session restore hooks, a backend-owned diagnostics-aware shell status bar, and an Extensions dock with backend-owned macro, addon, and external-workbench review lanes are implemented; broader layout polish and full parity are still incomplete. |
| D. Editing Surface Parity | In progress | Tree, property, task, report, diagnostics, history, and jobs surfaces are functional, but full editing parity is not done. |
| E. Viewport Parity | In progress | STEP focus, fit-all, reset, standard views, selection linkage, and shell-local wheel zoom are working; full navigation-feel parity is still missing. |
| F. Standards Foundation | In progress | AP242 and early EXPRESS groundwork are implemented, but broader standards transport and downstream workflows remain partial. |
| G. Core Workbench Parity | Not started | Start, Part, PartDesign, Sketcher, and Assembly are not yet usable end to end in the TS shell, and no downstream workbench family has reached TS-shell parity yet. |
| H. Cutover Readiness | Not started | The TS shell is not yet the daily-driver default for bundled workflows. |
| I. Qt Removal | Not started | Production runtime still depends on Qt. |

Interpretation:

- `Largely complete` means the milestone has substantial implemented coverage in the current tree, but may still have cleanup or parity gaps.
- `In progress` means there is verified implementation in the repo, but the milestone exit criteria are not yet met.
- `Not started` means the milestone goal is still mostly future work.

## Related Documents

- `docs/QT_SURFACE_INVENTORY.md`
- `docs/QT_UI_FORM_INVENTORY.md`
- `docs/PYSIDE_USAGE_TABLE.md`
- `docs/GUI_OWNERSHIP_TABLE.md`
- `docs/SRC_GUI_FILE_LEVEL_OWNERSHIP_INVENTORY.md`
- `docs/FREECAD_RUST_BACKEND_MIGRATION_PLAN.md`
- `docs/ASTERFORGE_FREECAD_FEATURESET_STATUS.md`
- `docs/PLASTICITY_UX_BACKEND_BENCHMARK.md`
- `docs/FRONTEND_PARITY_BASELINE_SPEC.md`
- `docs/QT_TO_TYPESCRIPT_REPO_EXECUTION_PLAN.md`
- `docs/architecture/ADR-0010-typescript-shell-and-qt-retirement.md`
- `docs/architecture/qt-to-typescript-migration-checklist.md`
- `docs/architecture/qt-to-typescript-milestone-issues.md`

## Current Repository State

The repository is already beyond pure planning for the shell migration. The active implementation anchor is the AsterForge variant under `variants/asterforge`.

For a stricter implementation-versus-gap audit of the current migrated FreeCAD-facing featureset, see `docs/ASTERFORGE_FREECAD_FEATURESET_STATUS.md`.

Implemented slices in the current tree:

- React plus TypeScript shell scaffold exists in `variants/asterforge/frontend/app`
- Rust backend shell services exist in `variants/asterforge/backend/crates`
- protocol schemas and generated bindings exist in `variants/asterforge/protocol`
- the current shell renders menu bar, toolbar bands, combo view, tree, property, task panel, report, diagnostics, history, jobs, and status surfaces from backend payloads, and the shell snapshot now carries a backend-owned status-bar payload for active workbench, save state, selection mode, selection summary, diagnostics, dock context, worker mode, jobs, and panel visibility instead of leaving that footer as a frontend-only composition
- command, toolbar, and workbench icon metadata now flow through the shell via a shared TypeScript icon renderer instead of frontend-only placeholders
- a repo-level launcher now exists at `Start-FreeCADShell.ps1` so Qt, AsterForge, or dual-shell startup can be invoked from one shell-neutral entry point
- a repeatable Qt parity capture runner now exists at `tools/profile/capture_qt_shell_matrix.ps1` with a repo-owned starter manifest under `docs/parity/fixtures`
- the Qt parity lane now includes committed screenshot baselines, acceptance thresholds, a dated screenshot review log, and a scaffolded recording-review lane under `docs/parity`
- the native GUI bootstrap now has a runtime-only branch so `FREECAD_SHELL_MODE=runtime-only` can initialize the GUI runtime without constructing the Qt `MainWindow`
- an initial STEP foundation now exists in `variants/asterforge/backend/crates/step-core` with memory-mapped file access, parallel entity indexing, lazy entity loading, and early-bound Rust structs for representative EXPRESS entities
- `asterforge-api-gateway` now exposes parser-backed STEP document and scene endpoints and binds them to the active document path instead of a global fixture-only response
- STEP documents now project a backend-owned synthetic model tree, property groups, selection state, diagnostics summary, task panel summary, and viewport drawables so the shell can inspect imported topology through the same panel surfaces used by FCStd-backed documents
- the React shell now conditionally loads STEP scene payloads for `.stp`, `.step`, and `.p21` documents and renders a selectable STEP viewport that uses the same object identifiers as the backend selection and property model
- the command palette now supports both `F` and `Ctrl+K` quick-open paths outside editable fields, while selection-mode switching now also supports numeric `1-9` shortcuts based on the backend-published mode order so viewport interaction is faster and more keyboard-forward
- the viewport shell now includes a dedicated in-canvas quick-access strip for search and session context plus a backend-driven command shelf sourced from task and hover suggestions, and that shelf can now expand suggested argument-bearing commands into the shared inline command editor directly inside the viewport instead of forcing those flows back into distant docks or palettes, while the layout has been rebalanced toward a narrower subordinate combo view, a shorter lower dock, lighter top chrome, and a stronger viewport-first visual hierarchy aligned with the Plasticity benchmark direction without copying Plasticity assets or exact composition
- the React shell now includes in-canvas viewport heads-up controls, backend-owned STEP focus, fit-all framing, reset-to-home, and standard view-direction commands including mirrored left, back, and bottom inspection views, a live orientation readout, viewport-level selection mode controls, shell-local wheel zoom for the STEP renderer, and hover-candidate action cards that resolve shared shell command metadata, while task, hover, selection, command-palette, structured-report, and Shell Notice surfaces now share the same metadata-resolved command presentation path and parameterized command editor implementation, and task, hover, and selection suggestion surfaces also share suggested-command state orchestration, so model, task, report, focus, low-travel selection changes, target-aware palette execution against selected or hovered objects, actionable structured inspection refresh/focus workflows, backend activity select/focus plus topic-aware reinspection and remeasurement actions, and remaining selection-scoped plus global command-status notices are available inside the graphics area through the same actionable notice surface instead of splitting into separate event-only and command-only affordance paths, without duplicating the same live backend activity across notice and report surfaces, surfacing low-signal progress, viewport-sync chatter, worker-lifecycle open progress, shell-local selection, workbench, and dock-layout status chatter, or repeated background job-update bursts in those user-facing report channels, emitting a second command-status notice for the same PMI or measurement activity already represented by matching backend activity in either the Shell Notice stack or the report feed, emitting a second failed-command warning when the same rejection is already represented by a backend warning event, falling back to raw command ids in command-status notice titles when shared command metadata is already available, spending two notice slots on the same open-document change burst, spending the capped Shell Notice stack on low-value document-change, background job-update chatter, or informational command-status noise ahead of higher-severity or more actionable inspection notices, spending the report-dock backend activity feed on that same low-value document and job chatter ahead of warnings or actionable inspection updates, spending the report-dock backend activity feed on repeated document-change, job-update, or same-object PMI annotation bursts that could be summarized into one row, or spending the Shell Notice stack on repeated PMI annotation rows for the same inspected object
- the frontend app now includes a focused Vitest regression harness for shell view helpers and rendered shell surfaces so structured report filtering, structured inspection command-notice suppression, command-status deduplication against matching backend activity notices, report-feed activity, and backend warning events, open-document change-burst summarization, job-update burst summarization, priority ordering of actionable inspection notices over generic document and job status chatter when the event-notice list is capped, severity-first ranking across the combined Shell Notice stack so stronger backend warnings and event notices can displace low-value informational command notices instead of reserving a fixed command slot, report-dock ordering that surfaces warnings and actionable STEP inspection activity ahead of generic document-open and job-update chatter while preserving those rows in the feed, report-feed burst summarization for repeated document-change, job-update, and same-object PMI annotation rows, metadata-resolved command-status notice titles and selection-scoped plus global notice actions, the report-dock activity empty state, actionable backend activity rows, Shell Notice action cards, report-tab backend activity notice deduplication, low-signal backend progress filtering, shell-local event filtering for selection, preselection, workbench, layout, and worker-lifecycle chatter, PMI annotation burst summarization, backend activity topic-to-command mapping for PMI and measurement workflows, expanded STEP viewport preset projection for mirrored left, back, and bottom navigation views, the viewport HUD, structured inspection panels, and command-palette parameter submission are covered by executable tests instead of build-only checks
- STEP documents now expose a STEP-specific read-only command deck in the backend catalog, including fit-all plus reset and preset viewport commands, parent-child topology navigation, PMI inspection, measurement, and visibility controls that drive task-panel drill-down, structured report-dock inspection, command-palette discovery, and viewport emphasis for inspected STEP targets through a dedicated shell inspection state carried by the shell snapshot
- STEP inspection now includes backend-owned visibility controls for imported topology, including isolate, hide-selection, and show-all commands that update the tree, task panel, diagnostics, viewport, and STEP shell chrome from one shared state model, and the STEP frontend renderer now filters its static scene bundle through the backend viewport-visible drawable set so hidden geometry no longer remains visible client-side
- STEP inspection now includes backend-owned measurement for imported topology, with a measure-selection command that computes tessellated extents and surfaces them through the task panel, structured report-dock inspection, command deck, and STEP shell chrome
- STEP documents now switch the shell snapshot to a STEP-specific workbench identity, menu bar, and toolbar band layout so imported Part 21 sessions no longer inherit PartDesign-oriented chrome, and that chrome now exposes the same backend-owned fit-all, reset, and standard view commands used by the in-canvas viewport HUD
- the AsterForge shell now has a first backend-owned plugin and macro compatibility surface: backend menus route into a dedicated Extensions dock tab, the shared shell snapshot carries an extension-compatibility inventory for macros, AddonManager flows, and external workbench registration, each compatibility lane now advertises its own backend action ids through that shared payload, refreshed lanes can publish concrete inventory entries with provenance, compatibility, and trust metadata through the normal shell refresh path, reviewed shell-safe entries can now expose backend-owned run actions that cover launcher-backed fixture execution plus dock-visible categorized run results for success, trust-policy rejection, and launcher or fixture failures instead of frontend-only placeholders, and the AddonManager lane now has a dedicated backend review command that stages addon provenance, blocker diagnostics, and shell-candidate inventory entries inside the same Extensions dock contract

Still incomplete in the current tree:

- screenshot baselines are captured from the Qt runtime, but the manual interaction recording set still awaits reviewer execution and acceptance sign-off
- desktop-host startup handoff is still script-driven rather than integrated into a packaged product path, even though the native runtime can now start without the Qt main window
- viewport navigation and workbench workflow parity are still partial, while selection feel now includes in-canvas mode switching, backend-owned reset, standard-view, focus camera state, shell-local wheel zoom, and hover-action affordances but still lacks broader gesture and navigation parity
- no bundled production workbench family has completed end-to-end TypeScript-shell migration yet, including Start, Part, PartDesign, Sketcher, Assembly, Draft, TechDraw, BIM, CAM, FEM, Spreadsheet, Material, Mesh, Surface, ReverseEngineering, Robot, and addon or macro-driven plugin flows
- plugin, macro, AddonManager, and external workbench compatibility still depend on Qt or PySide-era assumptions; the new Extensions dock, shell-snapshot inventory, lane-owned action ids, inventory entries, trust metadata, reviewed-entry run actions, launcher-backed reviewed fixture execution, backend execution events with launcher-output excerpts, dock-visible categorized run results plus detail, and initial backend state mutations are only the first TS-shell staging surface, not a shipped compatibility solution

## Complete Feature Stack Coverage

The migration plan must explicitly cover the full bundled feature stack, not only the shell and STEP inspection slices. The following families are in scope for parity and de-Qt work.

| Feature family | Representative modules or surfaces | Migration lane | Current plan status |
| --- | --- | --- | --- |
| Shell and workbench platform | `src/Gui`, workbench selector, command routing, docks, layout persistence, status surfaces | P0 foundation | In progress in AsterForge; not complete |
| Plugin and extension system | `src/Mod/AddonManager`, macros, `InitGui.py`, PySide dialogs, external workbench registration, addon installation and updates | P0 compatibility foundation | Planned, not implemented end to end |
| Core modeling | Start, Part, PartDesign, Sketcher | P0 primary workflow | Planned, not migrated |
| Mechanical assembly | Assembly, BOM, joint task panels, assembly view creation | P0 or P1 depending on product priority | Planned, not migrated |
| Drafting and documentation | Draft, TechDraw, annotation and drawing task flows | P1 | Planned, not migrated |
| BIM and built environment | BIM, IFC-facing property and project flows | P1 compatibility-heavy | Planned, not migrated |
| Manufacturing | CAM, operation editors, tool libraries, setup and simulator flows | P1 | Planned, not migrated |
| Simulation and analysis | FEM, Material, solver setup, post-processing | P1 or P2 | Planned, not migrated |
| Supporting data tools | Spreadsheet, Import, Material, Start-page onboarding, preferences-heavy support flows | P1 or P2 depending on workflow criticality | Planned, not migrated |
| Specialist geometry workbenches | Mesh, Surface, ReverseEngineering, Robot, other specialist modules | P2 | Planned, not migrated |

Coverage rule:

- the migration is not considered complete unless the plan tracks a supported path for every bundled workbench family and for addon, macro, and external plugin compatibility
- if a workbench is not targeted for first-wave migration, the plan must still assign it either a migration lane or an explicit compatibility lane

Continuation order after the current STEP-focused shell work:

1. plugin and extension compatibility foundation
2. Start, Part, PartDesign, and Sketcher workflow surfaces
3. Assembly shell and task-panel flows
4. Draft and TechDraw workflow parity
5. BIM and CAM compatibility-heavy migrations
6. FEM, Spreadsheet, Material, and remaining specialist workbenches

## 1. Goal

Replace the current Qt-based FreeCAD application shell with a TypeScript-based frontend while preserving the current product visuality, interaction patterns, workbench structure, and document workflows.

This is not a one-step library swap. Qt is currently embedded into:

- application chrome and window management
- actions, menus, toolbars, docks, and task panels
- workbench activation and command routing
- Python and PySide tooling in many workbenches
- 3D viewport hosting and GUI lifecycle

The correct strategy is a staged shell replacement where Qt is first isolated, then hollowed out, then removed after the TypeScript shell reaches proven parity.

## 2. Target End State

The target desktop product should look and behave like FreeCAD, but the UI stack should be:

- frontend: React plus TypeScript
- desktop shell: Tauri preferred, Electron only if required by a hard blocker
- backend orchestration: Rust service layer
- native CAD bridge: C++ FreeCAD and OCCT retained behind explicit APIs
- rendering: web-native viewport stack hosted by the TypeScript shell, with native services for scene extraction, picking data, and heavy geometry tasks

The target data platform should also absorb industrial CAD exchange workloads that are currently spread across ad hoc import and export paths. In practice that means the Rust application layer needs a dedicated STEP and EXPRESS subsystem that can:

- decode and generate Part 21 STEP payloads for AP203, AP214, and AP242
- treat AP242 as the primary modern target for semantic PMI, graphical PMI, GD&T, exact B-Rep, and tessellated representations
- expose lazy, backend-owned assembly, tessellation, and PMI payloads to the TypeScript shell without leaking parser internals

Qt should be fully absent from the runtime UI shell in the final state.

## 2.1 Competitive Standards Baseline

If the TypeScript and Rust migration is meant to remain globally competitive with Inventor and SolidWorks, the plan must treat standards support as a first-class product requirement rather than a later interoperability add-on.

The migrated product should explicitly plan for compliance and interoperability across the following standards domains.

### Technical Documentation and Presentation

- ISO 128, including ISO 128-1:2020, for technical drawing conventions such as line types, line weights, projections, and scales
- ISO 13567 for CAD layer naming and hierarchical organization in multidisciplinary projects
- DIN 1356 and the ASME Y14 drawing series where regional drafting conventions still matter for text sizing, tolerance presentation, and arrowhead conventions

Planning implication:

- the future document and drawing surfaces cannot hardcode one drafting dialect
- drawing, annotation, and export services need standards-aware presentation profiles

### Geometric Dimensioning and Tolerancing

- ASME Y14.5 for North American GD&T workflows
- ISO 1101 and ISO 2768 for international geometric and general tolerancing workflows

Planning implication:

- AP242 and MBD work cannot stop at geometry transport
- backend-owned PMI and tolerance semantics need explicit support for both ASME and ISO interpretation modes

### Model-Based Definition

- ASME Y14.41 and ISO 16792 for semantic PMI embedded directly in the 3D model
- MIL-STD-31000A and GB/T 24734 where defense and regional MBD deliverables are required

Planning implication:

- the viewport and document protocols must reserve space for semantic PMI, graphical PMI, surface finish, datum systems, and inspection-facing annotations
- the Rust backend should become the authoritative owner of MBD payloads, not the TypeScript renderer

### Data Exchange and Advanced Manufacturing

- ISO 10303 STEP with AP203, AP214, and especially AP242
- ISO 10303-238 STEP-NC as an emerging path for CNC-oriented downstream manufacturing exchange beyond legacy G-code workflows

Planning implication:

- `step-core` should evolve toward both AP242 model exchange and a future STEP-NC-adjacent manufacturing handoff path
- import/export services should be designed as standards adapters, not as one-off file translators

### BIM and Built-Environment Interoperability

- IFC 2x3 and IFC 4 for current building-information workflows
- IFC 4x3 for infrastructure and modern asset-placement interoperability

Planning implication:

- the backend data model should leave room for IFC-facing property and placement export
- mechanical equipment placement and facility-integration workflows should not be treated as out-of-scope edge cases

### Regulated Traceability and Process Compliance

- ISO 13485 for medical device design controls
- AS9100 Rev D for aerospace traceability and controlled engineering change
- FDA 21 CFR Part 11 for secure electronic records and signatures where regulated auditability matters

Planning implication:

- document history, command execution, approval state, and audit metadata need to be designed into the backend event model early
- future PDM, Vault, or repository integrations should preserve accountable design history rather than treating traceability as an external concern

### AI Governance

- ISO 42001 as the baseline governance model for future generative design and AI-assisted engineering features

Planning implication:

- any future AI assistant, design recommendation, or automated repair workflow must be backed by auditable prompts, model versioning, traceability, and opt-in governance boundaries

## 2.2 Standards-Driven Product Direction

The migration plan should assume that competitive parity is not just visual parity with current FreeCAD. It is also standards parity with incumbent commercial systems in the workflows that matter most to industrial teams.

That means the Rust and TypeScript platform should converge toward:

- standards-aware drawing and annotation presentation
- dual-path GD&T support for ISO and ASME conventions
- AP242-first MBD and PMI transport
- a growth path toward STEP-NC manufacturing exchange
- IFC-capable equipment and facility interoperability
- traceable, auditable document and workflow history
- governance hooks for future AI-assisted features

## 2.3 Incumbent CAD UX Benchmark Baseline

The migration plan should also track competitor UX baselines from incumbent mechanical CAD systems, because industrial users judge parity not only against current FreeCAD but against Inventor and SolidWorks interaction expectations.

### Autodesk Inventor Benchmark

Based on the Autodesk Human Interface Guidelines and public Inventor help surfaces, Inventor should be treated as the reference point for:

- high-density professional desktop layout, where ribbon chrome, properties, and model state are visible simultaneously without excessive whitespace
- strict tokenized spacing and typography rules, including compact panel spacing, small-label discipline, and deterministic visual rhythm rather than consumer-style responsive looseness
- contextual ribbon behavior, where command availability and grouping follow the active task rather than exposing one static command field for every mode
- in-canvas navigation patterns centered around ViewCube and marking-menu style interaction to reduce pointer travel and keep attention inside the modeling canvas
- semantic color use for attention and state, where selection, expression state, warnings, and surface targeting are visually distinguishable without over-styling the shell

Planning implication:

- the TypeScript shell should support a high-density token set as a first-class mode, not as a late compact-theme afterthought
- toolbar bands, task panels, and properties should be measurable against compact spacing rules and not drift toward padded web-dashboard layouts
- viewport-adjacent controls should preserve in-canvas workflows such as radial or marking-menu style command invocation and persistent orientation affordances

### SolidWorks Benchmark

Based on SOLIDWORKS public help, the benchmark surface includes:

- a stable left-side manager-pane pattern where the FeatureManager design tree, PropertyManager, and related manager tabs are dynamically linked to the graphics area
- a CommandManager-centered command surface rather than fragmented floating tool palettes
- a Heads-Up View toolbar directly inside the graphics area for common view manipulation tasks
- graphics-area interaction accelerators such as mouse gestures, the S-key shortcut bar, and selection breadcrumbs that keep command access close to the active modeling context
- a tree-to-graphics linkage where selecting in either pane should reveal corresponding state in the other pane, including parent-child and history relationships

Planning implication:

- the AsterForge shell should preserve a manager-pane architecture for tree, property, and contextual task editing rather than scattering those surfaces across unrelated docks
- in-canvas command affordances should be treated as core workflow requirements, not optional polish
- tree, property, and graphics selection must remain tightly synchronized by contract for both native FreeCAD documents and imported STEP documents

### Plasticity Benchmark

Based on Plasticity's public docs, product site, and public repository, Plasticity should be treated as a benchmark for shell comfort, direct-manipulation command flow, and viewport-first interaction rather than as a source of brand or asset cloning.

Plasticity is a useful reference point for:

- calm, dense, low-chroma desktop chrome that keeps attention on the model instead of on dashboard-like panel framing
- viewport-first command access through command palette, command bar, radial-menu style interaction, view cube, and contextual prompts
- compact dialogs and gizmos that work together during an active command instead of pushing the user into distant form-heavy workflows
- explicit editor architecture with centralized command execution, history, backup, keybindings, theme loading, and viewport helper layers

Planning implication:

- the TypeScript shell should pursue Plasticity-like comfort through spacing discipline, restrained chrome, compact prompts, and low-travel command access without copying Plasticity branding, icons, wording, or exact layouts
- the Rust backend should continue toward an explicit session and command-runtime architecture where preview, commit, cancel, cleanup, autosave, history, settings, and keybindings are first-class services rather than ad hoc UI behavior
- viewport protocols should distinguish durable geometry, preview geometry, and helper overlays so command previews and gizmos remain lightweight and deterministic
- shell review should include a dedicated benchmark pass against Plasticity for direct-editing comfort and viewport dominance alongside the existing Inventor and SolidWorks engineering-shell checks

### Accessibility, Internationalization, and Procurement Baseline

Public vendor accessibility materials also establish a procurement baseline that the migration plan should explicitly track.

- Autodesk and Dassault both publish accessibility commitments and conformance materials oriented toward WCAG and VPAT-style review by enterprise and government buyers
- Dassault publicly states partial accessibility conformance for its web estate and provides a VPAT-format conformance report, which is a useful reminder that accessibility must be measured continuously rather than assumed from design-system intent alone
- internationalized CAD shells must externalize user-facing strings and reserve layout space for translated text expansion so dense engineering UI does not break in German, Japanese, or other high-expansion locales

Planning implication:

- all user-facing shell strings should live in resource catalogs rather than inline React literals
- parity testing should include keyboard-only traversal, focus order, contrast review, and screen-reader-auditable landmarks for shell chrome and major panels
- layout acceptance should include text expansion and locale stress cases so compact toolbars, tabs, and property panes remain usable after translation

## 3. Non-Negotiable Constraints

1. Do not rewrite the modeling kernel first.
2. Do not let frontend code own recompute logic or document truth.
3. Do not attempt full workbench migration before shell parity exists.
4. Do not remove Qt from the build until the TypeScript shell can run the primary workflows end to end.
5. Visual parity must be measured, not guessed.

## 4. Definition of "Same Visuality"

"Keep the same visuality" should be treated as a hard engineering requirement with measurable outputs.

The TypeScript shell must preserve:

- menu hierarchy and labels
- toolbar grouping and iconography
- dock and panel layout model
- tree view structure and affordances
- property editor grouping and editing behavior
- task panel flow and button placement
- viewport background, navigation affordances, and selection overlays
- typography scale, spacing rhythm, icon sizes, and density
- light and dark theme appearance
- command discoverability, shortcut behavior, and workbench switching patterns
- high-density desktop information packing comparable to incumbent CAD manager-pane and ribbon layouts
- in-canvas accelerators such as orientation widgets, heads-up controls, radial or gesture-friendly command access, and low-travel selection workflows
- robust keyboard, accessibility-tree, and localization behavior for shell chrome and contextual panels

Visual parity should be validated through:

- screenshot baselines for major screens
- layout metric baselines such as panel widths, toolbar heights, padding, and font sizes
- interaction recordings for core workflows
- user acceptance review against the current Qt shell
- benchmark review against representative Inventor and SolidWorks shell patterns for density, command proximity, and manager-pane behavior

## 5. Recommended Repository Shape

The repository already points toward the right architecture through the AsterForge variant. The migration should converge toward a structure like this:

```text
frontend/
  app/
  design-system/
  viewport/
  workbench-shell/
backend/
  api-gateway/
  command-service/
  document-service/
  step-service/
  session-service/
  ui-layout-service/
native/
  freecad-bridge/
protocol/
  ui.proto or schema definitions
  step.schema definitions
  generated types
src/
  legacy native FreeCAD core and remaining bridge code
```

For the current repository shape under `variants/asterforge`, the next backend expansion should converge toward:

```text
variants/asterforge/
  backend/
    crates/
      api-gateway/
      command-core/
      document-core/
      protocol-types/
      step-core/
  frontend/
    app/
      src/
        stepTypes.ts
        stepClient.ts
  native/
    freecad-bridge/
```

## 5.1 STEP and EXPRESS Foundation Workstream

The shell migration should explicitly include a production-grade CAD exchange workstream instead of treating STEP as a later import detail. AsterForge needs a backend-owned subsystem that can parse, validate, index, and later emit STEP data fast enough for large industrial assemblies.

### Scope

- support AP203 and AP214 for legacy compatibility
- prioritize AP242 for model-based definition, PMI, tessellated payloads, and exact geometry interchange
- generate early-bound Rust types from EXPRESS schemas rather than performing runtime schema discovery in hot paths
- use memory-mapped I/O and lazy entity materialization for gigabyte-to-terabyte scale files
- expose assembly hierarchy, tessellated scene data, and PMI payloads to the TypeScript frontend through typed backend APIs

### Architecture

```text
TypeScript React shell
    |
    | HTTP/JSON now, streaming scene transport later
    v
asterforge-api-gateway
    |
    +--> document-core
    |
    +--> step-core
            |
            +--> mmap Part 21 reader
            +--> map-reduce entity indexer
            +--> lazy entity loader
            +--> EXPRESS early-bound Rust structs
            +--> AP203/AP214/AP242 protocol classification
    |
    +--> freecad-bridge / OCCT import-export adapters
```

### Binding Strategy

Use early binding for EXPRESS schemas. The repository should eventually generate Rust structs and enums directly from selected EXPRESS definitions at build time, with generated TypeScript mirrors for frontend-facing DTOs. This is the correct tradeoff for the AsterForge target because:

- compile-time binding gives strict type safety for AP242 entity relationships
- Rust object layouts remain smaller and faster than runtime dictionary-based late binding
- frontend contracts can be versioned from backend-owned DTOs instead of reverse-engineered from parser output

### Large-File Methodology

For very large STEP documents, the backend should not eagerly hydrate every geometric entity into memory.

Required strategy:

- memory-map the source file so ASCII entity records can be traversed without copying the whole file into heap buffers
- parse the HEADER and assembly-facing entity index first
- defer exact geometry, tessellation, and PMI body expansion until the frontend requests them
- batch geometry decoding for visible or selected subtrees rather than decoding the whole DATA section at open time

### Parallel Parsing Strategy

The parser should follow a map-reduce shape:

1. build stable entity record boundaries from the memory-mapped DATA section
2. map chunks of those records across worker threads
3. produce thread-local entity spans, references, and lightweight descriptors
4. reduce the local results into a global STEP reference graph
5. resolve cross-chunk references after merge rather than forcing a global lock during parsing

Rust ownership and borrowing rules are the reason to build this subsystem in Rust rather than TypeScript or Python. The parser, lazy loaders, and later geometry healing pipeline can remain concurrent without data races.

### Frontend Contract

The TypeScript frontend should not receive raw STEP text. It should receive typed payloads such as:

- document header and protocol summary
- assembly tree nodes
- tessellated scene packets for rendering
- semantic PMI and graphical PMI annotations
- exact-geometry lookup handles for advanced inspection workflows

Recommended transport sequence:

- phase 1: HTTP and JSON for document index, assembly tree, and PMI metadata
- phase 2: chunked or streaming transport for tessellated meshes and large scene updates
- phase 3: binary scene transport when viewport scale requires it

## 6. Migration Strategy Summary

Use a 10-phase migration.

1. inventory the Qt surface area
2. freeze the existing visual contract
3. define backend-owned UI contracts
4. build the TypeScript shell skeleton
5. replicate the shell chrome with static parity
6. migrate command, document, and layout state behind APIs
7. replace tree, property, and task panels
8. replace viewport hosting and scene presentation
9. migrate workbench UIs incrementally
10. remove Qt and PySide dependencies from production UI paths

Each phase must end with explicit acceptance criteria.

## 7. Step-by-Step Plan

### Step 1. Create a Qt Dependency Inventory

Map every direct and indirect Qt dependency across:

- `src/Gui`
- workbench GUI modules under `src/Mod/*/Gui`
- Python GUI code using PySide
- resource pipelines such as icons, translations, and UI forms
- startup lifecycle and main window creation

Deliverables:

- `qt-surface-inventory.md`
- module ownership table
- dependency heatmap: easy to replace, hard to replace, blocked by native assumptions

Exit criteria:

- every Qt class category is accounted for
- every PySide-dependent workbench is identified
- all startup-critical Qt dependencies are listed

### Step 2. Capture the Existing Visual Contract

Before replacing anything, capture the current UI as a reproducible baseline.

Produce a visual parity suite for:

- start screen
- empty document shell
- Part workbench
- PartDesign workbench
- Sketcher task flow
- import/open workflow
- preferences window
- dark theme and light theme states

Capture:

- full-window screenshots
- panel-level screenshots
- spacing and typography tokens
- icon atlas and toolbar composition
- keyboard shortcut map

Deliverables:

- `frontend-parity-baseline/` screenshots
- `design-tokens-baseline.json`
- `interaction-baseline.md`

Exit criteria:

- design baselines can be compared automatically in CI
- visual regressions can be reported numerically

### Step 3. Define a UI Protocol Owned by the Backend

Do not re-encode FreeCAD semantics in React components. Introduce a backend-owned contract for UI composition.

Define protocol messages for:

- application layout state
- menu definitions
- toolbar definitions
- command state: enabled, checked, visible, tooltip, icon, shortcut
- workbench list and active workbench
- document tree model
- property panel schema and editors
- task panel schema
- notifications, progress, jobs, and diagnostics
- selection and preselection state

Recommended representation:

- schema-first contracts under `protocol/`
- generated Rust and TypeScript types
- versioned API rules

Deliverables:

- initial protocol schema
- generated TS and Rust models
- backend adapter layer that translates current FreeCAD state into protocol payloads

Exit criteria:

- no frontend feature requires direct access to Qt objects
- menus, toolbars, and command state can be rendered from protocol payloads alone

### Step 4. Build the TypeScript Desktop Shell

Create the production shell using:

- Tauri desktop host
- React plus TypeScript frontend
- Vite build pipeline
- design token system for theme control
- persistent layout state

At this stage, do not connect full document semantics yet. Only establish:

- window frame
- menu bar region
- toolbar bands
- left and right dock regions
- central viewport region
- status bar
- command palette

Deliverables:

- bootable desktop shell
- routing and shell state model
- theme token implementation

Exit criteria:

- app launches with native desktop packaging
- shell matches the FreeCAD frame proportions and density

### Step 5. Recreate the Application Chrome with Static Visual Parity

Replicate the current FreeCAD chrome exactly before wiring complex behavior.

Sequencing rule for the shell workstream:

- first clone the current FreeCAD frontend layout as closely as possible, including frame proportions, menu height, toolbar density, dock geometry, spacing rhythm, and status-bar packing
- require screenshot-diff and proportion review against the Qt shell before introducing any standards-driven upgrades, benchmark embellishments, or shell-specific visual cleanup
- only after the FreeCAD clone is visually credible should the standards backlog from this plan be layered in for accessibility, localization, standards-aware drafting, MBD, interoperability, and incumbent-CAD benchmark improvements

Rebuild in TypeScript:

- menu bar
- top and side toolbars
- combo view region
- report view region
- tree panel shell
- property panel shell
- status bar zones
- workbench selector

Use the captured baseline to tune:

- font sizes
- toolbar padding
- icon scale
- border and divider styling
- panel spacing
- hover and pressed states
- window-frame and dock proportions
- manager-pane density before any standards-driven polish pass

Deliverables:

- screenshot-diff clean room shell
- icon and theme asset pipeline

Exit criteria:

- baseline screenshots match within agreed tolerance
- product team can switch between Qt shell and TS shell and recognize no major visual drift

### Step 6. Move Command and Workbench State Behind Services

Replace Qt `QAction`, `QMenu`, `QToolBar`, and workbench-selector logic with backend-driven state.

Implement services for:

- command registry
- command execution
- command enablement and check state
- shortcut registration
- workbench activation
- recent files and document tabs

This is the key step that stops Qt from being the command backbone.

Deliverables:

- backend command service
- TS command store
- protocol events for command-state updates

Exit criteria:

- menus and toolbars in the TS shell function without Qt action objects
- active workbench changes are driven through backend APIs

### Step 7. Replace the Tree View, Property Editor, and Task Panels

These three surfaces define most of FreeCAD's day-to-day UX and must be migrated before Qt can disappear.

Sub-steps:

1. Replace the document tree with a virtualized TS tree component.
2. Replace the property editor with schema-driven editors.
3. Replace task panels with backend-described workflows.
4. Replace report and diagnostics views.
5. Replace selection synchronization between panels and viewport.

Important rule:

The backend owns object identity, property metadata, read-only rules, and transaction boundaries. The frontend only renders and edits through commands.

Deliverables:

- TS tree component with large-document support
- property schema renderer
- task panel runtime
- selection sync service

Exit criteria:

- primary editing flows can be completed without any Qt panel widgets
- tree and property edits preserve undo and recompute behavior

### Step 8. Replace the Viewport Host

Qt removal fails if the project does not replace the viewport correctly.

Do not try to port Coin3D widget hosting directly. Instead:

- define a scene payload API from native backend to frontend
- stream tessellated geometry, transforms, materials, visibility, and selection IDs
- render with a web-native viewport stack in TypeScript
- move camera, navigation, overlays, and hit-testing integration into the frontend
- keep heavy geometry generation and authoritative picking metadata in native or backend services

Recommended path:

- frontend rendering with Three.js or a similar GPU-friendly stack
- backend-generated scene graph payloads and incremental updates
- backend-owned selection IDs and stable object mapping

Deliverables:

- viewport scene protocol
- TS viewport renderer
- navigation controls matching current FreeCAD behavior
- overlay layer for preselection, sectioning, measurement, and gizmos

Exit criteria:

- open, navigate, select, hide/show, fit, and isolate work reliably
- camera and selection behavior are familiar to current FreeCAD users

### Step 9. Migrate Workbench UI Surfaces Incrementally

After shell parity exists, migrate workbench UI one domain at a time.

Suggested order:

1. Start
2. Part
3. PartDesign
4. Sketcher
5. Assembly
6. Draft
7. TechDraw
8. BIM
9. CAM
10. FEM, Material, Spreadsheet, and support workbenches
11. Mesh, Surface, ReverseEngineering, Robot, and other specialist workbenches
12. addon, macro, and plugin compatibility surfaces

For each workbench:

- convert commands to backend descriptors
- convert task panels to protocol-driven forms
- replace PySide widgets with TS components
- inventory `InitGui.py`, PySide, macro, and plugin entry points that touch the workbench
- map workbench-specific tree, property, task, report, and viewport contracts before UI replacement
- preserve labels, icons, ordering, and flow structure unless a deliberate redesign is approved

Deliverables:

- workbench migration checklist
- parity review for each migrated workbench

Exit criteria:

- the workbench can run in the TS shell without Qt widgets
- visual and workflow parity are signed off

### Step 10. Build a PySide and Plugin Compatibility Strategy

Qt removal will break plugins and macros unless compatibility is planned explicitly.

Introduce three compatibility modes:

1. pure backend plugin API for new extensions
2. TS frontend contribution API for UI extensions
3. temporary legacy adapter for PySide-heavy plugins during transition

The plugin lane must explicitly include:

- AddonManager installation, update, enable, disable, and trust flows
- macro discovery, execution, and packaging flows
- external workbench registration and workbench-selector integration
- PySide-heavy bundled or third-party dialogs that cannot move immediately
- deprecation guidance for Qt-bound extension APIs

Rules:

- no new plugin should depend on Qt after the migration midpoint
- legacy PySide plugins may run in a compatibility lane for a limited time
- each major bundled workbench should get a de-Qt plan before the final cutover

Deliverables:

- plugin migration guide
- deprecation schedule for PySide GUI plugins
- compatibility adapter design
- addon and macro capability matrix
- extension contribution manifest for backend and TS shell surfaces

Exit criteria:

- extension authors have a supported path forward
- core bundled workflows no longer rely on PySide

### Step 11. Move Preferences, Theming, and Layout Persistence Out of Qt

Qt currently provides much of the application preferences and layout persistence behavior.

Replace it with backend-owned services for:

- preferences schema
- persisted layout state
- theme tokens and overrides
- shortcut customization
- recent files and shell memory

Deliverables:

- preferences service
- TS preferences UI
- layout serialization format

Exit criteria:

- user layout survives restarts without Qt state restoration
- themes and shortcuts can be managed entirely in the new shell

### Step 12. Run Dual-Shell Operation

Do not cut over immediately. Run both shells in parallel during a controlled transition period.

Mode A:

- legacy Qt shell

Mode B:

- TypeScript shell backed by the same native document and command services

Use this period to compare:

- startup times
- workflow completion rates
- crash rates
- visual parity
- missing commands
- extension compatibility

Deliverables:

- dual-shell launch option
- telemetry and acceptance dashboards

Exit criteria:

- TS shell is good enough for daily engineering workflows
- remaining Qt-only blockers are small and enumerated

### Step 13. Remove Qt from Production Runtime Paths

Only after parity is proven should you begin actual removal.

Removal order:

1. stop launching Qt shell by default
2. remove Qt-only UI modules from production startup path
3. remove PySide dependencies from bundled workbenches
4. remove Qt resource and form pipelines no longer used
5. shrink `src/Gui` to bridge-only or remove it entirely where superseded
6. remove Qt from build requirements for the shipping product

Keep a temporary legacy branch if required, but avoid permanent dual maintenance.

Deliverables:

- production build without Qt runtime dependency
- cleanup PR series removing dead Qt code

Exit criteria:

- packaged product runs without Qt libraries
- core workflows and bundled workbenches are supported in the TS shell

## 8. Visual Parity Management Plan

To preserve the same visuality, create a dedicated parity workstream.

### 8.1 Design Token Extraction

Extract and codify:

- fonts
- font sizes
- icon sizes
- spacing scale
- border radii
- panel gaps
- colors
- shadows
- hover and selected states
- compact and high-density variants for ribbon chrome, manager panes, and property rows
- accessibility tokens for focus indication, minimum contrast, and keyboard-visible state

Order of operations:

- phase 1 tokens mirror current FreeCAD chrome as closely as possible for pixel-precise shell cloning
- phase 2 tokens add standards-driven refinement from this plan after the clone has passed screenshot review

Store these as explicit TS design tokens, not informal CSS values.

### 8.2 Screenshot Testing

Add screenshot baselines for:

- app shell states
- each primary workbench
- dialogs and task flows
- light and dark themes
- high-DPI layouts
- compact versus high-density shell density profiles
- translated or text-expanded shell states for major toolbars, panels, and tabs

### 8.3 Interaction Parity Testing

Test:

- keyboard shortcuts
- toolbar overflow behavior
- menu traversal
- property editing sequences
- sketch workflow and task completion flows
- docking and panel resizing behavior
- manager-pane linkage between tree, properties, and graphics area
- in-canvas command access patterns such as heads-up controls, context surfaces, and orientation widgets
- keyboard-only traversal and focus visibility for shell chrome, docks, menus, and task panels
- locale expansion behavior for long labels and translated command strings

### 8.4 User Review Gates

Require sign-off from users familiar with current FreeCAD before declaring parity on:

- shell chrome
- modeling workflow surfaces
- viewport feel
- preferences and customization
- density, command proximity, and manager-pane ergonomics against incumbent CAD expectations
- accessibility and localization readiness for enterprise deployment

## 9. Technical Risks and Mitigations

### Risk 1. Qt is too deeply coupled into `src/Gui`

Mitigation:

- isolate GUI semantics behind protocol adapters first
- avoid direct replacement attempts inside the existing Qt widget tree

### Risk 2. PySide workbenches block removal

Mitigation:

- treat PySide migration as a separate tracked workstream
- provide temporary compatibility adapters

### Risk 3. Viewport replacement regresses usability

Mitigation:

- preserve camera and selection behavior by contract
- validate against real models and large assemblies early

### Risk 4. Frontend becomes a hidden second application core

Mitigation:

- keep command rules, recompute, and document truth in backend services
- use schema-driven rendering instead of hardcoded domain logic in React

### Risk 5. Plugin ecosystem fragments

Mitigation:

- publish extension APIs early
- document migration paths and deprecation windows

### Risk 6. Standards coverage falls behind competitive CAD expectations

Mitigation:

- track ISO, ASME, DIN, IFC, MBD, and regulated-traceability requirements as named work items rather than generic future enhancements
- make AP242, GD&T, PMI, and auditability visible in milestones and acceptance reviews
- avoid shipping a TypeScript shell that looks modern but regresses standards interoperability

### Risk 7. Shell parity regresses against incumbent CAD ergonomics

Mitigation:

- treat Inventor high-density ribbon workflows and SolidWorks manager-pane workflows as explicit benchmark inputs during shell review
- measure in-canvas command distance, tree-to-graphics synchronization, and panel density instead of relying on subjective visual approval
- avoid web-style spacing inflation that reduces visible engineering context on typical workstation monitors

### Risk 8. Accessibility and localization remain procurement blockers

Mitigation:

- externalize shell strings early and run text-expansion review before cutover milestones
- add keyboard and focus-order checks to parity gates, not only screen captures
- maintain a VPAT and WCAG-oriented conformance workstream for the TypeScript shell rather than deferring accessibility until packaging time

## 10. Milestone Sequence

### Milestone A. Discovery and Baselines

- Qt inventory complete
- screenshot and interaction baselines complete
- migration ownership assigned

### Milestone B. Static TS Shell Parity

- TS shell launches
- shell chrome visually matches FreeCAD
- density tokens and manager-pane geometry benchmarked against incumbent CAD baselines
- no core workflow behavior yet required

### Milestone C. Command and Layout Parity

- menus, toolbars, and workbench switching functional
- preferences and layout persistence functional
- in-canvas command access and orientation affordances defined for benchmark workflows

### Milestone D. Editing Surface Parity

- tree, property panel, report view, and task panels functional

### Milestone E. Viewport Parity

- open, inspect, select, and navigate models in TS shell
- tree, property, and graphics linkage proven for both native documents and imported STEP sessions

### Milestone F. Standards Foundation

- AP242 foundation and early-bound EXPRESS infrastructure operational in Rust
- PMI and GD&T transport contracts defined for frontend consumption
- standards backlog established for ISO 128, ISO 1101, ASME Y14.5, ISO 16792, IFC, and traceability workflows
- accessibility, VPAT, and localization backlog established for shell procurement readiness

### Milestone G. Core Workbench Parity

- Start, Part, PartDesign, Sketcher, and Assembly usable in TS shell
- plugin and workbench selector metadata can route users into the migrated workflow family without falling back to Qt-only shell behavior

### Milestone H. Cutover Readiness

- TS shell is stable for daily use
- Qt shell is no longer required for bundled primary workflows
- Draft, TechDraw, BIM, CAM, FEM, addon, macro, and specialist workbench families have either a migrated TS implementation or an explicit supported compatibility lane

### Milestone I. Qt Removal

- production runtime no longer depends on Qt

## 11. Recommended First 90 Days

### Days 1-15

- build Qt dependency inventory
- capture screenshot baselines
- define parity metrics

### Days 16-30

- define protocol contracts for commands, layout, tree, properties, and tasks
- generate TS and Rust types

### Days 31-45

- stand up TS desktop shell
- recreate static FreeCAD chrome

### Days 46-60

- wire menus, toolbars, workbench selector, and status bar to backend state

### Days 61-75

- implement tree and property panel protocol rendering

### Days 76-90

- prototype viewport bridge and validate with real documents
- decide final viewport stack

## 12. Recommended Acceptance Metrics

- less than 5 percent screenshot delta on approved parity views
- 100 percent menu and toolbar command coverage for migrated workbenches
- no mandatory Qt widget dependency for migrated shell surfaces
- startup and open-document flows complete in the TS shell
- no regression in primary workflow completion for Part, PartDesign, and Sketcher pilot users
- no regression in primary workflow completion for Assembly pilot users once Assembly enters the migrated lane
- all bundled primary workflows pass parity review before Qt runtime removal
- every bundled workbench family is accounted for by either a migration checklist or a supported compatibility checklist before production cutover
- AP242 document indexing, lazy entity loading, and PMI transport validated against representative exchange samples
- standards backlog exists for ISO and ASME drawing plus GD&T behaviors, IFC interoperability, and regulated auditability before production cutover
- benchmark shell reviews confirm acceptable density, manager-pane behavior, direct-editing comfort, and in-canvas command proximity against representative Inventor, SolidWorks, and Plasticity workflows
- keyboard traversal, focus visibility, and contrast checks pass for shell chrome and primary panels before production cutover
- localization review demonstrates that translated or text-expanded command labels do not break major menu, toolbar, tab, and property layouts

## 13. Final Recommendation

Do not try to "remove Qt from FreeCAD" as a direct refactor inside the existing UI layer.

The viable plan is:

1. preserve the native modeling core
2. move UI semantics behind explicit backend contracts
3. build a TypeScript shell with screenshot-verified visual parity
4. migrate workbench surfaces incrementally
5. cut over only after the TypeScript shell is genuinely usable
6. remove Qt last, not first

That sequence gives the best chance of keeping FreeCAD recognizable while replacing its frontend stack without destabilizing the product.