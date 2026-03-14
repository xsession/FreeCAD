# Mesh Module

> **Library**: `Mesh.dll` / `libMesh.so`  
> **Source**: `src/Mod/Mesh/`  
> **Files**: ~148 .cpp · ~193 .h · ~5 .py  
> **Dependencies**: FreeCADApp, FreeCADBase, WildMagic4

---

## 📋 Overview

The **Mesh** module handles **triangular mesh** (tessellated surface) data. It provides:

- **MeshFeature** — mesh-bearing DocumentObject
- **Mesh kernel** — half-edge data structure for mesh operations
- **Import/Export** — STL, OBJ, PLY, OFF, AMF, 3MF, BMS, SMF, IV
- **Operations** — Boolean (union/intersect/cut), refine, smooth, fill holes, decimation, segmentation
- **WildMagic4** — embedded math library for computational geometry

Mesh is primarily for import/export and visualization of tessellated surfaces, not for parametric modeling.

---

## 🏗️ Architecture

| Component | Description |
|---|---|
| `MeshFeature` | DocumentObject holding a mesh |
| `MeshObject` | Mesh data container |
| `MeshKernel` | Half-edge mesh data structure |
| `Facet` | Triangle face |
| `Edge` | Mesh edge |
| `MeshPoint` | Vertex |
| `SetOperations` | Boolean operations on meshes |
| `Evaluation` | Mesh quality analysis |
| `WildMagic4/` | Computational geometry library (BSpline fitting, distance, intersection) |

### Supported Formats

| Format | Import | Export | Description |
|---|---|---|---|
| STL | ✅ | ✅ | Stereolithography (binary & ASCII) |
| OBJ | ✅ | ✅ | Wavefront |
| PLY | ✅ | ✅ | Stanford polygon |
| OFF | ✅ | ✅ | Object File Format |
| AMF | ✅ | ✅ | Additive Manufacturing |
| 3MF | ✅ | ✅ | 3D Manufacturing Format |
| BMS | ✅ | ✅ | FreeCAD binary mesh |
| SMF | ✅ | ✅ | Simple Mesh Format |
| IV | ✅ | — | Open Inventor |
| VRML | ✅ | ✅ | Virtual Reality Modeling |
| X3D | — | ✅ | X3D format |

---

## 📅 Historical Timeline

| Year | Milestone |
|---|---|
| 2002 | Initial mesh module — STL support |
| 2005 | Boolean operations on meshes |
| 2008 | OBJ, PLY, OFF support |
| 2012 | WildMagic4 integration |
| 2015 | Mesh evaluation tools |
| 2020 | AMF, 3MF support |
| 2025 | Performance improvements |

---

*Part of the [FreeCAD Documentation Hub](../README.md)*
