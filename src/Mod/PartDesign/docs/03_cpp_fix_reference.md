# 03 — C++ Fix Technical Reference: `FeatureDressUp.cpp`

> **Classification:** Engineering Reference · **Audience:** Core C++ Developers  
> **File:** `src/Mod/PartDesign/App/FeatureDressUp.cpp`  
> **Original Author:** Jürgen Riegel (2010) · **Fix Author:** 2026-03-14

---

## 1. Fix Summary

| Property | Value |
|----------|-------|
| **File** | `src/Mod/PartDesign/App/FeatureDressUp.cpp` |
| **Methods** | `getContinuousEdges()` (line ~214), `getFaces()` (line ~270) |
| **Pattern** | TNP fallback: stale mapped name → strip `?` → try short name |
| **Impact** | Fillet, Chamfer, Thickness survive upstream mutations |
| **Risk** | Low — fallback only on error path, no normal-path changes |

---

## 2. Root Cause Analysis

### 2.1 Failure Sequence (Before Fix)

```
┌────────────────────────────────────────────────────────────────────────┐
│                  FAILURE SEQUENCE DIAGRAM                               │
│                                                                        │
│  Timeline ──────────────────────────────────────────────────────▶       │
│                                                                        │
│  T0: User creates Pad + Fillet(Edge1)                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                             │
│  │  Sketch   │──│   Pad    │──│  Fillet  │                             │
│  │  (XY)     │  │  (10mm)  │  │ (Edge1)  │                             │
│  └──────────┘  └──────────┘  └──────────┘                             │
│                                                                        │
│  Shadow Subs at T0:                                                    │
│  ┌─────────────────────────────────────────────────────────────┐       │
│  │ newName: ";#f:1;:G;XTR;:H353:7,E.Edge1"   ← VALID         │       │
│  │ oldName: "Edge1"                            ← VALID         │       │
│  └─────────────────────────────────────────────────────────────┘       │
│                                                                        │
│  T1: User moves Sketch → Pad recomputes → new shape, new element map  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                             │
│  │  Sketch   │──│   Pad    │──│  Fillet  │                             │
│  │ (moved)   │  │ (recomp) │  │ (recomp) │                             │
│  └──────────┘  └──────────┘  └──────────┘                             │
│                                                                        │
│  Shadow Subs at T1 (PropertyLinks couldn't resolve):                   │
│  ┌─────────────────────────────────────────────────────────────┐       │
│  │ newName: ";#f:1;:G;XTR;:H353:7,E.Edge1"   ← STALE!        │       │
│  │ oldName: "?Edge1"                           ← HAS PREFIX   │       │
│  └─────────────────────────────────────────────────────────────┘       │
│              ▲                                                         │
│              │ "?" = MISSING_PREFIX from ElementNamingUtils.h          │
│                                                                        │
│  T2: getContinuousEdges() runs:                                        │
│  ┌─────────────────────────────────────────────────────────────┐       │
│  │ 1. ref = newName (";#f:1;:G;XTR;:H353:7,E.Edge1")         │       │
│  │ 2. shape.getSubShape(ref) → NULL (stale name!)             │       │
│  │ 3. throw CADKernelError("Invalid edge link: ...")  ← CRASH │       │
│  └─────────────────────────────────────────────────────────────┘       │
│                                                                        │
│  Result: ❌ Fillet marked as INVALID / error                           │
└────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Fix Sequence (After Patch)

```
┌────────────────────────────────────────────────────────────────────────┐
│                  FIXED SEQUENCE DIAGRAM                                 │
│                                                                        │
│  T2: getContinuousEdges() runs WITH FALLBACK:                          │
│  ┌─────────────────────────────────────────────────────────────┐       │
│  │ 1. ref = newName (";#f:1;:G;XTR;:H353:7,E.Edge1")         │       │
│  │ 2. shape.getSubShape(ref) → NULL (stale name!)             │       │
│  │                                                             │       │
│  │ ┌──────────── NEW FALLBACK PATH ──────────────────────┐    │       │
│  │ │ 3. Check: newName.size() > 0 && oldName.size() > 0  │    │       │
│  │ │ 4. fallback = oldName.c_str() → "?Edge1"            │    │       │
│  │ │ 5. *fallback == '?' → true → ++fallback → "Edge1"   │    │       │
│  │ │ 6. FC_WARN("...stale, falling back to 'Edge1'")     │    │       │
│  │ │ 7. shape.getSubShape("Edge1") → ✅ FOUND!           │    │       │
│  │ └─────────────────────────────────────────────────────┘    │       │
│  │                                                             │       │
│  │ 8. Process edge normally (C0 continuity check, etc.)       │       │
│  └─────────────────────────────────────────────────────────────┘       │
│                                                                        │
│  Result: ✅ Fillet recomputes successfully                             │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Code Changes

### 3.1 `getContinuousEdges()` — Edge-Based Fallback

**Location:** `FeatureDressUp.cpp`, approximately line 214–232

