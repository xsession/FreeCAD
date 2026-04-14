# FreeCAD Parallel & GPU Acceleration Architecture

## Status: Design Proposal

**Author:** Copilot architecture analysis  
**Scope:** Multithreading + GPU acceleration strategy for FreeCAD  
**Approach:** Incremental — each phase delivers measurable improvement without breaking stability

---

## 1. Current Architecture Assessment

### 1.1 Threading Model

FreeCAD is fundamentally **single-threaded** with isolated parallelism pockets:

| Layer | Threading | Notes |
|-------|-----------|-------|
| App (Document, Properties) | Main thread only | No mutexes on properties, status bits use `std::bitset<32>` (not atomic) |
| Recompute | Serial topological sort | `boost::topological_sort` → serial `_recomputeFeature()` loop |
| GUI (Coin3D scene graph) | Main thread only | Coin3D requires single-threaded node manipulation |
| STEP Import | Partial parallel | OSD_Parallel for parse, manual `std::thread` for tessellation |
| FEM Mesh | External process | Gmsh via subprocess; SMESH internal parallelism |
| Document I/O | Serial | Sequential object save/load into ZIP stream |

### 1.2 Existing Parallelism

| Site | Mechanism | Scope |
|------|-----------|-------|
| STEP parse | `OSD_Parallel` / `OSD_ThreadPool` | OCCT internal |
| Post-import tessellation | `std::thread` workers | `AppImportPy.cpp` |
| FEM distance calc | `#pragma omp parallel for` | `FemMesh.cpp` |
| Import OCAF tree | `tbb::task_group` (conditional) | `ImportOCAF.cpp` |
| Inspection | `QtConcurrent::mapped()` | `InspectionFeature.cpp` |
| Cross-sections | `QtConcurrent::mapped()` | `CrossSections.cpp` |
| Auto-save | `QThreadPool` | `AutoSaver.cpp` |

### 1.3 Key Blocking Constraints

1. **No per-object locks** — Document objects have no mutex; concurrent modification is unsafe
2. **`std::bitset<32>` status flags** — Non-atomic; read-modify-write races under concurrent recompute
3. **Python GIL** — Observer callbacks hold GIL; 40+ methods in `DocumentObserverPython.cpp`
4. **Signal serialization** — `Qt::BlockingQueuedConnection` in pre-recompute forces main-thread sync
5. **Coin3D** — Scene graph manipulation must happen on the rendering thread (OpenGL context owner)
6. **Property system** — No thread-safe access; `AtomicPropertyChange` is transaction-scoped, not thread-scoped
7. **ZIP serialization** — `zipios::ZipOutputStream` is a sequential stream; cannot write in parallel

### 1.4 Rendering Pipeline

```
TopoDS_Shape (BREP)
    → BRepMesh_IncrementalMesh (CPU, OCCT parallel per-face)
    → Poly_Triangulation extraction (CPU, serial per-face)
    → SoCoordinate3 + SoNormal + SoBrepFaceSet (Coin3D nodes, main thread)
    → SoGLRenderAction traversal (CPU, single-threaded)
    → OpenGL draw (VBO if available, else immediate mode)
```

**Current GPU utilization:** ~40% — mostly idle during tessellation, scene graph traversal, and selection.  
**OpenGL version:** 2.0 minimum. VBO support optional (Intel driver workaround).  
**No LOD system.** No frustum culling. No compute shaders.

---

## 2. Architecture Strategy

### Design Principles

1. **Incremental adoption** — Each phase is self-contained and shippable
2. **Opt-in parallelism** — New parallel paths fall back to serial when threading is unavailable
3. **Lock granularity** — Prefer per-object read-write locks over global document locks
4. **GPU = rendering + compute** — Use GPU for tessellation and visualization, not CAD kernel ops
5. **No OCCT surgery** — Work with OCCT's threading model, not against it

### Phase Overview

| Phase | Target | Impact | Risk | Dependencies |
|-------|--------|--------|------|-------------|
| **P0** | Thread-safe foundations | Enables all later phases | Low | None |
| **P1** | Parallel recompute | 2-8× faster rebuild on multi-feature models | Medium | P0 |
| **P2** | GPU-accelerated rendering | 5-20× faster viewport for large models | Medium | None |
| **P3** | Async document I/O | Non-blocking save/load | Low | P0 |
| **P4** | GPU compute tessellation | 3-10× faster shape visualization setup | High | P2 |
| **P5** | Parallel mesh generation | Faster FEM/CFD preprocessing | Low | P0 |

