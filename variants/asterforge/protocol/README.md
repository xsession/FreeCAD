# AsterForge Protocol

This package defines the first transport and payload contracts for the AsterForge architecture.

## Goals

- keep the frontend independent from FreeCAD Qt internals
- make backend state the canonical source of truth
- define payloads that can survive a later move from local desktop to remote transport

## Current Assets

- `proto/asterforge.proto`: service contracts and core messages
- `schemas/document.schema.json`: document payload shape
- `schemas/selection.schema.json`: selection payload shape
- `schemas/property.schema.json`: property metadata payload shape
- `schemas/command.schema.json`: command invocation payload shape
- `schemas/object-tree.schema.json`: initial object tree payload
- `schemas/property-groups.schema.json`: initial grouped property payload
- `schemas/workbench-catalog.schema.json`: workbench list and active workbench state
- `schemas/menu-bar.schema.json`: menu composition state
- `schemas/toolbar-band.schema.json`: toolbar composition state
- `schemas/shell-layout.schema.json`: panel layout and visibility state
- `schemas/shell-snapshot.schema.json`: combined shell hydration payload
- `SHELL_PROTOCOL_EXPANSION_DRAFT.md`: next shell-facing contract plan

## Shell Contracts Promoted to Proto

The reviewed shell JSON drafts now have matching `.proto` coverage for:

- workbench catalog state
- menu bar composition state
- toolbar band composition state
- shell layout state
- shell snapshot hydration payload

The long-term source of truth remains `proto/asterforge.proto`; JSON schemas remain in place as review-friendly companion artifacts.

## Notes

- The `.proto` file is the long-term source of generated client/server bindings.
- The JSON schemas make it easier to review contracts before code generation is wired in.
- Large mesh payloads are intentionally out of scope for this first slice.
- `DocumentService.FetchShellSnapshot(...)` is the preferred shell hydration boundary for the TypeScript app.

## Generation

- Rust generated bindings compile through `backend/crates/protocol-types` using `prost-build` plus vendored `protoc`.
- TypeScript generated bindings are emitted to `frontend/app/src/generated` via `npm run generate:protocol` in `frontend/app`.
- The frontend `src/protocol.ts` file should remain a thin fetch facade over generated transport types, not a second handwritten schema source.
