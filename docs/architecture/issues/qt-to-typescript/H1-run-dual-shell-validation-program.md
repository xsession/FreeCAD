# H1 Run Dual-Shell Validation Program

Status: proposed

## Outcome

Validate the TypeScript shell against the Qt shell in real workflows before cutover.

## Why This Matters

The project needs a controlled transition period where parity, stability, and missing surface area are measured directly instead of inferred from implementation confidence.

## Primary Scope

- packaging
- launchers
- parity dashboards
- workflow validation

## In Scope

- internal dual-shell builds
- parity dashboard inputs from screenshots and workflow reviews
- blocker enumeration before default-shell cutover

## Out of Scope

- immediate removal of the Qt shell
- permanent support for two shells indefinitely

## Deliverables

- dual-shell validation plan
- blocker list with severity and cutover impact
- parity and workflow review dashboard inputs

## Repo Anchors

- `docs/parity/**`
- `docs/architecture/qt-to-typescript-migration-checklist.md`
- packaging and launcher paths in the repo execution plan

## Dependencies

- F1
- F2
- G1
- G2

## Acceptance Checklist

- the remaining Qt-only blockers are enumerated and acceptable for cutover
- both shells can be launched and compared for selected workflows
- cutover decisions are made from recorded evidence rather than anecdotal confidence

## Risks And Notes

- dual-shell operation should be time-boxed; otherwise it becomes an expensive permanent state