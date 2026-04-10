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

---

## Display / Rendering Optimization

> **Problem:** Large STEP models (37 MB+) cause severe UI stuttering, while CPU/GPU utilization
> remains low. 100+ MB models are essentially unusable for interactive viewing.

### Root Causes

1. **Excessive tessellation** — Default `Deviation=0.5%` creates millions of triangles for
   models with thousands of faces. A 37 MB STEP can produce 5–20M triangles.
2. **Single compound mesh** — When `merge=true` (default), all shapes merge into one
   `SoBrepFaceSet` node → no per-object culling, one massive VBO upload.
3. **No LOD** — Same tessellation quality whether zoomed out (whole model) or zoomed in
   (single feature).
4. **Edge rendering overhead** — "Flat Lines" display mode renders every edge line on top of
   faces, often doubling draw call count.
5. **Render cache disabled** — Sub-separators have `renderCaching=OFF` (intentional design),
   but the root `RenderCache` preference defaults to `AUTO` which may not cache large objects.

### Adaptive Tessellation (C++ — automatic)

`setupCoinGeometry()` now adjusts tessellation quality based on shape complexity:

| Preference | Type | Default | Description |
|---|---|---|---|
| `Mod/Part/AdaptiveDeviation` | Bool | `true` | Enable automatic deviation scaling |
| `Mod/Part/AdaptiveDeviationFaceThreshold` | Int | `2000` | Face count above which scaling applies |
| `Mod/Part/AdaptiveDeviationMaxScale` | Float | `10.0` | Maximum deviation multiplier |

**Scaling formula:** `deviation *= sqrt(numFaces / threshold)`, capped at `maxScale`.

| Model Faces | Scale Factor | Effective Deviation | ~Triangle Reduction |
|---|---|---|---|
| 2,000 | 1.0x | 0.5% (default) | None |
| 8,000 | 2.0x | 1.0% | ~4x fewer |
| 50,000 | 5.0x | 2.5% | ~25x fewer |

For shapes with > 5× threshold faces, angular deflection is also relaxed to ≥33°.

### Python Optimizer (`LargeModelOptimizer.py`)

Located at `src/Mod/Part/LargeModelOptimizer.py`. Use from FreeCAD Python console:

```python
from Part import LargeModelOptimizer

LargeModelOptimizer.diagnose()              # Model complexity report
LargeModelOptimizer.optimize()              # Auto-optimize per object
LargeModelOptimizer.set_profile("fast")     # Preset: fast/balanced/quality
LargeModelOptimizer.set_display_mode("Shaded")  # Skip edge rendering
LargeModelOptimizer.optimize_render_settings()   # Enable GL caching
```

**Profiles:**

| Profile | Deviation | AngDefl | Adaptive | RenderCache | Use Case |
|---|---|---|---|---|---|
| `fast` | 5.0% | 33° | ON (threshold=500) | Distributed | 100+ MB STEP |
| `balanced` | 1.5% | 28.5° | ON (threshold=2000) | Distributed | 20–100 MB STEP |
| `quality` | 0.5% | 28.5° | OFF | Auto | Small models |

### Manual Quick Fixes (no code change needed)

1. **Increase Deviation** — Select all objects → Properties → `Deviation = 2.0` to `5.0`
2. **Switch to Shaded** — `View → Display Mode → Shaded` (no edge lines = ~2x faster)
3. **Enable Render Cache** — `Edit → Preferences → Display → 3D View → Render Cache = Distributed`
4. **Import as separate objects** — In STEP import options: uncheck `Merge` or enable `Use LinkGroup`
   → enables per-object culling and independent visibility toggling
5. **Hide unnecessary objects** — Toggle visibility of individual bodies in the model tree