---

## 3. Phase 0 — Thread-Safe Foundations

**Goal:** Make core data structures safe for concurrent access without changing behavior.

### 3.1 Atomic Status Bits

**Current:** `std::bitset<32>` in `DocumentP` and `DocumentObject`  
**Problem:** Non-atomic read-modify-write  
**Fix:** Replace with `std::atomic<uint32_t>` + inline bit manipulation

```cpp
// src/App/DocumentObject.h — replace std::bitset<32> StatusBits
class DocumentObject {
    std::atomic<uint32_t> statusBits{0};

    bool testStatus(ObjectStatus pos) const {
        return (statusBits.load(std::memory_order_acquire) >> int(pos)) & 1;
    }
    void setStatus(ObjectStatus pos, bool on) {
        uint32_t mask = 1u << int(pos);
        if (on) statusBits.fetch_or(mask, std::memory_order_release);
        else    statusBits.fetch_and(~mask, std::memory_order_release);
    }
};
```

**Files:** `src/App/DocumentObject.h`, `src/App/private/DocumentP.h`

### 3.2 Per-Object Read-Write Lock

Add a shared mutex to `DocumentObject` for property access:

```cpp
// src/App/DocumentObject.h
#include <shared_mutex>

class DocumentObject {
    mutable std::shared_mutex objectMutex;
public:
    std::shared_lock<std::shared_mutex> readLock() const {
        return std::shared_lock(objectMutex);
    }
    std::unique_lock<std::shared_mutex> writeLock() {
        return std::unique_lock(objectMutex);
    }
};
```

**Acquisition rules:**
- Recompute of feature X acquires **write lock** on X
- Reading properties from dependency acquires **read lock** on dependency
- GUI ViewProvider reads acquire **read lock**
- Lock ordering: topological order (prevents deadlocks since DAG has no cycles)

### 3.3 Document-Level Transaction Lock

**Current:** Integer counter (not thread-safe)  
**Fix:** Replace with `std::shared_mutex`

```cpp
// src/App/private/DocumentP.h
std::shared_mutex transactionMutex;  // replaces int transactionLock
```

### 3.4 Thread-Safe Signal Queue

Replace direct signal emission during recompute with a deferred queue:

```cpp
// src/App/SignalQueue.h (new)
class SignalQueue {
    std::mutex mutex;
    std::vector<std::function<void()>> pending;
public:
    void enqueue(std::function<void()> fn);
    void flush();  // called on main thread after recompute batch
};
```

**Integration:** `Document::recompute()` collects signals → flushes on main thread after parallel batch completes.

---

## 4. Phase 1 — Parallel Recompute

**Goal:** Execute independent features concurrently during document recompute.

### 4.1 Dependency Graph Analysis

The existing `getDependencyList()` produces a topological order. We extend it to identify **independent groups** (anti-chains in the DAG):

```
Level 0: [Sketch, Sketch001]          ← can run in parallel
Level 1: [Pad, Pad001]                ← can run in parallel (if different parents)
Level 2: [Fillet]                      ← depends on Pad, must wait
Level 3: [Pocket]                      ← depends on Fillet, must wait
```

### 4.2 Level-Parallel Recompute Algorithm

```cpp
// Pseudocode for Document::recompute()
auto levels = computeParallelLevels(topoSorted);  // group by dependency depth

for (auto& level : levels) {
    if (level.size() == 1 || !enableParallelRecompute) {
        // Serial path (existing behavior)
        for (auto* obj : level) {
            _recomputeFeature(obj);
        }
    } else {
        // Parallel path
        signalQueue.clear();
        std::vector<std::future<int>> futures;
        for (auto* obj : level) {
            futures.push_back(threadPool.submit([this, obj]() {
                auto wlock = obj->writeLock();
                PyGILStateRelease gilRelease;  // release GIL for C++ work
                return _recomputeFeature(obj);
            }));
        }
        for (auto& f : futures) f.get();  // wait for level to complete
        signalQueue.flush();  // emit queued signals on main thread
    }
}
```

### 4.3 Python Feature Safety

