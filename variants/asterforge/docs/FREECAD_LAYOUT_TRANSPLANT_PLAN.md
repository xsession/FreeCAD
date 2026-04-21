# AsterForge FreeCAD Layout Transplant Plan

Status: structural parity implemented in the React shell on 2026-04-20. The remaining work is refinement, persistence, and deeper backend-owned menu and toolbar models.

## Goal

Clone the practical FreeCAD desktop layout into the React shell as closely as possible, while keeping Rust as the authoritative backend and reusing the slices already implemented in AsterForge.

This plan is about layout and workflow parity first:

- menu bar structure
- toolbar density
- document tabs
- combo view behavior
- center viewport dominance
- bottom utility docks
- status bar feedback

It is not yet a pixel-for-pixel skin copy of every Qt widget. The immediate target is a faithful React transplant of the FreeCAD workspace model.

## FreeCAD Regions To Recreate

### Menu Bar

Match the classic desktop application frame:

- File
- Edit
- View
- Tools
- Macro
- Window
- Help

### Toolbar Deck

The top chrome should behave like FreeCAD's dense toolbar rows:

- workbench selector
- primary file and edit actions
- recompute and save affordances
- selection and workflow shortcuts
- command palette access as an AsterForge enhancement

### Document Tabs

Keep tabbed document switching visible near the top of the shell, not hidden in dashboard-style cards.

### Combo View

The left dock should become the FreeCAD-style combo view:

- Model tab
- Tasks tab

Inside `Model`, provide:

- tree/content view
- property view

Inside `Tasks`, host:

- active task panel
- selection guidance
- command forms related to the current task or preselection

### Central Viewport

The center must become the dominant workspace area:

- viewport at top
- interaction overlays kept minimal
- workbench and selection tools attached to the viewport region

### Bottom Utility Dock

This should mirror the report-style utility area used by FreeCAD:

- Report view
- Python console
- Jobs
- Diagnostics
- History
- Commands

`Python Console` can ship as a placeholder first, but the dock slot must exist now.

### Status Bar

The bottom status strip should continuously show:

- active workbench
- save state
- selected object
- backend worker mode
- service and job health

## Implementation Phases

### Phase 1: Structural Parity

Replace the current dashboard shell with a desktop CAD frame:

- remove hero-first layout
- add menubar and toolbar stack
- convert left side into combo view
- convert lower area into tabbed bottom dock
- add status bar

### Phase 2: Visual Density Parity

Tune spacing and proportions toward FreeCAD:

- flatter panels
- tighter toolbar controls
- dock borders instead of card-first composition
- more desktop-like vertical compression

### Phase 3: Interaction Parity

Bring behavior closer to FreeCAD:

- persist active combo view tab
- persist bottom dock tab
- add keyboard focus and selection cues
- map more toolbars directly to command groups

### Phase 4: Detailed Layout Clone

Push closer to 1:1 shell parity:

- menu ownership by backend command taxonomy
- proper toolbar grouping
- dock resize handles
- detachable or reconfigurable panels
- layout persistence profiles

## Mapping Existing AsterForge Features Into The New Shell

### Combo View / Model

- object tree
- properties

### Combo View / Tasks

- task panel
- selection inspector

### Center Viewport

- backend-owned scene payload
- preselection overlay
- selection mode toolbar
- quick actions

### Bottom Dock / Report

- backend activity stream
- notice cards

### Bottom Dock / Python Console

- placeholder now
- real backend automation console later

### Bottom Dock / Jobs

- jobs panel

### Bottom Dock / Diagnostics

- diagnostics panel

### Bottom Dock / History

- feature timeline

### Bottom Dock / Commands

- command catalog

## Immediate Acceptance Criteria

This step is complete when:

1. the React app no longer presents a dashboard hero layout
2. the shell visually reads as a desktop CAD workspace
3. the object tree, task panel, properties, viewport, activity stream, jobs, diagnostics, history, and command deck all remain accessible
4. the viewport is the dominant center region
5. the left side behaves like a combo view
6. the bottom area behaves like a utility dock
7. the status bar reports live backend state

## Next Targets

- persist dock tabs across sessions
- add toolbar groups derived from backend command metadata
- add a real menu command model
- add a Python console service and panel
- add resizable dock splitters
- continue tuning spacing and contrast toward a closer FreeCAD clone
