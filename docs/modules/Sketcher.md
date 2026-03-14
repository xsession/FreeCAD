# Sketcher Module

> **Library**: `Sketcher.dll` / `libSketcher.so`  
> **Source**: `src/Mod/Sketcher/`  
> **Files**: ~77 .cpp · ~100 .h · ~16 .py  
> **Dependencies**: FreeCADApp, Part, Eigen3  
> **Architecture SVG**: [sketcher_architecture.svg](../svg/sketcher_architecture.svg)

---

## 📋 Overview

The **Sketcher** module provides **2D parametric constraint-based sketching**, which is the foundation for most 3D modeling in FreeCAD. Key features:

- **Geometry elements** — points, lines, arcs, circles, ellipses, B-splines, conics
- **Constraint solver** — PlaneGCS (custom built-in solver, no external dependency)
- **DOF analysis** — degrees of freedom tracking, redundancy/conflict detection
- **Construction geometry** — reference geometry that doesn't form profiles
- **External geometry** — references to edges from other features
- **Auto-constraint** — automatic constraint suggestion during drawing

Sketches serve as input profiles for PartDesign (Pad, Pocket, Revolution, etc.) and other operations.

---

## 🏗️ Architecture

### SketchObject

Central class — extends `Part2DObject`:

```python
sketch = App.ActiveDocument.addObject("Sketcher::SketchObject", "Sketch")
sketch.addGeometry(Part.LineSegment(v1, v2))
sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 1))
```

SketchObject manages:
- **Geometry list** — ordered collection of geometric elements
- **Constraint list** — ordered collection of constraints
- **Solver state** — PlaneGCS synchronization
- **External geometry** — references to edges from other features
- **Construction mode** — geometry flagged as non-profile

### Geometry Elements

| Element | Description |
|---|---|
| `GeomPoint` | Single point |
| `GeomLineSegment` | Line between two points |
| `GeomCircle` | Full circle (center + radius) |
| `GeomArcOfCircle` | Circular arc |
| `GeomEllipse` | Full ellipse |
| `GeomArcOfEllipse` | Elliptical arc |
| `GeomArcOfParabola` | Parabolic arc |
| `GeomArcOfHyperbola` | Hyperbolic arc |
| `GeomBSplineCurve` | B-spline curve (degree, knots, control points) |

**GeometryFacade** wraps each element with:
- Construction flag (reference-only, not part of profile wire)
- Internal alignment flag (B-spline control polygon)
- Geometry ID tracking

### Constraint System

#### Geometric Constraints (no value)
| Constraint | Effect |
|---|---|
| `Coincident` | Two points share same location |
| `Tangent` | Curves touch smoothly |
| `Parallel` | Lines have same direction |
| `Perpendicular` | Lines at 90° |
| `Equal` | Equal length/radius |
| `Symmetric` | Mirror across line |
| `Horizontal` | Line/points aligned horizontally |
| `Vertical` | Line/points aligned vertically |
| `Block` | Fix all DOF of element |
| `PointOnObject` | Point lies on curve |

#### Dimensional Constraints (with value)
| Constraint | Effect |
|---|---|
| `Distance` | Length or point-point/point-line distance |
| `Angle` | Angle between lines or at point |
| `Radius` | Circle/arc radius |
| `Diameter` | Circle/arc diameter |
| `Lock` | Fix point at coordinates |
| `DistanceX/Y` | Horizontal/vertical distance |

#### Special Constraints
| Constraint | Effect |
|---|---|
| `InternalAlignment` | B-spline knot/pole alignment |
| `SnellsLaw` | Refraction constraint |

### PlaneGCS Solver

FreeCAD's built-in 2D geometric constraint solver:

```
GCS::System
  ├── addConstraint*(params)  // register constraints
  ├── solve()                  // find solution
  ├── diagnose()              // DOF, redundancy analysis
  └── getDOF()                // remaining degrees of freedom
```

