# FreeCAD Development Session Log

> **Date:** June 2025  
> **Repository:** `C:\GIT\FreeCAD` (branch `main`)  
> **Environment:** Windows 10, Visual Studio 2019 Community (MSVC 19.29), pixi 0.65.0  
> **Build:** CMake preset `conda-windows-debug`, Ninja, C++20, RelWithDebInfo

---

## Table of Contents

1. [Overview](#overview)
2. [Phase 1 — Patch Implementation (28 Files)](#phase-1--patch-implementation-28-files)
3. [Phase 2 — build.bat Fixes](#phase-2--buildbat-fixes)
4. [Phase 3 — CMake Configure & Build](#phase-3--cmake-configure--build)
5. [Phase 4 — Build Error Fixes](#phase-4--build-error-fixes)
   - [4a. tsp_solver Linker Errors](#4a-tsp_solver-linker-errors)
   - [4b. Console.h Backward Compatibility](#4b-consoleh-backward-compatibility)
   - [4c. ReaderStep.cpp const Error](#4c-readersteppcpp-const-error)
   - [4d. ImpExpDxf MSVC 2019 ICE (Major)](#4d-impexpdxf-msvc-2019-ice-major)
6. [Phase 5 — VS Code Debug Configuration](#phase-5--vs-code-debug-configuration)
7. [Phase 6 — Successful Build](#phase-6--successful-build)
8. [Phase 7 — FreeCAD Launch](#phase-7--freecad-launch)
9. [Complete File Inventory](#complete-file-inventory)
10. [Technical Reference](#technical-reference)

---

## Overview

This session implemented a large patch from `CHANGELOG_PATCH.md` across 28 files in the FreeCAD repository, then resolved all build issues and successfully compiled and launched FreeCAD.exe.

### Key Achievements

| Milestone | Status |
|-----------|--------|
| 28 patch files implemented | ✅ |
| `build.bat` Windows automation | ✅ |
| CMake configure | ✅ |
| All build errors resolved (4 major) | ✅ |
| VS Code debug configuration | ✅ |
| Full build completed | ✅ |
| FreeCAD.exe launched successfully | ✅ |

---

## Phase 1 — Patch Implementation (28 Files)

All files from `CHANGELOG_PATCH.md` were created or modified:

### Source Files Modified (12)

| File | Change |
|------|--------|
| `src/Mod/PartDesign/App/FeatureFillet.cpp` | Crash prevention, pre-validation, improved errors |
| `src/Mod/PartDesign/App/FeatureChamfer.cpp` | Crash prevention, parameter validation, improved errors |
| `src/Mod/Assembly/App/AssemblyObject.cpp` | NaN validation, dangling pointer safety, error logging |
| `src/App/Document.cpp` | Recompute cascade guard, `CanAbortRecompute` default |
| `src/Mod/Part/App/TopoShapePyImp.cpp` | TNP `makeElementChamfer`, improved Python API errors |
| `src/Gui/AutoSaver.cpp` | Thread safety, specific exception handling |
| `src/Mod/Import/App/ReaderStep.cpp` | Thread pool, read params, file size detection, adaptive precision |
| `src/Mod/Import/App/ReaderStep.h` | Timing/size accessors, private state |
| `src/Mod/Import/App/ImportOCAF2.cpp` | Parallel maps, pre-allocation, SkipRecompute, progress |
| `src/Mod/Import/App/ImportOCAF2.h` | ImportOCAFOptions fields, progress methods |
| `src/Mod/Import/App/AppImportPy.cpp` | Large-file flag passthrough, timing, phase logging |
| `src/Mod/Part/App/OCAF/ImportExportSettings.cpp` | STEP read performance parameters |

### New Test Files (5)

| File | Tests |
|------|-------|
| `tests/src/Mod/PartDesign/App/FeatureFilletRobustness.cpp` | 5 |
| `tests/src/Mod/PartDesign/App/FeatureChamferRobustness.cpp` | 5 |
| `tests/src/Mod/Assembly/App/AssemblyRobustness.cpp` | 9 |
| `tests/src/App/DocumentRecompute.cpp` | 6 |
| `tests/src/Mod/Part/App/ChamferTNP.cpp` | 4 |

### New Build/Deploy/Doc Files

| File | Purpose |
|------|---------|
| `build.bat` | Windows one-command build automation |
| `BUILD.md` | Comprehensive build guide |
| `cMake/CPackConfig.cmake` | Cross-platform packaging |
| `FREECAD_1.0_MAJOR_ISSUES.md` | Issue research |
| `LARGE_MODEL_OPTIMIZATION.md` | Large file import docs |
| `CHANGELOG_PATCH.md` | Complete patch changelog |

### CMakeLists.txt Updated (5)

| File | Change |
|------|--------|
| `tests/CMakeLists.txt` | Test install rules |
| `tests/src/App/CMakeLists.txt` | Added `DocumentRecompute.cpp` |
| `tests/src/Mod/Assembly/App/CMakeLists.txt` | Added `AssemblyRobustness.cpp` |
| `tests/src/Mod/Part/App/CMakeLists.txt` | Added `ChamferTNP.cpp` |
| `tests/src/Mod/PartDesign/App/CMakeLists.txt` | Added 2 robustness test files |

---

## Phase 2 — build.bat Fixes

The `build.bat` script required several fixes for the local environment:

| Issue | Fix |
|-------|-----|
| pixi not on system PATH | Added `%USERPROFILE%\.pixi\bin` to PATH at script start |
| Git submodule check | Check for `tests\lib\googletest\CMakeLists.txt` |
| VS 2019 auto-detection | Use `vswhere.exe` to find VS installation path |
| `ProgramFiles(x86)` breaks batch | Use delayed expansion (`!ProgramFiles(x86)!`) — parentheses in env var names break normal `%` expansion |

---

## Phase 3 — CMake Configure & Build

```
pixi run cmake --preset conda-windows-debug
```

### Key Build Configuration

| Setting | Value |
|---------|-------|
| CMake preset | `conda-windows-debug` |
| Generator | Ninja |
| Build type | RelWithDebInfo |
| C++ standard | C++20 |
| Compiler flags | `/O2 /Ob1 /DNDEBUG -std:c++20 -MD /Zm150 /bigobj` |
| Debug info | `/Z7` |

### Key Dependencies

| Library | Version |
|---------|---------|
| OpenCASCADE | 7.8.1 |
| Qt | 6.8.3 |
| Python | 3.11.14 |
| Boost | 1.84.0 |
| pybind11 | 3.0.1 |
| Coin3D | 4.0+ |

---

## Phase 4 — Build Error Fixes

### 4a. tsp_solver Linker Errors

**Symptom:** 52 unresolved CRT external symbols during linking of `tsp_solver` in the CAM module.

**Root Cause:** `tsp_solver` was built as a shared library (DLL) but didn't link the MSVC C runtime libraries.

**Fix:** In `src/Mod/CAM/App/CMakeLists.txt`:
- Changed to `add_library(tsp_solver SHARED ...)`
- Added explicit MSVC CRT libs: `ucrt.lib`, `vcruntime.lib`, `msvcrt.lib`

---

### 4b. Console.h Backward Compatibility

**Symptom:** Compile errors across many files — the patch renamed `Console().Error()` → `Console().error()` (lowercase) but hundreds of call sites still used uppercase.

**Root Cause:** The patch changed the API but didn't update all callers.

**Fix:** Added backward-compatible forwarding aliases in `src/Base/Console.h`:
```cpp
// Backward-compatible aliases
template<typename... Args> void Message(Args&&... args) { message(std::forward<Args>(args)...); }
template<typename... Args> void Warning(Args&&... args) { warning(std::forward<Args>(args)...); }
template<typename... Args> void Error(Args&&... args) { error(std::forward<Args>(args)...); }
template<typename... Args> void Log(Args&&... args) { log(std::forward<Args>(args)...); }
```

---

### 4c. ReaderStep.cpp const Error

**Symptom:** `NbRootsForTransfer()` called on wrong object — `aReader.Reader().NbRootsForTransfer()` failed because `Reader()` returns a const reference.

**Fix:** Changed to `aReader.NbRootsForTransfer()` (the wrapper class provides the method directly).

---

### 4d. ImpExpDxf MSVC 2019 ICE (Major)

This was the most complex issue, requiring extensive debugging over multiple hours.

**Symptom:** MSVC 2019 crashed with **Internal Compiler Error** (ICE) at `p2/main.c line 213` when compiling `ImpExpDxf.cpp`.

**Error message:**
```
fatal error C1001: Internal compiler error.
(compiler file 'msc1.cpp', line 1590)
...
internal error at <FILE>p2\main.c</FILE> line 213
```

**Investigation Process:**

1. **Initial hypothesis: large translation unit** — Split `ImpExpDxf.cpp` into 5 files. ICE persisted in specific files.

2. **Binary search** — Systematically bisected the code to isolate the trigger.

3. **Root cause identified:** MSVC 2019's C++20 **parenthesized aggregate initialization** (P0960R3) implementation is buggy. The compiler's code generator crashes when:
   - A struct/class has a `TopoDS_Shape` member (complex OCC type)
   - The struct also has a default member initializer
   - The struct is constructed with C++20 parenthesized aggregate init: `GeometryBuilder(edge)`

4. **Minimal reproducer:**
   ```cpp
   struct GeometryBuilder {
       TopoDS_Shape shape;                           // Complex OCC type
       PrimitiveType type = PrimitiveType::None;     // Default member init
   };
   
   // This crashes MSVC 2019's code generator:
   GeometryBuilder builder(edge);  // C++20 parenthesized aggregate init
   ```

**Fix:** Added an explicit constructor to `GeometryBuilder` in `ImpExpDxf.h`:
```cpp
explicit GeometryBuilder(const TopoDS_Shape& s) : shape(s) {}
```

This bypasses C++20 parenthesized aggregate initialization entirely — the compiler uses the explicit constructor instead.

**Final file structure** (consolidated from 5 files to 3):

| File | Purpose | Lines |
|------|---------|-------|
| `ImpExpDxf.cpp` | Core ImpExpDxfRead methods | ~812 |
| `ImpExpDxfCallbacks.cpp` | OnRead* callbacks, DrawingEntityCollector, Layer | ~500 |
| `ImpExpDxfWrite.cpp` | DXF export (ImpExpDxfWrite) + getStatsAsPyObject | ~811 |
| `ImpExpDxfHelpers.h` | Shared inline helper functions | ~150 |

**CMakeLists.txt** (`src/Mod/Import/App/CMakeLists.txt`) references all 3 source files.

---

## Phase 5 — VS Code Debug Configuration

Created complete VS Code development environment:

| File | Purpose |
|------|---------|
| `.vscode/launch.json` | 6 debug configurations |
| `.vscode/tasks.json` | Build tasks |
| `.vscode/c_cpp_properties.json` | IntelliSense configuration |
| `.vscode/extensions.json` | Recommended extensions |
| `.vscode/settings.json` | Workspace settings |

### Launch Configurations

1. **Debug FreeCAD (C++)** — Full build + debug
2. **Debug FreeCAD (No Build)** — Attach without rebuilding
3. **Debug FreeCAD (C++ + Python)** — Compound C++ and Python debugging
4. **Python Debugger (Attach)** — Attach to FreeCAD's Python
5. **Debug C++ Tests** — Run test executables under debugger
6. **Attach to FreeCAD** — Attach to already-running process

All configurations include `QT_PLUGIN_PATH` environment variable (see Phase 7).

---

## Phase 6 — Successful Build

### Disk Space Issue

During the full build, the C: drive ran out of space. Resolved by:
- Clearing ccache: **2.57 GB** freed (`C:\Users\Riko\AppData\Local\ccache`)
- Clearing temp files
- Building with `-j 2` (reduced parallelism) and `CCACHE_DISABLE=1`

### Build Command

```batch
call "C:\Program Files (x86)\Microsoft Visual Studio\2019\Community\VC\Auxiliary\Build\vcvars64.bat"
cd /d C:\GIT\FreeCAD\build\debug
set CCACHE_DISABLE=1
ninja -j 2
```

**Result:** BUILD_OK after ~1 hour with `-j 2`.

---

## Phase 7 — FreeCAD Launch

### First Attempt — Qt Plugin Error

```
qt.qpa.plugin: Could not find the Qt platform plugin "windows" in ""
This application failed to start because no Qt platform plugin could be initialized.
```

**Root Cause:** Qt 6 plugins are in the pixi environment, and `QT_PLUGIN_PATH` was not set.

### Fix

```
set QT_PLUGIN_PATH=C:\GIT\FreeCAD\.pixi\envs\default\Library\lib\qt6\plugins
```

### Successful Launch

```
C:\GIT\FreeCAD\build\debug\bin\FreeCAD.exe
```

FreeCAD started successfully — PID 50112, ~409 MB memory usage.

The `QT_PLUGIN_PATH` was added to all VS Code launch configurations in `.vscode/launch.json`.

---

## Complete File Inventory

### Files Created in This Session

| File | Type |
|------|------|
| `build.bat` | Build automation |
| `BUILD.md` | Documentation |
| `CHANGELOG_PATCH.md` | Documentation |
| `FREECAD_1.0_MAJOR_ISSUES.md` | Documentation |
| `LARGE_MODEL_OPTIMIZATION.md` | Documentation |
| `cMake/CPackConfig.cmake` | CMake packaging |
| `src/Mod/Import/App/dxf/ImpExpDxfCallbacks.cpp` | C++ source (new) |
| `src/Mod/Import/App/dxf/ImpExpDxfWrite.cpp` | C++ source (new) |
| `src/Mod/Import/App/dxf/ImpExpDxfHelpers.h` | C++ header (new) |
| `tests/src/App/DocumentRecompute.cpp` | C++ test |
| `tests/src/Mod/Assembly/App/AssemblyRobustness.cpp` | C++ test |
| `tests/src/Mod/Part/App/ChamferTNP.cpp` | C++ test |
| `tests/src/Mod/PartDesign/App/FeatureChamferRobustness.cpp` | C++ test |
| `tests/src/Mod/PartDesign/App/FeatureFilletRobustness.cpp` | C++ test |
| `.vscode/launch.json` | VS Code config |
| `.vscode/tasks.json` | VS Code config |
| `.vscode/c_cpp_properties.json` | VS Code config |
| `.vscode/extensions.json` | VS Code config |

### Files Modified in This Session

| File | Change Summary |
|------|----------------|
| `src/Mod/PartDesign/App/FeatureFillet.cpp` | Crash prevention, edge length validation |
| `src/Mod/PartDesign/App/FeatureChamfer.cpp` | Crash prevention, better error messages |
| `src/Mod/Assembly/App/AssemblyObject.cpp` | NaN/Inf validation, error logging |
| `src/App/Document.cpp` | Recompute cascade guard |
| `src/Mod/Part/App/TopoShapePyImp.cpp` | TNP chamfer path |
| `src/Gui/AutoSaver.cpp` | Thread safety |
| `src/Mod/Import/App/ReaderStep.cpp` | STEP parallelization + const fix |
| `src/Mod/Import/App/ReaderStep.h` | Timing accessors |
| `src/Mod/Import/App/ImportOCAF2.cpp` | Parallel maps, large file support |
| `src/Mod/Import/App/ImportOCAF2.h` | Options fields |
| `src/Mod/Import/App/AppImportPy.cpp` | Phase logging |
| `src/Mod/Part/App/OCAF/ImportExportSettings.cpp` | STEP read params |
| `src/Mod/Import/App/dxf/ImpExpDxf.h` | GeometryBuilder explicit ctor (ICE fix) |
| `src/Mod/Import/App/dxf/ImpExpDxf.cpp` | Reorganized (core reader methods) |
| `src/Mod/Import/App/CMakeLists.txt` | 3 DXF source files |
| `src/Mod/CAM/App/CMakeLists.txt` | tsp_solver MSVC CRT fix |
| `src/Base/Console.h` | Backward-compatible uppercase aliases |
| `tests/CMakeLists.txt` | Test install rules |
| `tests/src/App/CMakeLists.txt` | Added DocumentRecompute.cpp |
| `tests/src/Mod/Assembly/App/CMakeLists.txt` | Added AssemblyRobustness.cpp |
| `tests/src/Mod/Part/App/CMakeLists.txt` | Added ChamferTNP.cpp |
| `tests/src/Mod/PartDesign/App/CMakeLists.txt` | Added 2 robustness tests |
| `.vscode/settings.json` | Workspace settings update |

### Temporary Files (can be cleaned up)

| File | Purpose |
|------|---------|
| `_compile_test.bat` | Used during ICE debugging |
| `_compile_test_output.log` | ICE debug output |
| `_build_full.log` | Build log |
| `_run_full_build.bat` | Build script |
| `_build_with_vcvars.bat` | Build script |

---

## Technical Reference

### How to Build

```batch
REM Option 1: Using build.bat
build.bat

REM Option 2: Manual
call "C:\Program Files (x86)\Microsoft Visual Studio\2019\Community\VC\Auxiliary\Build\vcvars64.bat"
cd /d C:\GIT\FreeCAD
pixi run cmake --preset conda-windows-debug
cd build\debug
ninja -j 4
```

### How to Run

```batch
set QT_PLUGIN_PATH=C:\GIT\FreeCAD\.pixi\envs\default\Library\lib\qt6\plugins
C:\GIT\FreeCAD\build\debug\bin\FreeCAD.exe
```

### How to Debug (VS Code)

1. Open `C:\GIT\FreeCAD` in VS Code
2. Install recommended extensions (C/C++, CMake Tools, Python)
3. Select "Debug FreeCAD (C++)" from the Run and Debug panel
4. F5 to start debugging

### MSVC 2019 ICE Workaround

If you encounter ICE in DXF-related files, ensure:
1. `ImpExpDxf.h` has the explicit `GeometryBuilder` constructor
2. Code is split across 3 `.cpp` files (not one monolithic file)
3. `#pragma optimize("", off)` is present for MSVC < 1930

---

*Generated from AI-assisted development session on the FreeCAD repository.*
