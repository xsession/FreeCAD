# 05 — Infographics & Diagrams

> **Classification:** Visual Reference · **Audience:** All stakeholders  
> **Format:** ASCII art + Mermaid-compatible descriptions  
> **Print-friendly:** Yes (monospace font recommended)

---

## 1. The Big Picture: TNP Resolution Pipeline

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                            ║
║                    THE TOPOLOGICAL NAMING PROBLEM                          ║
║                         AND ITS RESOLUTION                                 ║
║                                                                            ║
║   ┌─────────────────────────────────────────────────────────────────────┐  ║
║   │                          USER ACTION                                │  ║
║   │                                                                     │  ║
║   │    "I moved my base sketch by 2mm.  Will my Fillet break?"          │  ║
║   └───────────────────────────┬─────────────────────────────────────────┘  ║
║                               │                                            ║
║                               ▼                                            ║
║   ┌─────────────────────────────────────────────────────────────────────┐  ║
║   │                     PARAMETRIC RECOMPUTE                            │  ║
║   │                                                                     │  ║
║   │  Sketch ──recompute──▶ Pad ──recompute──▶ Fillet                   │  ║
║   │  (moved)               (new shape)         (needs Edge1)           │  ║
║   └───────────────────────────┬─────────────────────────────────────────┘  ║
║                               │                                            ║
║              ┌────────────────┴────────────────┐                           ║
║              ▼                                 ▼                           ║
║   ┌──────────────────────┐          ┌──────────────────────┐               ║
║   │   WITHOUT FIX  ❌    │          │   WITH FIX  ✅       │               ║
║   │                      │          │                      │               ║
║   │ TNP name → NULL      │          │ TNP name → NULL      │               ║
║   │ throw "Invalid edge" │          │ Fallback → "Edge1"   │               ║
║   │ Fillet = INVALID     │          │ Edge1 → FOUND        │               ║
║   │ Model = BROKEN       │          │ Fillet = VALID       │               ║
║   │                      │          │ Model = INTACT       │               ║
║   └──────────────────────┘          └──────────────────────┘               ║
║                                                                            ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## 2. Feature Tree & Data Flow

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                            ║
║              PARTDESIGN FEATURE TREE (Typical Test Model)                   ║
║                                                                            ║
║  Document                                                                  ║
║  └── Body                                                                  ║
║      ├── Origin (XY, XZ, YZ Planes + Axes)                                ║
║      │                                                                     ║
║      ├── 1️⃣  Sketch ─────────────────── Attachment: XY_Plane              ║
║      │   │   Rectangle (0,0)→(10,10)   MapMode: FlatFace                  ║
║      │   │                                                                 ║
║      │   ▼                                                                 ║
║      ├── 2️⃣  Pad ────────────────────── Profile: Sketch                   ║
║      │   │   Length: 10mm              Shape: 10×10×10 box                 ║
║      │   │   Faces: 6, Edges: 12      Volume: 1000 mm³                    ║
║      │   │                                                                 ║
║      │   ├── Face1..Face6 ─────── Each face is referenceable               ║
║      │   ├── Edge1..Edge12 ────── Each edge is referenceable               ║
║      │   └── Vertex1..Vertex8 ── Each vertex is referenceable              ║
║      │   │                                                                 ║
║      │   ▼                                                                 ║
║      ├── 3️⃣  Sketch2 ───────────────── Attachment: (Pad, "Face6")         ║
║      │   │   Rectangle (2,2)→(6,6)    MapMode: FlatFace                   ║
║      │   │                                                                 ║
║      │   ▼                                                                 ║
║      ├── 4️⃣  Pad2 ──────────────────── Profile: Sketch2                   ║
║      │       Length: 5mm              Volume: 1180 mm³                     ║
║      │                                                                     ║
║      ├── 5️⃣  Fillet ────────────────── Base: (Pad, ["Edge1"])             ║
║      │       Radius: 1.0mm            Uses: getContinuousEdges()          ║
║      │                                                                     ║
║      └── 6️⃣  Chamfer ───────────────── Base: (Pad, ["Edge1"])             ║
║              Size: 1.0mm              Uses: getContinuousEdges()           ║
║                                                                            ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## 3. Element Map Lifecycle

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                            ║
║                   ELEMENT MAP LIFECYCLE                                     ║
║                                                                            ║
║  ┌─────────┐    ┌─────────────┐    ┌──────────────┐    ┌──────────────┐   ║
║  │ Sketch  │    │ OCC Kernel  │    │ TopoShape    │    │ ElementMap   │   ║
║  │ Geometry│───▶│ BRepPrimAPI │───▶│ + Mapper     │───▶│ Database     │   ║
║  │         │    │ _MakePrism  │    │              │    │              │   ║
║  └─────────┘    └─────────────┘    └──────────────┘    └──────┬───────┘   ║
║                                                               │            ║
║                        CREATION PHASE                         │            ║
║  ─────────────────────────────────────────────────────────────│────────    ║
║                        STORAGE PHASE                          │            ║
║                                                               ▼            ║
║                                    ┌──────────────────────────────────┐    ║
║                                    │         PropertyLinks           │    ║
║                                    │                                  │    ║
║                                    │  SubValues: ["Edge1"]            │    ║
║                                    │  ShadowSubs: [{                  │    ║
║                                    │    newName: ";#f:1;:G;XTR..."   │    ║
║                                    │    oldName: "Edge1"              │    ║
║                                    │  }]                              │    ║
║                                    └──────────────┬───────────────────┘    ║
║                                                   │                        ║
║  ─────────────────────────────────────────────────│────────────────────    ║
║                        RECOMPUTE PHASE            │                        ║
║                                                   ▼                        ║
║         ┌────────────────────────────────────────────────────────┐         ║
║         │              getShadowSubs()                           │         ║
║         │                                                        │         ║
║         │  Try to resolve newName against current element map    │         ║
║         │                                                        │         ║
║         │     ┌──────────────────┐    ┌────────────────────┐     │         ║
║         │     │  ✅ Resolved     │    │  ❌ Stale          │     │         ║
║         │     │                  │    │                    │     │         ║
║         │     │ newName: valid   │    │ newName: stale     │     │         ║
║         │     │ oldName: "Edge1" │    │ oldName: "?Edge1"  │     │         ║
║         │     └──────────────────┘    └────────┬───────────┘     │         ║
║         └──────────────────────────────────────│─────────────────┘         ║
║                                                │                           ║
║  ─────────────────────────────────────────────│────────────────────────    ║
║                        FALLBACK PHASE         ▼  (NEW FIX)                ║
║                                                                            ║
║         ┌────────────────────────────────────────────────────────┐         ║
║         │            getContinuousEdges() / getFaces()           │         ║
║         │                                                        │         ║
║         │  1. getSubShape(newName)  → NULL                       │         ║
║         │  2. fallback = oldName    → "?Edge1"                   │         ║
║         │  3. strip '?'            → "Edge1"                     │         ║
║         │  4. getSubShape("Edge1") → ✅ FOUND                   │         ║
║         └────────────────────────────────────────────────────────┘         ║
║                                                                            ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## 4. Class Hierarchy Diagram

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                            ║
║                   CLASS HIERARCHY — DRESSUP FEATURES                       ║
║                                                                            ║
║  App::DocumentObject                                                       ║
║  │                                                                         ║
║  └── Part::Feature                                                         ║
║      │   Shape: Part::TopoShape                                           ║
║      │                                                                     ║
║      └── PartDesign::Feature                                               ║
║          │   BaseFeature: PropertyLink                                     ║
║          │                                                                 ║
║          └── PartDesign::FeatureAddSub                                     ║
║              │   AddSubShape: TopoShape                                    ║
║              │   Type: Additive / Subtractive                              ║
║              │                                                             ║
║              └── PartDesign::DressUp  ◄─── THE FIX IS HERE               ║
║                  │                                                         ║
║                  │   Properties:                                           ║
║                  │   ├── Base: PropertyLinkSub ←── stores edge/face refs  ║
║                  │   └── SupportTransform: PropertyBool                    ║
║                  │                                                         ║
║                  │   Methods (PATCHED):                                    ║
║                  │   ├── getContinuousEdges() ←── edge fallback added     ║
║                  │   └── getFaces()           ←── face fallback added     ║
║                  │                                                         ║
║                  ├── PartDesign::Fillet     ╗                              ║
║                  │   Radius: PropertyLength ║  Edge-based                  ║
║                  │                          ║  → uses getContinuousEdges() ║
║                  ├── PartDesign::Chamfer    ║                              ║
║                  │   Size: PropertyLength   ╝                              ║
║                  │                                                         ║
║                  └── PartDesign::Thickness  ╗  Face-based                  ║
║                      Value: PropertyLength  ╝  → uses getFaces()           ║
║                                                                            ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## 5. Shadow Sub State Machine

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                            ║
║                  SHADOW SUB STATE MACHINE                                   ║
║                                                                            ║
║                         ┌──────────────┐                                   ║
║                         │              │                                   ║
║               ┌────────▶│   CREATED    │                                   ║
║               │         │              │                                   ║
║               │         └──────┬───────┘                                   ║
║               │                │  User sets Base = (Pad, ["Edge1"])         ║
║               │                ▼                                           ║
║               │         ┌──────────────┐                                   ║
║               │         │   RESOLVED   │                                   ║
║               │         │              │                                   ║
║               │         │ new: "TNP.." │                                   ║
║    User edits │         │ old: "Edge1" │                                   ║
║    Base       │         └──────┬───────┘                                   ║
║    property   │                │  Upstream feature recomputes               ║
║               │                ▼                                           ║
║               │         ┌──────────────┐                                   ║
║               │         │  RESOLVING   │                                   ║
║               │         │              │                                   ║
║               │         │ PropertyLinks│                                   ║
║               │         │ tries to     │                                   ║
║               │         │ resolve      │                                   ║
║               │         └──┬───────┬───┘                                   ║
║               │            │       │                                       ║
║               │      ✅ Found   ❌ Not Found                               ║
║               │            │       │                                       ║
║               │            ▼       ▼                                       ║
║               │    ┌─────────┐  ┌──────────┐                               ║
║               │    │RESOLVED │  │  STALE   │                               ║
║               │    │         │  │          │                               ║
║               │    │new: OK  │  │new: stale│                               ║
║               │    │old: OK  │  │old: ?Edge│                               ║
║               │    └────┬────┘  └────┬─────┘                               ║
║               │         │            │                                     ║
║               │         │            ▼                                     ║
║               │         │     ┌──────────────┐                             ║
║               │         │     │  FALLBACK    │ ← getContinuousEdges()     ║
║               │         │     │              │                             ║
║               │         │     │ strip "?"    │                             ║
║               │         │     │ try "Edge1"  │                             ║
║               │         │     └──────┬───────┘                             ║
║               │         │            │                                     ║
║               │         │      ┌─────┴─────┐                               ║
║               │         │   ✅ Found    ❌ Not Found                       ║
║               │         │      │           │                               ║
║               │         ▼      ▼           ▼                               ║
║               │    ┌──────────────┐  ┌──────────┐                          ║
║               └────│   ACTIVE     │  │  ERROR   │                          ║
║                    │              │  │          │                          ║
║                    │ Feature is   │  │ "Invalid │                          ║
║                    │ valid and    │  │  edge    │                          ║
║                    │ up to date   │  │  link"   │                          ║
║                    └──────────────┘  └──────────┘                          ║
║                                                                            ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## 6. Test Coverage Heat Map

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                            ║
║               TEST COVERAGE MATRIX                                         ║
║                                                                            ║
║  Feature ×        │Pad │Pad2│Pocket│Fillet│Chamfer│Save│getShape│ElemMap   ║
║  Mutation ↓       │    │    │      │      │       │Rest│        │         ║
║  ─────────────────┼────┼────┼──────┼──────┼───────┼────┼────────┼─────── ║
║  Sketch offset    │ ✅ │ ✅ │  ✅  │ ⭐  │       │    │   ✅   │         ║
║  Sketch resize    │ ✅ │ ✅ │      │      │       │    │        │         ║
║  Pad length Δ     │ ✅ │ ✅ │      │      │  ⭐   │    │        │         ║
║  Middle offset    │ ✅ │ ✅ │      │      │       │    │        │         ║
║  Deep chain       │ ✅ │ ✅ │      │      │       │    │        │         ║
║  Save/restore     │ ✅ │ ✅ │      │      │       │ ✅ │        │   ✅    ║
║  Multi-recompute  │ ✅ │    │      │      │       │    │        │         ║
║  No mutation      │ ✅ │    │      │      │       │    │        │   ✅    ║
║  ─────────────────┼────┼────┼──────┼──────┼───────┼────┼────────┼─────── ║
║                                                                            ║
║  ✅ = Covered    ⭐ = Directly validates C++ fix                          ║
║                                                                            ║
║  CONFIDENCE LEVEL PER AREA:                                                ║
║  ████████████████████████████████████  Pad chain workflows     HIGH        ║
║  ████████████████████████████████      Element map integrity   HIGH        ║
║  ████████████████████████              DressUp edge fallback   HIGH        ║
║  ████████████████████                  DressUp face fallback   MEDIUM      ║
║  ████████████████                      Save/Restore pipeline   MEDIUM      ║
║  ████████████                          GUI selection           LOW*        ║
║                                                                            ║
║  * GUI tests auto-skip in headless mode (CI)                               ║
║                                                                            ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## 7. Timeline: From Bug to Fix

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                            ║
║              PROJECT TIMELINE                                              ║
║                                                                            ║
║  ═══════════════════════════════════════════════════════════════════════    ║
║                                                                            ║
║  📅 2010          Jürgen Riegel creates FeatureDressUp.cpp                ║
║  │                (original DressUp base class)                            ║
║  │                                                                         ║
║  │  ... (years of development) ...                                         ║
║  │                                                                         ║
║  📅 2023-2024     TNP / Element Map system merged into FreeCAD             ║
║  │                ├── ElementMap.cpp, ElementNamingUtils.h                  ║
║  │                ├── PropertyLinks shadow sub support                     ║
║  │                ├── TopoShape mapper infrastructure                      ║
║  │                └── MISSING_PREFIX "?" introduced                        ║
║  │                                                                         ║
║  📅 2025-01       Test: Do not write test files into CWD                   ║
║  📅 2025-09       PartDesign: Fix revolution's Toponaming support          ║
║  📅 2025-11       All: Reformat according to new standard                  ║
║  📅 2025-12       PD: Modify tests to use SideType instead of Midplane    ║
║  │                                                                         ║
║  📅 2026-02       SPDX license identifiers added to PartDesign             ║
║  │                                                                         ║
║  📅 2026-03-14    ⭐ THIS FIX                                             ║
║  │                ├── Phase 1: Create TestSketchOnFace.py (18 tests)       ║
║  │                ├── Phase 2: Add 12 TNP proof tests (total 30)           ║
║  │                ├── Phase 3: Discover Fillet/Chamfer TNP failures         ║
║  │                ├── Phase 4: Root cause analysis                          ║
║  │                │   └── getContinuousEdges() missing fallback            ║
║  │                ├── Phase 5: Iteration 1 — basic fallback (FAILED)       ║
║  │                │   └── oldName was "?Edge1" not "Edge1"                 ║
║  │                ├── Phase 6: Iteration 2 — strip "?" prefix (SUCCESS)    ║
║  │                ├── Phase 7: Verify 30/30 + 68/68 tests pass             ║
║  │                └── Phase 8: Enterprise documentation                    ║
║  │                                                                         ║
║  ═══════════════════════════════════════════════════════════════════════    ║
║                                                                            ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## 8. Decision Flow: What Happens When You Move a Sketch?

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                            ║
║         DECISION FLOWCHART: SKETCH MUTATION → FILLET RECOMPUTE             ║
║                                                                            ║
║  ┌────────────────────┐                                                    ║
║  │ User moves Sketch  │                                                    ║
║  └─────────┬──────────┘                                                    ║
║            │                                                               ║
║            ▼                                                               ║
║  ┌────────────────────┐                                                    ║
║  │ Pad recomputes     │                                                    ║
║  │ (new TopoDS_Shape) │                                                    ║
║  └─────────┬──────────┘                                                    ║
║            │                                                               ║
║            ▼                                                               ║
║  ┌────────────────────────┐                                                ║
║  │ Fillet recomputes      │                                                ║
║  │ getContinuousEdges()   │                                                ║
║  └─────────┬──────────────┘                                                ║
║            │                                                               ║
║            ▼                                                               ║
║  ┌────────────────────────┐    ┌─────────────────────┐                     ║
║  │ Base.getShadowSubs()   │───▶│ [{newName, oldName}]│                     ║
║  └────────────────────────┘    └──────────┬──────────┘                     ║
║                                           │                                ║
║            ┌──────────────────────────────┘                                ║
║            ▼                                                               ║
║  ╔═══════════════════════╗                                                 ║
║  ║ newName has content?  ║                                                 ║
║  ╚═══════╤═══════╤═══════╝                                                 ║
║       YES│       │NO                                                       ║
║          ▼       ▼                                                         ║
║  ┌───────────┐ ┌───────────┐                                               ║
║  │ref=newName│ │ref=oldName│                                               ║
║  └─────┬─────┘ └─────┬─────┘                                               ║
║        └──────┬──────┘                                                     ║
║               ▼                                                            ║
║  ╔════════════════════════════╗                                             ║
║  ║ shape.getSubShape(ref)    ║                                             ║
║  ║ returns non-null?         ║                                             ║
║  ╚═══════╤══════════╤════════╝                                             ║
║       YES│          │NO                                                    ║
║          │          ▼                                                      ║
║          │  ╔═══════════════════════╗                                      ║
║          │  ║ newName && oldName    ║                                      ║
║          │  ║ both have content?    ║                                      ║
║          │  ╚═══════╤═══════╤══════╝                                      ║
║          │       YES│       │NO                                            ║
║          │          ▼       ▼                                              ║
║          │  ┌──────────┐  ┌──────────────┐                                 ║
║          │  │ fallback  │  │ THROW ERROR  │                                ║
║          │  │ = oldName │  │ "Invalid     │                                ║
║          │  └─────┬─────┘  │  edge link"  │                                ║
║          │        │        └──────────────┘                                ║
║          │        ▼                                                        ║
║          │  ╔═══════════════════╗                                          ║
║          │  ║ starts with '?'? ║                                          ║
║          │  ╚═══╤══════════╤═══╝                                          ║
║          │   YES│          │NO                                             ║
║          │      ▼          │                                               ║
║          │  ┌──────────┐   │                                               ║
║          │  │ strip '?' │   │                                               ║
║          │  │ ++fallback│   │                                               ║
║          │  └─────┬─────┘   │                                               ║
║          │        └────┬────┘                                              ║
║          │             ▼                                                   ║
║          │  ┌──────────────────────────┐                                   ║
║          │  │ FC_WARN("stale, falling  │                                   ║
║          │  │  back to '<fallback>'")  │                                   ║
║          │  └────────────┬─────────────┘                                   ║
║          │               ▼                                                 ║
║          │  ╔════════════════════════════╗                                  ║
║          │  ║ shape.getSubShape(fallback)║                                  ║
║          │  ║ returns non-null?          ║                                  ║
║          │  ╚═══════╤═══════════╤═══════╝                                  ║
║          │       YES│           │NO                                        ║
║          │          │           ▼                                          ║
║          │          │  ┌──────────────┐                                     ║
║          │          │  │ THROW ERROR  │                                     ║
║          │          │  │ "Invalid     │                                     ║
║          │          │  │  edge link"  │                                     ║
║          │          │  └──────────────┘                                     ║
║          │          │                                                      ║
║          └────┬─────┘                                                      ║
║               ▼                                                            ║
║  ┌────────────────────────────┐                                            ║
║  │ ✅ Process edge normally   │                                            ║
║  │ (C0 continuity check, etc.)│                                            ║
║  └────────────────────────────┘                                            ║
║                                                                            ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## 9. Test Model Geometries

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                            ║
║         TEST MODEL GEOMETRIES (Cross-Section Views)                        ║
║                                                                            ║
║  ┌───────────────────┐  ┌───────────────────┐  ┌───────────────────┐      ║
║  │                   │  │     ┌───┐         │  │                   │      ║
║  │                   │  │     │P2 │         │  │     ┌───────┐     │      ║
║  │      Pad          │  │     └───┘         │  │     │POCKET │     │      ║
║  │    (base box)     │  │   Pad (base)      │  │     │(cutout│     │      ║
║  │    10×10×10       │  │   + Pad2 on top   │  │     └───────┘     │      ║
║  │                   │  │                   │  │   Pad + Pocket    │      ║
║  │   Vol: 1000       │  │   Vol: 1180       │  │   Vol: 892        │      ║
║  └───────────────────┘  └───────────────────┘  └───────────────────┘      ║
║  Tests: 1-5              Test: 12              Test: TNP3                  ║
║                                                                            ║
║  ┌───────────────────┐  ┌───────────────────┐  ┌───────────────────┐      ║
║  │                 ╱ │  │                 ╲ │  │ ┌─┐               │      ║
║  │   Pad         ╱  │  │   Pad         ╲  │  │ │ │┌─┐            │      ║
║  │   + Fillet   ╱   │  │   + Chamfer   ╲  │  │ │ ││ │┌─┐         │      ║
║  │   (Edge1)  ╱    │  │   (Edge1)    ╲  │  │ │ ││ ││ │         │      ║
║  │           ╱     │  │             ╲  │  │ │ ││ ││ │         │      ║
║  │                  │  │                 │  │ └─┘└─┘└─┘         │      ║
║  └───────────────────┘  └───────────────────┘  └───────────────────┘      ║
║  Test: TNP8              Test: TNP11           Test: TNP9                  ║
║  Fillet survives         Chamfer survives      4-deep chain               ║
║                                                                            ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## 10. Regression Safety Net

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                            ║
║                    REGRESSION SAFETY NET                                    ║
║                                                                            ║
║  ┌──────────────────────────────────────────────────────────────────────┐  ║
║  │                                                                      │  ║
║  │              TestSketchOnFace (30 tests)                              │  ║
║  │              ═══════════════════════════                              │  ║
║  │  ┌────────┬────────┬────────┬────────┬────────┬────────┬────────┐   │  ║
║  │  │Geom(5) │Elem(3) │API(3)  │Face(2) │Map(1)  │GUI(3)  │TNP(12)│   │  ║
║  │  │ ✅✅✅ │ ✅✅✅ │ ✅✅✅ │ ✅✅  │ ✅    │ ✅✅✅ │✅✅✅✅│   │  ║
║  │  │ ✅✅  │        │        │        │        │        │✅✅✅✅│   │  ║
║  │  │        │        │        │        │        │        │✅✅✅✅│   │  ║
║  │  └────────┴────────┴────────┴────────┴────────┴────────┴────────┘   │  ║
║  │                                                                      │  ║
║  └──────────────────────────────────────────────────────────────────────┘  ║
║                                                                            ║
║  ┌──────────────────────────────────────────────────────────────────────┐  ║
║  │                                                                      │  ║
║  │           TestTopologicalNamingProblem (68 tests)                    │  ║
║  │           ═══════════════════════════════════════                    │  ║
║  │  ┌──────────────────────────────────────────────────────────────┐   │  ║
║  │  │ ✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅│   │  ║
║  │  │ ✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅│   │  ║
║  │  └──────────────────────────────────────────────────────────────┘   │  ║
║  │                                                                      │  ║
║  └──────────────────────────────────────────────────────────────────────┘  ║
║                                                                            ║
║  Combined: 98/98 tests passing ─ ZERO regressions                          ║
║                                                                            ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

*Next: [06 — Changelog & History](./06_changelog_history.md)*
