# Surface Module

> **Library**: `Surface.dll` / `libSurface.so`  
> **Source**: `src/Mod/Surface/`  
> **Files**: ~24 .cpp · ~23 .h · ~5 .py  
> **Dependencies**: FreeCADApp, Part, OpenCASCADE

---

## 📋 Overview

The **Surface** module provides tools for creating and manipulating **NURBS surfaces**:

- **Filling** — create surface from boundary edges (Gordon surface)
- **GeomFillSurface** — fill bounded region with surface
- **Sections** — surface through cross-section curves
- **Extend** — extend existing surface
- **BlendCurve** — smooth transition curves between surfaces
- **CurveOnMesh** — project curve onto mesh surface

---

## 🏗️ Key Features

| Feature | Description |
|---|---|
| `Filling` | Creates a surface from a set of boundary edges and optional constraints |
| `GeomFillSurface` | Fills a bounded region with a smooth surface (Coons/Gordon patch) |
| `Sections` | Creates a surface passing through multiple cross-section curves |
| `Extend` | Extends an existing surface face |
| `BlendCurve` | Creates smooth transition curves between two surfaces |
| `CurveOnMesh` | Projects and creates a curve on a mesh surface |

All operations use OpenCASCADE surface algorithms (GeomFill, BRepOffsetAPI, etc.).

---

## 📅 Timeline

| Year | Milestone |
|---|---|
| 2016 | Initial Surface module |
| 2018 | Filling, Sections |
| 2020 | GeomFillSurface, Extend |
| 2023 | BlendCurve |
| 2025 | CurveOnMesh improvements |

---

*Part of the [FreeCAD Documentation Hub](../README.md)*
