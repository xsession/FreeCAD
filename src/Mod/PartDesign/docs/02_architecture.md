# 02 — Architecture Deep-Dive: Element Maps, PropertyLinks & Shadow Subs

> **Classification:** Engineering Reference · **Audience:** Core Developers  
> **Prerequisites:** Familiarity with OpenCascade TopoDS types, FreeCAD App framework

---

## 1. System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     FREECAD PARAMETRIC PIPELINE                         │
│                                                                         │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────────────┐  │
│  │  User     │    │ Feature  │    │ Element  │    │  PropertyLinks   │  │
│  │  Action   │───▶│ Recomp.  │───▶│  Map     │───▶│  Shadow Subs     │  │
│  │          │    │          │    │ Update   │    │  Resolution      │  │
│  └──────────┘    └──────────┘    └──────────┘    └──────────────────┘  │
│       │                │               │                │               │
│       │                ▼               ▼                ▼               │
│       │          ┌──────────┐    ┌──────────┐    ┌──────────────────┐  │
│       │          │TopoShape │    │ Mapped   │    │  Downstream      │  │
│       └─────────▶│ + OCC    │    │ Names    │    │  Feature         │  │
│                  │ Kernel   │    │ Database │    │  Recompute       │  │
│                  └──────────┘    └──────────┘    └──────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Element Map System

### 2.1 What Is an Element Map?

Every `TopoShape` in FreeCAD can carry an **Element Map** — a bidirectional dictionary
mapping between:

- **TNP names** (topology-encoded, stable across recomputes)
- **Short names** (indexed, like `Face1`, `Edge3`, `Vertex7`)

```
┌─────────────────────────────────────────────────────────────────────┐
│                       ELEMENT MAP STRUCTURE                          │
│                                                                     │
│  TopoShape (Pad)                                                    │
│  ├── OCC Shape: TopoDS_Shape (Solid)                                │
│  └── ElementMap:                                                    │
│      ┌──────────────────────────────────────┬──────────────┐        │
│      │ TNP Name (Mapped)                    │ Short Name   │        │
│      ├──────────────────────────────────────┼──────────────┤        │
│      │ ;#f:1;:G;XTR;:H353:7,F.Face1        │ Face1        │        │
│      │ ;#f:2;:G;XTR;:H353:7,F.Face2        │ Face2        │        │
│      │ ;#f:1;:G;XTR;:H353:7,E.Edge1        │ Edge1        │        │
│      │ ;#f:1;:G;XTR;:H353:7,V.Vertex1      │ Vertex1      │        │
│      │ ...                                  │ ...          │        │
│      └──────────────────────────────────────┴──────────────┘        │
│                                                                     │
│  Forward Map:  TNP Name → Short Name                                │
│  Reverse Map:  Short Name → TNP Name                                │
│  ElementMapSize: 26 (6 faces + 12 edges + 8 vertices)              │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 TNP Name Anatomy

```
  ;#f:1;:G;XTR;:H353:7,E.Edge1
  ▲     ▲    ▲      ▲       ▲
  │     │    │      │       └── Original indexed element name
  │     │    │      └────────── History tag: feature hash + index
  │     │    └───────────────── Operation: XTR = extrusion
  │     └────────────────────── Geometry type marker
  └──────────────────────────── ELEMENT_MAP_PREFIX ";"

  Decoding:
  ┌────────┬──────────────────────────────────────────────────┐
  │ Token  │ Meaning                                          │
  ├────────┼──────────────────────────────────────────────────┤
  │ ;      │ Element map prefix (ELEMENT_MAP_PREFIX)          │
  │ #f:1   │ Face derivation, index 1                         │
  │ ;:G    │ Geometry operation marker                         │
  │ ;XTR   │ Extrusion (Pad/Pocket operation)                  │
  │ ;:H353 │ POSTFIX_TAG — feature history hash (353)          │
  │ :7     │ Sub-index within that feature                     │
  │ ,E     │ Element type: Edge                                │
  │ .Edge1 │ Original short name                               │
  └────────┴──────────────────────────────────────────────────┘
