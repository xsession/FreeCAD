# FEM Module — Finite Element Analysis

> **Library**: `Fem.dll` / `libFem.so`  
> **Source**: `src/Mod/Fem/`  
> **Files**: ~135 .cpp · ~126 .h · ~389 .py  
> **Dependencies**: FreeCADApp, Part, SMESH, VTK, Netgen  
> **Architecture SVG**: [fem_architecture.svg](../svg/fem_architecture.svg)

---

## 📋 Overview

The **FEM** module provides a complete **Finite Element Analysis** framework within FreeCAD. It supports multiple external solvers and offers a full workflow from geometry to post-processing:

- **Multi-solver**: CalculiX (structural), Elmer (multi-physics), Z88 (structural), OpenFOAM (CFD)
- **Meshing**: Gmsh (external), Netgen (built-in), SMESH (Salome mesh library)
- **Constraints**: Forces, pressures, fixed supports, temperatures, heat flux, contact
- **Materials**: Mechanical and fluid material properties
- **Post-processing**: VTK-based pipeline with color maps, deformation, clipping

FEM is one of FreeCAD's most Python-heavy modules (~389 .py files vs ~135 .cpp).

---

## 🏗️ Architecture

### FemAnalysis Container

```
FemAnalysis (Document object)
  ├── FemMesh (mesh object)
  │    └── SMESH_Mesh (Salome mesh kernel)
  ├── MaterialMechanical / MaterialFluid
  ├── FemConstraint* (loads & boundary conditions)
  │    ├── ConstraintForce
  │    ├── ConstraintPressure
  │    ├── ConstraintFixed
  │    ├── ConstraintTemperature
  │    └── ConstraintHeatFlux, Contact, Displacement...
  ├── Solver (CalculiX / Elmer / Z88 / OpenFOAM)
  └── Results → FemPostPipeline (VTK visualization)
```

### Solvers

| Solver | Type | Capabilities |
|---|---|---|
| **CalculiX** | Structural | Linear/nonlinear static, frequency, buckling, heat transfer |
| **Elmer** | Multi-physics | Electrostatics, magnetostatics, fluid flow, heat, elasticity |
| **Z88** | Structural | Linear static analysis |
| **OpenFOAM** | CFD | Computational fluid dynamics |

Each solver has:
- **Writer** — generates input deck (`.inp`, `.sif`, etc.)
- **Solver task** — launches external process
- **Reader** — imports results back into FreeCAD

### Meshing Pipeline

```
3D Shape (TopoShape)
  ├── Gmsh (external) → .unv / .med / .bdf
  ├── Netgen (built-in) → tetrahedral mesh
  └── SMESH API → direct mesh operations
       ↓
  FemMesh (in-memory)
  ├── Tet4/Tet10 (tetrahedra)
  ├── Hex8/Hex20 (hexahedra)  
  ├── Tri3/Tri6 (triangles)
  ├── Quad4/Quad8 (quadrilaterals)
  ├── Seg2/Seg3 (segments)
  └── Node groups / Element groups
```

### Constraint Types

| Category | Constraints |
|---|---|
| **Mechanical** | Force, Pressure, Fixed, Displacement, PlaneRotation, Contact, Tie, SectionPrint |
| **Thermal** | Temperature, HeatFlux, InitialTemperature, BodyHeatSource |
| **Flow** | FlowVelocity, InitialFlowVelocity, FlowPressure |
| **Electromagnetic** | ElectrostaticPotential, Magnetization, CurrentDensity |

### Post-Processing (VTK Pipeline)

```
FemPostPipeline
  ├── FemPostFilter
  │    ├── ClipFilter (cut planes)
  │    ├── WarpVectorFilter (deformation)
  │    ├── ScalarClipFilter
  │    └── CutFilter (cross-sections)
  ├── Color maps (stress, displacement, temperature)
  └── Animation (deformation scaling)
```

---

## 🐍 Python API

```python
import FreeCAD as App
import ObjectsFem

doc = App.newDocument()
analysis = ObjectsFem.makeAnalysis(doc, "Analysis")

# Add mesh
mesh = ObjectsFem.makeMeshGmsh(doc, "FEMMesh")
analysis.addObject(mesh)

# Add material
material = ObjectsFem.makeMaterialSolid(doc, "Steel")
material.Material = {"YoungsModulus": "210000 MPa", "PoissonRatio": "0.3"}
analysis.addObject(material)

# Add constraint
fixed = ObjectsFem.makeConstraintFixed(doc, "FixedFace")
analysis.addObject(fixed)

force = ObjectsFem.makeConstraintForce(doc, "Load")
force.Force = 1000.0  # Newtons
analysis.addObject(force)
```

---

## 📅 Historical Timeline

| Year | Milestone |
|---|---|
| 2013 | Initial FEM module — CalculiX integration |
| 2015 | Elmer solver support, multi-physics |
| 2016 | Material framework overhaul |
| 2017 | VTK post-processing pipeline |
| 2018 | OpenFOAM CFD integration |
| 2019 | Gmsh mesher integration |
| 2020 | Z88 solver, improved mesh handling |
| 2022 | Constraint system refinement |
| 2023 | Gmsh integration improvements |
| 2025 | Post-processing pipeline enhancements |

---

## 📂 Key Files

| File | Purpose |
|---|---|
| `App/FemAnalysis.h/cpp` | Analysis container |
| `App/FemMesh.h/cpp` | Mesh data object |
| `App/FemConstraint*.h/cpp` | ~20 constraint types |
| `App/FemPostPipeline.h/cpp` | VTK post-processing |
| `App/FemPostFilter.h/cpp` | Result filters |
| `femguiobjects/` | GUI view providers |
| `femsolver/calculix/` | CalculiX writer/reader |
| `femsolver/elmer/` | Elmer writer/reader |
| `femsolver/z88/` | Z88 writer/reader |
| `femsolver/openfoam/` | OpenFOAM writer |
| `femmesh/` | Mesh generation tools |
| `femresult/` | Result handling |
| `femobjects/` | Python object definitions |

---

## 🔗 Dependency Graph

```
FEM depends on:
  ├── Part (TopoShape for geometry)
  ├── App (Document, Property)
  ├── SMESH (Salome mesh library)
  ├── VTK (post-processing visualization)
  ├── Netgen (built-in mesher)
  └── External: CalculiX, Elmer, Z88, OpenFOAM, Gmsh

Used by:
  └── Standalone analysis workflows
```

---

*Part of the [FreeCAD Documentation Hub](../README.md)*
