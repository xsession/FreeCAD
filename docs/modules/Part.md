# Part Module

> **Library**: `Part.dll` / `libPart.so`  
> **Source**: `src/Mod/Part/`  
> **Files**: ~263 .cpp · ~162 .h · ~42 .py  
> **Dependencies**: FreeCADApp, FreeCADBase, OpenCASCADE (OCCT)  
> **Architecture SVG**: [part_architecture.svg](../svg/part_architecture.svg)

---

## 📋 Overview

The **Part** module is FreeCAD's **OpenCASCADE kernel wrapper** — it bridges OCCT's BRep (Boundary Representation) geometry engine to FreeCAD's document/property model. It provides:

- **TopoShape** — the fundamental shape class wrapping `TopoDS_Shape` with TNP element maps
- **Geometry classes** — curves, surfaces, B-splines
- **Boolean operations** — Cut, Fuse, Common, Section, BooleanFragments
- **Primitives** — Box, Cylinder, Cone, Sphere, Torus, Helix, etc.
- **Feature operations** — Extrusion, Revolution, Loft, Sweep, Fillet, Chamfer, Offset, Thickness
- **Attachment system** — positioning objects relative to geometry references
- **STEP/IGES/BREP import/export**

Almost every geometric module in FreeCAD depends on Part.

---

## 🏗️ Architecture

### TopoShape — The Core

`TopoShape` is FreeCAD's central shape class. It wraps `OCC::TopoDS_Shape` and adds:

- **Element maps** — TNP name tracking across operations
- **Python bindings** — `Part.Shape`, `Part.Wire`, `Part.Face`, etc.
- **Serialization** — save/restore to BREP format in `.FCStd`
- **Sub-shape access** — `.Edges`, `.Faces`, `.Vertexes`, `.Shells`, `.Solids`

Hierarchy:
```
TopoShape
├── TopoShapeVertex
├── TopoShapeEdge  
├── TopoShapeWire
├── TopoShapeFace
├── TopoShapeShell
├── TopoShapeSolid
└── TopoShapeCompound / TopoShapeCompSolid
```

### Boolean Operations

| Operation | OCCT Algorithm | Result |
|---|---|---|
| **Cut** | `BRepAlgoAPI_Cut` | A minus B |
| **Fuse** | `BRepAlgoAPI_Fuse` | A union B |
| **Common** | `BRepAlgoAPI_Common` | A intersect B |
| **Section** | `BRepAlgoAPI_Section` | Intersection curves |
| **BooleanFragments** | `BOPAlgo_MakerVolume` | All split pieces |
| **MultiFuse** | N-way fuse | Union of N shapes |
| **MultiCommon** | N-way intersect | Common of N shapes |

### Geometry Classes

| Category | Classes |
|---|---|
| **Curves** | `GeomLine`, `GeomCircle`, `GeomEllipse`, `GeomArcOfCircle/Ellipse/Parabola/Hyperbola`, `GeomBSplineCurve`, `GeomBezierCurve`, `GeomOffsetCurve` |
| **Surfaces** | `GeomPlane`, `GeomCylinder`, `GeomCone`, `GeomSphere`, `GeomToroid`, `GeomBSplineSurface`, `GeomBezierSurface`, `GeomOffsetSurface` |
| **2D** | `Geom2dPoint`, `Geom2dLine`, `Geom2dCircle`, `Geom2dEllipse`, `Geom2dBSplineCurve` |

### Primitives

Built-in parametric primitive features:

| Primitive | Parameters |
|---|---|
| `Box` | Length, Width, Height |
| `Cylinder` | Radius, Height, Angle |
| `Cone` | Radius1, Radius2, Height, Angle |
| `Sphere` | Radius, Angle1, Angle2, Angle3 |
| `Torus` | Radius1, Radius2, Angle1, Angle2, Angle3 |
| `Prism` | Polygon, Circumradius, Height |
| `Helix` | Pitch, Height, Radius, Angle |
| `Spiral` | Growth, Rotations |
| `Wedge` | Various edge parameters |
| `Ellipsoid` | Semi-axes |

### Attachment System

The `Attacher` / `AttachEngine` system positions objects relative to geometry references:

```python
sketch.AttachmentSupport = [(body_face, "Face6")]
sketch.MapMode = "FlatFace"
```

Attachment modes: FlatFace, Tangent, Normal, Through, Translate, Rotate, etc.

### Part2DObject & FaceMaker

- `Part2DObject` — base for 2D features (sketches, draft shapes)
- `FaceMaker` — converts wire collections into faces
  - `FaceMakerBullseye` — handles nested wires (holes inside faces)
  - `FaceMakerSimple` — simple planar face from single wire
  - `FaceMakerCheese` — faces with holes (Swiss cheese approach)

### BodyBase

`BodyBase` defines the container concept used by PartDesign:
```
BodyBase (Part module)
  └── Body (PartDesign module)
       └── contains features in a chain
```

---

## 📅 Historical Timeline

| Year | Milestone |
|---|---|
| 2002 | Initial OCC wrapper — TopoShape, basic primitives |
| 2005 | Boolean operations (Cut, Fuse, Common) |
| 2007 | STEP/IGES import/export |
| 2010 | Geometry class hierarchy |
| 2012 | Attachment system |
| 2014 | BooleanFragments, MultiFuse, MultiCommon |
| 2016 | FaceMaker framework (Bullseye, Cheese) |
| 2019 | Enhanced B-spline support |
| 2020 | Offset3DSurface, Tube |
| 2023 | TNP element maps integrated into TopoShape |
| 2025 | OCCT 7.8 compatibility updates |

---

## 📂 Key Files

| File | Purpose |
|---|---|
| `App/TopoShape.h/cpp` | Core shape class |
| `App/TopoShapeEdgePy.xml` | Python binding for edges |
| `App/TopoShapeFacePy.xml` | Python binding for faces |
| `App/PartFeature.h/cpp` | Shape-bearing DocumentObject |
| `App/Part2DObject.h/cpp` | 2D feature base (sketches) |
| `App/Geometry.h/cpp` | Curve/surface geometry |
| `App/Attacher.h/cpp` | Attachment engine |
| `App/BodyBase.h/cpp` | Body container base |
| `App/FaceMaker*.h/cpp` | Wire-to-face conversion |
| `App/FeatureBoolean.h/cpp` | Boolean operation features |
| `App/FeaturePartBox.h/cpp` | Box primitive |
| `App/FeatureExtrusion.h/cpp` | Extrusion feature |
| `App/FeatureRevolution.h/cpp` | Revolution feature |
| `App/FeatureFillet.h/cpp` | Fillet feature |
| `App/FeatureChamfer.h/cpp` | Chamfer feature |

---

## 🔗 Dependency Graph

```
Part depends on:
  ├── App (Document, Property, ElementMap)
  ├── Base (Vector3d, Placement, etc.)
  └── OpenCASCADE (BRep kernel, STEP/IGES, Boolean)

Used by:
  ├── PartDesign (Body, features)
  ├── Sketcher (Part2DObject)
  ├── FEM (mesh from shape)
  ├── TechDraw (shape projection)
  ├── CAM (toolpath from shape)
  ├── Draft (2D shapes)
  ├── BIM (architectural shapes)
  ├── Surface (surface operations)
  ├── MeshPart (mesh from shape)
  └── Assembly (shape references)
```

---

*Part of the [FreeCAD Documentation Hub](../README.md)*