```cpp
// BEFORE (simplified):
for (const auto& v : Base.getShadowSubs()) {
    TopoDS_Shape subshape;
    const auto& ref = v.newName.size() ? v.newName : v.oldName;
    subshape = shape.getSubShape(ref.c_str(), true);
    if (subshape.IsNull()) {
        FC_THROWM(Base::CADKernelError, "Invalid edge link: " << ref);
    }
    // ... process edge
}

// AFTER (with fallback):
for (const auto& v : Base.getShadowSubs()) {
    TopoDS_Shape subshape;
    const auto& ref = v.newName.size() ? v.newName : v.oldName;
    subshape = shape.getSubShape(ref.c_str(), true);
    
    // ─── TNP FALLBACK ───────────────────────────────────────────
    if (subshape.IsNull() && v.newName.size() && v.oldName.size()) {
        const char* fallback = v.oldName.c_str();
        if (*fallback == '?') {       // Strip MISSING_PREFIX
            ++fallback;
        }
        FC_WARN(getFullName()
                 << ": mapped edge name '" << v.newName
                 << "' is stale, falling back to '" << fallback << "'");
        subshape = shape.getSubShape(fallback, true);
    }
    // ─── END FALLBACK ───────────────────────────────────────────
    
    if (subshape.IsNull()) {
        FC_THROWM(Base::CADKernelError, "Invalid edge link: " << ref);
    }
    // ... process edge
}
```

### 3.2 `getFaces()` — Face-Based Fallback

**Location:** `FeatureDressUp.cpp`, approximately line 260–280

```cpp
// BEFORE (simplified):
for (auto& val : vals) {
    auto& sub = subs[i++];
    auto& ref = sub.newName.size() ? sub.newName : val;
    TopoShape subshape;
    try {
        subshape = shape.getSubTopoShape(ref.c_str());
    } catch (...) {}

    if (subshape.isNull()) {
        // ... error handling
    }
}

// AFTER (with fallback):
for (auto& val : vals) {
    auto& sub = subs[i++];
    auto& ref = sub.newName.size() ? sub.newName : val;
    TopoShape subshape;
    try {
        subshape = shape.getSubTopoShape(ref.c_str());
    } catch (...) {}

    // ─── TNP FALLBACK ───────────────────────────────────────────
    if (subshape.isNull() && sub.newName.size() && sub.oldName.size()) {
        const char* fallback = sub.oldName.c_str();
        if (*fallback == '?') {       // Strip MISSING_PREFIX
            ++fallback;
        }
        FC_WARN(getFullName()
                 << ": mapped face name '" << sub.newName
                 << "' is stale, falling back to '" << fallback << "'");
        try {
            subshape = shape.getSubTopoShape(fallback);
        } catch (...) {}
    }
    // ─── END FALLBACK ───────────────────────────────────────────
}
```

---

## 4. Design Decisions

### 4.1 Why Fallback Instead of Fix-Forward?

```
┌─────────────────────────────────────────────────────────────────────┐
│                DESIGN DECISION MATRIX                                │
│                                                                     │
│  Option A: Fix PropertyLinks to always resolve                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ + Would fix all features at once                             │   │
│  │ - Extremely complex (PropertyLinks is core infrastructure)   │   │
│  │ - High regression risk across entire codebase                │   │
│  │ - Element map evolution may invalidate fix                   │   │
│  │ Verdict: TOO RISKY                                           │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  Option B: Fallback in DressUp (CHOSEN)                             │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ + Targeted, minimal change (12 lines per method)             │   │
│  │ + Only triggers on error path (zero normal-path impact)      │   │
│  │ + Logs warning for diagnostic visibility                     │   │
│  │ + Easy to verify with unit tests                             │   │
│  │ + Consistent with similar patterns elsewhere in FreeCAD      │   │
│  │ Verdict: SAFE AND EFFECTIVE                                  │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  Option C: Re-resolve TNP names during recompute                    │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ + Theoretically most correct                                 │   │
│  │ - Requires deep integration with element map update pipeline │   │
│  │ - Performance concern (double element map lookups)           │   │
│  │ Verdict: FUTURE ENHANCEMENT                                  │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.2 Why Strip `?` Instead of Using oldName Directly?

```
┌────────────────────────────────────────────────────────────────┐
│  The MISSING_PREFIX "?" Problem:                                │
│                                                                │
│  PropertyLinks marks unresolvable names with "?" prefix:       │
│                                                                │
│    oldName = "?Edge1"                                          │
│               ▲                                                │
│               └── This "?" is NOT part of the element name!    │
│                                                                │
│  shape.getSubShape("?Edge1") → NULL  (no element named that)  │
│  shape.getSubShape("Edge1")  → OK   (found the edge)          │
│                                                                │
│  First fix attempt (without stripping) FAILED because:         │
│    We assumed oldName was a clean short name like "Edge1"      │
│    But PropertyLinks had prepended "?" to signal staleness     │
│                                                                │
│  Second fix (with stripping) SUCCEEDED:                        │
│    if (*fallback == '?') ++fallback;                           │
│    → Defensive: only strips if prefix is present               │
│    → Single pointer increment (zero allocation)                │
│    → Works for both "?Edge1" → "Edge1" and "Edge1" → "Edge1"  │
└────────────────────────────────────────────────────────────────┘
```

### 4.3 Why `FC_WARN` Instead of Silent Fallback?

```
Diagnostic visibility is critical for enterprise debugging:

  FC_WARN(getFullName()
           << ": mapped edge name '" << v.newName
           << "' is stale, falling back to '" << fallback << "'");

