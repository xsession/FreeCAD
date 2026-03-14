# FreeCAD — Enterprise Developer Documentation

> **Version** 1.2.0-dev · **Generated** 2026-03-14 · **License** LGPL-2.1-or-later

---

## 📚 Documentation Portal

Welcome to the central developer documentation for the FreeCAD project.
This documentation covers every module, core component, and cross-cutting
system in the codebase with architecture diagrams, historical context,
and visual infographics.

---

## 🗂️ Documentation Map

### Core Framework

| Module | Docs | Description |
|--------|------|-------------|
| [**Base**](./modules/Base.md) | [Architecture SVG](./svg/base_architecture.svg) | Math primitives, I/O, units, type system, serialization |
| [**App**](./modules/App.md) | [Architecture SVG](./svg/app_architecture.svg) | Documents, properties, expressions, element maps, extensions |
| [**Gui**](./modules/Gui.md) | [Architecture SVG](./svg/gui_architecture.svg) | 3D viewer, commands, selection, workbenches, task panels |

### CAD & Design Modules

| Module | Docs | Description |
|--------|------|-------------|
| [**Part**](./modules/Part.md) | [Architecture SVG](./svg/part_architecture.svg) | OpenCascade wrapper, B-Rep shapes, booleans, attachment |
| [**PartDesign**](./modules/PartDesign.md) | [Architecture SVG](./svg/partdesign_architecture.svg) | Parametric feature-based modeling, Body, Pad, Pocket, DressUp |
| [**Sketcher**](./modules/Sketcher.md) | [Architecture SVG](./svg/sketcher_architecture.svg) | 2D constraint solver, geometric constraints, PlaneGCS |
| [**Assembly**](./modules/Assembly.md) | [Architecture SVG](./svg/assembly_architecture.svg) | Assembly constraints, OndselSolver, joints, BOM |
| [**Surface**](./modules/Surface.md) | [Architecture SVG](./svg/surface_architecture.svg) | NURBS surface creation, filling, sections, blending |

### Analysis & Simulation

| Module | Docs | Description |
|--------|------|-------------|
| [**FEM**](./modules/FEM.md) | [Architecture SVG](./svg/fem_architecture.svg) | Finite Element Analysis, solvers (CalculiX, Elmer, Z88) |
| [**CAM**](./modules/CAM.md) | [Architecture SVG](./svg/cam_architecture.svg) | CNC toolpath generation, GCode, post-processors |
| [**Inspection**](./modules/Inspection.md) | — | Shape distance comparison, deviation color maps |
| [**Measure**](./modules/Measure.md) | — | Distance, angle, area, radius measurement |

### Visualization & Output

| Module | Docs | Description |
|--------|------|-------------|
| [**TechDraw**](./modules/TechDraw.md) | [Architecture SVG](./svg/techdraw_architecture.svg) | Technical drawing generation, views, dimensions, templates |
| [**Mesh**](./modules/Mesh.md) | [Architecture SVG](./svg/mesh_architecture.svg) | Triangle mesh processing, STL/OBJ/PLY import/export |
| [**MeshPart**](./modules/MeshPart.md) | — | Mesh↔Part bridge, tessellation, cross-sections |
| [**Spreadsheet**](./modules/Spreadsheet.md) | [Architecture SVG](./svg/spreadsheet_architecture.svg) | Cell expressions, formulas, XLSX import |

### 2D Design & Architecture

| Module | Docs | Description |
|--------|------|-------------|
| [**Draft**](./modules/Draft.md) | [Architecture SVG](./svg/draft_architecture.svg) | 2D drafting, DXF/DWG/SVG import/export, arrays |
| [**BIM**](./modules/BIM.md) | [Architecture SVG](./svg/bim_architecture.svg) | Building modeling, IFC, walls, roofs, structures |

### Data & I/O

| Module | Docs | Description |
|--------|------|-------------|
| [**Import**](./modules/Import.md) | [Architecture SVG](./svg/import_architecture.svg) | STEP/IGES import/export via OCC |
| [**Material**](./modules/Material.md) | [Architecture SVG](./svg/material_architecture.svg) | Material database, properties, FCMat cards |
| [**Points**](./modules/Points.md) | — | Point cloud data, E57/PLY/PCD |
| [**OpenSCAD**](./modules/OpenSCAD.md) | — | CSG import/export, OpenSCAD interop |

### Specialized & Utility

| Module | Docs | Description |
|--------|------|-------------|
| [**ReverseEngineering**](./modules/ReverseEngineering.md) | — | Point cloud → surface fitting, Poisson reconstruction |
| [**Robot**](./modules/Robot.md) | — | Industrial 6-axis robot simulation, trajectories |
| [**Start**](./modules/Start.md) | — | Welcome screen, recent files, examples |
| [**AddonManager**](./modules/AddonManager.md) | — | Third-party addon install/update/management |
| [**Utilities**](./modules/Utilities.md) | — | Help browser, Show (TempoVis), Plot charting |

### Cross-Cutting Systems

| System | Docs | Description |
|--------|------|-------------|
| [**Element Maps & TNP**](./systems/ElementMaps_TNP.md) | [Pipeline SVG](./svg/tnp_pipeline.svg) | Topological naming, element maps, shadow subs |
| [**Build System**](./systems/BuildSystem.md) | [Pipeline SVG](./svg/build_pipeline.svg) | CMake, pixi, vcpkg, presets |
| [**Property System**](./systems/PropertySystem.md) | [Hierarchy SVG](./svg/property_hierarchy.svg) | Property types, serialization, links |
| [**Expression Engine**](./systems/ExpressionEngine.md) | [Pipeline SVG](./svg/expression_pipeline.svg) | Cell formulas, property expressions, dependencies |

---

## 📊 Codebase Statistics

| Category | C++ Files | Header Files | Python Files | Total |
|----------|----------:|-------------:|-------------:|------:|
| **Core** (Base + App + Gui) | 527 | 499 | 8 | 1,034 |
| **Modules** (all Mod/) | 1,357 | 1,364 | 1,623 | 4,344 |
| **Grand Total** | **1,884** | **1,863** | **1,631** | **5,378** |

---

## 🏗️ Architecture Overview

See the [full system architecture SVG](./svg/freecad_system_architecture.svg) for a visual overview.

The FreeCAD codebase follows a layered architecture:

```
┌─────────────────────────────────────────────────────────┐
│                    USER INTERFACE                         │
│  Workbenches · Task Panels · 3D Viewer · Property Editor │
├─────────────────────────────────────────────────────────┤
│                     Gui (FreeCADGui)                      │
│  Commands · ViewProviders · Selection · Navigation        │
├─────────────────────────────────────────────────────────┤
│                     App (FreeCADApp)                      │
│  Documents · Objects · Properties · Expressions · Links   │
├─────────────────────────────────────────────────────────┤
│                    Base (FreeCADBase)                     │
│  Math · Units · I/O · Type System · Console · Python     │
├─────────────────────────────────────────────────────────┤
│                   External Libraries                     │
│  OpenCascade · Coin3D · Qt · Python · Boost · Eigen      │
└─────────────────────────────────────────────────────────┘
```

---

*FreeCAD is free software under LGPL-2.1-or-later · [Source](https://github.com/FreeCAD/FreeCAD)*
