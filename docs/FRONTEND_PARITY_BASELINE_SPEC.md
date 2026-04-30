# FreeCAD Frontend Parity Baseline Spec

Status: planning spec for visual and interaction parity capture

## 1. Purpose

This document defines what should be captured before shell replacement work begins so that “same visuality” is measurable instead of subjective.

It complements the migration plan by describing the baseline assets, test scenes, and acceptance measures needed for parity reviews.

## 2. Baseline Asset Types

The parity baseline should include four asset classes:

### A. Screenshot Baselines

Capture full-window and panel-level screenshots for stable reference states.

### B. Layout Metrics

Capture measurable dimensions such as:

- main toolbar heights
- panel widths
- status bar heights
- tree indentation and row heights
- property editor row spacing
- task panel header and footer spacing

### C. Interaction Recordings

Capture short recordings for primary flows to preserve timing and motion expectations.

### D. Command and Surface Inventory Snapshots

Capture the shell composition visible in each baseline state:

- active workbench
- visible toolbars
- visible dock panels
- active task panel
- active theme

## 3. Required Baseline States

### Shell States

1. startup window
2. empty document shell
3. document shell with default panel layout
4. light theme shell
5. dark theme shell

### Workbench States

1. Start
2. Part
3. PartDesign
4. Sketcher
5. Import flow after opening a document
6. TechDraw primary shell state

### Editing Surface States

1. tree with expanded object hierarchy
2. property view with grouped editable properties
3. report view populated
4. task panel active in a modeling workflow

### Viewport States

1. empty 3D viewport
2. simple part model
3. multi-body PartDesign model
4. large assembly import state
5. selected object and preselection overlay state

## 4. Required Capture Set Per State

For each baseline state, capture:

1. full-window screenshot
2. cropped viewport screenshot if relevant
3. cropped tree and property screenshot if relevant
4. metadata file describing workbench, theme, visible panels, and document fixture

Recommended metadata fields:

- `baseline_id`
- `theme`
- `workbench`
- `fixture_document`
- `visible_toolbars`
- `visible_panels`
- `active_task`
- `notes`

## 5. Suggested Fixture Documents

Use a small set of stable reference fixtures:

- empty document
- simple cube or primitive document
- Part boolean and fillet example
- PartDesign body with sketch and pad
- Sketcher constraint-rich sketch
- large STEP assembly
- TechDraw example document

The large assembly parity set should include at least one real-world STEP file large enough to expose shell and viewport stress cases.

## 6. Interaction Baselines

Record the following interactions as short clips or step logs:

1. switch workbench
2. open preferences and navigate between pages
3. create a sketch and edit a few properties
4. complete a standard task-panel flow
5. open and inspect a large STEP assembly
6. fit all, orbit, pan, and select in the viewport
7. dock or resize the main side panels

## 7. Acceptance Metrics

### Visual Metrics

- screenshot diff threshold for shell screens
- screenshot diff threshold for viewport and overlay screens
- acceptable icon, spacing, and font drift thresholds

### Structural Metrics

- command coverage for visible menus and toolbars
- panel presence and ordering parity
- workbench switch path parity

### Interaction Metrics

- shortcut behavior parity
- task flow completion parity
- viewport navigation parity

## 8. Recommended Repository Layout

Suggested artifact layout:

```text
docs/parity/
  baselines/
    screenshots/
    recordings/
    metadata/
  fixtures/
  acceptance/
```

Suggested file naming:

- `shell-empty-light.png`
- `part-workbench-default-light.png`
- `partdesign-task-pad-dark.png`
- `step-large-assembly-shaded.png`

## 9. Review Gates

Use three review gates:

### Gate 1. Static Shell Review

- menus, toolbars, combo view shell, report view, and status bar are visually within tolerance

### Gate 2. Editing Surface Review

- tree, property editor, and task panel layouts are visually and behaviorally acceptable

### Gate 3. Viewport Review

- navigation, selection, overlays, and large-model behavior are acceptable on real documents

## 10. Recommendation

Build the parity baseline before significant shell reimplementation work. Without that baseline, “same visuality” will drift into opinion and the migration will lose a reliable acceptance target.

## Related Execution Artifacts

- `docs/parity/README.md`
- `docs/parity/baselines/baseline-manifest.md`
- `docs/parity/baselines/metadata/metadata-schema.json`
- `docs/parity/baselines/metadata/baseline-metadata-template.json`
- `docs/parity/fixtures/fixture-manifest.md`
- `docs/parity/acceptance/thresholds.md`