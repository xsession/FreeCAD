# ADR-0003 – Schema-versioned `.FCStd` file format

**Status:** Accepted  
**Date:** 2026-01

## Context

FreeCAD's `.FCStd` files contain a `SchemaVersion` attribute in `Document.xml`,
but there was no mechanism to migrate older files forward.  When a property was
renamed or serialisation format changed, loading old files silently produced
wrong data or hard crashes.

## Decision

Introduce two components:

1. **`constexpr int CurrentSchemaVersion = 4`** in
   `src/App/DocumentMigration.h` — a single source-of-truth for the active
   schema version written into every saved document.

2. **`App::DocumentMigration::migrate(Document&, int fileSchemaVersion)`** —
   a registry of step-wise migration functions.  Each step upgrades one schema
   version to the next.  Document loading calls this automatically when
   `fileSchemaVersion < CurrentSchemaVersion`.

## Alternatives considered

* **`if (schema < N)` scattered in individual property restores** – Already
  partially present in the code (e.g. `Points::restore`); inconsistent and hard
  to maintain; superceded.
* **Separate migration tool** – External tooling cannot access FreeCAD's full
  object model; rejected.

## Consequences

**Positive:**
- Old documents can be loaded by any future FreeCAD version.
- Each migration step is isolated and individually testable.
- `MinReadableSchemaVersion` guards against loading documents that are too old.

**Negative:**
- Schema bumps require a new migration step; developers must not forget to
  update `CurrentSchemaVersion` and write the migration.
- Migration is one-way: saving with a new schema makes the file unreadable by
  old FreeCAD versions.
