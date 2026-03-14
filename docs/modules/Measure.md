# Measure Module

> **Source**: `src/Mod/Measure/` · ~25 .cpp · ~21 .h · ~4 .py  
> **Dependencies**: FreeCADApp, Part

## 📋 Overview
Interactive measurement tools for the 3D viewer. Supports distance, angle, area, radius, and position measurements between geometry elements.

## Key Features
| Tool | Measurement |
|---|---|
| `MeasureDistance` | Point-to-point, point-to-edge, edge-to-edge |
| `MeasureAngle` | Angle between faces/edges |
| `MeasureArea` | Face surface area |
| `MeasureRadius` | Circle/arc radius |
| `MeasureLength` | Edge length |

All measurements are persistent (stored in document) and update when geometry changes.

---
*Part of the [FreeCAD Documentation Hub](../README.md)*
