# Reverse Engineering Module

> **Source**: `src/Mod/ReverseEngineering/` · ~15 .cpp · ~15 .h · ~2 .py  
> **Dependencies**: FreeCADApp, Part, Mesh, Points

## 📋 Overview
Surface reconstruction from point clouds and meshes. Converts scan data into BRep surfaces.

## Key Features
| Feature | Description |
|---|---|
| `ApproxSurface` | B-spline surface approximation from points |
| `Poisson` | Poisson surface reconstruction from point cloud |
| `BSplineFitting` | Fit B-spline curves/surfaces to data |
| `MeshSegmentation` | Segment mesh into planar/cylindrical/spherical regions |
| `FitBSpline` | Interactive B-spline fitting |

Workflow: Point cloud → Mesh → Surface segmentation → B-spline fitting → BRep solid.

---
*Part of the [FreeCAD Documentation Hub](../README.md)*