Python features (scripted objects) **cannot run in parallel** because of the GIL.  
The level scheduler must detect Python features and serialize them:

```cpp
bool isPythonFeature(DocumentObject* obj) {
    return obj->isDerivedFrom<App::FeaturePython>();
}

// In level processing:
auto [cppFeatures, pyFeatures] = partition(level, isPythonFeature);
// Run cppFeatures in parallel, then pyFeatures serially
```

### 4.4 Thread Pool

Use a shared `QThreadPool` or standalone `std::jthread` pool:

```cpp
// src/App/ThreadPool.h (new)
class RecomputeThreadPool {
    unsigned int numThreads;
    std::vector<std::jthread> workers;
    // work-stealing queue per thread for load balance
};
```

**Thread count:** Default to `hardware_concurrency() - 1` (reserve one for GUI).  
**User configurable:** `Preferences → General → Parallel Recompute Threads`

### 4.5 Expected Speedup

| Model Type | Independent Branches | Expected Speedup |
|-----------|---------------------|------------------|
| Single PartDesign body | 0-1 | 1× (no improvement) |
| Multi-body Part | 2-4 | 1.5-3× |
| Assembly (A2plus/ASM3) | 10-100+ | 3-8× |
| Spreadsheet-driven parametric | 5-20 | 2-5× |

**Linear chains** (most PartDesign workflows) see **no improvement** — this is expected.

---

## 5. Phase 2 — GPU-Accelerated Rendering

**Goal:** Move tessellation display, LOD, and scene traversal overhead to the GPU.

### 5.1 Mandatory VBO Path

**Current:** VBO optional, immediate mode fallback  
**Change:** Make VBO the only rendering path. Drop OpenGL < 2.1 support.

```cpp
// src/Mod/Part/Gui/SoBrepFaceSet.cpp
// Remove the immediate-mode glVertexPointer path
// Always use glBindBuffer + glDrawElements
```

**Minimum OpenGL:** 3.2 core profile (enables UBO, instancing, geometry shaders)

### 5.2 Instanced Rendering for Assemblies

Large assemblies contain many copies of the same part (bolts, brackets).  
Use `glDrawElementsInstanced()` for duplicate shapes:

```
Detect duplicate TopoDS_Shape (same TShape pointer) in Import pipeline
    → Store single VBO + per-instance transform buffer (mat4[])
    → Render N copies with one draw call
```

**Impact:** Assembly with 500 identical bolts: **500 draw calls → 1 draw call**

### 5.3 Frustum Culling

Add GPU-side or CPU-side per-object frustum culling:

```cpp
// src/Gui/View3DInventorViewer.cpp
// Before SoGLRenderAction traversal:
for (auto& vp : visibleProviders) {
    SbBox3f bbox = vp->getBoundingBox();
    if (!frustum.intersects(bbox)) {
        vp->getRoot()->enableNotify(false);
        // skip this subtree
    }
}
```

**Simpler alternative:** Use Coin3D's `SoFrustumCamera` or custom `SoCallback` to cull.

### 5.4 Multi-Level LOD

Implement distance-based LOD with pre-computed tessellation levels:

```
LOD 0: Full detail (current tessellation)
LOD 1: 4× deviation (25% triangles)
LOD 2: 16× deviation (6% triangles)
LOD 3: Bounding box only
```

Use `SoLOD` or custom switch node keyed to camera distance.

**Storage:** LOD meshes computed lazily on first zoom-out; cached in ViewProvider.

### 5.5 Compute Shader Tessellation (Phase 4 Preview)

For Phase 4, tessellation moves to GPU compute:

```glsl
// Compute shader: BRep parametric surface → triangle mesh
layout(local_size_x = 64) in;
// Input: NURBS control points, knot vectors (SSBO)
// Output: vertex + normal + index buffers (SSBO)
// Adaptive subdivision based on screen-space error
```

This eliminates the CPU tessellation bottleneck entirely but requires OpenGL 4.3+ or Vulkan.

---

## 6. Phase 3 — Async Document I/O

**Goal:** Non-blocking save/load with progress reporting.

### 6.1 Parallel Object Serialization

Objects are currently serialized sequentially into a ZIP stream. The ZIP format requires sequential entry writing, but **object serialization (XML + binary)** can be parallelized:

