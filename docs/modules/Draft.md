# Draft Module

> **Source**: `src/Mod/Draft/`  
> **Files**: ~2 .cpp · ~2 .h · ~238 .py  
> **Dependencies**: FreeCADApp, Part  
> **Type**: Mostly Python

---

## 📋 Overview

The **Draft** module provides **2D drafting and basic 3D modeling** tools, similar to a lightweight 2D CAD. It's almost entirely Python-based (~238 .py files):

- **2D shapes** — Wire, Circle, Rectangle, Polygon, BSpline, BezCurve, Dimension, Text, Label
- **Modification tools** — Move, Rotate, Scale, Mirror, Offset, Trim, Array, Clone
- **Arrays** — OrthoArray, PolarArray, CircularArray, PathArray, PointArray
- **DXF/DWG import/export** — 2D drawing interchange
- **Annotation** — Dimensions, Text, Labels, ShapeStrings (text from fonts)
- **Snapping** — comprehensive object snap system (endpoint, midpoint, center, etc.)
- **Working Plane** — configurable 2D drawing plane

---

## 🏗️ Architecture

### Object Types

| Object | Description |
|---|---|
| `Wire` | Polyline (connected line segments) |
| `Circle` | Circle or arc |
| `Rectangle` | Rectangular shape |
| `Polygon` | Regular polygon |
| `BSpline` | B-spline curve |
| `BezCurve` | Bezier curve |
| `Dimension` | Linear/angular dimension |
| `Text` | Text annotation |
| `Label` | Leader + text label |
| `ShapeString` | Text extruded from font |
| `Array` | Rectangular/polar/circular pattern |
| `Clone` | Parametric copy |
| `Point` | Single point |
| `Facebinder` | Face reference |

### Snap System

```
DraftSnap
  ├── Endpoint · Midpoint · Center · Perpendicular
  ├── Intersection · Extension · Nearest
  ├── Grid · Angle · Parallel
  └── WorkingPlane · Special (ortho, constrain)
```

### Import/Export

| Format | Description |
|---|---|
| DXF | AutoCAD Drawing Exchange (via ezdxf) |
| DWG | AutoCAD native (via ODA converter) |
| SVG | Scalable Vector Graphics |
| OCA | Open CAD format |

---

## 📅 Historical Timeline

| Year | Milestone |
|---|---|
| 2008 | Initial Draft module |
| 2010 | Snap system, arrays |
| 2013 | DXF/DWG improvements |
| 2016 | Working plane overhaul |
| 2019 | Array objects (OrthoArray, PolarArray) |
| 2021 | BIM integration begins |
| 2023 | Annotation improvements |
| 2025 | Performance, ezdxf migration |

---

*Part of the [FreeCAD Documentation Hub](../README.md)*
