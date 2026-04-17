# ADR-0005 – Ribbon bar replacing classic toolbars

**Status:** Accepted  
**Date:** 2026-03

## Context

FreeCAD's classic toolbar approach was copied from early CAD-software UI
paradigms.  With workbench switching, many toolbars appeared and disappeared,
confusing new users.  Key requests from user research:

- Discoverable command grouping (panels / tabs)
- Command search (keyboard-first)
- Contextual tabs that appear only when editing a Sketch or Assembly
- File / backstage overlay replacing the legacy File menu

## Decision

Introduce `Gui::RibbonBar` (`src/Gui/RibbonBar.h/.cpp`):

- A tab/panel hierarchy (`RibbonTabPage` > `RibbonPanel` > `RibbonButton`)
  styled with theme tokens from `ThemeTokens`.
- Contextual tabs for Sketch and Assembly workbenches, auto-shown/hidden as
  the active workbench changes.
- A minimise/preview mode toggled by double-clicking any tab.
- A `CommandSearch` palette (Ctrl+F) for keyboard-first command discovery.
- A `BackstageView` overlay triggered by the "File" tab, replacing the
  File menu with pages (New, Open, Save, Recent, Settings, Exit).
- Keytip overlays (`RibbonKeyTip`) for Alt-key keyboard navigation.

The classic toolbar mode is retained and toggled via
`Std_ToggleRibbonBar`; user preference persisted in
`BaseApp/Preferences/MainWindow/UseRibbonBar`.

## Consequences

**Positive:**
- Modern, discoverable UI consistent with Inventor/SolidWorks conventions.
- Keytip system makes ribbon navigable without a mouse.
- Contextual tabs reduce visual noise.

**Negative:**
- Extra complexity maintaining both ribbon and classic-toolbar code paths.
- Existing macros that call `Gui.getMainWindow().findChildren(QToolBar, ...)`
  may not find expected toolbars when ribbon is active.
