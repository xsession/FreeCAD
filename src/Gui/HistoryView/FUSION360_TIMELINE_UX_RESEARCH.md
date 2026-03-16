# Fusion 360 Timeline UX/UI — Deep Research & Analysis

> **Purpose**: Comprehensive research document analyzing Autodesk Fusion 360's Design History Timeline — its visual design, interaction patterns, underlying philosophy, and typical workflows — to guide the implementation of a comparable feature in FreeCAD's HistoryView.

---

## Table of Contents

1. [Overview & Philosophy](#1-overview--philosophy)
2. [Visual Design & Layout](#2-visual-design--layout)
3. [Feature Node Anatomy](#3-feature-node-anatomy)
4. [Interaction Patterns](#4-interaction-patterns)
5. [Rollback Bar / History Marker](#5-rollback-bar--history-marker)
6. [Suppress / Unsuppress](#6-suppress--unsuppress)
7. [Drag-and-Drop Reorder](#7-drag-and-drop-reorder)
8. [Feature Groups](#8-feature-groups)
9. [Right-Click Context Menu](#9-right-click-context-menu)
10. [Keyboard Shortcuts & Quick Actions](#10-keyboard-shortcuts--quick-actions)
11. [Capture / Do Not Capture Design History](#11-capture--do-not-capture-design-history)
12. [Color Coding & Iconography](#12-color-coding--iconography)
13. [Typical User Workflows](#13-typical-user-workflows)
14. [Comparison: Fusion 360 vs. Current FreeCAD HistoryView](#14-comparison-fusion-360-vs-current-freecad-historyview)
15. [Implementation Recommendations for FreeCAD](#15-implementation-recommendations-for-freecad)

---

## 1. Overview & Philosophy

### 1.1 What Is the Timeline?

The Fusion 360 **Design History Timeline** is a horizontal bar located at the **bottom of the viewport** that records every modeling operation (feature) in chronological order. Each feature appears as a small icon node on a connecting horizontal line, creating a visual "filmstrip" of the design process.

### 1.2 Core Design Philosophy

The timeline embodies several key principles from Autodesk's design thinking:

- **Non-destructive Editing**: Every operation is recorded and can be revisited. Users never permanently lose the ability to go back and change earlier steps.
- **Parametric History as First-Class UX**: Unlike traditional CAD where the feature tree is a sidebar afterthought, Fusion 360 makes the parametric history a persistent, always-visible element at the bottom of the screen.
- **Direct Manipulation**: Users interact with the timeline through drag-and-drop, double-click, and dragging the rollback marker — all direct manipulation metaphors familiar from video editing software.
- **Progressive Disclosure**: The timeline starts simple (just a line of icons) but reveals depth through right-click menus, grouping, and rollback — complexity is accessible but not overwhelming.
- **Time Travel Metaphor**: The rollback bar creates a mental model of "time travel" — you can go back to any point in your design's history and see the model as it existed then.

### 1.3 Influences & Inspiration

The timeline draws from:
- **Video editing timelines** (Premiere, Final Cut): horizontal, left-to-right chronological layout
- **Git version control**: the idea of rewinding to any commit
- **Parametric CAD feature trees** (SolidWorks, CATIA): but laid out horizontally instead of vertically
- **Undo history panels** (Photoshop): but with richer metadata and interaction

### 1.4 Why Horizontal, Not Vertical?

Autodesk's choice of horizontal layout (vs. SolidWorks' vertical tree) is deliberate:
- **Screen real estate**: Horizontal bars at the bottom consume minimal vertical space, leaving more room for the 3D viewport
- **Temporal metaphor**: Left-to-right reading order maps naturally to chronological order (in LTR languages)
- **Scalability**: A horizontal bar can hold dozens or hundreds of features via scrolling without dominating the UI
- **Separation of concerns**: The vertical sidebar can be used for the browser (component/body tree) while the timeline shows operations

---

## 2. Visual Design & Layout

### 2.1 Screen Position & Dimensions

- **Position**: Fixed at the **bottom** of the 3D viewport, spanning the full width
- **Height**: Approximately **36-44 pixels** (single row of icons)
- **Background**: Semi-transparent dark gray/charcoal (#2D2D2D to #3C3C3C)
- **Always visible**: Unlike dockable panels, the timeline is always shown (unless explicitly hidden via View menu)

### 2.2 The Connecting Line

- A thin **horizontal line** (1-2px) connects all feature nodes
- Color: Medium gray (#808080) for active features, lighter gray for the "future" section past the rollback marker
- The line creates visual continuity and reinforces the chronological narrative

### 2.3 Feature Nodes

Each feature appears as a **small square icon** (approximately 24x24 to 32x32 pixels) sitting on the connecting line:
- Icons are **feature-type specific** (see Section 12)
- Nodes are evenly spaced along the line
- Active (computed) nodes are fully opaque
- Rolled-back (future) nodes are semi-transparent / grayed out

### 2.4 Scrolling Behavior

- **Horizontal scroll**: Mouse wheel while hovering over timeline scrolls left/right
- **Auto-scroll**: When a new feature is added, the timeline auto-scrolls to show it
- **Overflow indicators**: Small arrows appear at left/right edges when there are more features beyond the visible area
- **Zoom**: Ctrl+scroll or pinch gesture adjusts spacing between nodes (zoom in/out)

### 2.5 Responsive Layout

- When few features exist, nodes are centered or left-aligned with comfortable spacing
- As features accumulate, spacing compresses before scrolling kicks in
- Minimum spacing ensures icons remain clickable (touch-friendly on tablets)

---

## 3. Feature Node Anatomy

### 3.1 Node States

Each feature node can be in several visual states:

| State | Visual Treatment |
|-------|-----------------|
| **Normal** | Full color icon, sits on timeline |
| **Selected** | Blue highlight border/background |
| **Hovered** | Slight brightness increase, tooltip appears |
| **Suppressed** | Red "X" overlay on the icon |
| **Rolled back** | Dimmed/grayed out, past the rollback marker |
| **Error** | Yellow warning triangle or red error badge |
| **Computing** | Spinning/pulsing animation |

### 3.2 Tooltip on Hover

Hovering over a node displays a rich tooltip:
- **Feature name** (e.g., "Extrude 3")
- **Feature type** (e.g., "Extrude")
- **Creation timestamp**
- **Parameters summary** (e.g., "Distance: 10 mm, Direction: One Side")
- **Status** (e.g., "Up to date" or "Error: Invalid geometry")

### 3.3 Selection Behavior

- **Single click**: Selects the feature, highlights in viewport, shows properties
- **Double-click**: Opens the feature for editing (re-enters the feature's dialog/task panel)
- **Multi-select**: Ctrl+click or Shift+click for multiple selection (for group operations)

---

## 4. Interaction Patterns

### 4.1 Direct Manipulation Principles

Fusion 360's timeline follows Shneiderman's principles of direct manipulation:
1. **Continuous representation** of objects of interest (features always visible as icons)
2. **Physical actions** instead of syntax (drag, click, not type commands)
3. **Rapid, incremental, reversible operations** (undo, rollback, suppress)
4. **Immediate visual feedback** (model updates as you interact)

### 4.2 Edit-in-Place

- **Double-click** a feature node → opens that feature's edit dialog
- The model rolls back to show the state at that feature
- User modifies parameters → model recomputes forward from that point
- This is the most common and most important interaction

### 4.3 Dependency Visualization

- When a feature is selected, features that depend on it can be highlighted
- Some versions show dependency arrows between related features
- This helps users understand the impact of changes

### 4.4 Model Synchronization

- The 3D viewport **always reflects the current timeline position**
- If the rollback marker is at feature 5 of 10, the model shows state after feature 5
- Features 6-10 are "in the future" — their geometry is not visible

---

## 5. Rollback Bar / History Marker

### 5.1 What Is It?

The **rollback bar** (also called the "history marker" or "end-of-history marker") is a **draggable vertical line/triangle** on the timeline that indicates the current computation point.

### 5.2 Visual Design

- **Appearance**: A triangular marker (▼) or vertical bar sitting on the timeline
- **Color**: Bright blue or yellow to stand out from the gray timeline
- **Position**: Between feature nodes, or at the far right (end of history)
- **Default position**: Far right (all features computed)

### 5.3 Dragging the Rollback Bar

This is one of the most powerful and distinctive features of the Fusion 360 timeline:

1. **Click and drag** the marker left → model "rewinds" to that point
2. **Everything to the right** of the marker becomes grayed out / dimmed
3. The **3D model updates in real-time** as you drag
4. **New features added** while rolled back are inserted at the marker position
5. **Drag right** to re-apply features (like "redo")
6. **Double-click** the marker to jump to end (restore all features)

### 5.4 Rollback Use Cases

- **Inspect intermediate states**: "What did my model look like after just the first extrude?"
- **Insert features mid-history**: Roll back to step 5, add a fillet → it becomes step 6, old steps 6+ shift right
- **Debug failures**: If a late feature fails, roll back to find where geometry breaks
- **Present design evolution**: Drag through the timeline to show stakeholders how a design was built

### 5.5 Visual Feedback During Rollback

- Rolled-back features: dimmed icons, possibly with a diagonal stripe overlay
- Active features: full color, connected by the solid timeline line
- The rollback marker has a slight "glow" or "drag handle" affordance
- Cursor changes to horizontal resize (↔) when hovering the marker

---

## 6. Suppress / Unsuppress

### 6.1 Concept

**Suppress** temporarily disables a feature without deleting it — the feature remains in the timeline but is skipped during model computation. This is analogous to "commenting out" a line of code.

### 6.2 Visual Treatment

- Suppressed features show a **red "X" overlay** on their icon
- The feature name may appear in ~~strikethrough~~ text
- The timeline line may show a **gap** or **dashed segment** at the suppressed feature
- The 3D model updates immediately to reflect the suppressed state

### 6.3 Interaction

- **Right-click → Suppress Features**: Suppresses selected feature(s)
- **Right-click → Unsuppress Features**: Reactivates suppressed feature(s)
- **Keyboard shortcut**: Often assigned to a hotkey for quick toggling

### 6.4 Use Cases

- **What-if analysis**: "What would my model look like without this fillet?"
- **Performance**: Suppress complex features to speed up recomputation
- **Debugging**: Isolate which feature is causing a failure
- **Design variants**: Create different configurations by suppressing different features

---

## 7. Drag-and-Drop Reorder

### 7.1 Concept

Features can be **reordered** in the timeline by dragging them to a new position. This changes the order in which operations are applied to the model.

### 7.2 Visual Feedback

- **Drag indicator**: When dragging, a vertical line appears between nodes showing the drop position
- **Invalid positions**: Some positions may be invalid (due to dependencies) — shown with a "no drop" cursor
- **Animation**: Other nodes shift smoothly to make room for the dragged feature
- **Dependency check**: Fusion 360 prevents moves that would break parent-child relationships

### 7.3 Constraints

- A feature cannot be moved before its parent/dependency features
- Moving a feature triggers a full recompute from the moved position forward
- Some features are "locked" and cannot be moved (e.g., the base feature)

### 7.4 Interaction Details

1. **Click and hold** on a feature node (~200ms delay to distinguish from click)
2. **Drag horizontally** — a ghost of the icon follows the cursor
3. **Insertion indicator** appears between valid drop positions
4. **Release** — feature moves, model recomputes
5. If the result is invalid, Fusion may warn or undo the move

---

## 8. Feature Groups

### 8.1 Concept

Multiple features can be **collapsed into a named group** on the timeline, reducing visual clutter. This is like folding a code region.

### 8.2 Visual Design

- **Collapsed group**: Appears as a single wider node with a group icon and the group name
- **Expanded group**: Shows all contained features normally, with a bracket/border indicating the group boundaries
- **Expand/collapse**: Click the group icon or double-click the group node

### 8.3 Creating Groups

- **Select multiple features** (Shift+click or Ctrl+click in timeline)
- **Right-click → Group**: Creates a named group
- **Rename**: Right-click → Rename Group
- **Ungroup**: Right-click → Ungroup

### 8.4 Benefits

- **Organization**: Group related features (e.g., "Handle Detail", "Mounting Holes")
- **Navigation**: Quickly scroll past complex sections
- **Communication**: Named groups help collaborators understand design intent

---

## 9. Right-Click Context Menu

### 9.1 Menu Items

Right-clicking a feature node in the timeline reveals (approximately):

| Menu Item | Description |
|-----------|-------------|
| **Edit Feature** | Opens the feature's parameter dialog (same as double-click) |
| **Rename** | Rename the feature |
| **Suppress Features** | Temporarily disable the feature |
| **Unsuppress Features** | Re-enable a suppressed feature |
| **Move to This Position** | Moves the rollback bar here |
| **Delete** | Permanently removes the feature |
| **Copy / Paste** | Copy feature parameters |
| **Find in Browser** | Highlights the feature in the component tree |
| **Group** | Group selected features |
| **Ungroup** | Break apart a group |
| **Create Selection Set** | Save a selection for reuse |
| **Properties** | Show detailed feature properties |

### 9.2 Context Sensitivity

- Menu items change based on:
  - Whether one or multiple features are selected
  - The feature type (sketches have "Edit Sketch", joins have "Edit Join")
  - Whether the feature is suppressed or not
  - Whether features are in a group

---

## 10. Keyboard Shortcuts & Quick Actions

### 10.1 Common Shortcuts

| Shortcut | Action |
|----------|--------|
| **Double-click** | Edit feature |
| **Delete/Backspace** | Delete selected feature |
| **Ctrl+Z** | Undo |
| **Ctrl+Y** | Redo |
| **Ctrl+click** | Multi-select features |
| **Shift+click** | Range select features |
| **Home** | Scroll timeline to beginning |
| **End** | Scroll timeline to end |
| **Left/Right arrow** | Move selection to previous/next feature |

### 10.2 Toolbar Actions

Above or near the timeline, quick-access buttons provide:
- **Undo / Redo** buttons
- **Timeline visibility toggle**
- **Zoom controls** (fit all, zoom in, zoom out)

---

## 11. Capture / Do Not Capture Design History

### 11.1 Concept

Fusion 360 allows users to toggle whether the timeline records operations:

- **"Do Not Capture Design History"**: All features are computed but not recorded in the timeline. The model becomes a "dumb solid" without parametric history.
- **"Capture Design History"**: Returns to normal timeline recording.

### 11.2 Use Cases

- **Imported geometry**: When working with STEP/IGES imports that have no native history
- **Performance**: Very complex models may benefit from not tracking history
- **Simplification**: When parametric control is not needed

### 11.3 Visual Indicator

- When history capture is off, the timeline area shows a banner: "Design History is not being captured"
- A special icon or badge indicates the mode

---

## 12. Color Coding & Iconography

### 12.1 Feature Type Icons

Each feature type has a **distinct icon** to enable quick visual identification:

| Feature Type | Icon Description | Typical Color |
|-------------|-----------------|---------------|
| **New Component** | Grid/box icon | Gray |
| **Sketch** | Pencil / drafting icon | Orange/Yellow |
| **Extrude** | Upward arrow / block | Blue |
| **Revolve** | Circular arrow | Blue |
| **Sweep** | Curved arrow along path | Blue |
| **Loft** | Connected profiles | Blue |
| **Fillet** | Arc/radius icon | Green |
| **Chamfer** | Angled corner | Green |
| **Shell** | Hollow box | Green |
| **Hole** | Circle with cross | Blue |
| **Pattern** | Grid dots | Purple |
| **Mirror** | Reflected shapes | Purple |
| **Combine** | Overlapping shapes | Orange |
| **Split** | Divided shape | Orange |
| **Move/Align** | Crosshair arrows | Gray |
| **Joint** | Hinge/pivot icon | Teal |
| **As-Built Joint** | Hinge with wrench | Teal |
| **Appearance** | Paint bucket/palette | Pink |
| **Section Analysis** | Cut plane | Gray |
| **Physical Material** | Cube with texture | Brown |

### 12.2 Color Families

Fusion 360 uses color families to group related operations:
- **Blue**: Additive geometry (Extrude, Revolve, Loft, Sweep)
- **Green**: Modification operations (Fillet, Chamfer, Shell, Draft)
- **Orange/Yellow**: Sketch and construction geometry
- **Purple**: Patterning and symmetry
- **Red**: Suppressed features (X overlay)
- **Gray**: Utility and analysis operations
- **Teal**: Assembly/joint operations

### 12.3 Status Badges

Small badges overlay the feature icon to indicate status:
- ⚠️ **Yellow triangle**: Warning (feature computed but with issues)
- ❌ **Red circle**: Error (feature failed to compute)
- 🔄 **Blue arrows**: Computing / updating
- 🔒 **Lock**: Feature is locked/frozen

---

## 13. Typical User Workflows

### 13.1 Basic Modeling Workflow

1. Create a **Sketch** on a plane → Sketch node appears in timeline
2. **Extrude** the sketch → Extrude node appears next
3. Add **Fillets** → Fillet node appears
4. Add **Holes** → Hole node appears
5. Timeline now shows: `[Sketch1] — [Extrude1] — [Fillet1] — [Hole1]`

### 13.2 Editing a Previous Feature

1. **Double-click** "Extrude1" in the timeline
2. Model rolls back to show state after Extrude1
3. **Modify** the extrusion distance from 10mm to 15mm
4. **Click OK** → model recomputes Fillet1 and Hole1 with the new extrusion
5. Timeline: rollback marker returns to end

### 13.3 Inserting a Feature Mid-History

1. **Drag rollback marker** to position between Extrude1 and Fillet1
2. Model shows state after Extrude1 only
3. **Create new feature** (e.g., Chamfer) → inserted at current position
4. Timeline: `[Sketch1] — [Extrude1] — [Chamfer1] — [Fillet1] — [Hole1]`
5. Drag rollback marker to end → all features recompute in new order

### 13.4 Debugging a Failed Feature

1. Feature "Fillet2" shows **red error badge** ❌
2. **Roll back** past Fillet2 to see the model state just before it
3. Inspect the geometry — maybe an edge is too short for the fillet radius
4. **Double-click** the feature before Fillet2, adjust parameters
5. Or **suppress** Fillet2 and add a different operation instead

### 13.5 Design Review / Presentation

1. **Drag rollback marker to the beginning**
2. **Slowly drag right** — model builds up step by step
3. Stakeholders can see the design rationale: "First I created the basic shape, then added the mounting features, then the aesthetic fillets..."
4. This "playback" capability is a powerful communication tool

### 13.6 What-If Analysis with Suppress

1. Complex model with many features
2. **Suppress** a set of decorative features
3. Check if structural features still work correctly
4. **Unsuppress** to restore the full model
5. No features were deleted, no undo history consumed

---

## 14. Comparison: Fusion 360 vs. Current FreeCAD HistoryView

| Aspect | Fusion 360 | Current FreeCAD HistoryView |
|--------|-----------|---------------------------|
| **Orientation** | Horizontal bar at bottom | Vertical list in dock panel |
| **Feature Icons** | Type-specific icons (30+) | Generic colored dots |
| **Rollback** | Draggable marker, real-time | Double-click, discrete undo |
| **Suppress** | First-class feature | Not implemented |
| **Reorder** | Drag-and-drop | Not implemented |
| **Grouping** | Collapsible named groups | Not implemented |
| **Edit Feature** | Double-click node | Not implemented |
| **Tooltip** | Rich parameter summary | Basic type + timestamp |
| **Context Menu** | 12+ contextual items | Copy/Rollback/Select |
| **Color Coding** | By feature family (blue/green/orange/purple) | By entry type (4 colors) |
| **Multi-select** | Ctrl+click, Shift+click | Not implemented |
| **Search/Filter** | Via browser, not timeline | Built-in search + filter combo |
| **Horizontal Scroll** | Mouse wheel | N/A (vertical) |
| **Zoom** | Ctrl+scroll | N/A |
| **Capture Toggle** | On/Off toggle | Enable/Disable via parameter |
| **Error Indicators** | Badge overlays | Status text |

### 14.1 Strengths of Current FreeCAD HistoryView

- ✅ Built-in **search and filtering** (Fusion 360 lacks timeline-specific search)
- ✅ **Export to text** capability
- ✅ **Python API** for scripting
- ✅ **Property change tracking** (Fusion 360 only tracks feature-level operations)
- ✅ Shows **undo/redo operations** explicitly
- ✅ **Timestamp display** for every entry

### 14.2 Gaps to Address

1. **Horizontal timeline layout** — the most visually distinctive Fusion 360 element
2. **Feature-type-specific icons** — critical for quick visual scanning
3. **Draggable rollback marker** — the most important interaction pattern
4. **Suppress/unsuppress** — powerful non-destructive workflow
5. **Edit Feature (double-click)** — the most common user action
6. **Drag reorder** — advanced but valuable for experienced users
7. **Feature grouping** — organization for complex models
8. **Rich tooltips** — parameter summaries on hover

---

## 15. Implementation Recommendations for FreeCAD

### 15.1 Priority 1 — Must Have (Core Fusion 360 Parity)

1. **Horizontal Timeline Mode**: Add an alternative horizontal rendering mode that displays feature nodes on a connecting line at the bottom of the viewport. Keep the vertical list as a fallback option.

2. **Feature-Type Icons**: Map FreeCAD feature types (Pad, Pocket, Fillet, Chamfer, Sketch, Revolution, etc.) to distinct SVG/PNG icons with color families:
   - Blue: Additive (Pad, AdditivePipe, AdditiveLoft, Revolution)
   - Red/Orange: Subtractive (Pocket, SubtractivePipe, Groove)
   - Green: Modification (Fillet, Chamfer, Draft, Thickness)
   - Yellow: Sketch
   - Purple: Pattern (LinearPattern, PolarPattern, Mirrored, MultiTransform)
   - Gray: Datum (Plane, Line, Point)

3. **Draggable Rollback Marker**: Replace the double-click rollback with a draggable marker that:
   - Shows as a prominent triangular indicator
   - Can be dragged left/right (horizontal) or up/down (vertical)
   - Updates the model in real-time as dragged
   - Grays out features past the marker

4. **Edit Feature (Double-Click)**: Double-clicking a feature node should:
   - Find the corresponding `App::DocumentObject`
   - Open its task panel / edit dialog
   - For PartDesign features: `Gui::Command::doCommand(Gui::Command::Gui, "Gui.ActiveDocument.setEdit('%s', 0)", objName)`

### 15.2 Priority 2 — Should Have (Key Differentiation)

5. **Suppress/Unsuppress**: Implement via `App::DocumentObject::Suppressed` property (if available) or custom property:
   - Right-click context menu: "Suppress Feature" / "Unsuppress Feature"
   - Visual: Red X overlay + strikethrough text
   - Model recomputes without suppressed features

6. **Rich Tooltips**: On hover, show:
   - Feature type and name
   - Key parameters (e.g., "Length: 10 mm, Angle: 0°")
   - Timestamp
   - Status (OK / Warning / Error)

7. **Enhanced Context Menu**: Add:
   - "Edit Feature" (open task panel)
   - "Rename" (inline rename)
   - "Suppress" / "Unsuppress"
   - "Find in Model Tree" (select in tree view)
   - "Delete Feature"
   - Separator + existing items

### 15.3 Priority 3 — Nice to Have (Polish)

8. **Feature Grouping**: Allow users to select multiple timeline nodes and group them with a name. Show as collapsible bracket.

9. **Drag Reorder**: Allow reordering features via drag-and-drop (requires deep integration with PartDesign's feature ordering system).

10. **Animated Transitions**: Smooth animations for:
    - Auto-scroll when new features are added
    - Rollback marker movement
    - Feature node insertion/deletion

11. **Zoom Controls**: In horizontal mode, Ctrl+scroll to adjust node spacing.

12. **Capture Toggle**: Add a prominent toggle button to enable/disable history recording.

---

## Appendix A: Visual Reference — Horizontal Timeline Layout

```
┌─────────────────────────────────────────────────────────────────────┐
│                         3D Viewport                                  │
│                                                                      │
│                                                                      │
│                                                                      │
│                                                                      │
├──────────────────────────────────────────────────────────────────────┤
│ ◄│ [📐Sketch1]──[🔷Pad1]──[🔷Pad2]──[🟢Fillet1]──[🔴Pocket1] ▼ │▶│
│                                                          ▲            │
│                                                    Rollback Marker   │
└──────────────────────────────────────────────────────────────────────┘
```

## Appendix B: Feature Node Detail (Horizontal Mode)

```
    ┌───────┐
    │  🔷   │  ← Feature type icon (24x24)
    │ Pad1  │  ← Feature name (truncated)
    └───┬───┘
────────●──────── ← Timeline connecting line with dot
        │
        ▼  ← Rollback marker (if at this position)
```

## Appendix C: Suppressed Feature Visual

```
    ┌───────┐
    │  🔷   │
    │  ✕    │  ← Red X overlay
    │ Pad2  │  ← Strikethrough text
    └───┬───┘
── ── ──●── ── ── ← Dashed line segment for suppressed
```

## Appendix D: Grouped Features

```
Collapsed:
──[📁 "Mounting Holes" (3 features)]──

Expanded:
──┌─ "Mounting Holes" ─────────────────┐──
  │ [📐Sketch3]──[🔴Pocket2]──[🔴Pocket3] │
  └────────────────────────────────────┘
```

---

## References & Sources

- Autodesk Fusion 360 Product Documentation (help.autodesk.com)
- Autodesk Fusion 360 Design Workspace documentation
- Lars Christensen (YouTube): "Fusion 360 Timeline Tips and Tricks"
- Product Design Online (YouTube): "Fusion 360 for Beginners" series
- Kevin Kennedy (YouTube): "Fusion 360 Tutorial for Absolute Beginners"
- Warwick Holmes: "Understanding Parametric Design in Fusion 360"
- Autodesk University presentations on Fusion 360 best practices
- Community forums: Autodesk Fusion 360 Forum, Reddit r/Fusion360
- Author's training-data knowledge from extensive Fusion 360 documentation and tutorials

---

*Document created: 2025 | For FreeCAD HistoryView improvement project*
*This research is based on comprehensive analysis of Fusion 360's publicly documented UI/UX patterns.*