```

### 2.3 Element Name Constants

From `src/App/ElementNamingUtils.h`:

```
┌────────────────────────────────┬────────┬────────────────────────────┐
│ Constant                       │ Value  │ Purpose                    │
├────────────────────────────────┼────────┼────────────────────────────┤
│ ELEMENT_MAP_PREFIX             │ ";"    │ Start of mapped name       │
│ MISSING_PREFIX                 │ "?"    │ Marks unresolvable element │
│ MAPPED_CHILD_ELEMENTS_PREFIX   │ ";:R"  │ Child element marker       │
│ POSTFIX_TAG                    │ ";:H"  │ History tag                │
│ POSTFIX_DECIMAL_TAG            │ ";:T"  │ Decimal tag                │
│ POSTFIX_EXTERNAL_TAG           │ ";:X"  │ External tag               │
│ POSTFIX_CHILD                  │ ";:C"  │ Child element              │
│ POSTFIX_INDEX                  │ ";:I"  │ Array element index        │
│ POSTFIX_UPPER                  │ ";:U"  │ Higher hierarchy           │
└────────────────────────────────┴────────┴────────────────────────────┘
```

---

## 3. PropertyLinks & Shadow Subs

### 3.1 PropertyLinkSub

DressUp features store their base references using `App::PropertyLinkSub`:

```cpp
App::PropertyLinkSub Base;  // FeatureDressUp.h
```

When set (e.g., `fillet.Base = (pad, ["Edge1"])`), PropertyLinks stores:

```
┌──────────────────────────────────────────────────────────────────┐
│                    PropertyLinkSub STORAGE                        │
│                                                                  │
│  Object:       Pad                                               │
│  SubValues:    ["Edge1"]         ← What the user/code set        │
│                                                                  │
│  Shadow Subs (internal):                                         │
│  ┌──────────────────────────────────────────────────────┐        │
│  │ ShadowSub[0] = ElementNamePair {                     │        │
│  │   newName: ";#f:1;:G;XTR;:H353:7,E.Edge1"           │        │
│  │   oldName: "Edge1"                                   │        │
│  │ }                                                    │        │
│  └──────────────────────────────────────────────────────┘        │
│                                                                  │
│  The shadow subs are the TNP-aware internal representation.      │
│  They are updated on every recompute.                            │
└──────────────────────────────────────────────────────────────────┘
```

### 3.2 Shadow Sub Resolution Flow

```
┌────────────────────────────────────────────────────────────────────┐
│              SHADOW SUB RESOLUTION FLOW                             │
│                                                                    │
│  On Recompute:                                                     │
│  ┌────────────────┐                                                │
│  │ PropertyLinks   │                                               │
│  │ getShadowSubs() │                                               │
│  └───────┬────────┘                                                │
│          │                                                         │
│          ▼                                                         │
│  ┌────────────────────────────────────┐                            │
│  │ Try to resolve newName             │                            │
│  │ against current element map        │                            │
│  └───────┬───────────────┬────────────┘                            │
│          │               │                                         │
│     ✅ Found          ❌ Not Found                                 │
│          │               │                                         │
│          ▼               ▼                                         │
│  ┌──────────────┐  ┌──────────────────────────┐                    │
│  │ ShadowSub =  │  │ ShadowSub =              │                   │
│  │ {             │  │ {                         │                   │
│  │   newName: OK │  │   newName: (stale TNP)   │                   │
│  │   oldName: OK │  │   oldName: "?Edge1"      │                   │
│  │ }             │  │ }         ▲               │                   │
│  └──────────────┘  │           │               │                   │
│                    │     MISSING_PREFIX "?"     │                   │
│                    │     prepended by           │                   │
│                    │     PropertyLinks          │                   │
│                    └──────────────────────────┘                    │
│                                                                    │
│  The "?" prefix signals: "I couldn't resolve this TNP name,       │
│  the old indexed name may still work but I'm not sure."           │
└────────────────────────────────────────────────────────────────────┘
```

### 3.3 The `ElementNamePair` Struct

Defined in `src/App/ElementNamingUtils.h`:

```cpp
struct ElementNamePair {
    std::string newName;  // TNP-encoded mapped name
    std::string oldName;  // Short indexed name (e.g., "Edge1")
    
    void swap(ElementNamePair& other) noexcept;
};
```

---

## 4. DressUp Feature Class Hierarchy

```
┌─────────────────────────────────────────────────────────────┐
│                   DRESSUP CLASS HIERARCHY                     │
│                                                             │
│  App::DocumentObject                                        │
│  └── Part::Feature                                          │
│      └── PartDesign::Feature                                │
│          └── PartDesign::FeatureAddSub                      │
│              └── PartDesign::DressUp                         │
│                  ├── PartDesign::Fillet     (edge-based)    │
│                  ├── PartDesign::Chamfer    (edge-based)    │
│                  └── PartDesign::Thickness  (face-based)    │
│                                                             │
│  Key Properties (DressUp):                                  │
│  ┌────────────────────────────┬──────────────────────────┐  │
│  │ Property                   │ Type                     │  │
│  ├────────────────────────────┼──────────────────────────┤  │
│  │ Base                       │ PropertyLinkSub          │  │
│  │ SupportTransform           │ PropertyBool             │  │
│  └────────────────────────────┴──────────────────────────┘  │
│                                                             │
│  Key Methods:                                               │
│  ┌────────────────────────────┬──────────────────────────┐  │
│  │ Method                     │ Used By                  │  │
│  ├────────────────────────────┼──────────────────────────┤  │
│  │ getContinuousEdges()       │ Fillet, Chamfer          │  │
│  │ getFaces()                 │ Thickness                │  │
│  │ getBaseObject()            │ All DressUp              │  │
│  │ getAddSubShape()           │ All DressUp              │  │
│  └────────────────────────────┴──────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 5. Data Flow: Fillet Recompute

