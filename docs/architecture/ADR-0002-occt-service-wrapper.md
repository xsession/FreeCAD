# ADR-0002 – OcctService wrapper namespace

**Status:** Accepted  
**Date:** 2026-01

## Context

OCCT (Open Cascade Technology) calls frequently throw C++ exceptions that,
when unhandled, crash FreeCAD with no useful diagnostic.  The existing code
called OCCT APIs directly from `DocumentObject::execute()` bodies, making it
easy to miss exception handlers and difficult to add consistent error reporting.

## Decision

Introduce the `OcctService` namespace (`src/Mod/Part/App/OcctService.h`) that
wraps selected OCCT calls with:

- A catch-all wrapper (`OcctService::invoke`) that catches `Standard_Failure`,
  `std::exception`, and `...`, logs a structured error message, and returns a
  sentinel value so callers can handle the failure gracefully.
- Centralised OCCT initialisation and thread-safety flags (one-time BRep
  builder init, etc.).

## Alternatives considered

* **Per-call try/catch blocks** – Repetitive, error-prone, inconsistently
  applied; rejected.
* **OCCT error callbacks** – OCCT's `Standard_Failure::Raise()` mechanism does
  not easily integrate with FreeCAD's logging system; rejected.

## Consequences

**Positive:**
- Crashes from unhandled OCCT exceptions are eliminated in wrapped code paths.
- Error messages include operation name and `Standard_Failure::GetMessageString`.

**Negative:**
- Not all OCCT call sites are wrapped yet; coverage is incremental.
- The sentinel-return pattern requires callers to check return values rather
  than rely purely on exceptions.
