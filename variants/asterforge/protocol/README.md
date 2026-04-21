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

## Notes

- The `.proto` file is the long-term source of generated client/server bindings.
- The JSON schemas make it easier to review contracts before code generation is wired in.
- Large mesh payloads are intentionally out of scope for this first slice.
