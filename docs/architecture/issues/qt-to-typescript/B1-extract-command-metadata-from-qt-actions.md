# B1 Extract Command Metadata from Qt Actions

Status: proposed

## Outcome

Stop using `QAction` as the source of truth for command state.

## Why This Matters

Menus, toolbars, workbench switching, and much of shell behavior are currently mediated through Qt action objects. That prevents a non-Qt shell from owning command presentation.

## Primary Scope

- `src/Gui/Action*`
- `src/Gui/Command*`
- `src/Gui/MenuManager*`
- `src/Gui/ToolBarManager*`

## In Scope

- define backend-owned command descriptors
- expose enabled, checked, visible, label, icon, and shortcut state without `QAction`
- align extracted command state with the existing AsterForge command contracts

## Out of Scope

- complete menu parity rendering
- full workbench migration
- full plugin migration

## Deliverables

- command descriptor contract
- extraction adapter from current command system into protocol payloads
- mapping notes for commands that still rely on Qt widget-local behavior

## Repo Anchors

- `src/Gui/Action.cpp`
- `src/Gui/Command.cpp`
- `src/Gui/MenuManager.cpp`
- `src/Gui/ToolBarManager.cpp`
- `variants/asterforge/protocol/schemas/command.schema.json`
- `variants/asterforge/protocol/schemas/menu-bar.schema.json`
- `variants/asterforge/protocol/schemas/toolbar-band.schema.json`

## Dependencies

- shell protocol design

## Acceptance Checklist

- menus and toolbars can be rendered from backend-owned command descriptors
- command enablement and check state are available without reading live Qt action instances
- the extracted model is stable enough for later TS menu and toolbar rendering

## Risks And Notes

- command grouping and dynamic visibility are likely to expose hidden Qt assumptions
- avoid duplicating command logic into the new transport layer