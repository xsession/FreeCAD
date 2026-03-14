# MeshPart Module

> **Source**: `src/Mod/MeshPart/` · ~16 .cpp · ~14 .h · ~3 .py  
> **Dependencies**: FreeCADApp, Part, Mesh

## 📋 Overview
Bridge between Part (BRep) and Mesh (tessellation) modules. Provides mesh generation from shapes and curve projection.

## Key Features
| Feature | Description |
|---|---|
| `Mesher` | Generate mesh from TopoShape (standard/Mefisto/Netgen) |
| `MeshAlgos` | Mesh algorithms (section, projection) |
| `CurveProjector` | Project curves onto mesh surfaces |
| `CrossSections` | Generate cross-section curves from mesh |
| `FlipNormals` | Fix mesh normal orientation |

---
*Part of the [FreeCAD Documentation Hub](../README.md)*
