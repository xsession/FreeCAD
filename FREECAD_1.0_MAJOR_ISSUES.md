# FreeCAD 1.0 — Major Community-Reported Issues

> **Date:** March 2026  
> **Source:** Reddit, GitHub Issues, FreeCAD Forum  
> **Scope:** Top 7 critical issues reported after the FreeCAD 1.0 release

---

## Issue 1: Fillet/Chamfer Crashes (SIGSEGV)

**Frequency:** Very High — reported across all platforms  
**Symptoms:** Selecting edges for fillet or chamfer with parameters that exceed edge length causes uncaught OCC kernel exceptions or segmentation faults.  
**Root Cause:** No pre-validation of radius/size against geometry dimensions; only `Standard_Failure` was caught.  
**Impact:** Complete application crash with no recovery possible.

## Issue 2: Assembly Solver Instability

**Frequency:** High  
**Symptoms:** Parts "fly away" to extreme coordinates after solving; solver produces NaN or Infinity values.  
**Root Cause:** No validation of solver output; catch-all blocks silently discard errors.  
**Impact:** Corrupted part positions; user must manually undo or restart.

## Issue 3: Recompute Cascade / Performance

**Frequency:** High  
**Symptoms:** Editing one feature triggers recomputation of entire document; large models become unusable.  
**Root Cause:** `enforceRecompute()` called on all dependents regardless of success/failure; no abort capability by default.  
**Impact:** Minutes-long waits for simple edits on complex models.

## Issue 4: Toponaming Problem (TNP) Incomplete

**Frequency:** Medium-High  
**Symptoms:** Some operations bypass the TNP-aware element naming pipeline, causing reference breakage on model edit.  
**Root Cause:** Legacy code paths using raw OCC APIs instead of `makeElement*` functions.  
**Impact:** Downstream features break when upstream geometry changes.

## Issue 5: STEP Import Performance

**Frequency:** High  
**Symptoms:** STEP import uses only ~10% CPU; large files (100+ MB) take 30-60 minutes.  
**Root Cause:** No parallel processing configured; OCC thread pool not initialized; sequential face/edge mapping.  
**Impact:** Professional users cannot import industry-standard files in reasonable time.

## Issue 6: AutoSave Thread Safety

**Frequency:** Low-Medium  
**Symptoms:** Occasional crash during auto-save, especially with complex documents.  
**Root Cause:** Generic catch-all swallows all exceptions silently; no per-type exception handling.  
**Impact:** Silent auto-save failures; potential data loss.

## Issue 7: Large Model Support (500+ MB STEP)

**Frequency:** Medium  
**Symptoms:** Files over 500 MB crash or take 2+ hours to import; memory spikes cause OOM kills.  
**Root Cause:** No file-size-aware optimization; fixed precision settings; no pre-allocation; no progress reporting.  
**Impact:** Professional/industrial workflows blocked.

---

*This research informed the 6 work sessions documented in [CHANGELOG_PATCH.md](CHANGELOG_PATCH.md).*
