# FreeCAD Enterprise Modernization & Refactoring Plan

**Version:** 1.0  
**Date:** 2025  
**Scope:** Full-stack transformation from open-source hobbyist CAD to professional-grade engineering platform  
**Baseline:** FreeCAD 1.2.0-dev (current trunk)

---

## Table of Contents

1. [Executive Product Goal](#1-executive-product-goal)
2. [Current-State Diagnosis](#2-current-state-diagnosis)
3. [Product Benchmark Model](#3-product-benchmark-model)
4. [Target Architecture](#4-target-architecture)
5. [Technology Stack](#5-technology-stack)
6. [UX / Interaction Redesign](#6-ux--interaction-redesign)
7. [Mechanical CAD Workflow Improvements](#7-mechanical-cad-workflow-improvements)
8. [Enterprise Features](#8-enterprise-features)
9. [Plugin / Automation Platform](#9-plugin--automation-platform)
10. [Refactoring Strategy](#10-refactoring-strategy)
11. [Repository / Module Reorganization](#11-repository--module-reorganization)
12. [Quality Engineering & Test Strategy](#12-quality-engineering--test-strategy)
13. [Performance Engineering](#13-performance-engineering)
14. [Governance / Product Management](#14-governance--product-management)
15. [Risk Register](#15-risk-register)
16. [Final Deliverables](#16-final-deliverables)

---

## 1. Executive Product Goal

### 1.1 Vision Statement

Transform FreeCAD from a capable but inconsistent open-source 3D modeler into a **production-grade parametric CAD platform** that a mechanical engineering team of 5–50 can deploy as a credible alternative to Autodesk Inventor, SolidWorks, or Siemens NX for small-to-medium assemblies (up to ~5000 parts).

### 1.2 Quantitative Targets

| Metric | Current State | 24-Month Target |
|--------|--------------|-----------------|
| Assembly size before UI stalls | ~200 parts | 5000+ parts at >30 FPS |
| STEP export round-trip fidelity | ~92% face preservation | 99.5%+ with TNP-stable names |
| Time to first sketch from cold start | ~8–12 seconds | <3 seconds |
| Recompute of 100-feature body | 15–45 seconds (serial) | <5 seconds (parallel DAG) |
| Crash rate per 100 operations | ~2–4 (OCCT exceptions, null shapes) | <0.1 (catch-all + recovery) |
| Automated test coverage (C++ + Python) | ~29 GTest cases, sporadic | >4000 unit + 200 integration |
| Plugin API breakage per release | Frequent (undocumented) | Zero (versioned, tested) |
| Dark mode visual consistency | Partial (hard-coded colors) | 100% theme token coverage |
| File format backward compat | Fragile (XML tag drift) | Schema-versioned with migration |

### 1.3 Non-Goals

- **Not** replacing CATIA/NX for 50,000-part aerospace assemblies
- **Not** building a cloud-native SaaS product (but architecture must not preclude it)
- **Not** rewriting OCCT — we wrap and isolate it, not replace it
- **Not** abandoning Python extensibility — it is a strategic advantage

### 1.4 Strategic Differentiators to Preserve

1. **Open-source parametric kernel** — no vendor lock-in on geometry
2. **Python-first automation** — macros, scripts, full API access
3. **Multi-physics integration** — FEM, CFD, electromagnetic solvers in one tool
4. **Extensible workbench architecture** — community-driven specialization
5. **Cross-platform** — Windows, Linux, macOS from single codebase

---

## 2. Current-State Diagnosis

### 2.1 Architectural Strengths

**2.1.1 Property System — Well-Designed Dynamic Typing**

The `App::Property` → `App::PropertyContainer` → `App::DocumentObject` hierarchy is the spine of FreeCAD. Every feature parameter is a typed `Property` instance with metadata flags (`ReadOnly`, `Hidden`, `Transient`, `Output`, `NoRecompute`). This design enables:

- Undo/Redo via `openTransaction()` / `commitTransaction()` on `App::Document`
- Expression binding: any property can be formula-driven via `PropertyExpression`
- Serialization: `Base::Persistence` + XML/ZIP persistence
- Python reflection: `getProperties()`, `getPropertyType()`, `getProperty(name)`

**Status bits** (32-bit `std::bitset`) provide fine-grained lifecycle control per object: `Touch`, `Error`, `Recompute`, `Restore`, `Freeze`, `PendingRecompute`, etc.

**2.1.2 Topological Naming — Major Achievement**

Implemented across ~40 Part/PartDesign operations with the `MappedElement` / `MappedName` / `IndexedName` system. Each sub-element gets an operation-aware encoded name:

```
;FUS;:H8c5:7,F;:H8c5:6,F
```

This encodes the operation code (`FUS` = Fuse), feature tag (`H8c5`), element index, and type (`F` = Face). The `StringHasher` compresses repeated fragments. `ElementMap` provides bidirectional lookup. Downstream features resolve references by mapped name, surviving parent topology changes.

**2.1.3 Expression Engine — Spreadsheet-Grade Formula Language**

The Flex/Bison parser supports ~80 built-in functions, unit-aware arithmetic (`5mm + 2in`), property cross-references (`Box.Length * 2`), cell ranges (`sum(Sheet.A1:A10)`), ternary expressions, and cross-document references (`file.FCStd#Box.Length`). Circular dependency detection via `ExpressionDeps` graph.

**2.1.4 Link System — Assembly-Ready**

`LinkBaseExtension` wraps any `DocumentObject` with independent `LinkPlacement`, `Scale`, `VisibilityList`, and `CopyOnChange` modes (`Disabled`, `Enabled`, `Owned`, `Tracking`). Shadow sub-names store TNP mapped names alongside traditional indexed names for element map resolution across links.

### 2.2 Architectural Weaknesses

**2.2.1 Single-Threaded Core — The Fundamental Bottleneck**

`App::Document`, `App::DocumentObject`, and all `Property` instances have **zero thread safety**. No mutexes, no atomic operations. `std::bitset<32>` status bits are non-atomic. `AtomicPropertyChange` is transaction-scoped, not thread-scoped. Recompute is strictly serial: one feature at a time, despite the dependency DAG often having wide parallelism.

**Impact:** A 100-feature Body recomputes in 15–45 seconds. Large assemblies with independent sub-assemblies still recompute serially. The GUI blocks during recompute because signal emission is synchronous (`signalRecomputed` fires on the same thread).

**2.2.2 Coin3D Scene Graph — Rendering Ceiling**

The 3D viewer is built on `Quarter::SoQTQuarterAdaptor` → `View3DInventorViewer`. Coin3D is a retained-mode scene graph that:

- Owns the OpenGL context on the main thread
- Renders synchronously with traversal
- Has no GPU instancing, no compute shaders, no Vulkan path
- Cannot multi-thread scene modification

Our post-processing pipeline (SSAO → Bloom → Composite → Sharpen) already pushes Coin3D's per-frame budget. Large assemblies with 5000+ shapes will overwhelm Coin3D's traversal.

**2.2.3 OCCT Exception Propagation — Crash Source**

OCCT throws `Standard_Failure` (and various subclasses) on invalid geometry, null shapes, and edge cases. Current FreeCAD code catches these inconsistently. Many `execute()` implementations let OCCT exceptions propagate to the recompute loop, causing:

- Cryptic error messages in the Report View
- Partial recompute (some features updated, others not)
- Occasionally: crash to desktop when exceptions escape through Python bindings

**2.2.4 GUI ↔ App Coupling**

`Gui::ViewProvider` directly calls `App::DocumentObject` methods on the main thread. Selection changes trigger immediate property updates. Task panels hold raw pointers to `DocumentObject` instances that can be deleted during recompute. There is no command/event bus separating intent from execution.

**2.2.5 Python GIL Bottleneck**

`FeaturePythonT` delegates ~15 virtual callbacks to Python via `FeaturePythonImp`. Every callback acquires the GIL. `DocumentObserverPython` has 40+ observer methods, all GIL-bound. This means:

- Python features cannot participate in parallel recompute
- GUI responsiveness drops during Python-heavy operations
- Macro execution blocks the entire application

**2.2.6 File Format Fragility**

The `FCStd` ZIP archive contains `Document.xml` with ad-hoc XML serialization. There is no schema version number in the XML root, no migration framework. Adding a new property to a `DocumentObject` silently drops on older versions. Removing a property silently applies defaults. Cross-version compatibility is accidental, not designed.

**2.2.7 Test Coverage Gap**

Only ~29 GTest cases across the entire C++ codebase. Test files exist in `tests/src/Mod/*/App/` but coverage is sparse:

- `FeatureFilletRobustness.cpp` — 5 tests (crash prevention, oversized radius)
- `FeatureChamferRobustness.cpp` — 5 tests
- `AssemblyRobustness.cpp` — 9 tests (NaN validation, dangling pointers)
- `DocumentRecompute.cpp` — 6 tests
- `ChamferTNP.cpp` — 4 tests (element map encoding)

No integration tests for multi-feature workflows, no fuzz tests for property serialization, no performance regression tests.

### 2.3 Module-Level Health Assessment

| Module | LOC (est.) | Quality | Key Issues |
|--------|-----------|---------|------------|
| `src/App` | ~40K | Medium | No thread safety, property races |
| `src/Base` | ~20K | Good | ParameterGrp XML is fragile but functional |
| `src/Gui` | ~80K | Medium | Coin3D coupling, hard-coded colors, pointer lifetime |
| `Mod/Part` | ~50K | Good | TNP implemented, OCCT wrapping solid |
| `Mod/PartDesign` | ~40K | Good | Feature chain enforced, preview available |
| `Mod/Sketcher` | ~60K | Good | PlaneGCS solver stable, 20+ constraint types |
| `Mod/Assembly` | ~10K | Immature | Pure Python prototype, solver not robust |
| `Mod/TechDraw` | ~40K | Medium | Functional but slow for large models |
| `Mod/FEM` | ~30K | Medium | CalculiX integration works, pre-processing needs UX |
| `Mod/Draft` | ~25K | Medium | 2D tools functional, UI inconsistent |
| `Mod/BIM` | ~20K | Medium | IFC import/export via ifcopenshell |
| `Mod/Material` | ~8K | Good | YAML libraries, UUID referencing, thread-safe singleton |
| `Mod/Start` | ~5K | Good | Card-based UI, first-run widget, theme selector |
| `Mod/AddonManager` | ~8K | Good | Async install, dependency resolver, catalog-based |

### 2.4 Dependency Risk Matrix

| Dependency | Version | Risk | Mitigation |
|-----------|---------|------|------------|
| OCCT | 7.8.x | **HIGH** — monolithic, thread-unsafe shapes | Isolate behind `OcctService` layer |
| Coin3D | 4.x | **HIGH** — rendering ceiling, no Vulkan | Overlay pipeline already bypasses for post-fx |
| Qt6 | 6.8.x | LOW | Stable, well-supported |
| Python | 3.11 | LOW | CPython stable ABI |
| PySide6 | 6.8.x | LOW | Follows Qt versioning |
| VTK | 9.x | MEDIUM | Used in FEM post-processing, version-sensitive |
| Eigen3 | 3.x | LOW | Header-only, stable API |
| Xerces-C++ | 3.x | LOW | XML parsing, mature |
| Boost | 1.8x | LOW | Header-only usage |
| TBB | 2022 | MEDIUM | Thread building blocks, version-locked |
| HDF5 | 1.14 | LOW | Data format library |

---

## 3. Product Benchmark Model

### 3.1 Autodesk Inventor Professional — Primary Benchmark

**What Inventor Gets Right:**

| Capability | Inventor Implementation | FreeCAD Gap |
|-----------|------------------------|-------------|
| **Sketch editing** | Hardware-accelerated, instant constraint feedback, auto-dimension inference | PlaneGCS is capable but UX lacks auto-inference and visual constraint guides |
| **Feature tree** | Click-to-suppress/unsuppress, drag-to-reorder, rollback bar | FreeCAD has suppress via extension, no drag-reorder, no rollback bar |
| **Assembly workflow** | Place → Constrain → Solve (real-time DOF feedback) | Assembly module is Python prototype, no real-time DOF display |
| **Sheet metal** | Integrated unfold, bend deduction, flat pattern export | No native sheet metal workbench (addon only) |
| **Drawing/documentation** | Auto-populated BOM, balloon notes, revision clouds | TechDraw is functional but manual, slow for large assemblies |
| **Frame generator** | Library of structural shapes, auto-trim, auto-miter | No equivalent |
| **iLogic** | Rule-based automation with VB.NET, parameter-driven configs | Python macros are more powerful but lack visual rule builder |
| **Vault integration** | Native PDM: check-in/out, revision history, BOM sync | No PDM integration |
| **Performance** | 5000+ part assemblies at interactive frame rates | Starts lagging at ~200 parts |
| **Material library** | Autodesk Material Library with 4000+ materials | ~200 materials in FreeCAD-materials repo |
| **Dark mode** | Full dark mode with consistent icon set | Partial dark mode, hard-coded colors leak through |

**What Inventor Gets Wrong (Our Opportunity):**

1. **Closed ecosystem** — no source access, no custom solver integration
2. **Windows-only** — no Linux, no macOS
3. **Expensive** — $2,845/year subscription
4. **No multi-physics** — separate products for FEA (Nastran), CFD (CFD), EM (none)
5. **No Python scripting** — iLogic is VB.NET only, limited API
6. **No community addons** — closed plugin ecosystem

### 3.2 SolidWorks — Secondary Benchmark

| Capability | SolidWorks | FreeCAD Gap |
|-----------|-----------|-------------|
| **Feature Manager** | Rollback bar, feature freeze, configuration tables | No rollback bar, basic freeze, no config tables |
| **Assembly mates** | 15+ mate types with visual DOF feedback | 6 joint types, no DOF visualization |
| **Simulation** | Integrated FEA with auto-meshing | FEM workbench requires manual meshing |
| **PDM** | SOLIDWORKS PDM, 3DExperience | None |
| **Renderer** | PhotoView 360, Visualize | No rendering (Blender export only) |
| **API** | COM-based, well-documented | Python API, under-documented |

### 3.3 Feature Priority Matrix

Based on competitive analysis, prioritize features by **user-visible impact** × **implementation feasibility**:

| Priority | Feature | Impact | Feasibility | Benchmark Source |
|----------|---------|--------|-------------|-----------------|
| P0 | Parallel recompute | 10 | 6 | All competitors |
| P0 | Assembly solver robustness | 10 | 5 | Inventor/SW |
| P0 | Dark mode completeness | 8 | 9 | All competitors |
| P1 | Rollback bar in feature tree | 9 | 7 | Inventor/SW |
| P1 | Sketch auto-constraint inference | 8 | 6 | Inventor/SW |
| P1 | DOF visualization in assembly | 9 | 5 | Inventor/NX |
| P1 | STEP export fidelity (TNP) | 9 | 7 | All competitors |
| P2 | Sheet metal workbench | 8 | 5 | Inventor |
| P2 | Configuration tables | 7 | 6 | SolidWorks |
| P2 | Visual rule builder | 6 | 4 | Inventor iLogic |
| P2 | PDM integration hooks | 7 | 5 | All competitors |
| P3 | Frame generator | 5 | 4 | Inventor |
| P3 | Rendering engine | 5 | 3 | SolidWorks |

---

## 4. Target Architecture

### 4.1 Layered Architecture (Current → Target)

**Current Architecture (Spaghetti):**

```
┌─────────────────────────────────────────────────────────┐
│  Python Scripts & Macros                                 │
├─────────────────────────────────────────────────────────┤
│  Workbench Modules (Mod/*)                               │
│  ┌──────┐ ┌──────────┐ ┌─────────┐ ┌─────┐ ┌─────┐    │
│  │ Part │ │PartDesign│ │Sketcher │ │ FEM │ │ ... │    │
│  └──┬───┘ └────┬─────┘ └────┬────┘ └──┬──┘ └──┬──┘    │
│     │          │            │          │       │        │
├─────┴──────────┴────────────┴──────────┴───────┴────────┤
│  GUI Layer (src/Gui)          ← TIGHTLY COUPLED         │
│  MainWindow ↔ View3DInventorViewer ↔ Selection          │
│  TaskView ↔ PropertyEditor ↔ TreeView ↔ Commands        │
├─────────────────────────────────────────────────────────┤
│  App Layer (src/App)          ← SINGLE-THREADED         │
│  Document ↔ DocumentObject ↔ Property ↔ Expression      │
├─────────────────────────────────────────────────────────┤
│  Base Layer (src/Base)                                   │
│  Parameter ↔ Persistence ↔ Console ↔ Math               │
├─────────────────────────────────────────────────────────┤
│  External (OCCT, Coin3D, Qt6, Python, VTK)              │
└─────────────────────────────────────────────────────────┘
```

**Target Architecture (Layered with Service Boundaries):**

```
┌─────────────────────────────────────────────────────────────┐
│                    PRESENTATION TIER                         │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Shell (MainWindow + RibbonBar + DockWindows)        │   │
│  │  ┌─────────┐ ┌──────────┐ ┌───────┐ ┌───────────┐  │   │
│  │  │Ribbon   │ │TreePanel │ │PropEd │ │TaskView   │  │   │
│  │  │Tabs     │ │+Rollback │ │+Live  │ │+Wizard    │  │   │
│  │  └─────────┘ └──────────┘ └───────┘ └───────────┘  │   │
│  ├──────────────────────────────────────────────────────┤   │
│  │  3D Viewport (Coin3D + Post-Processing Overlay)      │   │
│  │  ┌──────────┐ ┌──────┐ ┌───────┐ ┌──────────────┐  │   │
│  │  │SelectHlr │ │NavCub│ │Gizmo  │ │PostFX        │  │   │
│  │  │+PreHlr   │ │+Anim │ │+Manip │ │SSAO+Bloom+.. │  │   │
│  │  └──────────┘ └──────┘ └───────┘ └──────────────┘  │   │
│  └──────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│                    COMMAND / EVENT BUS                       │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  CommandDispatcher                                    │   │
│  │  ┌───────────┐ ┌──────────┐ ┌─────────────────────┐ │   │
│  │  │UndoableCmd│ │AsyncCmd  │ │MacroRecordableCmd   │ │   │
│  │  └───────────┘ └──────────┘ └─────────────────────┘ │   │
│  │  SignalQueue (batched, main-thread flush)             │   │
│  └──────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│                    DOMAIN SERVICE TIER                       │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐  │
│  │Modeling  │ │Assembly  │ │Sketch    │ │Simulation    │  │
│  │Service   │ │Service   │ │Service   │ │Service       │  │
│  │(Part/PD) │ │(Joints,  │ │(PlaneGCS │ │(FEM/CFD/EM)  │  │
│  │          │ │ Solver)  │ │ +Infer)  │ │              │  │
│  └─────┬────┘ └────┬─────┘ └────┬─────┘ └──────┬───────┘  │
│        │           │            │               │           │
├────────┴───────────┴────────────┴───────────────┴───────────┤
│                    MODEL / DATA TIER                         │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Document Model (Thread-Safe)                         │   │
│  │  ┌──────────┐ ┌──────────┐ ┌───────────────────────┐│   │
│  │  │Document  │ │Feature   │ │PropertyContainer      ││   │
│  │  │+Schema   │ │+DAG Node │ │+SharedMutex per obj   ││   │
│  │  │+Version  │ │+AtomicBit│ │+ExpressionBinding     ││   │
│  │  └──────────┘ └──────────┘ └───────────────────────┘│   │
│  │  RecomputeEngine (Parallel DAG Scheduler)             │   │
│  └──────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│                    GEOMETRY ISOLATION TIER                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  OcctService (thread-safe OCCT wrapper)               │   │
│  │  ┌─────────┐ ┌──────────┐ ┌────────────┐            │   │
│  │  │ShapeOps │ │MeshGen   │ │STEPCodec   │            │   │
│  │  │+BoolOps │ │+Parallel │ │+TNPPreserve│            │   │
│  │  └─────────┘ └──────────┘ └────────────┘            │   │
│  └──────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│                    PLATFORM ABSTRACTION                      │
│  ┌──────┐ ┌─────┐ ┌────────┐ ┌─────────┐ ┌──────────┐    │
│  │ Qt6  │ │OCCT │ │Python  │ │Coin3D   │ │ VTK/HDF5│    │
│  └──────┘ └─────┘ └────────┘ └─────────┘ └──────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 Key Architectural Changes

**4.2.1 Command / Event Bus**

Replace direct `DocumentObject` mutation from GUI code with a `CommandDispatcher`:

```cpp
// CURRENT: GUI directly mutates model
void TaskPadParameters::onLengthChanged(double val) {
    auto pad = static_cast<PartDesign::Pad*>(vp->getObject());
    pad->Length.setValue(val);  // Direct mutation, no undo grouping
    pad->recompute();          // Blocks UI thread
}

// TARGET: GUI dispatches command
void TaskPadParameters::onLengthChanged(double val) {
    dispatch(SetPropertyCmd{featureId, "Length", val});
    // Command handles: undo group, validation, async recompute, signal batching
}
```

**Implementation path:**
- `src/Gui/CommandDispatcher.h` — New command bus
- `UndoableCommand` base with `execute()` / `undo()` / `redo()` / `merge()`
- `AsyncCommand` variant that runs `execute()` on worker thread, signals completion
- Existing `Command` / `CommandManager` / `DEF_STD_CMD` macros wrap as thin adapters

**4.2.2 Parallel Recompute Engine**

Replace the serial `Document::recompute()` loop with a level-parallel DAG scheduler:

```cpp
// CURRENT (Document.cpp ~L2500)
for (auto obj : topoSortedObjects) {
    obj->recompute();  // Serial, one at a time
}

// TARGET
class RecomputeEngine {
    void recompute(std::vector<DocumentObject*>& dirty) {
        auto dag = buildDAG(dirty);
        auto levels = topologicalLevels(dag);
        for (auto& level : levels) {
            // All objects in a level are independent — run in parallel
            tbb::parallel_for_each(level.begin(), level.end(),
                [](DocumentObject* obj) {
                    std::unique_lock lock(obj->mutex());
                    obj->execute();
                });
        }
        // Flush batched signals on main thread
        SignalQueue::instance().flush();
    }
};
```

**Prerequisites:**
1. Atomic status bits (`std::atomic<uint32_t>` replacing `std::bitset<32>`)
2. Per-object `std::shared_mutex` on every `DocumentObject`
3. `SignalQueue` for batched, main-thread-only signal delivery
4. Transaction locks: recompute holds shared lock, undo/redo holds exclusive lock
5. Python features serialized via GIL or opt-in `allowParallel` flag

**4.2.3 OcctService — Geometry Isolation Layer**

Wrap all OCCT calls behind a service that:
- Catches `Standard_Failure` and converts to `App::OcctError` with context
- Provides thread-safe shape operations (OCCT shapes are immutable once built)
- Manages `OSD_ThreadPool` for parallel tessellation
- Handles STEP import/export with TNP preservation

```cpp
namespace OcctService {
    Result<TopoDS_Shape> fuse(const TopoDS_Shape& a, const TopoDS_Shape& b,
                               const ElementMapContext& ctx);
    Result<TopoDS_Shape> fillet(const TopoDS_Shape& base,
                                 const std::vector<TopoDS_Edge>& edges,
                                 double radius,
                                 const ElementMapContext& ctx);
    // Every function returns Result<T> = variant<T, OcctError>
}
```

**4.2.4 Schema-Versioned File Format**

Add schema version to `Document.xml` root element and implement migration framework:

```xml
<!-- CURRENT -->
<Document SchemaVersion="1">
  <!-- No version, no migration -->

<!-- TARGET -->
<Document SchemaVersion="4" MinReaderVersion="2" AppVersion="1.2.0">
  <Migration from="3" to="4">
    <RenameProperty old="App::Pad::Length" new="App::Pad::PadLength"/>
  </Migration>
```

Migration registry in `src/App/DocumentMigration.h`:
```cpp
class DocumentMigration {
    static void registerMigration(int fromVersion, int toVersion,
                                   MigrationFunc func);
    static void migrate(Document& doc, int fromVersion, int toVersion);
};
```

### 4.3 Module Dependency Rules (Target)

```
ALLOWED DEPENDENCIES:
  Mod/* → App, Base (never Gui directly)
  Gui   → App, Base
  App   → Base (never Gui)
  Base  → (standard library, Qt Core only)

FORBIDDEN:
  App → Gui (model must never know about view)
  Base → App (utilities must not depend on domain)
  Mod/A → Mod/B (modules communicate via App signals/links only)
```

Enforce via CMake `target_link_libraries` visibility and CI-time dependency checker.

---

## 5. Technology Stack

### 5.1 Current Stack Analysis

| Layer | Current | Version | Verdict |
|-------|---------|---------|---------|
| Language | C++20 | MSVC 2019+ / GCC 12+ / Clang 15+ | **Keep** — C++20 features (concepts, ranges, coroutines) enable cleaner code |
| Build | CMake 3.22 + Ninja + pixi (conda) | Latest | **Keep** — pixi-based dependency management is excellent |
| GUI Framework | Qt6 | 6.8 | **Keep** — stable, cross-platform |
| Python Bindings | PyCXX + manual PyImp.cpp | Custom | **Evolve** — add pybind11 for new modules |
| 3D Rendering | Coin3D 4.x + our post-processing overlay | 4.0 | **Keep + Layer** — add GPU compute for heavy scenes |
| Geometry Kernel | OpenCASCADE (OCCT) | 7.8 | **Keep + Isolate** — wrap behind OcctService |
| Constraint Solver | PlaneGCS (built-in) | Custom | **Keep + Extend** — already capable |
| Assembly Solver | None (Python prototype) | — | **Build** — need C++ solver |
| Mesh | SMESH + Gmsh + Netgen | Various | **Keep** — adequate |
| FEM Post | VTK | 9.x | **Keep** — industry standard |
| Data | HDF5, Xerces-C++ | Various | **Keep** |
| Package Mgr | pixi (conda) | Latest | **Keep** — excellent reproducibility |

### 5.2 New Technology Introductions

| Technology | Purpose | Justification |
|-----------|---------|---------------|
| **TBB 2022+** | Parallel recompute, parallel mesh | Already a dependency, just underused |
| **pybind11** | New module Python bindings | Cleaner than manual PyCXX, auto-generates stubs |
| **Google Benchmark** | Performance regression tests | Complements GTest for perf tracking |
| **nlohmann/json** | Modern JSON for config/IPC | Replaces ad-hoc XML for non-document data |
| **spdlog** | Structured logging | Replace printf-style `Base::Console` for diagnostics |
| **Catch2 or doctest** | (Alternative: stay GTest) | Consider for lighter test overhead |

### 5.3 Technology Decisions

**5.3.1 Keep Coin3D (Do Not Replace)**

Replacing Coin3D with a custom Vulkan renderer would require 2+ years and 50K+ LOC. Instead:
- Continue building our GLSL post-processing overlay (already done: SSAO, bloom, SSCS, sharpen)
- Add GPU-side frustum culling and LOD for large assemblies (Phase C already implemented)
- For future: evaluate `wgpu` or `filament` as a secondary renderer for photorealistic mode only

**5.3.2 Keep PyCXX for Existing Code, Use pybind11 for New**

Rewriting all `*PyImp.cpp` files is too risky. New modules (FlowStudio, Sheet Metal, etc.) should use pybind11. Provide a bridge: `pybind11::object` ↔ `Py::Object` conversion utilities.

**5.3.3 Adopt TBB for All Parallelism**

Standardize on TBB's `task_group`, `parallel_for_each`, `concurrent_hash_map` instead of mixing `QThreadPool`, `std::thread`, and `OSD_ThreadPool`. TBB already handles work-stealing and thread-pool management.

---

## 6. UX / Interaction Redesign

### 6.1 Design Principles

1. **Progressive disclosure** — Simple operations require no panel hunting; advanced options behind expand buttons
2. **Context-first** — Right-click and in-canvas interactions before menu diving
3. **Consistent visual language** — Every icon, color, spacing follows a design token system
4. **Zero-mode** — Avoid modes where the same gesture does different things; prefer tools that auto-deactivate

### 6.2 Shell Layout (Target)

```
┌────────────────────────────────────────────────────────────┐
│ [QAT: Save|Undo|Redo|Print]     FreeCAD 2.0      [—][□][×]│
├────────────────────────────────────────────────────────────┤
│ [Home] [Model] [Sketch] [Assembly] [Sheet Metal] [Drawing]│
│ ┌──────────────────────────────────────────────────────┐   │
│ │Ribbon Panels: [Sketch] [Features] [Modify] [Insert] │   │
│ │ ┌─────┐┌─────┐┌─────┐┌─────┐┌─────┐┌─────┐        │   │
│ │ │ Pad ││Pckt ││Fill ││Chmf ││Mirror│ │Patt │        │   │
│ │ └─────┘└─────┘└─────┘└─────┘└─────┘└─────┘        │   │
│ └──────────────────────────────────────────────────────┘   │
├────────┬───────────────────────────────────────┬───────────┤
│ MODEL  │                                       │PROPERTIES │
│        │                                       │           │
│ ▼ Body │         3D VIEWPORT                   │ Length: 10│
│  ├ Sk1 │                                       │ Width:  5 │
│  ├ Pad1│                   [NaviCube]          │ Angle: 45°│
│  ├ Sk2 │                                       │           │
│  ├ Pckt│                                       │───────────│
│  └ Fill│                                       │TASK PANEL │
│        │                                       │(when feat │
│ ──┤──  │ ← Rollback bar                       │ editing)  │
│ ▼ Assy │                                       │           │
│  ├Link1│                                       │           │
│  └Link2│                                       │           │
├────────┴───────────────────────────────────────┴───────────┤
│ [Report] [Python Console] [Selection Filter]    Ready ▪    │
└────────────────────────────────────────────────────────────┘
```

### 6.3 Theme Token System

Replace all hard-coded colors with design tokens. Create `src/Gui/ThemeTokens.h`:

```cpp
namespace ThemeTokens {
    // Surfaces
    constexpr auto SurfacePrimary    = "surface.primary";    // Main bg
    constexpr auto SurfaceSecondary  = "surface.secondary";  // Panel bg
    constexpr auto SurfaceElevated   = "surface.elevated";   // Floating panels

    // Content
    constexpr auto ContentPrimary    = "content.primary";    // Main text
    constexpr auto ContentSecondary  = "content.secondary";  // Subtle text
    constexpr auto ContentDisabled   = "content.disabled";   // Greyed out

    // Accent
    constexpr auto AccentPrimary     = "accent.primary";     // Selection, links
    constexpr auto AccentHover       = "accent.hover";       // Hover state
    constexpr auto AccentActive      = "accent.active";      // Active/pressed

    // Status
    constexpr auto StatusError       = "status.error";       // Errors
    constexpr auto StatusWarning     = "status.warning";     // Warnings
    constexpr auto StatusSuccess     = "status.success";     // Success

    // 3D Viewport
    constexpr auto ViewportPreselect = "viewport.preselect"; // Hover highlight
    constexpr auto ViewportSelect    = "viewport.select";    // Selection color
    constexpr auto ViewportEdge      = "viewport.edge";      // Edge color
    constexpr auto ViewportBackground= "viewport.background";// Gradient
}
```

Token resolution chain: `User Override → Theme YAML → Built-in Default`

Already partially implemented via `StyleParameters::ParameterManager` with `BuiltInParameterSource`, `YamlParameterSource`, `UserParameterSource`. Need to extend to cover:
- All hard-coded `QColor` in `Tree.cpp`, `PropertyEditor.cpp`, `RibbonBar.cpp`
- All hard-coded `SbColor` in `SoFCUnifiedSelection.cpp`, `SoFCBackgroundGradient.cpp`
- All hard-coded `glColor` / `vec3` in GLSL shaders

### 6.4 Ribbon Bar Enhancement

Current `RibbonBar` implementation (125px height, large 32px / small 16px icons) is functional but lacks:

| Missing Feature | Inventor Reference | Implementation |
|----------------|-------------------|----------------|
| **Contextual tabs** | Appear when sketch/assembly active | `RibbonBar::showContextualTab(name, color)` |
| **Galleries** | Visual previews of thread types, materials | `RibbonGallery` widget with thumbnail grid |
| **Backstage view** | File → full-page panel for print/export/settings | `BackstageView` replacing simple File menu |
| **Keyboard tips** | Alt+key reveals keytips on all ribbon items | `RibbonKeyTip` overlay system |
| **Minimize/expand** | Double-click tab to toggle ribbon | Already possible, needs polish |
| **Search command bar** | Type to find any command | `CommandSearch` widget in ribbon area |

### 6.5 Model Tree Enhancements

**6.5.1 Rollback Bar**

Add a draggable horizontal bar in the model tree that sets the "active tip" — features below the bar are suppressed and greyed out:

```
▼ Body
  ├ Sketch001        ┐
  ├ Pad              │ Active (computed)
  ├ Sketch002        │
  ├ Pocket           ┘
  ═══════════════════ ← Rollback bar (draggable)
  ├ Fillet            ┐
  ├ Chamfer           │ Suppressed (greyed)
  └ Mirror            ┘
```

Implementation: `TreeWidget::paintEvent()` draws the bar, drag events call `Body::setTip(feature)`.

**6.5.2 Tree Item Context Actions**

Right-click context menu for every tree item:
- **Feature:** Edit, Suppress/Unsuppress, Delete, Move Up/Down, Insert Before
- **Body:** New Sketch, New Feature, Toggle Visibility, Rename
- **Assembly:** Add Part, Constrain, Exploded View

**6.5.3 Multi-Selection Operations**

Select multiple features → right-click → "Suppress All", "Delete All", "Group Into".

### 6.6 In-Canvas Interaction

**6.6.1 Smart Dimension**

When sketching, hovering near a line segment and pressing `D` (or clicking Smart Dimension tool) auto-creates the correct constraint type:
- Horizontal line → Horizontal distance
- Vertical line → Vertical distance
- Two points → Distance between
- Arc → Radius
- Two lines → Angle between

**6.6.2 3D Manipulation Gizmo**

For Pad, Pocket, and Extrude: an in-canvas arrow gizmo that directly controls the depth parameter via drag. Already partially implemented in `EditableDatumLabel` — extend to full 3D gizmo with:
- Arrow for linear dimensions
- Arc for angle dimensions
- Plane for sketch-plane picking

**6.6.3 Selection Feedback**

Current cyan preselect + green select (Inventor-style, already implemented). Add:
- **Selection count badge** on status bar: "3 faces selected"
- **Selection filter bar** at bottom: [Vertices | Edges | Faces | Solids] toggle buttons
- **Persistent selection highlighting** that survives workbench switches

### 6.7 Start Page Modernization

Current `StartView` with `FileCardView` and `FirstStartWidget` is good. Enhance:

| Enhancement | Implementation |
|------------|----------------|
| **Template gallery** | Show thumbnails of part templates (bolt, bracket, enclosure) |
| **Learning tracks** | Step-by-step tutorials embedded in start page |
| **Recent + Pinned** | Pin frequently-used files to top of recent list |
| **Workspace recovery** | "Restore last session" button to reopen all previously open documents |

---

## 7. Mechanical CAD Workflow Improvements

### 7.1 Sketch Workflow

**7.1.1 Auto-Constraint Inference**

When drawing geometry, auto-apply constraints based on proximity and intent:

| User Action | Auto-Constraint |
|-------------|----------------|
| Draw line near horizontal | Horizontal constraint |
| End point near existing point | Coincident constraint |
| Draw line parallel to existing | Parallel constraint |
| Draw arc tangent to line | Tangent constraint |
| Draw line at same length as existing | Equal constraint |

PlaneGCS already supports all these constraint types. The gap is in the **inference engine** that detects intent and proposes/applies constraints during drawing.

Implementation: `SketchAutoConstraintEngine` in `src/Mod/Sketcher/Gui/`:
```cpp
class SketchAutoConstraintEngine {
    struct Proposal {
        Sketcher::ConstraintType type;
        int geo1, geo2;
        float confidence;  // 0.0–1.0
    };
    std::vector<Proposal> analyze(const DrawingContext& ctx,
                                   const SbVec2f& cursorPos);
};
```

**7.1.2 Sketch Editing UX Polish**

| Current Issue | Fix |
|--------------|-----|
| Constraint icons overlap on complex sketches | Implement constraint icon layout algorithm with collision avoidance |
| No visual DOF indicator | Show unconstrained DOF as green arrows on under-constrained geometry |
| No "fully constrained" celebration | Status bar turns green, brief flash on sketch when fully constrained |
| Exiting sketch requires button click | Escape key once = deselect tool, twice = exit sketch |

### 7.2 Part Design Workflow

**7.2.1 Feature Reorder (Drag-to-Reorder)**

Allow dragging features in the tree to change execution order:
- Validate: feature cannot move before its dependencies
- Show insertion marker and validity indicator during drag
- Update `BaseFeature` links automatically
- Trigger recompute from the moved feature downward

Implementation: Override `TreeWidget::dropEvent()`, validate via `DependencyGraph`, call `Body::reorderFeature()`.

**7.2.2 Feature Configuration Table**

SolidWorks-style "Design Table" that drives multiple configurations:

| Configuration | Pad1.Length | Pocket1.Depth | Fillet1.Radius |
|--------------|-------------|---------------|----------------|
| Default      | 10 mm       | 5 mm          | 1 mm           |
| Heavy Duty   | 15 mm       | 8 mm          | 2 mm           |
| Lightweight  | 6 mm        | 3 mm          | 0.5 mm         |

Implementation: Leverage existing `Spreadsheet` workbench. Each row = configuration. Expressions bind parameters to cells. A `ConfigurationManager` switches active row and triggers recompute.

**7.2.3 Multi-Body Design**

Currently: `Body` enforces single-solid rule. Target:
- Allow multiple bodies in a `Part` container
- Body-to-body boolean operations
- Multi-body STEP export with proper solid grouping
- Body references across link boundaries

### 7.3 Assembly Workflow

**7.3.1 Assembly Solver — C++ Rewrite**

The current Python assembly solver is inadequate for production. Need a C++ constraint solver:

```cpp
class AssemblySolver {
public:
    enum class JointType {
        Fixed, Revolute, Prismatic, Cylindrical,
        Planar, Ball, Rack_Pinion, Screw, Gear
    };

    struct Joint {
        JointType type;
        ObjectId part1, part2;
        gp_Trsf transform1, transform2;  // Local coordinate systems
        // Constraint-specific params:
        double lowerLimit, upperLimit;     // For prismatic/revolute
    };

    struct SolveResult {
        bool converged;
        int iterations;
        double residual;
        std::vector<gp_Trsf> placements;  // Computed transforms
        std::vector<int> dofPerPart;       // Remaining DOF per part
    };

    SolveResult solve(const std::vector<Joint>& joints,
                       const std::vector<gp_Trsf>& initialGuess,
                       double tolerance = 1e-6);
};
```

**7.3.2 DOF Visualization**

After each solve, display remaining degrees of freedom per part:
- **Fully constrained (0 DOF):** Part shown normally
- **Under-constrained (>0 DOF):** Colored arrows/arcs showing remaining freedom directions
- **Over-constrained:** Red highlight with conflict report

**7.3.3 Assembly Exploded View**

Generate exploded views for documentation:
1. Select assembly
2. Click "Exploded View"
3. Drag individual parts outward along explosion vectors
4. Auto-generate explosion lines
5. Save as named view for TechDraw reference

### 7.4 Sheet Metal Workflow

Currently: No native sheet metal. Addon only (unmaintained).

Needed as a first-class workbench:

| Operation | Description |
|-----------|-------------|
| **Base flange** | Start from sketch profile + thickness |
| **Edge flange** | Add flanges to existing edges |
| **Bend** | Apply bend with configurable radius and K-factor |
| **Unfold** | Generate flat pattern from bent model |
| **Corner relief** | Auto-add corner reliefs at intersections |
| **Punch** | Library of punch tool shapes |
| **Flat pattern DXF** | Export unfolded pattern for laser/waterjet |

Implementation: New `Mod/SheetMetal` with C++ `SheetMetalFeature` classes inheriting `PartDesign::Feature`. Use OCCT's `BRepOffsetAPI_MakeThickSolid` and `BRepBuilderAPI_MakeFace` for unfolding.

### 7.5 Drawing / Documentation Workflow

**TechDraw Enhancements:**

| Enhancement | Current | Target |
|------------|---------|--------|
| **Auto-BOM** | Manual BOM table | Auto-generated from assembly, auto-updating |
| **Balloon notes** | Manual placement | Auto-place, auto-number, linked to BOM |
| **Revision clouds** | None | Cloud annotation tool for marking changes |
| **Section views** | Basic | Aligned, offset, broken-out, removed sections |
| **Detail views** | Basic | Auto-scaled, auto-labeled |
| **View projection speed** | Slow for large models | Parallel HLRBREP computation |

---

## 8. Enterprise Features

### 8.1 PDM Integration Hooks

FreeCAD will not build a PDM system, but must expose hooks for integration:

```python
# PDM Provider Interface
class PDMProvider:
    def check_out(self, file_path: str) -> bool: ...
    def check_in(self, file_path: str, comment: str) -> bool: ...
    def get_revision(self, file_path: str) -> str: ...
    def get_history(self, file_path: str) -> list[Revision]: ...
    def lock(self, file_path: str) -> bool: ...
    def unlock(self, file_path: str) -> bool: ...
    def is_checked_out(self, file_path: str) -> bool: ...
    def get_latest(self, file_path: str) -> str: ...

# Register provider
FreeCAD.registerPDMProvider(MyGitPDMProvider())
# or
FreeCAD.registerPDMProvider(MyVaultProvider())
```

Status bar shows lock/checkout status. File → Check In / Check Out actions when PDM is configured.

### 8.2 Multi-User Collaboration

**Phase 1: File-level locking** (6 months)
- PDM provider reports lock status
- FreeCAD opens locked files as read-only
- Status bar shows "Locked by [username]"

**Phase 2: Object-level locking** (12 months)
- Lock individual features within a shared document
- Concurrent editing of different bodies in same assembly
- Conflict resolution UI when locks collide

**Phase 3: Real-time collaboration** (24+ months)
- CRDT-based property synchronization
- Live cursor/selection sharing
- Requires significant architecture changes (out of scope for this plan)

### 8.3 Licensing & Deployment

| Feature | Implementation |
|---------|---------------|
| **Silent install** | MSI/deb/rpm packages with `/S` flags |
| **Group policy** | System.cfg read-only defaults, User.cfg overrides |
| **Centralized config** | JSON config URL for enterprise defaults |
| **Telemetry** | Opt-in usage analytics with privacy policy |
| **Crash reporting** | Minidump collection + upload (opt-in) |
| **Auto-update** | Check for updates on startup, admin-controlled channel (stable/beta/nightly) |

### 8.4 Standards Compliance

| Standard | Current | Target |
|----------|---------|--------|
| **STEP AP214** | Import/export via OCCT | TNP-preserving export, validate round-trip |
| **STEP AP242** | Partial | Full tessellation + PMI support |
| **IGES** | Import/export | Maintain (legacy format) |
| **IFC** | Via ifcopenshell | Improve BIM integration |
| **DXF/DWG** | Import/export | Improve TechDraw export fidelity |
| **3MF** | Basic | Full color/material support |
| **JT** | Reader module exists | Maintain |
| **glTF** | None | Add for web/AR/VR export |
| **USD** | None | Consider for collaboration/rendering pipelines |

### 8.5 Audit Trail

For regulated industries (aerospace, medical devices), log every model change:

```cpp
struct AuditEntry {
    QDateTime timestamp;
    QString username;
    QString action;       // "Property changed", "Feature added", "Recomputed"
    QString objectName;
    QString propertyName;
    QString oldValue;
    QString newValue;
    QString documentHash; // SHA-256 of document state
};
```

Store in `Document.xml` as `<AuditTrail>` section. Export as CSV/PDF for compliance.

---

## 9. Plugin / Automation Platform

### 9.1 Current Plugin Architecture

Workbenches are loaded via `InitGui.py`:
1. `FreeCADGuiInit.py` scans `src/Mod/` for `InitGui.py` files
2. Each defines a `Workbench` subclass with `Initialize()`, `GetClassName()`
3. `activate()` → `setupMenuBar()` → `setupToolBars()` → `setupDockWindows()`
4. Commands registered via `FreeCADGui.addCommand("Name", CommandObject)`

**Strengths:** Full Python access, hot-reload possible, community addons work
**Weaknesses:** No API versioning, no sandboxing, no dependency declaration, no plugin lifecycle

### 9.2 Target Plugin Platform

**9.2.1 Versioned API**

Introduce API version declarations:

```python
# package.xml
<freecad>
    <workbench>
        <name>MyWorkbench</name>
        <api-version min="2.0" max="2.99"/>
        <dependencies>
            <dependency name="Part" min-version="2.0"/>
        </dependencies>
    </workbench>
</freecad>
```

FreeCAD checks API compatibility at load time. Incompatible plugins are disabled with a clear message.

**9.2.2 Plugin Lifecycle Hooks**

```python
class MyWorkbench(Workbench):
    def onInstall(self):     # Called once after install
    def onUpdate(self):      # Called after addon update
    def onUninstall(self):   # Called before uninstall (cleanup)
    def onActivate(self):    # Called when user switches to this workbench
    def onDeactivate(self):  # Called when user switches away
    def onDocumentOpened(self, doc):  # Called when a document is opened
    def getPreferencePage(self):      # Return preference page widget
```

**9.2.3 Stable C++ Extension Points**

For performance-critical plugins, expose stable C++ APIs:

```cpp
// Public API headers in include/FreeCAD/
#include <FreeCAD/App/Document.h>        // Stable document API
#include <FreeCAD/App/Feature.h>         // Stable feature base
#include <FreeCAD/Gui/ViewProvider.h>    // Stable VP base
#include <FreeCAD/Gui/Command.h>         // Stable command base

// ABI-stable plugin entry point
extern "C" {
    FREECAD_PLUGIN_EXPORT PluginInfo getPluginInfo();
    FREECAD_PLUGIN_EXPORT void initPlugin(PluginContext& ctx);
    FREECAD_PLUGIN_EXPORT void cleanupPlugin();
}
```

**9.2.4 Plugin Sandboxing**

For untrusted addons:
- Run Python in a restricted subprocess with limited `sys.path`
- Disable `os.system`, `subprocess`, `socket` by default
- File access limited to document directory + addon directory
- Network access opt-in via user permission prompt

### 9.3 Macro / Script Improvements

| Feature | Current | Target |
|---------|---------|--------|
| **Macro recorder** | Records Python commands | Records with undo groups, comments |
| **Script editor** | Basic `PythonEditorView` | Syntax highlighting, autocomplete, breakpoints |
| **Script debugger** | External debugpy attach | Integrated step-through in FreeCAD |
| **Script library** | User macros folder | Searchable library with categories + tags |
| **Headless execution** | `FreeCADCmd` binary | Improved: JSON I/O, batch processing, exit codes |

### 9.4 REST API for External Integration

For CAM, ERP, and PLM integration:

```
GET    /api/v1/documents                       → list open documents
GET    /api/v1/documents/{id}/objects           → list objects in document
GET    /api/v1/documents/{id}/objects/{name}    → get object properties
PUT    /api/v1/documents/{id}/objects/{name}    → set object properties
POST   /api/v1/documents/{id}/recompute        → trigger recompute
GET    /api/v1/documents/{id}/export?format=step → export document
POST   /api/v1/commands/{name}                  → execute command
```

Implemented as a lightweight HTTP server in Python (`flask` or `aiohttp`) running in a FreeCAD thread, exposing the existing Python API over REST.

---

## 10. Refactoring Strategy

### 10.1 Phased Roadmap

```
PHASE 0: FOUNDATIONS               (Months 1–3)
├── Atomic status bits
├── Per-object shared_mutex
├── SignalQueue (batched signals)
├── Transaction lock protocol
├── OcctService wrapper (Part/PartDesign boolean ops)
└── Schema version in Document.xml

PHASE 1: PARALLEL RECOMPUTE        (Months 3–6)
├── DAG-based level-parallel recompute
├── Python feature serialization (GIL-aware)
├── Background recompute with progress UI
├── Cancel-recompute support
└── Performance regression test suite

PHASE 2: UX MODERNIZATION          (Months 4–8)
├── Theme token system (replace all hard-coded colors)
├── Rollback bar in model tree
├── Contextual ribbon tabs
├── Command search bar
├── Backstage view (File menu replacement)
├── Selection filter bar
└── Smart dimension tool

PHASE 3: ASSEMBLY ROBUSTNESS       (Months 6–10)
├── C++ assembly constraint solver
├── DOF visualization
├── Drag-placement workflow
├── Exploded view generator
├── Assembly BOM auto-generation
└── Large assembly performance (5000+ parts)

PHASE 4: ENTERPRISE HOOKS          (Months 8–12)
├── PDM provider interface
├── File-level locking
├── Audit trail logging
├── Plugin API versioning
├── Silent install / group policy
└── Crash reporting system

PHASE 5: WORKFLOW POLISH            (Months 10–18)
├── Sheet metal workbench
├── Configuration table (design table)
├── Sketch auto-constraint inference
├── Feature drag-to-reorder
├── TechDraw auto-BOM + balloons
└── STEP AP242 full compliance

PHASE 6: PLATFORM MATURITY          (Months 15–24)
├── REST API for external integration
├── Plugin sandboxing
├── Multi-user object-level locking
├── Performance: <3s cold start
├── Test coverage: 4000+ unit tests
└── Documentation: complete API reference
```

### 10.2 Migration Strategy: Strangler Fig Pattern

For large subsystem rewrites (e.g., Assembly solver, Thread safety), use the Strangler Fig pattern:

1. **Wrap**: Create a new interface that delegates to the old implementation
2. **Route**: New code uses the new interface, old code continues as-is
3. **Replace**: Implement the new backend behind the interface
4. **Remove**: Delete old implementation once all callers migrate

Example — OcctService:
```
Step 1: Create OcctService::fuse() that calls BRepAlgoAPI_Fuse directly
Step 2: Part::Boolean::execute() calls OcctService::fuse() instead of raw OCCT
Step 3: OcctService::fuse() adds exception handling, TNP mapping, parallel hints
Step 4: All direct OCCT boolean calls removed from module code
```

### 10.3 Backward Compatibility Rules

| Category | Rule |
|----------|------|
| **File format** | Old files always open in new FreeCAD (migration framework) |
| **Python API** | Deprecation warnings for 2 releases before removal |
| **C++ API** | Internal. No backward compat guarantee (except public plugin API) |
| **Preferences** | Migration function for renamed/restructured preferences |
| **Macro** | Macro compatibility layer translates old command names |

### 10.4 Feature Flags

Use compile-time and runtime feature flags for gradual rollout:

```cpp
// Compile-time (CMakeLists.txt)
option(FREECAD_PARALLEL_RECOMPUTE "Enable parallel recompute engine" OFF)

// Runtime (user.cfg)
// User parameter:BaseApp/Preferences/FeatureFlags/ParallelRecompute = true

// Code
if (FeatureFlags::isEnabled("ParallelRecompute")) {
    RecomputeEngine::parallelRecompute(dirty);
} else {
    Document::serialRecompute(dirty);
}
```

---

## 11. Repository / Module Reorganization

### 11.1 Current Structure Issues

1. **Flat module directory:** `src/Mod/` contains 28+ modules with no grouping
2. **Mixed languages:** C++ `App/` and Python commands in same module, no clear boundary
3. **No public API headers:** All headers are internal, no stable interface for plugins
4. **Test isolation:** Tests in `tests/` mirror `src/` but don't co-locate with modules
5. **Build artifacts:** `build/debug/` at top level, mixed with source

### 11.2 Target Structure

```
FreeCAD/
├── CMakeLists.txt
├── CMakePresets.json
├── pixi.toml
├── build/                          # Build artifacts (gitignored)
│
├── include/                        # PUBLIC API HEADERS (stable)
│   └── FreeCAD/
│       ├── App/
│       │   ├── Document.h
│       │   ├── DocumentObject.h
│       │   ├── Property.h
│       │   └── Feature.h
│       ├── Gui/
│       │   ├── Command.h
│       │   ├── ViewProvider.h
│       │   └── Workbench.h
│       └── Plugin/
│           └── PluginAPI.h
│
├── src/
│   ├── App/                        # Core data model (unchanged)
│   ├── Base/                       # Utilities (unchanged)
│   ├── Gui/                        # GUI framework (unchanged)
│   ├── Main/                       # Entry points (unchanged)
│   │
│   └── Mod/
│       ├── Core/                   # Core modules (ship with FreeCAD)
│       │   ├── Part/
│       │   ├── PartDesign/
│       │   ├── Sketcher/
│       │   ├── Assembly/
│       │   ├── TechDraw/
│       │   ├── Material/
│       │   └── Spreadsheet/
│       │
│       ├── Analysis/               # Simulation modules
│       │   ├── FEM/
│       │   ├── FlowStudio/
│       │   └── Mesh/
│       │
│       ├── Manufacturing/          # CAM / fabrication
│       │   ├── CAM/
│       │   └── SheetMetal/         # NEW
│       │
│       ├── Architecture/           # BIM / construction
│       │   ├── BIM/
│       │   └── Draft/
│       │
│       └── Utility/                # Supporting modules
│           ├── Import/
│           ├── Start/
│           ├── AddonManager/
│           ├── Help/
│           └── Test/
│
├── tests/                          # Test co-located with modules
│   ├── unit/                       # Fast unit tests (<1s each)
│   │   ├── App/
│   │   ├── Gui/
│   │   └── Mod/
│   │       ├── Part/
│   │       ├── PartDesign/
│   │       └── Sketcher/
│   │
│   ├── integration/                # Multi-module tests (1–30s each)
│   │   ├── PartDesign_workflow/
│   │   ├── Assembly_workflow/
│   │   └── STEP_roundtrip/
│   │
│   ├── performance/                # Performance regression tests
│   │   ├── recompute_benchmark.cpp
│   │   ├── assembly_benchmark.cpp
│   │   └── rendering_benchmark.cpp
│   │
│   └── data/                       # Test fixtures (FCStd, STEP, STL)
│
├── docs/
│   ├── architecture/               # Architecture Decision Records (ADRs)
│   ├── api/                        # Generated API docs
│   ├── contributing/               # Contributor guides
│   └── migration/                  # Version migration guides
│
└── tools/
    ├── scripts/                    # Build/CI scripts
    ├── linters/                    # Custom lints (dependency checker, etc.)
    └── generators/                 # Code generators (Python stubs, etc.)
```

### 11.3 Migration Plan

**Phase 1 (Non-Breaking):** Create `include/FreeCAD/` with symlinked public headers. No moves.

**Phase 2 (Internal Reorg):** Group modules under `Core/`, `Analysis/`, `Manufacturing/`, `Architecture/`, `Utility/` by updating CMakeLists.txt include paths. Update `FreeCADGuiInit.py` module scanner to recurse subdirectories.

**Phase 3 (Test Restructure):** Move tests from flat `tests/src/Mod/*/` to structured `tests/unit/Mod/*/`, `tests/integration/`, `tests/performance/`.

### 11.4 CMake Module Conventions

Every module must follow:

```cmake
# src/Mod/Core/Part/CMakeLists.txt

add_library(Part SHARED
    App/PartFeature.cpp
    App/TopoShape.cpp
    # ...
)

target_include_directories(Part
    PUBLIC  ${CMAKE_SOURCE_DIR}/include
    PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}
)

target_link_libraries(Part
    PUBLIC  FreeCADApp FreeCADBase
    PRIVATE ${OCC_LIBRARIES}
)

# Tests
if(BUILD_TESTING)
    add_subdirectory(tests)
endif()
```

---

## 12. Quality Engineering & Test Strategy

### 12.1 Test Pyramid

```
                    ╱╲
                   ╱  ╲
                  ╱ E2E╲          ~20 tests
                 ╱ (GUI)╲         Full scenarios
                ╱────────╲
               ╱Integration╲      ~200 tests
              ╱  (multi-mod) ╲    Workflow tests
             ╱────────────────╲
            ╱    Unit Tests     ╲  ~4000 tests
           ╱  (per-class/func)  ╲  Fast, isolated
          ╱──────────────────────╲
         ╱    Static Analysis     ╲ Clang-Tidy, cppcheck
        ╱──────────────────────────╲
```

### 12.2 Unit Test Plan by Module

| Module | Current Tests | Target Tests | Key test types |
|--------|--------------|-------------|---------------|
| `App::Document` | 6 (recompute) | 200+ | Create/delete, undo/redo, recompute ordering, expression eval, serialization round-trip |
| `App::Property` | 0 | 300+ | Every property type: set/get, serialize, expression binding, undo, copy, deep copy |
| `App::Expression` | 0 | 200+ | Parser edge cases, unit conversion, circular detection, cross-document refs |
| `Gui::Selection` | 0 | 100+ | Add/remove/clear, multi-document, sub-element, preselection, gates |
| `Gui::Command` | 0 | 50+ | Registration, dispatch, undo/redo integration, macro recording |
| `Part::TopoShape` | 0 | 300+ | Boolean ops, fillet, chamfer, pipe, loft, TNP preservation |
| `PartDesign::Feature` | 10 | 200+ | Pad, pocket, fillet, chamfer, mirror, pattern + robustness |
| `Sketcher` | 0 | 400+ | Every constraint type, solver convergence, auto-constraint, over-constrained detection |
| `Assembly` | 9 | 150+ | Every joint type, solver convergence, DOF calculation, exploded view |
| `TechDraw` | 0 | 100+ | View projection, BOM generation, dimension placement |
| `Material` | 0 | 50+ | Library loading, UUID lookup, property access |

### 12.3 Integration Test Scenarios

```
SCENARIO: Part Design Workflow (Bolt)
  GIVEN a new document
  WHEN I create a sketch with a circle
  AND pad it 20mm
  AND add a hexagonal sketch on top face
  AND pocket it 5mm
  AND fillet all vertical edges at 0.5mm
  AND chamfer the top edge at 1mm
  THEN the model has the correct topology
  AND element maps survive recompute
  AND STEP export round-trips with <0.01mm deviation

SCENARIO: Assembly Workflow (Bracket Assembly)
  GIVEN two imported STEP parts (bracket + bolt)
  WHEN I create an assembly
  AND insert both parts as links
  AND constrain bolt hole to bracket hole (cylindrical)
  AND constrain bolt head to bracket face (planar)
  THEN assembly solves with 0 DOF
  AND parts are positioned correctly
  AND BOM lists both parts with quantities

SCENARIO: Multi-Body with Expressions
  GIVEN a spreadsheet with Length=10, Width=5
  WHEN I create a body with a pad using =Sheet.Length
  AND a second body with a pad using =Sheet.Width
  AND modify Sheet.Length to 20
  THEN both bodies recompute correctly
  AND the pad in body1 now has Length=20
```

### 12.4 Fuzz Testing

For OCCT-wrapping code that processes external geometry:

```cpp
// STEP import fuzz target
extern "C" int LLVMFuzzerTestOneInput(const uint8_t* data, size_t size) {
    std::string stepContent(reinterpret_cast<const char*>(data), size);
    try {
        OcctService::importSTEP(stepContent);
    } catch (const OcctError&) {
        // Expected — OCCT rejects invalid geometry
    }
    return 0;  // No crash = pass
}
```

Targets: STEP import, IGES import, DXF import, FCStd restore, Expression parser.

### 12.5 Performance Regression Tests

Using Google Benchmark:

```cpp
static void BM_Recompute100Features(benchmark::State& state) {
    auto doc = createTestDocument100Features();
    for (auto _ : state) {
        doc->touchAll();
        doc->recompute();
    }
}
BENCHMARK(BM_Recompute100Features)->Unit(benchmark::kMillisecond);

static void BM_STEPExport1000Faces(benchmark::State& state) {
    auto shape = createTestShape1000Faces();
    for (auto _ : state) {
        OcctService::exportSTEP(shape, "/dev/null");
    }
}
BENCHMARK(BM_STEPExport1000Faces)->Unit(benchmark::kMillisecond);

static void BM_AssemblySolve500Parts(benchmark::State& state) {
    auto assembly = createTestAssembly500Parts();
    for (auto _ : state) {
        AssemblySolver::solve(assembly);
    }
}
BENCHMARK(BM_AssemblySolve500Parts)->Unit(benchmark::kMillisecond);
```

CI pipeline fails if any benchmark regresses >10% from baseline.

### 12.6 Static Analysis Pipeline

| Tool | Purpose | Configuration |
|------|---------|---------------|
| **Clang-Tidy** | C++ linting | `modernize-*`, `performance-*`, `bugprone-*`, `cppcoreguidelines-*` |
| **cppcheck** | Bug detection | `--enable=all --suppress=missingInclude` |
| **Coverity** | Deep static analysis | Weekly scan on main branch |
| **flake8 + mypy** | Python linting + typing | All `Mod/` Python files |
| **Dependency checker** | Module dependency violations | Custom script: `App → Gui` = error |

### 12.7 CI Pipeline

```yaml
# .github/workflows/ci.yml (conceptual)
jobs:
  build:
    matrix:
      os: [ubuntu-22.04, windows-2022, macos-13]
      build-type: [Debug, Release]
    steps:
      - pixi install
      - cmake --preset conda-{os}-{type}
      - ninja -C build/{type}
      - ctest --test-dir build/{type} --output-on-failure

  static-analysis:
    steps:
      - clang-tidy src/**/*.cpp
      - cppcheck src/
      - flake8 src/Mod/
      - python tools/linters/dependency_checker.py

  performance:
    runs-on: self-hosted  # Deterministic hardware
    steps:
      - build Release
      - benchmark --benchmark_out=results.json
      - python tools/scripts/benchmark_compare.py baseline.json results.json
```

---

## 13. Performance Engineering

### 13.1 Critical Performance Paths

| Path | Current Bottleneck | Target | Approach |
|------|-------------------|--------|----------|
| **Cold start** | Module loading, Python init | <3s | Lazy-load workbenches, precompile .pyc, defer Coin3D init |
| **Recompute (100 features)** | Serial execution | 3–5× faster | Parallel DAG recompute (Phase 1) |
| **Large assembly render** | Coin3D traversal | 5000 parts @ 30 FPS | GPU frustum culling, LOD (already Phase C), instancing |
| **STEP import** | Serial parsing + tessellation | 2× faster | Parallel tessellation via TBB (partially done with OSD_ThreadPool) |
| **Sketch solving** | PlaneGCS sequential | 2× faster | Profile and optimize hot paths, SIMD for constraint evaluation |
| **TechDraw projection** | Serial HLRBREP | 5× faster | Parallel projection, caching, incremental updates |
| **File save** | Serial XML + ZIP | 50% faster | Parallel property serialization, background save |
| **Undo/Redo** | Full copy of changed properties | 10× less memory | Copy-on-write property storage |

### 13.2 Memory Optimization

**13.2.1 Shape Sharing**

OCCT `TopoDS_Shape` is already reference-counted internally. Ensure FreeCAD doesn't create unnecessary copies:

```cpp
// BAD: Copy shape
TopoDS_Shape result = baseShape;  // Increments refcount (cheap but still...)

// GOOD: Move shape
TopoDS_Shape result = std::move(baseShape);  // Zero-copy
```

Audit all `PropertyPartShape::setValue()` calls to ensure move semantics.

**13.2.2 Tessellation Cache**

Currently: Tessellation regenerated on every view update. Target:
- Cache tessellated mesh alongside BRep shape
- Invalidate only when shape changes (not on color/display-mode change)
- Store tessellation in FCStd file for instant reload

**13.2.3 Lazy Property Loading**

For large documents, don't deserialize all properties on open:

```cpp
class LazyProperty : public Property {
    mutable std::optional<Value> _cached;
    size_t _fileOffset;  // Offset in Document.xml for lazy load

    const Value& get() const {
        if (!_cached) {
            _cached = deserializeFromFile(_fileOffset);
        }
        return *_cached;
    }
};
```

### 13.3 Rendering Performance

**Already Implemented (Phases A–F):**
- SSAO with configurable radius/intensity
- Bloom with threshold/intensity
- Vignette overlay
- Screen-Space Contact Shadows (SSCS)
- CAS Sharpening
- Adaptive rendering (skip post-FX during interaction)
- Frustum culling (Phase C)
- LOD system (Phase C)

**Still Needed:**

| Feature | Impact | Complexity |
|---------|--------|-----------|
| **GPU instancing** | 10× for repeated parts in assemblies | Medium — Coin3D SoMultipleInstance or custom GL path |
| **Occlusion culling** | 2–3× for interior scenes | Medium — hierarchical Z-buffer |
| **Mesh simplification cache** | Faster LOD transitions | Low — cache simplified meshes |
| **Async texture upload** | Smoother material previews | Low — PBO streaming |
| **Deferred rendering** | Better lighting for many lights | High — requires Coin3D bypass |

### 13.4 Profiling Infrastructure

| Tool | Usage |
|------|-------|
| **Tracy** | Frame profiler (integrated into Coin3D render loop) |
| **Intel VTune** | CPU hotspot analysis for recompute |
| **RenderDoc** | GPU frame capture for shader optimization |
| **Valgrind/ASan** | Memory leak detection (already CMake options) |
| **perf** | Linux system profiling |
| **Windows Performance Analyzer** | ETW-based tracing |

Add profiling macros:
```cpp
FREECAD_PROFILE_SCOPE("Recompute");
FREECAD_PROFILE_SCOPE("STEP_Import");
FREECAD_PROFILE_SCOPE("Tessellation");
```

Compile-time switch: `FREECAD_ENABLE_PROFILING` (off in Release, on in Profile builds).

---

## 14. Governance / Product Management

### 14.1 Decision-Making Framework

| Decision Type | Authority | Process |
|--------------|-----------|---------|
| **Architecture** (new subsystem, major API change) | Architecture Review Board (3–5 senior devs) | ADR (Architecture Decision Record) in `docs/architecture/` |
| **Feature** (new workbench feature, UX change) | Module maintainer + UX review | RFC on forum → Design doc → PR |
| **Bug fix** | Any contributor | PR with test demonstrating fix |
| **Dependency update** | Build maintainer | Compatibility test → PR |
| **Release** | Release manager | Feature freeze → RC → stabilization → release |

### 14.2 Architecture Decision Records (ADRs)

Every significant architectural choice documented:

```markdown
# ADR-001: Parallel Recompute Engine

## Status: Accepted

## Context
FreeCAD's recompute is serial, causing 15–45s delays on complex models.

## Decision
Implement level-parallel DAG-based recompute using TBB task_group.
Python features will be serialized via GIL.

## Consequences
- Requires per-object shared_mutex (Phase 0)
- Requires atomic status bits (Phase 0)
- Requires SignalQueue for main-thread signal delivery
- Python features cannot benefit from parallelism (GIL limitation)
- Risk: race conditions in under-tested code paths
```

### 14.3 Release Cadence

| Channel | Cadence | Purpose |
|---------|---------|---------|
| **Nightly** | Daily | Automated build for CI/testing |
| **Beta** | Monthly | Feature preview for early adopters |
| **Stable** | Quarterly | Production release for users |
| **LTS** | Annual | Long-term support (2 years of security fixes) |

### 14.4 Contributor Onboarding

| Resource | Purpose |
|----------|---------|
| `docs/contributing/GETTING_STARTED.md` | Build instructions, first-PR guide |
| `docs/contributing/ARCHITECTURE.md` | System overview with diagrams |
| `docs/contributing/CODE_STYLE.md` | C++ and Python style guide |
| `docs/contributing/TESTING.md` | How to write and run tests |
| `docs/contributing/MODULE_GUIDE.md` | How to create a new workbench module |
| `good-first-issue` label | Curated list of beginner-friendly issues |

### 14.5 Metrics Dashboard

Track project health:

| Metric | Source | Target |
|--------|--------|--------|
| Build time | CI pipeline | <10 min (incremental) |
| Test pass rate | CTest results | >99.5% |
| Code coverage | gcov/llvm-cov | >60% (new code: >80%) |
| Open bug count | Issue tracker | <200 (P0/P1: <20) |
| PR review time | GitHub metrics | <3 days median |
| Crash rate | Telemetry | <0.1 per 100 ops |
| Start time | Benchmark | <3s cold, <1s warm |

---

## 15. Risk Register

### Top 25 Risks

| # | Risk | Probability | Impact | Severity | Mitigation |
|---|------|------------|--------|----------|------------|
| 1 | **OCCT race conditions in parallel recompute** — OCCT shapes may share internal state that races under concurrent builds | HIGH | HIGH | **CRITICAL** | OcctService isolation layer; deep-copy shapes when dispatching to parallel workers; stress test with TSan enabled |
| 2 | **Python GIL prevents parallel speedup** — Many features are Python-based, cannot run in parallel | HIGH | HIGH | **CRITICAL** | Classify features as C++-parallel-safe vs Python-serial; phase Python features into sub-interpreter isolation (Python 3.12+ subinterpreters) |
| 3 | **Coin3D rendering ceiling for large assemblies** — Scene graph traversal is O(n) per frame | HIGH | HIGH | **CRITICAL** | Already have frustum culling + LOD; add GPU instancing; evaluate Coin3D SoMultipleInstance; long-term: consider filament/wgpu for assembly viewport |
| 4 | **TNP regression during refactoring** — Element map encoding is fragile; changes to Part operations could break mapped names | MEDIUM | HIGH | **HIGH** | Dedicated TNP integration test suite with golden files; CI fails if any mapped name changes unexpectedly; ChamferTNP-style tests for every operation |
| 5 | **Plugin API breakage alienates community** — Any API change breaks existing addons | MEDIUM | HIGH | **HIGH** | Versioned plugin API; deprecation warnings for 2 releases; automated compatibility checker in CI; community addon test suite |
| 6 | **Undo/Redo corruption with parallel recompute** — Concurrent property modifications can corrupt transaction log | MEDIUM | HIGH | **HIGH** | Transaction lock protocol: parallel recompute holds shared lock, undo/redo holds exclusive lock; test with concurrent undo+recompute |
| 7 | **File format migration failures** — Schema versioning introduces complexity; old files may not migrate correctly | MEDIUM | MEDIUM | **HIGH** | Comprehensive migration test suite with files from every major version; always write latest schema, read any version ≥ MinReaderVersion |
| 8 | **Assembly solver instability** — C++ constraint solver may not converge for all joint configurations | MEDIUM | HIGH | **HIGH** | Extensive test coverage for every joint type combination; fallback to iterative refinement; user-visible "not converged" states |
| 9 | **Memory explosion with large assemblies** — 5000 parts × (BRep + tessellation + element map) = many GB | MEDIUM | MEDIUM | **MEDIUM** | Lazy property loading; shape sharing via links (not copies); tessellation caching with configurable LOD; memory budget warnings |
| 10 | **Contributor burnout** — Massive refactoring plan may overwhelm volunteer contributors | MEDIUM | HIGH | **HIGH** | Phase work into independent, mergeable chunks; assign clear ownership per phase; celebrate milestones; reduce review bottlenecks |
| 11 | **Qt6 / PySide6 incompatibility** — Qt updates may break UI behavior | LOW | MEDIUM | **MEDIUM** | Pin Qt version in pixi.toml; test on target Qt version in CI; maintain Qt compatibility macros |
| 12 | **Cross-platform regression** — Changes tested on Windows may break Linux/macOS | MEDIUM | MEDIUM | **MEDIUM** | CI matrix includes all three platforms; platform-specific tests for GPU, file paths, threading |
| 13 | **Expression engine circular dependency detection failure** — New property dependencies may not be detected | LOW | HIGH | **MEDIUM** | Unit test all dependency graph scenarios; add depth limit to prevent infinite recursion; fuzz test expression parser |
| 14 | **Ribbon bar usability regression** — Adding contextual tabs, galleries may confuse users accustomed to classic menus | MEDIUM | MEDIUM | **MEDIUM** | Maintain classic toolbar option; A/B testing with user surveys; gradual rollout behind feature flag |
| 15 | **STEP export fidelity degradation** — Changes to OcctService wrapping may alter export behavior | LOW | HIGH | **MEDIUM** | Round-trip test suite: import STEP → export STEP → compare geometry; deviation threshold <0.01mm |
| 16 | **Dark mode incomplete coverage** — Replacing hard-coded colors is tedious; may miss edge cases | HIGH | LOW | **MEDIUM** | Automated dark mode screenshot tests; CI comparison against golden screenshots; community bug reports |
| 17 | **Build time explosion** — Adding 4000+ tests, profiling, and static analysis increases CI time | MEDIUM | MEDIUM | **MEDIUM** | Parallelize CI jobs; use ccache (already configured); run static analysis on separate schedule; test sharding |
| 18 | **Sketch auto-constraint false positives** — Inference engine may apply wrong constraints | MEDIUM | MEDIUM | **MEDIUM** | Confidence threshold; undo-on-escape; visual preview before confirming; user-tunable sensitivity |
| 19 | **PDM provider interface incompleteness** — Different PDM systems have different capabilities | MEDIUM | LOW | **LOW** | Design interface as minimal; providers declare capabilities; FreeCAD gracefully degrades for missing capabilities |
| 20 | **Sheet metal unfold accuracy** — OCCT unfolding may not match commercial tools | MEDIUM | MEDIUM | **MEDIUM** | Validate against known test cases from manufacturing; configurable K-factor; user override for bend deduction |
| 21 | **REST API security** — Exposing HTTP API creates attack surface | MEDIUM | HIGH | **HIGH** | Bind to localhost only; require API key; configurable enable/disable; rate limiting; no sensitive data exposure |
| 22 | **Thread-safe preference access** — `ParameterGrp` is not thread-safe; parallel recompute may read preferences concurrently | MEDIUM | MEDIUM | **MEDIUM** | Cache preferences in thread-local storage; read-only access during recompute; write only on main thread |
| 23 | **Plugin sandboxing escape** — Python subprocess sandboxing may be bypassed | LOW | HIGH | **MEDIUM** | Defense in depth: subprocess isolation + restricted sys.path + seccomp/AppArmor on Linux; code review for trusted addons |
| 24 | **Configuration table complexity** — Design table feature must handle missing cells, type mismatches, circular references | MEDIUM | LOW | **LOW** | Validate on switch; report errors per-cell; fallback to default configuration |
| 25 | **Audit trail performance overhead** — Logging every property change slows operations | LOW | MEDIUM | **LOW** | Opt-in audit trail; batch log entries; async write; configurable verbosity level |

### Risk Heat Map

```
              ┌──────────────────────────────────┐
              │           IMPACT                  │
              │   LOW      MEDIUM      HIGH       │
  ┌───────────├──────────┬──────────┬─────────────┤
  │    HIGH   │  #16     │ #10,#12  │ #1,#2,#3    │
  │           │          │          │             │
P │  MEDIUM   │  #24     │#9,#14,   │#4,#5,#6,#7,│
R │           │          │#17,#18,  │ #8,#21      │
O │           │          │#20,#22   │             │
B │           │          │          │             │
  │    LOW    │  #19,#25 │ #11,#23  │ #13,#15     │
  │           │          │          │             │
  └───────────┴──────────┴──────────┴─────────────┘
```

---

## 16. Final Deliverables

### 16.1 Deliverable Checklist

| # | Deliverable | Phase | Format | Owner |
|---|------------|-------|--------|-------|
| D1 | **Thread-safe document model** | 0 | C++ code: atomic bits, shared_mutex, SignalQueue | Core team |
| D2 | **OcctService wrapper** | 0 | C++ library: `src/App/OcctService/` | Core team |
| D3 | **Schema-versioned file format** | 0 | C++ code + migration registry | Core team |
| D4 | **Parallel recompute engine** | 1 | C++ code: DAG scheduler with TBB | Core team |
| D5 | **Performance regression test suite** | 1 | Google Benchmark tests + CI integration | QA team |
| D6 | **Theme token system** | 2 | C++ tokens + YAML themes + migration of all hard-coded colors | UX team |
| D7 | **Rollback bar** | 2 | C++ TreeWidget modification | Gui team |
| D8 | **Contextual ribbon tabs** | 2 | C++ RibbonBar extension + workbench adapters | Gui team |
| D9 | **Command search bar** | 2 | C++ CommandSearch widget | Gui team |
| D10 | **C++ assembly solver** | 3 | C++ library in `Mod/Assembly/App/Solver/` | Assembly team |
| D11 | **DOF visualization** | 3 | C++ ViewProvider overlays | Assembly team |
| D12 | **Exploded view generator** | 3 | C++ + Python in Assembly module | Assembly team |
| D13 | **PDM provider interface** | 4 | Python ABC + C++ hooks | Platform team |
| D14 | **Plugin API v2.0** | 4 | Public API headers + versioning system | Platform team |
| D15 | **Audit trail system** | 4 | C++ logging in Document | Platform team |
| D16 | **Sheet metal workbench** | 5 | C++ module `Mod/SheetMetal/` | Feature team |
| D17 | **Configuration table** | 5 | C++ + Spreadsheet integration | Feature team |
| D18 | **Sketch auto-constraint** | 5 | C++ inference engine in Sketcher | Sketcher team |
| D19 | **TechDraw auto-BOM** | 5 | C++ + Python in TechDraw | Drawing team |
| D20 | **REST API** | 6 | Python HTTP server | Platform team |
| D21 | **4000+ unit test suite** | 6 | GTest + Python pytest | All teams |
| D22 | **Plugin sandboxing** | 6 | Python subprocess isolation | Platform team |
| D23 | **Architecture documentation** | Ongoing | ADRs in `docs/architecture/` | All teams |
| D24 | **API reference** | Ongoing | Doxygen + Sphinx auto-generated | All teams |

### 16.2 Success Criteria

The modernization is considered successful when:

1. **Performance:** 100-feature body recomputes in <5 seconds (measured by D5 benchmark suite)
2. **Scalability:** 5000-part assembly renders at >30 FPS (measured by rendering benchmark)
3. **Reliability:** Crash rate <0.1 per 100 operations over 30-day telemetry window
4. **Quality:** >60% C++ code coverage, >80% for new code, <20 P0/P1 open bugs
5. **Compatibility:** All files from FreeCAD 0.21+ open correctly (migration test suite passes)
6. **Plugin Stability:** Zero addon breakage when upgrading between minor versions (addon CI gate)
7. **UX Consistency:** 100% theme token coverage, zero hard-coded colors in dark mode screenshot diff
8. **Cold Start:** <3 seconds from double-click to usable viewport (measured on reference hardware)

### 16.3 Reference Hardware for Benchmarks

| Tier | Specification | Use Case |
|------|--------------|----------|
| **Minimum** | 4-core CPU, 8 GB RAM, Intel UHD 630 | Office workstation, basic parts |
| **Recommended** | 8-core CPU, 32 GB RAM, NVIDIA RTX 3060 | Complex parts, small assemblies |
| **Performance** | 16-core CPU, 64 GB RAM, NVIDIA RTX 4080 | Large assemblies (5000+ parts) |

All benchmarks report results for all three tiers. CI runs on "Recommended" equivalent.

### 16.4 Milestone Timeline

```
Month  1 ──── Phase 0: Thread-safe foundations ────────── D1, D2, D3
Month  3 ──── Phase 1: Parallel recompute ─────────────── D4, D5
Month  4 ──── Phase 2 start: UX modernization begins ──── D6, D7, D8, D9
Month  6 ──── Phase 3 start: Assembly solver begins ───── D10, D11, D12
Month  8 ──── Phase 2 complete, Phase 4 start: Enterprise D13, D14, D15
Month 10 ──── Phase 3 complete, Phase 5 start: Workflows ─ D16, D17, D18, D19
Month 12 ──── Phase 4 complete ─────────────────────────── Checkpoint: v2.0 Beta
Month 15 ──── Phase 5 complete, Phase 6 start ─────────── D20, D21, D22
Month 18 ──── Phase 5 polish ──────────────────────────── D23, D24
Month 24 ──── Phase 6 complete ─────────────────────────── v2.0 Stable Release
```

---

## Appendix A: Key File Reference

| Component | Primary Source File(s) |
|-----------|----------------------|
| Document Model | `src/App/Document.h`, `src/App/DocumentObject.h`, `src/App/Property.h` |
| Property System | `src/App/PropertyContainer.h`, `src/App/PropertyStandard.h`, `src/App/PropertyLinks.h` |
| Expression Engine | `src/App/Expression.h`, `src/App/ExpressionParser.h`, `src/App/ObjectIdentifier.h` |
| Link System | `src/App/Link.h`, `src/App/LinkBaseExtension.h` |
| TNP / Element Map | `src/App/MappedElement.h`, `src/App/MappedName.h`, `src/App/IndexedName.h` |
| File Persistence | `src/App/Document.cpp` (Save/Restore), `src/Base/Writer.h`, `src/Base/Persistence.h` |
| Command System | `src/Gui/Command.h`, `src/Gui/CommandManager.h` |
| Workbench System | `src/Gui/Workbench.h`, `src/Gui/FreeCADGuiInit.py` |
| Main Window | `src/Gui/MainWindow.h` |
| 3D Viewer | `src/Gui/View3DInventorViewer.h`, `src/Gui/SoFCPostProcessing.h` |
| Selection System | `src/Gui/Selection/Selection.h`, `src/Gui/Selection/SelectionObject.h` |
| Task Panel | `src/Gui/TaskView/TaskView.h`, `src/Gui/TaskView/TaskDialog.h` |
| Ribbon Bar | `src/Gui/RibbonBar.h` |
| Tree View | `src/Gui/TreeView.h`, `src/Gui/Tree.h` |
| Property Editor | `src/Gui/propertyeditor/PropertyEditor.h` |
| Toolbar / Menu | `src/Gui/ToolBarManager.h`, `src/Gui/MenuManager.h` |
| Theme System | `src/Gui/Application.cpp` (L2704+), `StyleParameters::ParameterManager` |
| Navigation | `src/Gui/Navigation/NavigationStyle.h`, `InventorNavigationStyle.cpp` |
| Part Feature | `src/Mod/Part/App/PartFeature.h`, `src/Mod/Part/App/TopoShape.h` |
| PartDesign Feature | `src/Mod/PartDesign/App/Feature.h`, `src/Mod/PartDesign/App/Body.h` |
| Sketch Solver | `src/Mod/Sketcher/App/planegcs/GCS.h`, `src/Mod/Sketcher/App/Sketch.h` |
| Assembly | `src/Mod/Assembly/JointObject.py`, `src/Mod/Assembly/CommandCreateJoint.py` |
| Material System | `src/Mod/Material/App/MaterialManager.h`, `src/Mod/Material/App/PropertyMaterial.h` |
| Preferences | `src/Base/Parameter.h` |
| Addon Manager | `src/Mod/AddonManager/Addon.py` |
| Build System | `CMakeLists.txt`, `pixi.toml`, `CMakePresets.json` |
| Post-Processing | `src/Gui/SoFCPostProcessing.h/.cpp`, GLSL shaders in Gui resources |
| Start Page | `src/Mod/Start/Gui/StartView.h` |

## Appendix B: Glossary

| Term | Definition |
|------|-----------|
| **ADR** | Architecture Decision Record — documented rationale for architectural choices |
| **BRep** | Boundary Representation — geometry stored as faces, edges, vertices |
| **DAG** | Directed Acyclic Graph — dependency graph for feature recompute ordering |
| **DOF** | Degrees of Freedom — remaining unconstrained motion in an assembly |
| **FCStd** | FreeCAD Standard file format — ZIP archive containing XML + binary data |
| **GIL** | Global Interpreter Lock — Python threading limitation |
| **LOD** | Level of Detail — rendering optimization using simplified geometry at distance |
| **OCCT** | OpenCASCADE Technology — open-source geometry kernel |
| **PlaneGCS** | Plane Geometric Constraint Solver — FreeCAD's 2D sketch solver |
| **PMI** | Product Manufacturing Information — annotations in 3D model (GD&T, notes) |
| **QAT** | Quick Access Toolbar — small toolbar above ribbon tabs |
| **SSAO** | Screen-Space Ambient Occlusion — rendering technique for contact shadows |
| **SSCS** | Screen-Space Contact Shadows — shadow technique for small gaps |
| **TBB** | Threading Building Blocks — Intel parallel programming library |
| **TNP** | Topological Naming Problem — instability of face/edge indices across recompute |
| **TSan** | Thread Sanitizer — runtime tool for detecting data races |

---

*End of document. This plan is a living document — update as implementation reveals new constraints and opportunities.*
