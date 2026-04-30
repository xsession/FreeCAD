# D3 Replace Task Panel Runtime

Status: proposed

## Outcome

Replace task panels and shell-level task dialogs with a TS task runtime backed by protocol schemas.

## Why This Matters

Task panels are a defining interaction pattern across modeling workflows. If task runtime remains Qt-only, primary workflow parity will stall even if the shell looks correct.

## Primary Scope

- `src/Gui/TaskView/**`
- shell-level task `.ui` assets

## In Scope

- shell-level task runtime lifecycle
- task header, body, footer, and action button conventions
- schema-driven task sections and rows for first-pass coverage

## Out of Scope

- every workbench-specific task panel in one issue
- final plugin-facing task contribution API

## Deliverables

- TS task runtime container
- task schema integration pattern
- migration notes for shell-level task assets that do not map cleanly to the first schema slice

## Repo Anchors

- `src/Gui/TaskView/TaskView.cpp`
- `src/Gui/TaskView/TaskDialog.cpp`
- `src/Gui/TaskTransform.cpp`
- `src/Gui/TaskElementColors.cpp`
- `variants/asterforge/protocol/asterforge.proto`

## Dependencies

- D2

## Acceptance Checklist

- primary task workflows can run without Qt task widgets
- task layout and action affordances remain familiar to current users
- shell-level task state can be described without Qt-specific widgets or `.ui` loading

## Risks And Notes

- do not reduce task schemas to static text rows if the workflow needs meaningful editing controls