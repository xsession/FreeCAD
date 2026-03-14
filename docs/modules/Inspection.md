# Inspection Module

> **Source**: `src/Mod/Inspection/` · ~7 .cpp · ~7 .h · ~2 .py  
> **Dependencies**: FreeCADApp, Part, Mesh

## 📋 Overview
Shape comparison and inspection tools. Compares two shapes or a shape against a mesh and visualizes deviations with color maps.

## Key Features
| Feature | Description |
|---|---|
| `InspectionFeature` | Computes distance deviation between shapes |
| `ViewProviderInspection` | Color-mapped deviation display |
| Distance-based comparison | Point-to-surface distance analysis |
| Color gradient | Red/green visualization of deviations |

Used for quality control: compare manufactured part scan against CAD nominal.

---
*Part of the [FreeCAD Documentation Hub](../README.md)*
