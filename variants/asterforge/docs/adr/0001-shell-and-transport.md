# ADR 0001: Desktop Shell and Initial Transport

## Status

Accepted for scaffold phase.

## Decision

- desktop shell target: Tauri
- canonical application platform: Rust backend
- initial transport shape: gRPC-style service contracts, with local in-process mocking allowed during early scaffolding

## Why

- Tauri aligns with the Rust-first backend plan.
- The frontend stays cleanly separated from the native CAD stack.
- The service contracts remain usable if the backend becomes out-of-process or remote later.

## Consequences

- The first frontend implementation can start in a plain Vite React shell.
- The backend must own domain semantics early instead of letting the frontend drift into command scripting.
- Native bridge workers should be isolated behind explicit interfaces rather than exposed directly to the UI.
