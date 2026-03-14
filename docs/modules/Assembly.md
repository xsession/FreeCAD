# Assembly Module

> **Library**: `Assembly.dll` / `libAssembly.so`  
> **Source**: `src/Mod/Assembly/`  
> **Files**: ~29 .cpp · ~20 .h · ~24 .py  
> **Dependencies**: FreeCADApp, Part, libOndselSolver  
> **Architecture SVG**: [assembly_architecture.svg](../svg/assembly_architecture.svg)

---

## 📋 Overview

The **Assembly** module is FreeCAD's **built-in constraint-based assembly solver**, powered by the **Ondsel Solver** (donated by Ondsel Inc. in 2024). It enables:

- **Multi-body assembly** — combine parts/bodies with positional constraints
- **Joint system** — 15+ joint types (revolute, cylindrical, slider, ball, gear, etc.)
- **Ondsel Solver** — kinematic constraint resolution engine
- **Bill of Materials** — automatic BOM generation
- **Exploded views** — visual assembly/disassembly sequences
- **Link-based** — uses Part::Link for lightweight references (no geometry copies)

Assembly was FreeCAD's most-requested feature for over a decade, with multiple community add-ons (A2plus, Assembly3, Assembly4) preceding the official module.

---

## 🏗️ Architecture

### AssemblyObject

```
AssemblyObject (Document object)
  ├── Parts (Links to Bodies/Parts)
  │    ├── Part::Link → Body1
  │    ├── Part::Link → Body2
  │    └── Part::Link → SubAssembly
  ├── Joints (constraints between parts)
  │    ├── JointFixed
  │    ├── JointRevolute
  │    ├── JointCylindrical
  │    └── ...
  ├── BomObject (Bill of Materials)
  └── Grounded Part (fixed reference)
```

### Joint Types

| Joint | DOF Removed | Description |
|---|---|---|
| **Fixed** | 6 | Parts locked together |
| **Revolute** | 5 | Hinge — rotation around one axis |
| **Cylindrical** | 4 | Rotation + translation along axis |
| **Slider** | 5 | Translation along one axis |
| **Ball** | 3 | Spherical — rotation around point |
| **Planar** | 3 | Slide on a plane |
| **Parallel** | 2 | Faces parallel |
| **Perpendicular** | 1 | Faces perpendicular |
| **Angle** | 1 | Fixed angle between faces |
| **Distance** | 1 | Fixed distance between elements |
| **RackPinion** | — | Gear-rack coupling |
| **Screw** | — | Helical motion |
| **Gears** | — | Gear-gear coupling |
| **Belt** | — | Belt/pulley coupling |

### Ondsel Solver

The solver is a C++ library (`libOndselSolver`) that:

1. Receives joint constraints and part positions
2. Builds a kinematic model
3. Solves for consistent part positions satisfying all constraints
4. Supports both assembly (static) and motion (kinematic) analysis

```
Joint definitions + Part geometry
  → OndselSolver::buildModel()
  → OndselSolver::solve()
  → Updated part placements
```

### Link-Based Architecture

Assembly uses `Part::Link` for lightweight references:
- No geometry duplication — links point to original bodies
- Supports cross-document references
- TNP-stable element naming for joint references
- Drag & drop from model tree

---

## 📅 Historical Timeline

| Year | Milestone |
|---|---|
| 2014 | A2plus add-on (community assembly) |
| 2016 | A2plus matures, widespread use |
| 2018 | Assembly3 by realthunder (Link-based) |
| 2019 | Assembly4 add-on (expression-based) |
| 2023 | Ondsel Inc. donates solver to FreeCAD |
| 2024 | **Official Assembly module in FreeCAD 1.0** |
| 2025 | Gear joints, Belt joints, Screw joints, BOM improvements |

---

## 🐍 Python API

```python
import FreeCAD as App
import Assembly

doc = App.newDocument()
assembly = doc.addObject("Assembly::AssemblyObject", "Assembly")

# Add parts (typically done via GUI drag & drop)
# Create joints
joint = Assembly.makeJointRevolute(assembly, part1, "Face6", part2, "Face3")

doc.recompute()
```

---

## 📂 Key Files

| File | Purpose |
|---|---|
| `App/AssemblyObject.h/cpp` | Assembly container |
| `App/JointObject.h/cpp` | Joint constraint types |
| `App/BomObject.h/cpp` | Bill of Materials |
| `Gui/ViewProviderAssembly.h/cpp` | Assembly view provider |
| `Gui/CommandAssembly.cpp` | GUI commands |
| `CommandCreateJoint.py` | Joint creation commands |
| `UtilsAssembly.py` | Assembly utilities |
| `libOndselSolver/` | Solver library (separate build) |

---

## 🔗 Dependency Graph

```
Assembly depends on:
  ├── Part (TopoShape, Link system)
  ├── App (Document, Property)
  ├── libOndselSolver (constraint solver)
  └── Base (Math, Placement)

Used by:
  ├── TechDraw (assembly drawings)
  └── FEM (analysis of assembled structures)
```

---

## 💡 Context: The Assembly Journey

Assembly functionality was the single most requested feature in FreeCAD history. Before the official module:

1. **A2plus** — Simple constraint-based assembly add-on
2. **Assembly3** (realthunder) — Full-featured, Link-based, used SolveSpace solver
3. **Assembly4** — Expression-based positioning (no solver needed)
4. **Ondsel** — Company built commercial tools on FreeCAD, donated their solver
5. **Official Assembly** — Integrated into FreeCAD 1.0 core with Ondsel solver

---

*Part of the [FreeCAD Documentation Hub](../README.md)*
