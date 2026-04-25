# Architecture Decision Records (ADRs)

This directory contains Architecture Decision Records for the FreeCAD
modernization effort.  Each file documents a significant architectural choice,
the forces that drove it, the alternatives considered, and the outcome.

## Index

| ADR | Title | Status |
|-----|-------|--------|
| [ADR-0001](ADR-0001-thread-safe-document-model.md) | Thread-safe document model | Accepted |
| [ADR-0002](ADR-0002-occt-service-wrapper.md) | OcctService wrapper namespace | Accepted |
| [ADR-0003](ADR-0003-schema-versioned-file-format.md) | Schema-versioned `.FCStd` file format | Accepted |
| [ADR-0004](ADR-0004-parallel-recompute-engine.md) | Parallel recompute engine with feature flags | Accepted |
| [ADR-0005](ADR-0005-ribbon-bar-architecture.md) | Ribbon bar replacing classic toolbars | Accepted |
| [ADR-0006](ADR-0006-plugin-api-v2.md) | Plugin API v2 lifecycle manager | Accepted |
| [ADR-0007](ADR-0007-pdm-provider-abc.md) | PDM provider Python ABC layer | Accepted |
| [ADR-0009](ADR-0009-frontend-mvp-architecture.md) | Frontend MVP architecture for FreeCAD | Proposed |

## Architecture Notes

| Document | Purpose |
|----------|---------|
| [frontend-shell-ux-plan.md](frontend-shell-ux-plan.md) | Shell UX direction for ribbon, workbench chooser, and task panels |
| [freecad-mvp-migration-plan.md](freecad-mvp-migration-plan.md) | Incremental migration plan for applying MVP across FreeCAD frontend surfaces |
| [freecad-visual-environment-deepsearch.md](freecad-visual-environment-deepsearch.md) | Human-centered visual-environment research synthesis for mechanical engineers |
| [freecad-visual-environment-implementation-plan.md](freecad-visual-environment-implementation-plan.md) | Phased rollout plan for applying the visual-environment model to the current frontend |
| [freecad-visual-environment-backlog.md](freecad-visual-environment-backlog.md) | Concrete backlog and milestone structure for implementation |
| [freecad-visual-environment-p0-roadmap.md](freecad-visual-environment-p0-roadmap.md) | Sprint-ready roadmap for the first implementation slice |

## Template

New ADRs should be created with the filename pattern
`ADR-NNNN-short-title.md` and include the sections:
Title, Status, Context, Decision, Consequences.
