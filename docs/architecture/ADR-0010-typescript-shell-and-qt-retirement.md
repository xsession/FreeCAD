# ADR-0010 TypeScript Shell and Qt Retirement Strategy

## Status

Accepted.

## Context

FreeCAD currently depends on Qt across:

- process startup
- the `FreeCADGui` shared library
- actions, menus, toolbars, and docking
- viewport hosting and view lifecycle
- multiple C++ workbench GUI modules
- Python and PySide-based workbench UIs

The repository also already contains a future-facing shell scaffold under `variants/asterforge` with:

- `frontend/app`
- `backend/crates`
- `native/freecad-bridge`
- `protocol`

The project needs a clear decision on whether Qt should be removed by refactoring the existing `src/Gui` stack in place or by building a new shell boundary and retiring Qt last.

## Decision

FreeCAD will pursue Qt retirement by building a new TypeScript desktop shell and removing Qt only after shell parity is proven.

The implementation strategy is:

1. keep native modeling, document, and OCCT-facing code in place initially
2. extract UI semantics from `src/Gui` into backend-owned protocols and services
3. use `variants/asterforge` as the canonical TypeScript, Rust, and native-bridge destination
4. run Qt and TypeScript shells in parallel during a dual-shell migration period
5. remove Qt from production runtime paths only after the TypeScript shell supports primary bundled workflows

## Consequences

### Positive

- avoids a destabilizing in-place rewrite of `src/Gui`
- preserves existing modeling and file workflows while UI replacement proceeds
- uses the existing `variants/asterforge` investment rather than creating a second migration architecture
- makes visual parity measurable through shell-to-shell comparison
- keeps backend semantics authoritative instead of letting frontend code become a second application core

### Negative

- requires a temporary dual-shell period
- increases short-term maintenance cost
- requires protocol and service extraction before visible UI replacement is complete
- forces explicit compatibility decisions for PySide-based plugins and bundled Python UIs

### Follow-On Decisions Required

- scene and viewport transport format
- plugin compatibility and deprecation policy
- preferences and layout persistence ownership
- whether app-layer Qt utility usage in `src/App` is fully removed or abstracted behind compatibility wrappers first

## Implementation Notes

- `src/Main/MainGui.cpp` and `src/Gui/CMakeLists.txt` are critical path files for the migration.
- `src/Gui/Action.*` is a critical command-semantics extraction point.
- `src/Gui/View3DInventor*` and `src/Gui/ViewProvider*` define a separate viewport replacement track.
- `src/Mod/AddonManager/**` and `src/Mod/BIM/**` are early PySide compatibility hotspots.