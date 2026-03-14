# PartDesign Module

> **Library**: `PartDesign.dll` / `libPartDesign.so`  
> **Source**: `src/Mod/PartDesign/`  
> **Dependencies**: FreeCADApp, Part, Sketcher  
> **Architecture SVG**: [partdesign_architecture.svg](../svg/partdesign_architecture.svg)  
> **Detailed Docs**: [src/Mod/PartDesign/docs/](../../src/Mod/PartDesign/docs/README.md)

---

## 📋 Overview

**PartDesign** is FreeCAD's **feature-based parametric solid modeling** workbench. It follows a strict Body-centric workflow:

- A **Body** contains a single contiguous solid
- Features are **added or subtracted sequentially** (Pad, Pocket, Revolution, etc.)
- The **Tip** marks the "current state" of the solid
- **Sketches** provide 2D profiles for 3D operations
- **DressUp** features modify edges/faces (Fillet, Chamfer, Draft, Thickness)
- **Patterns** replicate features (Linear, Polar, Mirrored, MultiTransform)

PartDesign is the recommended workflow for single-body solid models.

---

## 🏗️ Architecture

### Body Container

```
Body (extends Part::BodyBase)
  ├── Origin
  │    ├── XY_Plane, XZ_Plane, YZ_Plane
  │    └── X_Axis, Y_Axis, Z_Axis
  ├── Feature chain
  │    ├── Sketch001 → Pad (Tip)
  │    ├── Sketch002 → Pocket
  │    ├── Fillet → on Pocket edges
  │    └── LinearPattern → of Pocket
  └── Tip → pointer to "current" feature
```

### Feature Categories

#### ➕ Additive (add material)
| Feature | Description |
|---|---|
| `Pad` | Linear extrusion of sketch profile |
| `Revolution` | Rotational sweep around axis |
| `AdditiveLoft` | Sweep through multiple profiles |
| `AdditivePipe` | Sweep along a spine curve |
| `AdditiveHelix` | Helical sweep |
| `AdditiveBox/Cylinder/Sphere/Cone/Torus/Wedge/Prism/Ellipsoid` | Primitive shapes |

#### ➖ Subtractive (remove material)
| Feature | Description |
|---|---|
| `Pocket` | Linear cut into solid |
| `Groove` | Rotational cut |
| `SubtractiveLoft` | Multi-profile cut |
| `SubtractivePipe` | Cut along spine |
| `SubtractiveHelix` | Helical cut |
| `Subtractive*` primitives | Primitive cuts |

#### ✨ DressUp (modify edges/faces)
| Feature | Description |
|---|---|
| `Fillet` | Round edges |
| `Chamfer` | Bevel edges |
| `Draft` | Taper faces |
| `Thickness` | Shell a solid (hollow) |

All DressUp features extend `FeatureDressUp`, which includes TNP fallback logic (strips `?` prefix, tries short names).

#### 🔄 Patterns (replicate features)
| Feature | Description |
|---|---|
| `LinearPattern` | Array along direction |
| `PolarPattern` | Array around axis |
| `Mirrored` | Mirror across plane |
| `MultiTransform` | Combine multiple patterns |
| `Scaled` | Scale factor (within MultiTransform) |

#### 📌 Datum Geometry
| Feature | Description |
|---|---|
| `DatumPlane` | Reference plane |
| `DatumLine` | Reference line |
| `DatumPoint` | Reference point |
| `ShapeBinder` | Reference to external geometry |
| `SubShapeBinder` | Reference to sub-elements |

### Feature Pipeline

```
1. User creates/edits a Sketch
2. Sketch solver resolves constraints → closed wire(s)
3. Feature (Pad/Pocket/etc.) uses sketch profile
4. OCC Boolean operation (add/subtract from Body solid)
5. ElementMap propagates TNP names through operation
6. Body.Tip updated → solid state refreshed
7. Dependent features recompute
```

---

## 🔧 TNP DressUp Fix

The `FeatureDressUp.cpp` fix addresses stale topological names after model edits:

```
getContinuousEdges() / getFaces():
  1. Try element name directly → success? done
  2. Name starts with "?" (MISSING_PREFIX) → strip it
  3. Try stripped name as MappedName → success? done
  4. Try as IndexedName (e.g., "Edge3") → success? done
  5. All else fails → skip gracefully (no crash)
```

This prevents Fillet/Chamfer from crashing when referenced edges are renamed after upstream edits.

---

## 📅 Historical Timeline

| Year | Milestone |
|---|---|
| 2008 | Initial Pad/Pocket — basic extrusion |
| 2010 | Fillet, Chamfer, Revolution |
| 2012 | Body concept introduced |
| 2015 | **PartDesign Next** rewrite — strict Body workflow |
| 2016 | Loft, Pipe features |
| 2019 | Helix, Additive/Subtractive Primitives |
| 2020 | ShapeBinder improvements |
| 2023 | TNP integration — element maps in all features |
| 2025 | SubShapeBinder enhancements |
| 2026 | DressUp TNP fallback fix (Fillet/Chamfer) |

---

## 📂 Key Files

| File | Purpose |
|---|---|
| `App/Body.h/cpp` | Body container |
| `App/Feature.h/cpp` | Base PartDesign feature |
| `App/FeatureAddSub.h/cpp` | Add/subtract base |
| `App/FeaturePad.h/cpp` | Pad (extrusion) |
| `App/FeaturePocket.h/cpp` | Pocket (cut) |
| `App/FeatureRevolution.h/cpp` | Revolution |
| `App/FeatureDressUp.h/cpp` | DressUp base (TNP fallback) |
| `App/FeatureFillet.h/cpp` | Fillet |
| `App/FeatureChamfer.h/cpp` | Chamfer |
| `App/FeatureLinearPattern.h/cpp` | Linear array |
| `App/FeaturePolarPattern.h/cpp` | Polar array |
| `App/FeatureMirrored.h/cpp` | Mirror |
| `App/DatumPlane.h/cpp` | Reference plane |
| `App/ShapeBinder.h/cpp` | Geometry reference |
| `Gui/ViewProvider*.cpp` | Visual representation |

---

## 🔗 Dependency Graph

```
PartDesign depends on:
  ├── Part (TopoShape, BodyBase, Boolean ops)
  ├── Sketcher (2D profiles)
  ├── App (Document, Property, ElementMap)
  └── Base (Math, Types)

Used by:
  ├── Assembly (body references)
  ├── FEM (mesh from solid)
  ├── TechDraw (drawing projections)
  └── CAM (toolpaths from solid)
```

---

## 🧪 Test Suite

- **TestSketchOnFace.py** — 30 tests for sketch-on-face, Pad, Pocket, Fillet on all 6 box faces
- **TestPad.py**, **TestPocket.py**, **TestRevolution.py** — parametric feature tests
- **TestDressUp.py** — Fillet/Chamfer/Draft tests
- All tests pass: `30/30` (sketch-on-face) + full regression suite `68/68`

---

*Part of the [FreeCAD Documentation Hub](../README.md)*
