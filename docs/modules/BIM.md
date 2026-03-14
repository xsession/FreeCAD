# BIM Module (Building Information Modeling)

> **Source**: `src/Mod/BIM/`  
> **Files**: ~0 .cpp · ~215 .py  
> **Dependencies**: FreeCADApp, Part, Draft  
> **Type**: Pure Python

---

## 📋 Overview

The **BIM** module (formerly "Arch") provides **architectural and building design** tools. It's entirely Python-based and includes:

- **Architectural objects** — Wall, Structure, Window, Roof, Floor, Space, Site, Building
- **Structural elements** — Column, Beam, Slab, Rebar, Foundation
- **IFC integration** — Native IFC import/export (via nativeifc + IfcOpenShell)
- **BOM/Schedule** — Quantity takeoff, cost estimation
- **2D output** — Section planes, working planes

BIM merged the older Arch workbench with enhanced IFC capabilities.

---

## 🏗️ Architecture

### Object Types

| Category | Objects |
|---|---|
| **Walls & Structure** | ArchWall, ArchStructure, ArchColumn |
| **Openings** | ArchWindow, ArchDoor |
| **Roof & Floor** | ArchRoof, ArchFloor, ArchSlab |
| **Space & Site** | ArchSpace, ArchSite, ArchBuilding, ArchBuildingPart |
| **Reinforcement** | ArchRebar (straight, bent, stirrup, etc.) |
| **MEP** | ArchPipe, ArchPipeConnector |
| **Reference** | ArchReference (external file reference) |
| **Annotations** | ArchSectionPlane, ArchAxis, ArchGrid |

### IFC Integration (nativeifc)

```
IFC File (.ifc)
  ↔ nativeifc bridge
  ↔ IfcOpenShell (Python library)
  ↔ FreeCAD BIM objects
```

Supports IFC2x3 and IFC4 schemas:
- Import: Full geometry + properties + materials + relationships
- Export: Compliant IFC output for BIM software interchange
- Round-trip: Edit IFC files preserving structure

### Building Hierarchy

```
Site
  └── Building
       └── Floor (BuildingPart/Storey)
            ├── Wall
            │    └── Window / Door
            ├── Structure (column, beam)
            ├── Slab
            ├── Space (room)
            └── Equipment
```

---

## 📅 Historical Timeline

| Year | Milestone |
|---|---|
| 2012 | Arch workbench created |
| 2014 | Wall, Window, Structure objects |
| 2016 | IFC import via IfcOpenShell |
| 2018 | Rebar, Pipe support |
| 2020 | NativeIFC initiative starts |
| 2022 | **Renamed Arch → BIM** |
| 2023 | NativeIFC integration matures |
| 2025 | IFC4 full support, schedule improvements |

---

*Part of the [FreeCAD Documentation Hub](../README.md)*
