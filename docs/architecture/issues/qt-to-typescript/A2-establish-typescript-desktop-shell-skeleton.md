# A2 Establish TypeScript Desktop Shell Skeleton

Status: proposed

## Outcome

Stand up the production shell root in `variants/asterforge/frontend/app`.

## Why This Matters

The migration needs a real shell target early so protocol work, parity work, and shell extraction can converge on an executable product surface instead of staying abstract.

## Primary Scope

- `variants/asterforge/frontend/app`
- `variants/asterforge/backend/crates`

## In Scope

- desktop shell entry point
- shell chrome scaffolding
- backend connectivity for initial hydration
- theme and layout foundations needed for later parity work

## Out of Scope

- full command execution
- full document editing
- viewport parity
- workbench-complete UX

## Deliverables

- bootable TS shell
- backend service handshake for shell hydration
- shell layout root with menu, toolbar, panel, viewport, and status regions
- migration note covering current gaps between shell skeleton and parity target

## Repo Anchors

- `variants/asterforge/frontend/app`
- `variants/asterforge/backend/crates`
- `variants/asterforge/protocol`
- `docs/parity/README.md`

## Dependencies

- A1

## Acceptance Checklist

- the TypeScript shell launches with shell chrome scaffolding and backend connectivity
- the shell can consume snapshot-like shell state from the backend
- the scaffold is suitable for parity screenshot work in later issues

## Risks And Notes

- avoid implementing domain semantics directly in frontend state stores
- the skeleton should remain thin and protocol-driven, not become a second application core