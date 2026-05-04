# Plasticity UX and Backend Benchmark Notes

Status: benchmark input for AsterForge shell and Rust-service evolution

## Purpose

Plasticity is a useful benchmark for two reasons:

- the frontend feels calm, dense, and low-friction without looking like a generic web dashboard
- the public repository exposes a command, viewport, and editor architecture that is worth learning from even though FreeCAD has very different kernel and product constraints

This document is not a license to clone Plasticity assets, branding, copy, or exact UI composition. The target is to learn from the interaction model, density discipline, command flow, and editor architecture and translate those ideas into an original FreeCAD shell.

Public reference inputs used here:

- `https://doc.plasticity.xyz`
- `https://www.plasticity.xyz`
- `https://github.com/nkallen/plasticity`

## Frontend Patterns Worth Borrowing

### 1. Viewport-first shell

Plasticity keeps the viewport as the center of gravity. Supporting surfaces exist, but they do not visually compete with the modeling area.

Signals visible from the docs and product surface:

- outliner and assets exist as support panes, not the main spectacle
- command palette, command bar, radial menu, selection mode, and view cube are all first-class navigation surfaces
- common actions stay close to the viewport instead of forcing long pointer travel to distant chrome

Implication for AsterForge:

- continue pushing command access, selection mode, orientation controls, and contextual task actions into the graphics area
- keep docks visually subordinate to the active canvas instead of letting report or utility surfaces dominate the shell

### 2. Calm, dense visual language

Plasticity feels comfortable largely because it is visually restrained. It uses low-chroma chrome, compact spacing, and clear state contrast instead of loud panel framing.

Patterns worth translating:

- compact desktop density with tight spacing and small but legible typography
- restrained contrast in chrome so the model and active interaction state carry attention
- strong hover, selection, and active-command cues when they matter
- simple panel silhouettes instead of busy card-heavy web layouts

Implication for AsterForge:

- treat density tokens as a first-class shell contract
- reduce dashboard-style framing around utility panels
- keep accent colors reserved for selection, warnings, active tools, and command-ready states

### 3. Direct command flow over form-heavy workflow

Plasticity exposes a command palette, command bar, radial menu, viewport gizmos, and prompt-oriented steps. The visible pattern is low-friction command execution, not wizard-heavy form navigation.

Patterns worth translating:

- commands describe the next required pick or parameter clearly
- small dialogs and gizmos work together instead of competing
- keyboard-first and quasimode-style flows reduce travel and mode confusion
- direct editing feels immediate because command preview and confirmation stay close to the model

Implication for AsterForge:

- expand the existing command metadata path toward prompt-driven command sequences
- keep parameter editors compact and colocated with the active operation
- add radial or marking-menu style access for high-frequency viewport commands

### 4. Comfortable customization surfaces

Plasticity exposes configurable orbit-control schemes, theme loading, keymaps, and command lists. That matters because comfort is not only visual; it is also input ergonomics.

Implication for AsterForge:

- backend-owned preferences should include navigation presets, keymap profiles, and viewport behavior profiles early
- dual benchmarks should include Blender-, Maya-, and CAD-style navigation expectations instead of assuming one input scheme

## Backend and App-Architecture Lessons

Plasticity's repository is not a Rust service architecture, but its editor composition and command execution model are instructive.

### 1. Composition-root editor object

The public repo centers a single `Editor` that owns history, command execution, backup, selection, import/export, planes, highlighting, and viewport references.

Why this matters for AsterForge:

- FreeCAD should keep document truth in backend services, but the shell still needs an explicit session composition root
- the current AsterForge `ShellSnapshot` and service-container direction is correct; it should continue toward one authoritative session coordinator per open document or workspace

### 2. Strong command lifecycle discipline

Plasticity commands are explicit objects with lifecycle, cleanup, and history behavior. Commands own resources such as dialogs, gizmos, and factories, and execution cleanup is centralized.

Patterns worth adopting:

- command execution should have explicit preview, commit, cancel, and cleanup phases
- temporary helpers and preview state should be torn down deterministically
- command completion should be the trigger for history writes, autosave, and user-visible activity summaries

