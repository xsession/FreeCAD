# ADR-0001 – Thread-safe document model

**Status:** Accepted  
**Date:** 2026-01

## Context

FreeCAD's original document model assumed single-threaded access.  All
`signalRecomputed` and property-change signals fired on the main thread,
causing GUI blocks during large recomputes.  Attempting to call
`DocumentObject::touch()` from a background thread corrupted the
`DocumentObject::_Touches` bitset in unpredictable ways.

## Decision

Three components were introduced:

1. **`Base::AtomicBitset`** (`src/Base/AtomicBitset.h`) — A thread-safe
   bitset backed by `std::atomic<uint32_t>` that replaces the raw bitset used
   for dirty/touched flags.

2. **`App::ObjectLockManager`** (`src/App/ObjectLockManager.h`) — A
   per-object `std::shared_mutex` registry used to guard read/write access to
   individual `DocumentObject` instances from concurrent workers (e.g.
   the parallel recompute engine).

3. **`App::SignalQueue`** (`src/App/SignalQueue.h`) — A thread-safe queue of
   `std::function<void()>` lambdas that defers signal emission until the main
   thread calls `flush()`.  Workers enqueue signals; the main-thread event
   loop drains the queue after each recompute pass.

## Alternatives considered

* **Global mutex** – Simple but would create a bottleneck identical in effect
  to single-threaded execution; rejected.
* **Qt signal marshalling** – `QMetaObject::invokeMethod(..., Qt::QueuedConnection)`
  could route signals to the main thread, but requires all signal payloads to
  be `QMetaType`-registered and couples `App` to Qt; rejected.

## Consequences

**Positive:**
- Background workers can safely call `touch()` and enqueue signals.
- The parallel recompute engine (ADR-0004) relies on `ObjectLockManager` for
  safe concurrent mutation of independent feature outputs.

**Negative:**
- All callers that used raw bitfield access must be updated to go through
  `AtomicBitset`.
- `SignalQueue::flush()` must be called from the main-thread event pump; if
  forgotten signals may be lost.