This produces log output like:
  [WARN] Body.Fillet: mapped edge name 
  ';#f:1;:G;XTR;:H353:7,E.Edge1' is stale, 
  falling back to 'Edge1'

Benefits:
  ✓ Visible in FreeCAD Report View
  ✓ Captured in log files
  ✓ Helps developers identify models that need element map refresh
  ✓ Does not interrupt user workflow (warning, not error)
```

---

## 5. Iteration History

The fix went through two iterations before succeeding:

```
┌─────────────────────────────────────────────────────────────────────┐
│                    FIX ITERATION TIMELINE                             │
│                                                                     │
│  Iteration 1: Basic Fallback                                        │
│  ─────────────────────────────                                      │
│  ┌────────────────────────────────────────────────────────────┐     │
│  │ Code: subshape = shape.getSubShape(v.oldName.c_str())     │     │
│  │ Result: ❌ FAILED — oldName was "?Edge1", not "Edge1"     │     │
│  │ Build: ✅ Compiled                                         │     │
│  │ Tests: ❌ 2 failures (Fillet + Chamfer)                    │     │
│  └────────────────────────────────────────────────────────────┘     │
│                                                                     │
│  Investigation:                                                     │
│  ┌────────────────────────────────────────────────────────────┐     │
│  │ Added diagnostic FC_WARN to print oldName value            │     │
│  │ Discovered "?" MISSING_PREFIX from ElementNamingUtils.h    │     │
│  │ Line 57: constexpr const char* MISSING_PREFIX = "?";       │     │
│  └────────────────────────────────────────────────────────────┘     │
│                                                                     │
│  Iteration 2: Strip MISSING_PREFIX                                  │
│  ─────────────────────────────────                                  │
│  ┌────────────────────────────────────────────────────────────┐     │
│  │ Code: const char* fallback = v.oldName.c_str();            │     │
│  │       if (*fallback == '?') ++fallback;                    │     │
│  │       subshape = shape.getSubShape(fallback, true);        │     │
│  │ Result: ✅ PASSED — all 30 tests green                     │     │
│  │ Build: ✅ Compiled                                         │     │
│  │ Tests: ✅ 30/30 + 68/68 regression                        │     │
│  └────────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 6. Performance Analysis

```
┌─────────────────────────────────────────────────────────────────┐
│                 PERFORMANCE IMPACT ANALYSIS                      │
│                                                                 │
│  Normal Path (TNP name resolves):                               │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ getSubShape(tnpName) → found                            │    │
│  │ Cost: 0 additional operations                           │    │
│  │ Impact: ZERO                                            │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  Fallback Path (TNP name stale):                                │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ getSubShape(tnpName) → NULL                             │    │
│  │ + pointer comparison (*fallback == '?')     ~ 1 ns      │    │
│  │ + pointer increment (++fallback)            ~ 0 ns      │    │
│  │ + FC_WARN string construction               ~ 500 ns    │    │
│  │ + getSubShape(shortName) → found            ~ same      │    │
│  │ Total additional: ~1 µs per stale reference              │    │
│  │                                                          │    │
│  │ Typical model: 1-4 stale references after mutation       │    │
│  │ Total overhead: 1-4 µs (imperceptible)                   │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  Benchmark:                                                     │
│  ┌────────────────────────────────────┬────────────────────┐    │
│  │ Test Suite                         │ Time               │    │
│  ├────────────────────────────────────┼────────────────────┤    │
│  │ TestSketchOnFace (30 tests)        │ 1.779 s            │    │
│  │ TestTopologicalNaming (68 tests)   │ 3.647 s            │    │
│  │ Average per test                   │ ~55 ms             │    │
│  └────────────────────────────────────┴────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 7. Related Source Files

| File | Role |
|------|------|
| `src/Mod/PartDesign/App/FeatureDressUp.h` | DressUp class declaration |
| `src/Mod/PartDesign/App/FeatureDressUp.cpp` | **MODIFIED** — fallback logic |
| `src/App/ElementNamingUtils.h` | `MISSING_PREFIX`, `ELEMENT_MAP_PREFIX` constants |
| `src/App/PropertyLinks.cpp` | Shadow sub resolution, `?` prefix insertion |
| `src/Mod/Part/App/TopoShape.h` | `getSubShape()`, `getSubTopoShape()` methods |
| `src/App/ComplexGeoData.cpp` | Element map infrastructure |
| `src/App/ElementMap.cpp` | Element map storage and lookup |

---

*Next: [04 — Test Suite Documentation](./04_test_suite.md)*