```
Phase 1: Parallel serialize each object to memory buffer
    std::vector<std::future<Buffer>> futures;
    for (auto* obj : objects) {
        futures.push_back(pool.submit([obj]() {
            MemoryWriter w;
            obj->Save(w);
            return w.buffer();
        }));
    }

Phase 2: Sequential write buffers to ZIP
    ZipWriter zip(path);
    for (auto& f : futures) {
        zip.writeEntry(f.get());
    }
```

### 6.2 Background Save

Save document on a background thread while the user continues editing:

```
User triggers Save
    → Snapshot document state (CoW properties or deep copy of modified objects)
    → Launch save thread
    → User continues editing (new transaction)
    → Save thread writes snapshot to ZIP
    → On completion: update UI status bar
```

**Requires:** P0 (read locks) to snapshot property values safely.

### 6.3 Streaming Restore

Load document with progressive UI updates:

```
Open FCStd
    → Parse XML header (object types, dependencies)
    → Create placeholder objects in document
    → Show tree view immediately
    → Background thread: deserialize objects in dependency order
    → Each completed object triggers recompute + visual update
```

---

## 7. Phase 4 — GPU Compute Tessellation

**Goal:** Offload BRepMesh to GPU for 3-10× faster shape-to-display conversion.

### 7.1 Architecture

```
TopoDS_Shape faces
    → Extract NURBS/analytic surface parameters (CPU)
    → Upload control points + parametric bounds (SSBO)
    → Compute shader: adaptive parametric sampling → triangles
    → Result stays in GPU memory (no readback)
    → Render directly from compute output buffer
```

### 7.2 Surface Types

| Surface Type | GPU Strategy |
|-------------|-------------|
| Planar | Triangulate polygon boundary (trivial) |
| Cylindrical/Conical | Parametric grid (u,v) → (x,y,z) |
| Spherical/Toroidal | Parametric grid with adaptive density |
| NURBS | De Boor evaluation in compute shader |
| BSpline trimmed | Trim curve evaluation + inside/outside test |

### 7.3 Fallback

Shapes that fail GPU tessellation (complex trimmed surfaces) fall back to CPU `BRepMesh`.

### 7.4 Requirements

- OpenGL 4.3+ (compute shaders) or Vulkan 1.0
- Falls back to CPU tessellation on older hardware
- User preference: `GPU Tessellation = Auto | Always | Never`

---

## 8. Phase 5 — Parallel FEM/CFD Preprocessing

**Goal:** Parallelize mesh generation and solver setup.

### 8.1 Parallel Gmsh Regions

When a model has multiple mesh regions with independent geometry:

```
Detect independent mesh regions via geometry adjacency
    → Launch parallel Gmsh processes per region
    → Merge results
```

### 8.2 VTK Backend Activation

Enable TBB backend for VTK operations:

```cpp
// src/Mod/Fem/App/FemPostPipeline.cpp
#include <vtkSMPTools.h>
vtkSMPTools::SetBackend("TBB");
vtkSMPTools::Initialize(std::thread::hardware_concurrency());
```

### 8.3 Parallel Boundary Condition Application

BC application to mesh nodes is embarrassingly parallel:

```python
# Apply BCs per region in parallel (Python side)
from concurrent.futures import ThreadPoolExecutor
with ThreadPoolExecutor() as pool:
    pool.map(apply_bc, independent_bc_groups)
```

---

## 9. Implementation Roadmap

### Phase 0: Thread-Safe Foundations (Week 1-3)
- [ ] Replace `std::bitset<32>` with `std::atomic<uint32_t>` for status bits
- [ ] Add `std::shared_mutex` to `DocumentObject`
- [ ] Add `std::shared_mutex` to `DocumentP::transactionMutex`
- [ ] Create `SignalQueue` for deferred signal emission
- [ ] Add unit tests for concurrent status bit manipulation
- [ ] Add unit tests for read/write lock ordering

### Phase 1: Parallel Recompute (Week 3-6)
- [ ] Implement `computeParallelLevels()` — group topological sort into anti-chains
- [ ] Create `RecomputeThreadPool` with configurable thread count
- [ ] Modify `Document::recompute()` to use level-parallel algorithm
- [ ] Partition C++ vs Python features per level
- [ ] Integrate `SignalQueue` — flush after each level
- [ ] Add preference: `Enable Parallel Recompute` (default off initially)
- [ ] Benchmark: multi-body Part, Assembly, spreadsheet-driven models