**Solver algorithms** (selectable):
| Algorithm | Use Case |
|---|---|
| **DogLeg** | Default — trust-region method, robust |
| **Levenberg-Marquardt** | Alternative nonlinear least squares |
| **BFGS** | Quasi-Newton optimization |
| **SQP** | Sequential Quadratic Programming |

The solver operates on **parameters** (point coordinates, radii, angles) and minimizes constraint violation.

### DOF Analysis

```
Fully Constrained:  DOF = 0  →  green status
Under-constrained:  DOF > 0  →  orange status (N DOF remaining)
Over-constrained:   conflicts detected  →  red status
Redundant:          duplicate constraints  →  red/orange status
```

### SketchAnalysis

Automatic tools:
- **Auto-constrain** — suggest constraints based on geometry proximity
- **Merge coincident points** — fix near-coincident vertices
- **Find missing constraints** — detect unconstrained geometry
- **Remove redundant constraints** — clean up over-specification

---

## 🐍 Python API

```python
import FreeCAD as App
import Sketcher
import Part

doc = App.newDocument()
sketch = doc.addObject("Sketcher::SketchObject", "Sketch")

# Add geometry
sketch.addGeometry(Part.LineSegment(App.Vector(0,0,0), App.Vector(10,0,0)), False)
sketch.addGeometry(Part.LineSegment(App.Vector(10,0,0), App.Vector(10,10,0)), False)

# Add constraints
sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 1))
sketch.addConstraint(Sketcher.Constraint("Perpendicular", 0, 1))
sketch.addConstraint(Sketcher.Constraint("Distance", 0, 10.0))

doc.recompute()
print(f"DOF: {sketch.solve()}")
```

---

## 📅 Historical Timeline

| Year | Milestone |
|---|---|
| 2008 | Initial Sketcher with FreeGCS solver |
| 2010 | Basic constraints (Coincident, Parallel, Perpendicular) |
| 2013 | B-spline support, conic sections |
| 2015 | SketchAnalysis, auto-constraints |
| 2016 | External geometry references |
| 2018 | Improved B-spline editing |
| 2019 | Offset curve constraint |
| 2020 | Split edge, trim tools |
| 2023 | TNP integration — stable element naming |
| 2025 | Rendering/display rewrite, performance improvements |

---

## 📂 Key Files

| File | Purpose |
|---|---|
| `App/SketchObject.h/cpp` | Central sketch data model |
| `App/Sketch.h/cpp` | Solver bridge |
| `App/Constraint.h/cpp` | Constraint data types |
| `App/ExternalGeometryExtension.h/cpp` | External edge references |
| `App/GeometryFacade.h/cpp` | Geometry wrapper |
| `App/SketchAnalysis.h/cpp` | Auto-constraint tools |
| `App/planegcs/GCS.h/cpp` | Constraint solver core |
| `App/planegcs/Constraints.h/cpp` | Solver constraint types |
| `App/planegcs/Geo.h/cpp` | Solver geometry types |
| `Gui/ViewProviderSketch.h/cpp` | Sketch editing view |
| `Gui/EditModeConstraintCoinManager.h/cpp` | Constraint visualization |
| `Gui/EditModeGeometryCoinManager.h/cpp` | Geometry visualization |
| `Gui/DrawSketchHandler.h/cpp` | Drawing tool base |
| `Gui/CommandCreateGeo.cpp` | Geometry creation commands |
| `Gui/CommandConstraints.cpp` | Constraint commands |

---

## 🔗 Dependency Graph

```
Sketcher depends on:
  ├── Part (Part2DObject, geometry, TopoShape)
  ├── App (Document, Property, Expressions)
  ├── Base (Math, Types)
  └── Eigen3 (matrix operations in solver)

Used by:
  ├── PartDesign (profiles for Pad/Pocket/etc.)
  ├── Part (profiles for Extrusion/Revolution)
  └── Assembly (sketch-based joints)
```

---

*Part of the [FreeCAD Documentation Hub](../README.md)*