Implication for AsterForge:

- expand backend command execution contracts beyond fire-and-forget actions into explicit transactional phases
- keep preview and ephemeral geometry on a dedicated contract instead of mixing them with durable document state

### 3. History and backup tied to successful commands

The repo shows backup persistence triggered on successful commands and history changes.

Implication for AsterForge:

- autosave and recovery should key off backend command completion and document-state transitions, not arbitrary UI timers alone
- document history, undo, redo, and crash recovery should remain backend-owned event lanes

### 4. Viewport architecture separates permanent, phantom, and helper layers

Plasticity keeps separate scenes or layers for durable geometry, temporary phantom geometry, and helpers or gizmos.

Implication for AsterForge:

- formalize viewport payload categories for persisted drawables, preview drawables, and interaction helpers
- avoid pushing temporary command previews through the same long-lived scene contract used for document geometry

### 5. Input and command registration are infrastructural, not ad hoc

The public repo exposes a command registry, keybinding registration, and centralized dispatch from shell surfaces and viewport elements.

Implication for AsterForge:

- the shell needs a backend-owned keybinding and command registration service, not scattered React-only handlers
- menus, palettes, HUD actions, and future radial surfaces should all resolve the same command metadata and execution path

### 6. Theme and settings are loaded from user-editable config files

The repo loads theme and settings from config files and applies them to renderer and UI state.

Implication for AsterForge:

- preferences, theme tokens, and keymaps should be backed by explicit persisted schemas instead of ad hoc frontend local state
- shell startup should load those settings before viewport and chrome composition so the first frame already reflects the user's density and navigation preferences

## Translation Rules for FreeCAD

What to mimic:

- viewport-first attention model
- dense and calm desktop spacing
- low-travel command access
- prompt-driven command progression
- strong preview and helper lifecycle
- consistent command metadata across menus, palette, HUD, and contextual surfaces
- backend-owned recovery, history, and settings

What not to copy literally:

- Plasticity branding, wording, icons, product art, screenshots, or exact component shapes
- exact menu structure or commercial feature packaging
- assumptions that direct modeling should replace FreeCAD's history- and workbench-heavy workflows wholesale

## Recommended AsterForge Work Items

### Frontend work items

- define a high-density token pass for panel spacing, toolbar height, text scale, and icon rhythm
- add a viewport command bar or radial command surface for high-frequency actions
- keep the titlebar and menu chrome visually lighter so the viewport remains dominant
- make property and task editors more compact and prompt-oriented during active commands
- benchmark shell comfort against long sessions, not only screenshots

### Backend work items

- introduce explicit command phases for preview, commit, cancel, and cleanup in the Rust command runtime
- add a preview-drawable channel separate from durable scene payloads
- wire autosave and crash recovery to backend command-success and history events
- add preferences schemas for navigation modes, keymap presets, viewport options, and density modes
- preserve one shared command registry across menus, palettes, HUD, notices, and task suggestions

## Suggested Review Gate

For future shell work, benchmark against three distinct references instead of only one:

- FreeCAD for workflow and product identity
- Inventor and SolidWorks for engineering density and manager-pane expectations
- Plasticity for calm viewport-first interaction, low-travel command flow, and direct-manipulation comfort

## Applied in Current Tree

The current AsterForge shell now includes an initial Plasticity-inspired adaptation pass:

- the command palette can now open via `F` as well as `Ctrl+K` outside editable fields
- selection-mode switching now supports numeric `1-9` shortcuts derived from backend-published mode order
- palette, HUD, and overlay chrome were tightened to keep the shell denser and visually quieter around the viewport
- the viewport now carries its own quick-access strip for search and session context, a backend-driven command shelf sourced from hover and task suggestions, inline expansion of argument-bearing suggested commands through the shared command editor path, and a layout rebalance so the left dock and lower dock read more like supporting surfaces than primary chrome

This is still not full command-flow parity. The next practical step is to move backend-owned interaction preferences such as density, keymap, and navigation profiles into the shell contract, not to clone Plasticity's exact menus or gestures.