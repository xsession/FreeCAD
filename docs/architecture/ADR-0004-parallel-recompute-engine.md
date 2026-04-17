# ADR-0004 – Parallel recompute engine with feature flags

**Status:** Accepted  
**Date:** 2026-02

## Context

A 100-feature PartDesign Body recomputed serially in 15–45 seconds because
each feature triggered the next synchronously.  Independent sub-assemblies and
expression-linked spreadsheets also recomputed serially.

Enabling parallelism in the core DAG has a risk of regressions (subtle
race conditions, order-dependent side-effects in existing features), so it
cannot be the default immediately.

## Decision

1. **`App::RecomputeEngine`** (`src/App/RecomputeEngine.h/.cpp`) — a DAG
   scheduler that can execute topologically independent `DocumentObject`
   nodes in parallel using a thread pool (currently `std::thread` workers;
   TBB integration planned).

2. **`App::FeatureFlags`** (`src/App/FeatureFlags.h/.cpp`) — a per-session
   key/value store backed by `BaseApp/Preferences/Features`.  The key
   `"ParallelRecompute"` defaults to `false`, letting users opt in via
   Python or the preferences dialog.

## Alternatives considered

* **Always-on parallelism** – Introduced too many regressions in initial
  testing; rejected for now; may become default after a stabilisation period.
* **TBB `task_group` only** – TBB is an optional dependency; the engine is
  written to be back-ended by either native threads or TBB.

## Consequences

**Positive:**
- Users can opt in to the parallel engine at any time.
- Performance regression tests (D5) can measure both modes.

**Negative:**
- The opt-in mechanism adds code complexity.
- Not all features are safe with concurrent execution; unsafe ones must be
  decorated `RecomputeMode::Serial`.