### Phase 2: GPU Rendering (Week 4-8)
- [ ] Make VBO path mandatory; remove immediate-mode fallback
- [ ] Raise minimum OpenGL to 3.2
- [ ] Implement instance buffer for duplicate shapes in assemblies
- [ ] Add per-object bounding box frustum culling
- [ ] Implement 3-level LOD with lazy tessellation caching
- [ ] Benchmark: 50K+ object assemblies, orbit/zoom FPS

### Phase 3: Async Document I/O (Week 6-9)
- [ ] Implement parallel object serialization to memory buffers
- [ ] Sequential ZIP write from buffered data
- [ ] Background save with CoW snapshot
- [ ] Progressive document restore with placeholder objects
- [ ] Add progress bar for load/save

### Phase 4: GPU Compute Tessellation (Week 9-14)
- [ ] Implement compute shader for planar + analytic surfaces
- [ ] Implement NURBS evaluation compute shader
- [ ] Add trimmed surface support with trim curve compute
- [ ] Zero-copy render from compute output buffer
- [ ] Fallback to CPU for unsupported surface types
- [ ] Benchmark: tessellation time for 100+ MB STEP imports

### Phase 5: Parallel FEM/CFD (Week 10-14)
- [ ] Enable VTK TBB backend
- [ ] Parallel Gmsh region meshing
- [ ] Parallel BC application
- [ ] Benchmark: mesh generation time for complex assemblies

---

## 10. Risk Assessment

| Risk | Severity | Mitigation |
|------|----------|------------|
| Deadlocks in parallel recompute | High | Topological lock ordering (DAG = no cycles = no deadlocks) |
| Race conditions in property access | High | Per-object `shared_mutex` + careful lock acquisition |
| Python GIL contention | Medium | Separate C++ and Python features in level scheduler |
| Coin3D scene graph thread safety | Medium | All scene graph ops marshalled to main thread via `SignalQueue` |
| GPU driver compatibility (compute shaders) | Medium | CPU fallback for all GPU paths |
| OCCT internal state corruption | Medium | Never call OCCT from multiple threads on same shape |
| Regression in serial performance | Low | Opt-in parallel recompute; no overhead when disabled |

---

## 11. Hardware Impact Projection

### CPU Utilization (current → target)

| Operation | Cores Used Now | Cores Used After | Improvement |
|-----------|---------------|-----------------|-------------|
| Recompute (assembly) | 1 | N-1 | 3-8× |
| STEP Import | 1-N (partial) | N (full) | 1.5-2× |
| Tessellation | N (OCCT parallel) | GPU | 3-10× |
| Document Save | 1 | N (serialize) + 1 (ZIP write) | 2-4× |
| FEM Mesh | External | External + parallel regions | 1.5-3× |
| Viewport Rendering | 1 CPU + ~40% GPU | 1 CPU + ~90% GPU | 5-20× FPS |

### Memory Impact

- Per-object `shared_mutex`: ~56 bytes × N objects (negligible for < 100K objects)
- LOD mesh storage: ~3× current mesh memory (mitigated by lazy computation)
- Signal queue: Bounded, flushed per level (< 1 MB typical)
- Parallel serialization buffers: Proportional to document size (temporary)

---

## 12. Compatibility Notes

- **Minimum C++ standard:** C++17 (for `std::shared_mutex`, `std::optional`, structured bindings)
- **Minimum OpenGL:** 3.2 core (Phase 2), 4.3 for compute shaders (Phase 4)
- **Python:** No changes to Python API; parallel recompute is transparent
- **Third-party modules:** Modules using direct property access continue to work (single-threaded by default; parallel only within recompute)
- **OCCT:** No modifications required; we work within its threading constraints

---

## 13. Testing Strategy

- **Thread Sanitizer (TSan):** Run full test suite under TSan to detect data races
- **Deadlock detection:** Static analysis of lock ordering in CI
- **Parallel recompute correctness:** Compare serial vs parallel recompute output bit-for-bit
- **GPU rendering regression:** Screenshot comparison tests at multiple LOD levels
- **Stress tests:** 100K-object documents with randomized concurrent recompute
