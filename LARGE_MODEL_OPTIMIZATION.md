# Large Model Optimization — STEP Import (500+ MB)

> **Scope:** Handling 500+ MB STEP files with 100K+ shapes  
> **Target:** Import without crashing, in reasonable time (15–45 min for 500 MB)

---

## Three-Tier Auto-Detection

The STEP reader automatically detects file size and applies optimizations:

| Tier | File Size | Key Optimizations |
|------|-----------|-------------------|
| **Normal** | < 100 MB | Full parallelism, standard healing, user precision |
| **Large** | 100–500 MB | + precision capping (0.5), progress reporting, pre-allocation |
| **Very Large** | 500+ MB | + relaxed healing (0.1), surface curve skip, memory management |

## Optimizations Applied

### Thread Pool Initialization
- `OSD_ThreadPool` initialized to `std::thread::hardware_concurrency()` threads
- `OSD_Parallel::SetUseOcctThreads(true)` enables OCC's internal parallelism

### Adaptive Precision
- Normal: `read.precision.val = 0.0001`, `read.maxprecision.mode = 0` (file)
- Large: `read.maxprecision.val = 0.5` (capped), prevents hours healing edges
- Very Large: `read.maxprecision.val = 0.1` (relaxed), `surfacecurve.mode = 0`

### Hash Map Pre-allocation
- `myShapes.reserve()` and `myNames.reserve()` called with estimated shape count
- Eliminates rehashing memory spikes with 100K+ shapes

### Early Cache Release
- `myShapes`, `myNames`, `myCollapsedObjects` cleared before final recompute
- Frees import-time memory before visualization needs it

### OCC Parameters
```
read.step.product.mode       = 1    (assembly structure)
read.step.product.context    = 1    (all contexts)
read.step.shape.repr         = 1    (all representations)
read.step.assembly.level     = 1    (all levels)
```

### Timing & Progress
- Parse time and transfer time reported separately
- Root entity count shown after parse for ETA estimation
- Per-phase logging: `[STEP Import] Parse complete in 12.3s — 4500 root entities`

## Expected Performance

| File Size | Before | After |
|-----------|--------|-------|
| 500 MB | Crashes or 2+ hours | 15–45 min |
| 100 MB | 30–60 min | 5–15 min |
| 50 MB | 10–20 min | 3–8 min |

## User Configuration

The `LargeFileAutoTune` preference (default: `true`) in `BaseApp/Preferences/Mod/Part/STEP`
controls whether automatic STEP read optimization is enabled. Individual parameters can be
overridden in the STEP preferences panel.

---

*See [CHANGELOG_PATCH.md](CHANGELOG_PATCH.md) for the complete patch description.*
