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

## Template

New ADRs should be created with the filename pattern
`ADR-NNNN-short-title.md` and include the sections:
Title, Status, Context, Decision, Consequences.
