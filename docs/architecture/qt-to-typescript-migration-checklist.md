# Qt-to-TypeScript Migration Checklist

Status: tracking checklist

## Current Inventory Artifacts

- `docs/QT_SURFACE_INVENTORY.md`
- `docs/QT_UI_FORM_INVENTORY.md`
- `docs/PYSIDE_USAGE_TABLE.md`
- `docs/GUI_OWNERSHIP_TABLE.md`
- `docs/SRC_GUI_FILE_LEVEL_OWNERSHIP_INVENTORY.md`
- `docs/FRONTEND_PARITY_BASELINE_SPEC.md`
- `docs/architecture/qt-to-typescript-milestone-issues.md`
- `docs/parity/README.md`
- `variants/asterforge/protocol/SHELL_PROTOCOL_EXPANSION_DRAFT.md`
- `docs/architecture/issues/qt-to-typescript/README.md`

## Current Planning Status

- the inventory set is now frozen as the planning baseline for this migration program
- bundled Python UI hotspots have been classified by migration risk
- milestone-style planning issues now exist for the major subsystem slices
- reviewed shell JSON drafts now have matching `.proto` contracts in `variants/asterforge/protocol/proto/asterforge.proto`
- a repo-local parity capture workflow now exists for collecting shell baselines from the Qt runtime

## 1. Discovery

- [x] freeze a repo-owned Qt surface inventory
- [x] freeze a `.ui` form inventory
- [x] freeze a PySide usage inventory
- [ ] capture current shell screenshots for baseline parity
- [ ] capture current workbench interaction recordings for baseline parity
- [ ] define parity metrics and acceptance thresholds

## 2. Architecture

- [x] approve ADR-0010 for shell replacement strategy
- [x] define command protocol
- [x] define workbench protocol
- [x] define layout and docking protocol
- [x] define document tree protocol
- [x] define property panel protocol
- [x] define task panel protocol
- [x] define scene and viewport protocol

## 3. Shell Bootstrapping

- [ ] stand up desktop shell in `variants/asterforge/frontend/app`
- [ ] stand up backend shell services in `variants/asterforge/backend/crates`
- [ ] define shell-neutral startup path separate from `src/Main/MainGui.cpp`
- [ ] support side-by-side Qt shell and TypeScript shell startup

## 4. Static Shell Parity

- [ ] recreate menu bar visually
- [ ] recreate toolbar bands visually
- [ ] recreate combo view shell visually
- [ ] recreate tree panel shell visually
- [ ] recreate property panel shell visually
- [ ] recreate report view shell visually
- [ ] recreate status bar visually
- [x] recreate workbench selector visually
- [ ] implement shared icon pipeline
- [ ] implement shared theme token pipeline

## 5. Behavioral Shell Parity

- [x] recreate menu bar visually
- [ ] replace property editor rendering
- [ ] replace task panel rendering
- [ ] replace report and diagnostics rendering
- [x] backend owns dock visibility, active tabs, and size hints
- [ ] implement camera controls with FreeCAD-compatible feel
- [ ] implement object selection and preselection parity
- [ ] implement hide/show and isolate parity
- [x] replace task panel rendering
- [ ] Start workbench shell parity
- [ ] Part workbench parity
- [ ] PartDesign workbench parity
- [ ] Sketcher workbench parity
- [ ] Import workbench parity
- [ ] Spreadsheet workbench parity
- [ ] TechDraw workbench parity
- [ ] FEM workbench parity
- [ ] specialist workbench migration plans created

## 9. PySide and Plugin Compatibility

- [x] classify bundled Python UIs by migration risk
- [ ] define legacy compatibility lane for PySide-heavy plugins
- [ ] publish new frontend contribution API
- [ ] publish new backend plugin API
- [ ] define PySide deprecation schedule
- [ ] remove PySide from bundled primary workflows

## Prepared Execution Assets

- parity artifact scaffold exists under `docs/parity`
- parity capture helper exists at `tools/profile/capture_qt_shell_parity.py`
- shell protocol expansion draft, reviewed JSON schemas, and promoted proto shell contracts exist under `variants/asterforge/protocol`
- tracker-ready issue files exist under `docs/architecture/issues/qt-to-typescript`

## Remaining Immediate Gaps

- no real screenshot baselines have been captured yet
- no interaction recordings have been committed yet
- launcher-driven GUI script execution was not reliable in this session, so first parity captures still need a local run path

## 10. Preferences and Persistence

- [ ] move preferences schema out of Qt pages
- [ ] move layout persistence out of Qt state save and restore
- [ ] move shortcut customization out of Qt-owned runtime state
- [ ] move theme management to TS design tokens plus backend preferences

## 11. Dual-Shell Validation

- [ ] ship internal dual-shell builds
- [ ] compare startup and open-document flows
- [ ] compare crash rates
- [ ] compare screenshot parity
- [ ] compare primary workflow completion rates
- [ ] enumerate remaining Qt-only blockers

## 12. Qt Retirement

- [ ] stop defaulting to Qt shell launch
- [ ] remove Qt-only production startup path
- [ ] remove Qt-only shell modules from shipping runtime
- [ ] remove bundled PySide production dependencies
- [ ] remove Qt resource and form pipelines no longer used
- [ ] remove Qt from shipping product requirements

## 13. Done Criteria

- [ ] packaged product launches without Qt UI runtime libraries
- [ ] primary bundled workflows are supported in the TypeScript shell
- [ ] parity review passed for shell chrome, editing surfaces, and viewport
- [ ] plugin migration path is documented
- [ ] legacy Qt shell is retired from the main product line