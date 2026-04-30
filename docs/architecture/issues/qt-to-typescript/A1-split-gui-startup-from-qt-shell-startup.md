# A1 Split GUI Startup from Qt Shell Startup

Status: proposed

## Outcome

Make startup shell-neutral so the TypeScript shell can boot without `MainGui.cpp` owning the application lifecycle.

## Why This Matters

Qt currently owns the shipping GUI startup path. Until startup is split into shell-neutral and shell-specific stages, every later shell effort remains an add-on instead of a first-class runtime.

## Primary Scope

- `src/Main/MainGui.cpp`
- `src/Main/FreeCADGuiPy.cpp`
- `src/Gui/Application*`
- `src/Gui/MainWindow*`

## In Scope

- identify shell-neutral startup responsibilities
- separate process boot, backend boot, and shell boot responsibilities
- define a startup contract that a Qt shell and TS shell can both consume
- reduce direct assumptions that the shipping shell is always `QApplication` plus `MainWindow`

## Out of Scope

- replacing the shell UI itself
- porting menus, docks, or viewport logic
- plugin compatibility work beyond startup-critical coupling

## Deliverables

- startup responsibility map
- shell-neutral startup contract
- first backend boot path callable without Qt shell ownership
- migration note documenting remaining Qt-only startup blockers

## Repo Anchors

- `src/Main/MainGui.cpp`
- `src/Main/FreeCADGuiPy.cpp`
- `src/Gui/Application.cpp`
- `src/Gui/GuiApplication.cpp`
- `src/Gui/MainWindow.cpp`
- `docs/QT_TO_TYPESCRIPT_REPO_EXECUTION_PLAN.md`

## Dependencies

- ADR-0010 accepted

## Acceptance Checklist

- a second shell can start against backend services without inheriting the current Qt main window path
- startup responsibilities are documented as shell-neutral versus shell-specific
- no new migration workstream depends on `MainWindow` being the boot root

## Risks And Notes

- this issue is on the critical path for the entire migration program
- partial decoupling that still hides `QApplication` assumptions behind wrappers is not enough