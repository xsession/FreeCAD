# H2 Remove Qt from Production Runtime Paths

Status: proposed

## Outcome

Stop shipping the product with Qt as the UI runtime dependency.

## Why This Matters

This is the actual retirement step. All earlier work exists to make this safe, measurable, and non-destructive.

## Primary Scope

- startup path
- shell modules
- bundled PySide UI dependencies
- packaging requirements

## In Scope

- stop defaulting to Qt shell launch
- remove Qt-only runtime UI paths from the shipping product
- align packaging with the new production shell

## Out of Scope

- retaining the Qt shell as a co-equal long-term runtime
- unrelated app-layer cleanup that does not affect production runtime dependency

## Deliverables

- shipping configuration without Qt UI runtime dependency
- cleanup plan or PR series for retired shell code paths
- final blocker review before product-line cutover

## Repo Anchors

- startup and launcher paths from `docs/QT_TO_TYPESCRIPT_REPO_EXECUTION_PLAN.md`
- `src/Main/MainGui.cpp`
- `src/Gui/CMakeLists.txt`
- bundled PySide-heavy areas identified in `docs/PYSIDE_USAGE_TABLE.md`

## Dependencies

- H1

## Acceptance Checklist

- the packaged product launches and operates without Qt UI runtime libraries
- Qt shell is no longer required for supported bundled workflows
- packaging, runtime startup, and supported workflows all validate against the TS shell path

## Risks And Notes

- do not begin this issue before the dual-shell validation evidence is complete