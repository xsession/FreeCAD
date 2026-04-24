# Inventor UX Slice 01 - Shell Wayfinding Refinement

Version: 0.1
Date: 2026-04-24
Status: Sprint-ready

## Implementation Status Snapshot

Status as of 2026-04-24:

- implemented first parity step for combo-box selector mode
- combo mode now exposes the same searchable overflow and pinned-workbench management surface as the tabbed selector path
- overflow menus now expose visible purpose text rather than relying only on tooltips
- overflow menus now group workbenches by high-level category
- pinned-workbench behavior is now explained directly in the pin-management submenu
- pinned workbenches are now visibly marked in the main overflow list, not only in the pin-management submenu
- remaining work for this slice is now centered on:
  - optional refinement of overflow visual presentation beyond menu-based grouping

## Purpose

This slice refines the current workbench-selector experience so it behaves more like a professional mode navigator and less like a technical action list.

It intentionally builds on the current implementation rather than replacing it.

## Why This Slice Changed

The initial backlog assumed the first shell-wayfinding slice still required building:
- workbench purpose metadata
- favorites and recents persistence
- searchable overflow

Code review shows those foundations already exist in:
- `src/Gui/Action.cpp`
- `src/Gui/WorkbenchSelector.cpp`

So the real remaining work is narrower and more valuable:
- make the experience consistent across selector modes
- move guidance from hidden tooltips into visible UI
- reinforce mode-based navigation instead of relying mostly on ranking and labels

## Current Implementation Baseline

### Already implemented
- workbench purpose text mapping in `Action.cpp`
- composed tooltips including purpose text
- favorites persistence
- recent-workbench persistence and ranking
- tabbed selector primary tabs based on favorites
- searchable `More` overflow in `WorkbenchTabWidget`
- pinned-workbench management from overflow menu
- visible purpose text in overflow entries
- category-based grouping in overflow entries

### Remaining UX problems
- combo-box selector mode does not offer equivalent search and guidance behavior
- workbench purpose is mostly hidden in tooltips instead of being visible in the selection flow
- overflow presentation is still a flat action list with limited semantic grouping
- users are still choosing from implementation names more than from task-oriented descriptions

## Product Goal

Enable a user to answer these questions immediately when switching workbenches:
- what is this workbench for
- is it one of my primary modes
- if it is not pinned, how do I find it quickly
- what category of work does it belong to

## Scope

### In scope
- workbench selector UX in combo-box and tabbed modes
- visible purpose text and grouping in overflow surfaces
- small data-model additions needed to support categories or richer labels
- preference-safe improvements to the selector path

### Out of scope
- shell-state normalization for edit workflows
- ribbon `Home` logic
- task-panel redesign
- startup or backstage redesign

## User Stories

### Story 1
As a new mechanical-design user, I can find the right workbench without already knowing FreeCAD workbench names.

### Story 2
As a returning user, I can switch among my common workbenches with one click and find infrequent workbenches with one short search.

### Story 3
As a mixed-workflow user, I can infer whether a workbench is for modeling, assembly, simulation, documentation, or utilities.

## Proposed Changes

## 1. Selector-Mode Parity

### Problem
Tabbed mode has searchable overflow. Combo-box mode does not provide equivalent guided discovery.

### Change
Add a lightweight searchable path for combo-box users.

### Options

#### Preferred option
- keep the combo box for quick switching
- add a trailing or adjacent button that opens the same searchable overflow used by the tabbed selector

#### Acceptable option
- replace the raw combo popup with a custom popup that includes a search field and grouped sections

### Target files
- `src/Gui/WorkbenchSelector.h`
- `src/Gui/WorkbenchSelector.cpp`

### Acceptance
- combo-box users can reach any workbench through a short search flow without scanning a long list

## 2. Visible Purpose Cues

### Problem
Purpose text exists but is mostly hidden in tooltips.

### Change
Expose short descriptive text directly in the overflow path.

### Implementation direction
- in searchable overflow surfaces, render each workbench with:
  - icon
  - label
  - one-line purpose text
- keep label and purpose distinct so internal names do not carry all of the UX burden

### Target files
- `src/Gui/WorkbenchSelector.cpp`
- possibly supporting item delegates or menu-widget containers
- `src/Gui/Action.cpp` if purpose metadata needs extension

### Acceptance
- a user can infer the purpose of a workbench from the selection surface without hovering for a tooltip

## 3. Category-Based Grouping

### Problem
Overflow surfaces are still mostly flat lists.

### Change
Introduce light semantic grouping for major workbench categories.

### Suggested categories
- Modeling
- Assembly
- Simulation
- Documentation
- Data and Utility
- Experimental

### Data model
- add a small category mapping beside the existing purpose mapping
- keep it centralized and short

### Target files
- `src/Gui/Action.cpp`
- `src/Gui/WorkbenchSelector.cpp`

### Acceptance
- the overflow surface no longer feels like an unstructured list of internal modules

## 4. Better Favorite Management Feedback

### Problem
Pinned workbench management exists but remains tucked inside the overflow path.

### Change
- make favorite state more visible in selection surfaces
- clarify that pinned workbenches become primary tabs or primary modes

### Target files
- `src/Gui/WorkbenchSelector.cpp`

### Acceptance
- users understand the relationship between pinning and primary workbench visibility

## Interaction Design

## Tabbed mode
- keep primary favorites visible as tabs
- keep `More` as overflow entry point
- improve overflow entries with visible purpose text and category grouping
- preserve current search behavior

## Combo mode
- preserve simple quick-switch behavior
- add a searchable “all workbenches” discovery path
- use the same metadata and grouping model as tabbed mode

## Data Requirements

### Required metadata per workbench
- visible label
- internal id
- one-line purpose
- category
- favorite state
- recent rank

### Current data already available
- visible label
- internal id
- icon
- favorite state
- recent rank
- one-line purpose

### New data to add
- category

## Implementation Tasks

### Task A
Add centralized workbench category metadata.

Files:
- `src/Gui/Action.cpp`

### Task B
Refactor selector helper logic so combo and tabbed modes can share more overflow/discovery behavior.

Files:
- `src/Gui/WorkbenchSelector.h`
- `src/Gui/WorkbenchSelector.cpp`

### Task C
Implement visible purpose text in overflow entries.

Files:
- `src/Gui/WorkbenchSelector.cpp`

### Task D
Add combo-box parity for searchable workbench discovery.

Files:
- `src/Gui/WorkbenchSelector.h`
- `src/Gui/WorkbenchSelector.cpp`

### Task E
Document the selection behavior and expected UX contract.

Files:
- this document
- optionally `docs/architecture/frontend-shell-ux-plan.md`

## Verification Plan

### Manual verification
- switch between selector modes and confirm both support quick discovery
- confirm favorites still drive primary tabs
- confirm recent ordering remains stable
- confirm non-pinned workbenches are reachable in one short search path
- confirm purpose text is visible without tooltip dependency

### Regression targets
- existing selector behavior should not break for users who prefer the current tabbed mode
- no regression in workbench activation behavior
- no regression in saved favorites and recents preferences

## Success Criteria

This slice is complete when:
- combo-box and tabbed selector modes offer equivalent discovery quality
- overflow surfaces visibly explain what a workbench is for
- users can distinguish workbench categories at a glance
- the selector feels like mode navigation rather than a raw technical list

## Recommended Next Slice After This

After shell wayfinding refinement, the best next slice is:
- adaptive `Home` tab behavior for PartDesign, Sketcher, and Assembly

That work will build directly on the improved workbench-mode clarity from this slice.