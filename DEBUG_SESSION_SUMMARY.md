# FreeCAD Sub-Shape Lookup Regression — Debug Session Summary

## Problem Statement

After applying a stability patch (crash prevention in `ElementMap::setElementName`), users could no longer create a new sketch on a Pad face. Investigation revealed that **all sub-shape lookups were universally broken**:

```python
s = Part.makeBox(10, 10, 10)
len(s.Faces)            # → 6  ✅ (works — uses cache/ancestry path)
s.countElement('Face')  # → 0  ❌ (broken — uses shapeType() → countSubShapes())

Part.getShape(feat, "Face1", needSubElement=True)  # → null  ❌
feat.getSubObject("Face1")                          # → null  ❌
```

The bug affected **every shape** — `Part.makeBox`, manual extrusions, Pad features — not just element-mapped shapes.

## Investigation Timeline

### Phase 1: Python Diagnostics
- Created diagnostic scripts (`_d.py` through `_d6.py`) run via `FreeCADCmd.exe`
- Confirmed the bug is universal: `countElement('Face')` returns 0 for ALL shapes
- Confirmed `s.Faces` (6 faces) works but `s.countElement('Face')` (0) doesn't
- Key insight: both paths ultimately call `TopExp::MapShapes()` on the same OCC shape, so the shape data itself is fine

### Phase 2: Static Code Analysis
Traced the full code path:
- `countElement("Face")` → `countSubShapes("Face")` → `shapeType("Face", true)` → should return `TopAbs_FACE` (4)
- `shapeType()` iterates `_ShapeNames[]` array using `boost::starts_with()`
- `_ShapeNames` is `static std::array<std::string, 8>` lazily initialized by `initShapeNameMap()`
- **Everything looked correct on paper** — the logic was sound

### Phase 3: C++ Debug Logging
Added `Base::Console().Warning()` calls to:
- `countSubShapes(const char*)` — logged the enum result from `shapeType()`
- `countSubShapes(TopAbs_ShapeEnum)` — logged the `TopExp::MapShapes` extent
- `getSubTopoShape(const char*)` — logged `shapeTypeAndIndex()` results  
- `shapeType(const char*, bool)` — logged the `_ShapeNames` array contents

### Phase 4: Build System Battles
Multiple build attempts failed due to:
1. **`lrelease.exe` missing Qt DLLs** — Fixed by adding `Library\bin` to PATH
2. **Stale Ctrl+C interrupt signals** — Previous terminal interrupts caused persistent "Terminate batch job (Y/N)?" prompts in every `cmd.exe` child process
3. **Solution**: Used `Start-Process -WindowStyle Hidden` to spawn a completely new process tree

### Phase 5: Root Cause Discovery 🎯

The debug output revealed:

```
DBG shapeType: input='Face' arraySize=8 names=[ÿK1ÿY,ÿK1ÿY,pK1ÿY,PK1ÿY,ÿJ1ÿY,K1ÿY,ÿH1ÿY,0J1ÿY]
```

**The `_ShapeNames` array contained garbage memory!** Instead of `["Compound","CompSolid","Solid","Shell","Face","Wire","Edge","Vertex"]`, every entry was corrupted pointer data.

This meant:
- `boost::starts_with("Face", <garbage>)` → always `false`
- `shapeType("Face", true)` → always returned `TopAbs_SHAPE` (8) = "not found"
- `countSubShapes` → always returned 0
- `getSubTopoShape("Face1")` → always returned null

## Root Cause

**Static `std::string` memory corruption in a Windows DLL (`Part.pyd`)**

```cpp
// BEFORE (broken):
static std::array<std::string, TopAbs_SHAPE> _ShapeNames;  // file-scope mutable static

static void initShapeNameMap() {
    if (_ShapeNames[TopAbs_VERTEX].empty()) {  // guard check
        _ShapeNames[TopAbs_VERTEX] = "Vertex";
        // ... etc
    }
}
```

The `std::string` objects inside the `std::array` were corrupted during DLL loading. The corrupted `size` field was non-zero, so `empty()` returned `false`, and the lazy initialization guard never triggered — the array was never written with valid data.

This is a variant of the **static initialization order fiasco** specific to MSVC DLLs, where mutable static objects with non-trivial constructors can be corrupted if DLL load order or memory layout causes overwrites before the C++ runtime fully initializes them.

## The Fix

**File: `src/Mod/Part/App/TopoShape.cpp`**

Replaced the mutable `std::string` statics with compile-time constant data:

```cpp
// AFTER (fixed):
// Compile-time initialized — immune to DLL static init corruption
static const char* const _ShapeNamesCStr[] = {
    "Compound",   // TopAbs_COMPOUND  = 0
    "CompSolid",  // TopAbs_COMPSOLID = 1
    "Solid",      // TopAbs_SOLID     = 2
    "Shell",      // TopAbs_SHELL     = 3
    "Face",       // TopAbs_FACE      = 4
    "Wire",       // TopAbs_WIRE      = 5
    "Edge",       // TopAbs_EDGE      = 6
    "Vertex",     // TopAbs_VERTEX    = 7
};
static constexpr size_t _ShapeNamesCount = sizeof(_ShapeNamesCStr) / sizeof(_ShapeNamesCStr[0]);
```

For `shapeName()` (which returns `const std::string&`), used a **function-local static** which C++11 guarantees is initialized exactly once, thread-safely:

```cpp
const std::string& TopoShape::shapeName(TopAbs_ShapeEnum type, bool silent) {
    static const std::array<std::string, TopAbs_SHAPE> _ShapeNameStrings = {{
        "Compound", "CompSolid", "Solid", "Shell", "Face", "Wire", "Edge", "Vertex",
    }};
    if (type >= 0 && static_cast<size_t>(type) < _ShapeNameStrings.size()) {
        return _ShapeNameStrings[type];
    }
    // ...
}
```

### Why this works
- `const char* const[]` is placed in read-only data (`.rdata` section) — no constructor, no runtime initialization, no corruption possible
- Function-local `static const` uses the compiler-generated guard variable pattern, which is resistant to the DLL load-order issues that affected the file-scope mutable version

## All Modified Files

| File | Change | Purpose |
|------|--------|---------|
| `src/Mod/Part/App/TopoShape.cpp` | Replaced `_ShapeNames` + `initShapeNameMap()` with `const char*` array | **Core fix** — eliminates static corruption |
| `src/Mod/Part/App/TopoShapeExpansion.cpp` | Added `continue` guards for `elementIndex == 0` | Pad crash prevention (earlier patch) |
| `src/App/ElementMap.cpp` | Return `{}` instead of throwing `Base::ValueError` | Pad "Invalid input" crash fix (earlier patch) |
| `src/App/ComplexGeoData.cpp` | Skip null elements in bulk `setElementName` | Element map deserialization guard (earlier patch) |

## Verification

After the fix, all tests pass:

```
countElement('Face'): 6           ✅ (was 0)
countElement('Edge'): 12          ✅ (was 0)  
countElement('Vertex'): 8         ✅ (was 0)
Part.getShape(feat, "Face1"): non-null  ✅ (was null)
pad.getSubObject("Face1"): Face         ✅ (was null)
```

## Build Environment

- **OS**: Windows
- **Compiler**: MSVC 2019 Community (19.29)
- **Build System**: CMake + Ninja (debug preset)
- **Pixi Environment**: OCC 7.8.1, Qt 6.8.3, Python 3.11.14
- **Build Output**: `C:\GIT\FreeCAD\build\debug\`