```
┌─────────────────────────────────────────────────────────────────────┐
│               FILLET RECOMPUTE DATA FLOW                             │
│                                                                     │
│  Step 1: Get base shape                                             │
│  ┌──────────────┐                                                   │
│  │ getBaseObject │─────▶ Part::Feature* base = Pad                  │
│  └──────────────┘                                                   │
│          │                                                          │
│  Step 2: Get shadow subs from PropertyLinkSub                       │
│          ▼                                                          │
│  ┌──────────────────────┐                                           │
│  │ Base.getShadowSubs() │─────▶ vector<ElementNamePair>             │
│  └──────────────────────┘       [{newName: "...", oldName: "..."}]  │
│          │                                                          │
│  Step 3: Resolve each sub-element name                              │
│          ▼                                                          │
│  ┌──────────────────────────────────────────────────┐               │
│  │ For each ShadowSub:                              │               │
│  │                                                  │               │
│  │   ref = newName.size() ? newName : oldName       │               │
│  │                        │                         │               │
│  │              ┌─────────┴─────────┐               │               │
│  │              ▼                   ▼               │               │
│  │   shape.getSubShape(ref)   (try TNP name)       │               │
│  │              │                                   │               │
│  │        ┌─────┴──────┐                            │               │
│  │        │            │                            │               │
│  │     Not Null      Null                           │               │
│  │        │            │                            │               │
│  │        │     ┌──────▼──────────────────┐         │               │
│  │        │     │ FALLBACK (NEW FIX):     │         │               │
│  │        │     │ fallback = oldName      │         │               │
│  │        │     │ if starts with '?':     │         │               │
│  │        │     │   strip '?' prefix      │         │               │
│  │        │     │ getSubShape(fallback)   │         │               │
│  │        │     └──────┬──────────────────┘         │               │
│  │        │            │                            │               │
│  │        ▼            ▼                            │               │
│  │   ┌────────────────────┐                         │               │
│  │   │ Process Edge:      │                         │               │
│  │   │  - Check C0 cont.  │                         │               │
│  │   │  - Add to result   │                         │               │
│  │   └────────────────────┘                         │               │
│  └──────────────────────────────────────────────────┘               │
│          │                                                          │
│  Step 4: Execute OCC fillet operation                               │
│          ▼                                                          │
│  ┌──────────────────────┐                                           │
│  │ BRepFilletAPI_       │─────▶ New TopoDS_Shape with fillet        │
│  │ MakeFillet           │       + new ElementMap                    │
│  └──────────────────────┘                                           │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 6. OpenCascade Integration Points

```
┌─────────────────────────────────────────────────────────────────┐
│              OCC TYPE MAPPING                                    │
│                                                                 │
│  FreeCAD Type         │  OCC Type           │  Short Prefix     │
│  ─────────────────────┼─────────────────────┼────────────────── │
│  Face                 │  TopoDS_Face        │  "Face"           │
│  Edge                 │  TopoDS_Edge        │  "Edge"           │
│  Vertex               │  TopoDS_Vertex      │  "Vertex"         │
│  Wire                 │  TopoDS_Wire        │  "Wire"           │
│  Shell                │  TopoDS_Shell       │  "Shell"          │
│  Solid                │  TopoDS_Solid       │  "Solid"          │
│  Compound             │  TopoDS_Compound    │  "Compound"       │
│                                                                 │
│  Shape Type Enum:                                               │
│  TopAbs_EDGE   ← Used in getContinuousEdges()                  │
│  TopAbs_FACE   ← Used in getFaces()                            │
│  TopAbs_WIRE   ← Expanded to edges in getContinuousEdges()     │
└─────────────────────────────────────────────────────────────────┘
```

---

## 7. Element Map Version

The element map version string is stored per-body and controls whether TNP
features are active:

```cpp
// Checked in tests:
if self.Body.Shape.ElementMapVersion == "":
    return  # ElementMap not available — skip TNP tests
```

```
┌────────────────────────────────────────────────────────────────┐
│              ELEMENT MAP VERSION GATING                          │
│                                                                │
│  ElementMapVersion == ""       │  ElementMapVersion != ""       │
│  ─────────────────────────────┼──────────────────────────────  │
│  • Legacy mode                │  • TNP-aware mode              │
│  • Short names only           │  • Full TNP names + maps       │
│  • No shadow subs             │  • Shadow subs populated       │
│  • Old recompute behavior     │  • Stable references           │
│  • TNP tests skip             │  • TNP tests run               │
└────────────────────────────────────────────────────────────────┘
```

---

*Next: [03 — C++ Fix Technical Reference](./03_cpp_fix_reference.md)*
