# FlowStudio — Zero to Post-Processing

## Complete Step-by-Step Tutorial with 5 Difficulty Levels

**FlowStudio v0.2.0** · Multi-Physics Simulation Workbench for FreeCAD

---

## Table of Contents

1. [Introduction & What You Will Learn](#1-introduction--what-you-will-learn)
2. [Architecture Overview](#2-architecture-overview)
3. [Installation & First Launch](#3-installation--first-launch)
4. [The 9-Step Simulation Workflow](#4-the-9-step-simulation-workflow)
5. [Understanding the FlowStudio Interface](#5-understanding-the-flowstudio-interface)
6. [Physics Concepts Primer](#6-physics-concepts-primer)
7. [Meshing Deep-Dive](#7-meshing-deep-dive)
8. **Example Scenarios**
   - [Level 1 — Simple Box Cooling (Beginner)](#level-1--simple-box-cooling-beginner)
   - [Level 2 — Multi-Component PCB Cooling (Intermediate)](#level-2--multi-component-pcb-cooling-intermediate)
  - [Level 2B — Electronics Cooling CHT + Radiation Benchmark (Intermediate-Advanced)](#level-2b--electronics-cooling-cht--radiation-benchmark-intermediate-advanced)
   - [Level 3 — NACA 2412 Wing (Intermediate-Advanced)](#level-3--naca-2412-wing-intermediate-advanced)
   - [Level 4 — Server Rack Forced Cooling (Advanced)](#level-4--server-rack-forced-cooling-advanced)
   - [Level 5 — CT Detector Rotating System (Expert)](#level-5--ct-detector-rotating-system-expert)
9. [Post-Processing Deep-Dive](#9-post-processing-deep-dive)
10. [Solver Backend Reference](#10-solver-backend-reference)
11. [Troubleshooting & FAQ](#11-troubleshooting--faq)
12. [Appendix: Property Reference Tables](#12-appendix-property-reference-tables)

---

## 1. Introduction & What You Will Learn

FlowStudio is a **multi-physics simulation workbench** that brings commercial-grade CFD,
structural, electrostatic, electromagnetic, and thermal simulation workflows into the
open-source FreeCAD ecosystem. It supports three solver backends:

| Backend | Type | Best For | Hardware |
|---------|------|----------|----------|
| **OpenFOAM** | Finite Volume | Production CFD, industry standard | CPU (MPI parallel) |
| **FluidX3D** | Lattice Boltzmann | Real-time GPU CFD, fast turnaround | GPU (CUDA/OpenCL) |
| **Elmer** | Finite Element | Multi-physics (EM, thermal, structural) | CPU (MPI parallel) |

### What This Tutorial Covers

By the end of this guide you will be able to:

- Set up any simulation from scratch — geometry through post-processing
- Choose the right physics model, turbulence model, and solver
- Build high-quality meshes with boundary layers
- Configure boundary conditions for internal and external flows
- Run parallel simulations on multi-core CPUs and GPUs
- Interpret and visualise results with contour plots, streamlines, and probes
- Tackle increasingly complex real-world problems (5 levels)

### Prerequisite Knowledge

| Level | You Should Know | You Will Learn |
|-------|----------------|----------------|
| **1** | Basic FreeCAD navigation | How to run a simple CFD case |
| **2** | Creating simple 3D geometry | Multi-body heat transfer setup |
| **3** | Basic fluid dynamics concepts | External aerodynamics workflow |
| **4** | Reynolds number, turbulence basics | Complex internal flow + parallel |
| **5** | Rotating machinery, multi-physics | MRF zones, coupled EM+thermal+CFD |

---

## 2. Architecture Overview

FlowStudio follows a clean layered architecture that separates concerns:

```
┌────────────────────────────────────────────────────────────────┐
│                    FreeCAD Application                         │
├────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐ │
│  │  FlowStudio  │  │  Task Panels │  │  View Providers      │ │
│  │  Commands    │  │  (Qt GUIs)   │  │  (3D visualization)  │ │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘ │
│         │                 │                      │             │
│  ┌──────▼─────────────────▼──────────────────────▼───────────┐ │
│  │              FlowStudio Document Objects                  │ │
│  │  Analysis │ PhysicsModel │ Material │ BCs │ Mesh │ Solver │ │
│  └──────────────────────┬────────────────────────────────────┘ │
│                         │                                      │
│  ┌──────────────────────▼────────────────────────────────────┐ │
│  │                 Solver Runners                            │ │
│  │  OpenFOAMRunner  │  FluidX3DRunner  │  ElmerRunner        │ │
│  └──────────────────────┬────────────────────────────────────┘ │
│                         │                                      │
│  ┌──────────────────────▼────────────────────────────────────┐ │
│  │              Enterprise Layer (optional)                  │ │
│  │  Adapters │ Job Manager │ Telemetry │ Remote Execution    │ │
│  └───────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────┘
```

### Physics Domain Architecture

FlowStudio registers **five physics domains**, each with its own analysis types,
boundary conditions, material models, and solver backends:

```
                        ┌─────────────┐
                        │  FlowStudio │
                        │   Domains   │
                        └──────┬──────┘
            ┌──────┬───────┬───┴───┬────────────┐
            ▼      ▼       ▼       ▼            ▼
         ┌─────┐┌─────┐┌──────┐┌──────────┐┌────────┐
         │ CFD ││Struc││Elec- ││Electro-  ││Thermal │
         │     ││tural││static││ magnetic ││        │
         └──┬──┘└──┬──┘└──┬───┘└────┬─────┘└───┬────┘
            │      │      │         │           │
  Solvers:  │      │      │         │           │
  OpenFOAM ─┤      │      │         │           │
  FluidX3D ─┤      │      │         │           │
  Elmer ────┼──────┼──────┼─────────┼───────────┤
            │      │      │         │           │
  BCs:      │      │      │         │           │
  Inlet ────┤      │      │         │           │
  Outlet ───┤      │      │         │           │
  Wall ─────┤      │      │         │           │
  Symmetry ─┤      │      │         │           │
  OpenBnd ──┤      │      │         │           │
  FixedDisp─┼──────┤      │         │           │
  Force ────┼──────┤      │         │           │
  Potential─┼──────┼──────┤         │           │
  SrfCharge─┼──────┼──────┤         │           │
  MagPot ───┼──────┼──────┼─────────┤           │
  Current ──┼──────┼──────┼─────────┤           │
  Temp BC ──┼──────┼──────┼─────────┼───────────┤
  HeatFlux ─┼──────┼──────┼─────────┼───────────┤
  Convect ──┼──────┼──────┼─────────┼───────────┤
  Radiate ──┼──────┼──────┼─────────┼───────────┤
```

---

## 3. Installation & First Launch

### 3.1 Prerequisites

| Component | Minimum | Recommended | Purpose |
|-----------|---------|-------------|---------|
| FreeCAD | 0.22+ | 1.0+ | Host application |
| GMSH | 4.11+ | 4.13+ | Mesh generation |
| OpenFOAM | v2312+ | v2406+ | CFD solver |
| FluidX3D | 2.18+ | 2.19+ | GPU LBM solver |
| Elmer | 9.0+ | 9.0+ | Multi-physics FEM |
| ParaView | 5.11+ | 5.12+ | Advanced post-processing |

### 3.2 Checking Dependencies

FlowStudio includes a built-in dependency checker. After launching FreeCAD:

```
Menu: FlowStudio → Check Workflow
```

Or use the Python console:

```python
from flow_studio.solver_deps import check_all, recommend_parallel_settings

# Check all solver backends
reports = check_all()
for name, report in reports.items():
    status = "✓ Available" if report.available else "✗ Missing"
    print(f"  {name}: {status}")
    for dep in report.deps:
        flag = "✓" if dep.found else "✗"
        print(f"    {flag} {dep.name}: {dep.path or dep.hint}")

# Get recommended parallel settings
rec = recommend_parallel_settings()
print(f"\nCPU cores: {rec['cpu_cores']}")
print(f"Recommended MPI procs: {rec['recommended_mpi_procs']}")
```

**Expected output on a properly configured system:**

```
  OpenFOAM: ✓ Available
    ✓ simpleFoam: /usr/bin/simpleFoam
    ✓ pimpleFoam: /usr/bin/pimpleFoam
    ✓ blockMesh: /usr/bin/blockMesh
    ✓ decomposePar: /usr/bin/decomposePar
  FluidX3D: ✓ Available
    ✓ FluidX3D: /usr/local/bin/FluidX3D
  Elmer: ✓ Available
    ✓ ElmerSolver: /usr/bin/ElmerSolver
    ✓ ElmerGrid: /usr/bin/ElmerGrid
  ParaView: ✓ Available
    ✓ pvpython: /usr/bin/pvpython
  Meshing: ✓ Available
    ✓ gmsh: /usr/bin/gmsh
```

### 3.3 First Launch

1. Open FreeCAD
2. Switch to the **FlowStudio** workbench via the workbench selector dropdown
3. The toolbar will show these groups:

```
┌─────────────────────────────────────────────────────────────────────┐
│ FlowStudio Analysis │ CFD Setup │ Boundary Conditions │ Meshing │  │
│ ─────────────────── │ ───────── │ ──────────────────── │ ─────── │  │
│ [New CFD Analysis]  │ [Physics] │ [Inlet]  [Outlet]   │ [Mesh]  │  │
│ [New Structural]    │ [Material]│ [Wall]   [Symmetry]  │ [Refine]│  │
│ [New Electrostatic] │ [Init.C.] │ [Open Boundary]     │ [B.Layer]│ │
│ [New Electromagnetic]│          │                      │         │  │
│ [New Thermal]       │          │                      │         │  │
├─────────────────────┴──────────┴──────────────────────┴─────────┤  │
│ Solve              │ Post-Processing           │ Enterprise      │  │
│ ─────              │ ─────────────────         │ ──────────      │  │
│ [Solver Settings]  │ [Post Pipeline]           │ [Job Manager]   │  │
│ [Run Solver]       │ [Contour] [Streamlines]   │ [Remote Submit] │  │
│ [Workflow Guide]   │ [Probe] [Force Report]    │                 │  │
│ [Check Workflow]   │ [Measurement Point/Srf/Vol]│                │  │
│                    │ [Generate Paraview Script] │                 │  │
└────────────────────┴────────────────────────────┴─────────────────┘
```

---

## 4. The 9-Step Simulation Workflow

Every simulation in FlowStudio follows the same fundamental 9-step workflow.
This is the single most important concept in this tutorial.

```
    ┌─────────────────────────────────────────────────────────┐
    │                  THE 9-STEP WORKFLOW                     │
    │                                                         │
    │  ┌───┐  ┌───┐  ┌───┐  ┌───┐  ┌───┐  ┌───┐  ┌───┐     │
    │  │ 1 │→ │ 2 │→ │ 3 │→ │ 4 │→ │ 5 │→ │ 6 │→ │ 7 │     │
    │  └───┘  └───┘  └───┘  └───┘  └───┘  └───┘  └───┘     │
    │    │                                          │         │
    │    ▼                                          ▼         │
    │  Create                                   Set Initial   │
    │  Analysis                                 Conditions    │
    │                                                         │
    │                    ┌───┐  ┌───┐                         │
    │                    │ 8 │→ │ 9 │                         │
    │                    └───┘  └───┘                         │
    │                      │      │                           │
    │                      ▼      ▼                           │
    │                   Run    Post-                          │
    │                  Solver  Process                        │
    └─────────────────────────────────────────────────────────┘
```

### Step-by-Step Breakdown

#### Step 1: Create Analysis

**What it does:** Creates a container object that holds all simulation components.
When you create an analysis, FlowStudio automatically adds:
- Physics Model (flow regime, turbulence, etc.)
- Fluid Material (density, viscosity, etc.)
- Initial Conditions (starting field values)
- Solver object (solver backend + numerics)

**How to do it:**
```
Menu: FlowStudio → New CFD Analysis
   or: FlowStudio → New Thermal Analysis
   or: FlowStudio → New Electromagnetic Analysis
   ... etc.
```

**The Model Tree after Step 1:**
```
📁 Document
  └── 📂 CFDAnalysis
        ├── ⚙ PhysicsModel
        ├── 💧 FluidMaterial
        ├── 🎯 InitialConditions
        └── ▶ Solver
```

> **Key Concept:**  Every object you create (BCs, mesh, etc.) must be placed
> *inside* the analysis container. FlowStudio does this automatically for
> commands invoked while an analysis is selected.

---

#### Step 2: Import / Create Geometry

**What it does:** Provides the solid 3D shape that defines your simulation domain.

**Options:**
- Create geometry in FreeCAD's Part or Part Design workbench
- Import STEP/IGES/STL/BREP files via `File → Import`
- Use the CAD modelling tools to create boxes, cylinders, etc.

**For internal flow** (e.g., box cooling):
The geometry IS the fluid volume. If you have a solid enclosure, you
need to create a Boolean subtraction to get the internal air volume.

**For external flow** (e.g., wing):
You create a **wind tunnel** box around the wing, then Boolean-subtract
the wing solid from the tunnel to get the fluid domain.

```
  Internal Flow:                    External Flow:

  ┌──────────────┐                ┌──────────────────┐
  │  ▓▓▓▓▓▓▓▓▓▓  │                │                  │
  │  ▓ Fluid   ▓  │  Inlet →      │    ┌──────┐      │  → Outlet
  │  ▓ Volume  ▓  │                │    │ Wing │      │
  │  ▓▓▓▓▓▓▓▓▓▓  │                │    └──────┘      │
  └──────────────┘                └──────────────────┘
   Geometry = fluid                Geometry = tunnel − wing
```

> **Tip:** For internal electronics cooling, model the enclosure as a hollow
> box. The *inner* volume is what gets meshed and simulated. Heat-generating
> components are represented by *wall boundary conditions* with **Fixed Heat Flux**.

---

#### Step 3: Configure Physics Model

**What it does:** Sets the fundamental physics assumptions for the simulation.

**Properties to configure:**

| Property | Options | When to Use |
|----------|---------|-------------|
| **FlowRegime** | `Laminar`, `Turbulent` | Turbulent for Re > ~2300 (pipe) or Re > ~500,000 (flat plate) |
| **TurbulenceModel** | `kOmegaSST` (default), `kEpsilon`, `SpalartAllmaras`, `LES-Smagorinsky`, `LES-WALE`, `LBM-Implicit` | k-ω SST for general use; S-A for aerospace; LES for time-resolved |
| **Compressibility** | `Incompressible`, `Compressible`, `Weakly-Compressible` | Incompressible when Ma < 0.3; Compressible for Ma > 0.3 |
| **TimeModel** | `Steady`, `Transient` | Steady for most cases; Transient for rotating/pulsating/unsteady flows |
| **Gravity** | `On/Off` | Enable for natural convection, buoyancy-driven flows |
| **HeatTransfer** | `On/Off` | Enable when temperature differences matter (electronics cooling!) |
| **Buoyancy** | `On/Off` | Enable for natural convection (Boussinesq approximation) |

**Decision flowchart for turbulence model selection:**

```
                        Start
                          │
                    Is Re > 2300?
                   ╱           ╲
                 No             Yes
                 │               │
              Laminar      Need time-resolved
              (no model)    unsteady detail?
                           ╱           ╲
                         No             Yes
                          │               │
                   Aerospace          Is GPU available?
                   application?       ╱           ╲
                   ╱        ╲       No             Yes
                 Yes        No       │               │
                  │          │    LES-WALE      LBM-Implicit
            Spalart-    k-ω SST   (CPU)         (FluidX3D)
            Allmaras    (default,
                        general
                        purpose)
```

---

#### Step 4: Assign Material Properties

**What it does:** Defines the fluid (or solid) material properties.

**Built-in presets:**

| Preset | ρ [kg/m³] | μ [Pa·s] | Cp [J/(kg·K)] | k [W/(m·K)] | Pr |
|--------|-----------|----------|----------------|--------------|------|
| **Air (20°C, 1atm)** | 1.225 | 1.81e-5 | 1005 | 0.0257 | 0.707 |
| **Water (20°C)** | 998.2 | 1.002e-3 | 4182 | 0.60 | 7.01 |
| **Oil (SAE 30)** | 891.0 | 0.29 | 1900 | 0.145 | 3800 |
| **Glycerin** | 1261.0 | 1.412 | 2427 | 0.286 | 11970 |
| **Mercury** | 13534.0 | 1.526e-3 | 139.3 | 8.514 | 0.025 |

> **When to use custom values:** If your fluid operates at a temperature
> significantly different from 20°C, or if you have a specialized coolant
> (e.g., Fluorinert, liquid nitrogen), enter custom values. You can look
> up properties in the NIST Chemistry WebBook or Engineering Toolbox.

> **Key Relationship:**  Kinematic viscosity ν = μ / ρ
> This is what enters the Reynolds number: Re = U·L / ν

---

#### Step 5: Define Boundary Conditions

**What it does:** Tells the solver what happens at every surface of your geometry.

> **Critical Rule:** Every face of your geometry must have EXACTLY ONE boundary
> condition. Unassigned faces default to wall (no-slip) in most solvers, but
> it is best practice to explicitly assign every face.

**Available CFD boundary conditions:**

```
┌──────────────────────────────────────────────────────────────────┐
│                    BOUNDARY CONDITIONS                           │
│                                                                  │
│  INLET                        OUTLET                            │
│  ┌──────────────┐             ┌──────────────┐                  │
│  │ • Velocity   │             │ • Static     │                  │
│  │ • Mass Flow  │     →→→     │   Pressure   │                  │
│  │ • Vol. Flow  │   (flow)    │ • Mass Flow  │                  │
│  │ • Total Press│             │ • Zero Grad. │                  │
│  └──────────────┘             └──────────────┘                  │
│                                                                  │
│  WALL                         SYMMETRY                          │
│  ┌──────────────┐             ┌──────────────┐                  │
│  │ • No-Slip    │             │ Mirror plane  │                  │
│  │ • Slip       │             │ (zero normal  │                  │
│  │ • Moving     │             │  gradients)   │                  │
│  │   (transl.)  │             └──────────────┘                  │
│  │ • Moving     │                                               │
│  │   (rotation) │             OPEN BOUNDARY                     │
│  │ • Rough Wall │             ┌──────────────┐                  │
│  ├──────────────┤             │ Far-field /   │                  │
│  │ Thermal:     │             │ ambient for   │                  │
│  │ • Adiabatic  │             │ external flow │                  │
│  │ • Fixed Temp │             └──────────────┘                  │
│  │ • Heat Flux  │                                               │
│  │ • HTC (h)    │                                               │
│  └──────────────┘                                               │
└──────────────────────────────────────────────────────────────────┘
```

**Inlet type selection guide:**

| When you know... | Use | Example |
|------------------|-----|---------|
| The velocity of the incoming flow | **Velocity** | Wind tunnel at 10 m/s |
| The pump/fan flow rate in kg/s | **Mass Flow Rate** | Pump delivering 0.5 kg/s |
| The pump/fan flow rate in m³/s | **Volumetric Flow Rate** | Fan delivering 200 CFM |
| The upstream pressure | **Total Pressure** | Pressurized plenum |

**Wall thermal type selection guide:**

| When you know... | Use | Example |
|------------------|-----|---------|
| The wall is insulated / unimportant | **Adiabatic** | Outer casing (insulated) |
| The exact wall temperature | **Fixed Temperature** | Water-cooled cold plate at 25°C |
| The power dissipated per area | **Fixed Heat Flux** | IC chip: 50W / 0.01m² = 5000 W/m² |
| The exterior convection conditions | **HTC (h)** | h=10 W/(m²·K), T_amb=25°C |

---

#### Step 6: Generate Mesh

**What it does:** Divides your geometry into millions of small cells where the
equations will be solved.

**Key properties:**

| Property | Default | Description |
|----------|---------|-------------|
| **CharacteristicLength** | 10.0 mm | Base element size |
| **MinElementSize** | 1.0 mm | Smallest allowed element |
| **MaxElementSize** | 50.0 mm | Largest allowed element |
| **Algorithm3D** | Delaunay | Meshing algorithm (Delaunay, Frontal, HXT) |
| **ElementOrder** | 1st Order | Linear (CFD) or Quadratic (FEM) elements |
| **GrowthRate** | 1.3 | Size growth from surface to bulk |

**Mesh sizing rules of thumb:**

```
┌────────────────────────────────────────────────────────────────┐
│                    MESH SIZING GUIDE                           │
│                                                                │
│  Very fine: 0.5-2 mm   ← Near walls, small features          │
│  Fine:      2-5 mm     ← Around heat sources, obstacles      │
│  Medium:    5-20 mm    ← Main flow region                    │
│  Coarse:    20-50 mm   ← Far-field, bulk volume              │
│                                                                │
│  Total cells rule of thumb:                                    │
│    Small case (< 0.1 m³):     100K - 500K cells              │
│    Medium case (0.1 - 1 m³):  500K - 2M cells                │
│    Large case (> 1 m³):       2M - 10M cells                 │
│    Production (rotating):      5M - 50M cells                │
│                                                                │
│  ⚠  More cells = more accurate but slower!                    │
│  Start coarse, refine where gradients are high.               │
└────────────────────────────────────────────────────────────────┘
```

**Boundary layer mesh (crucial for accuracy):**

Near solid walls, the flow velocity changes rapidly from zero (at the wall)
to the free-stream value. To capture this correctly, you need thin prismatic
cells stacked on the wall — this is the **boundary layer mesh**.

```
                        Bulk mesh (tetrahedral)
                     ┌─────────────────────────
                     │  △  △  △  △  △  △  △
  Transition zone    │ △  △  △  △  △  △  △  △
                     │━━━━━━━━━━━━━━━━━━━━━━━━
                     │▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒  Layer 5 (thickest)
  Boundary layers    │▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒  Layer 4
  (prismatic cells)  │▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  Layer 3
                     │████████████████████████  Layer 2 (thinner)
                     │████████████████████████  Layer 1 (thinnest)
                     ┗━━━━━━━━━━━━━━━━━━━━━━━━  WALL
```

**Boundary layer specification modes:**

| Mode | When to Use |
|------|-------------|
| **First Layer + Expansion** | You know the required first cell height (from y⁺ calc) |
| **First Layer + Total Thickness** | Fixed total BL thickness needed |
| **Overall Thickness + Expansion** | Know total thickness, auto-compute first cell |
| **Target y⁺ (auto)** | Let FlowStudio compute first cell from velocity and ν |

**The y⁺ concept (very important!):**

y⁺ = y · u_τ / ν  where u_τ = √(τ_w / ρ) is the friction velocity.

| y⁺ Target | Approach | When to Use |
|-----------|----------|-------------|
| y⁺ ≈ 1 | Wall-resolved | Best accuracy; captures flow separation perfectly |
| y⁺ ≈ 30 | Wall functions | Good accuracy; ~10× fewer cells; OK for attached flow |
| y⁺ ≈ 100+ | Too coarse | ⚠ Inaccurate — refine your mesh! |

FlowStudio has a built-in y⁺ height estimator:

```python
from flow_studio.utils.mesh_utils import estimate_y_plus_height

# For a fan blade at 30 m/s, 100mm chord, air
first_cell = estimate_y_plus_height(
    velocity=30.0,       # m/s
    length=0.1,          # characteristic length [m]
    nu=1.5e-5,           # kinematic viscosity [m²/s]
    y_plus_target=1.0,   # target y+
)
print(f"First cell height: {first_cell*1000:.4f} mm")
# → First cell height: ~0.015 mm (15 microns)
```

---

#### Step 7: Set Initial Conditions

**What it does:** Defines the starting field values everywhere in the domain
before the solver begins iterating.

| Property | Default | Description |
|----------|---------|-------------|
| **Ux, Uy, Uz** | 0.0, 0.0, 0.0 | Initial velocity [m/s] |
| **Pressure** | 0.0 | Initial gauge pressure [Pa] |
| **Temperature** | 293.15 | Initial temperature [K] |
| **TurbulentKineticEnergy (k)** | 0.001 | Initial k [m²/s²] |
| **SpecificDissipationRate (ω)** | 1.0 | Initial ω [1/s] |
| **UsePotentialFlow** | False | Initialize velocity from potential solution |

> **Tip:** For better convergence, set initial velocity close to the expected
> inlet velocity. For internal flows, this reduces the number of iterations
> needed to reach a converged solution by 30-50%.

> **Tip:** Enable **UsePotentialFlow** for external aero cases (wings, cars).
> The potential flow solution provides a much better initial velocity field
> than uniform values, dramatically improving convergence.

---

#### Step 8: Run Solver

**What it does:** Writes case files for the selected solver backend and
launches the computation.

**Pre-flight checks performed automatically:**
1. ✓ Analysis exists with physics model
2. ✓ Material properties defined
3. ✓ At least one boundary condition assigned
4. ✓ Mesh generated and completed (NumCells > 0)
5. ✓ Solver backend installed and accessible

**Solver selection guide:**

| Scenario | Recommended Solver | OpenFOAM App |
|----------|-------------------|--------------|
| Steady incompressible | OpenFOAM | `simpleFoam` |
| Transient incompressible | OpenFOAM | `pimpleFoam` |
| Steady + heat | OpenFOAM | `buoyantSimpleFoam` |
| Transient + heat | OpenFOAM | `buoyantPimpleFoam` |
| Compressible | OpenFOAM | `rhoSimpleFoam` |
| Free surface (VOF) | OpenFOAM | `interFoam` |
| Quick GPU preview | FluidX3D | — |
| Multi-physics (EM/thermal) | Elmer | — |

**Parallel execution:**

For large meshes (>500K cells), enable parallel execution:

| Property | Recommendation |
|----------|---------------|
| **NumProcessors** | Number of *physical* CPU cores (not hyper-threads) |
| **AutoParallel** | Set `True` for automatic detection |

The rule of thumb: **≥50,000 cells per MPI process** for good parallel efficiency.

```
  Cells:     500,000   →   NumProcessors = 8  (62.5K cells/proc)
  Cells:   2,000,000   →   NumProcessors = 32 (62.5K cells/proc)
  Cells:  10,000,000   →   NumProcessors = 64 (156K cells/proc)
```

---

#### Step 9: Post-Process Results

**What it does:** Creates visualisations and extracts quantitative data from
the solver results.

FlowStudio provides five built-in post-processing tools plus ParaView script export:

| Tool | Purpose | Typical Use |
|------|---------|-------------|
| **Post Pipeline** | Result visualization container | Always create this first |
| **Contour Plot** | Color maps on surfaces/cut planes | Pressure, velocity, temperature fields |
| **Streamlines** | Flow path visualisation | Visualize flow patterns, recirculation |
| **Point Probe** | Single-point field query | Monitor temperature at specific location |
| **Force Report** | Drag/lift/moment computation | Aerodynamic forces on wing/body |
| **Measurement Point/Surface/Volume** | Field sampling for export | Data extraction for reports |
| **Generate ParaView Script** | Auto-create pvpython script | Advanced post-processing |

---

## 5. Understanding the FlowStudio Interface

### 5.1 The Model Tree

After a complete setup, the model tree looks like this:

```
📁 MySimulation.FCStd
  ├── 🔲 EnclosureGeometry          ← Step 2: Geometry
  └── 📂 CFDAnalysis                ← Step 1: Analysis container
        ├── ⚙ PhysicsModel          ← Step 3: Physics settings
        ├── 💧 FluidMaterial         ← Step 4: Fluid properties
        ├── 🎯 InitialConditions     ← Step 7: Starting fields
        ├── ▶ Solver                 ← Step 8: Solver settings
        ├── 🧱 MeshGmsh             ← Step 6: Mesh settings
        │     ├── 📐 MeshRegion1     ← Local refinement
        │     └── 📏 BoundaryLayer1  ← Inflation layers
        ├── 🔴 BCInlet               ← Step 5: BCs
        ├── 🔵 BCOutlet
        ├── ⬛ BCWall_Chip
        ├── ⬛ BCWall_Housing
        └── 📊 PostPipeline          ← Step 9: Results
              ├── 🎨 ContourVelocity
              ├── ➰ Streamlines
              └── 📍 ProbeChipTemp
```

### 5.2 The Workflow Guide Panel

Access via: **FlowStudio → Workflow Guide**

This displays a checklist showing which steps are complete and which still
need attention:

```
┌─────────────────────────────────────────┐
│         WORKFLOW GUIDE                   │
│                                         │
│  ✅ 1. Create Analysis                  │
│  ✅ 2. Import / Create Geometry         │
│  ✅ 3. Configure Physics Model          │
│  ✅ 4. Assign Material Properties       │
│  ✅ 5. Define Boundary Conditions       │
│  ⚠️ 6. Generate Mesh (not run yet)      │
│  ✅ 7. Set Initial Conditions           │
│  ⛔ 8. Run Solver (needs: mesh)         │
│  ⛔ 9. Post-process (needs: solver run) │
│                                         │
│  [Run Check] [Show Details]             │
└─────────────────────────────────────────┘
```

---

## 6. Physics Concepts Primer

### 6.1 Reynolds Number — The Most Important Number in CFD

The Reynolds number tells you if flow is laminar (smooth) or turbulent (chaotic):

$$Re = \frac{U \cdot L}{\nu}$$

Where:
- $U$ = characteristic velocity [m/s]
- $L$ = characteristic length [m]
- $\nu$ = kinematic viscosity [m²/s]

```
  Re < 2,300 (pipe)     → LAMINAR     (smooth, predictable)
  2,300 < Re < 4,000    → TRANSITION  (intermittently turbulent)
  Re > 4,000 (pipe)     → TURBULENT   (chaotic, need turbulence model)

  Re < 500,000 (plate)  → LAMINAR
  Re > 500,000 (plate)  → TURBULENT
```

**Quick calculation for common scenarios:**

| Scenario | U [m/s] | L [m] | ν [m²/s] | Re | Regime |
|----------|---------|-------|----------|-----|--------|
| Electronics box (air) | 2 | 0.3 | 1.5e-5 | 40,000 | Turbulent |
| CPU heatsink channel | 5 | 0.01 | 1.5e-5 | 3,300 | Transitional |
| Wing at cruise | 70 | 1.5 | 1.5e-5 | 7,000,000 | Turbulent |
| Server rack row | 3 | 0.6 | 1.5e-5 | 120,000 | Turbulent |
| CT detector housing | 5 | 0.8 | 1.5e-5 | 267,000 | Turbulent |

### 6.2 The Navier-Stokes Equations (What the Solver Solves)

The solver numerically solves these equations at every cell:

**Continuity (mass conservation):**
$$\nabla \cdot \mathbf{u} = 0$$

**Momentum (Newton's second law for fluids):**
$$\frac{\partial \mathbf{u}}{\partial t} + (\mathbf{u} \cdot \nabla)\mathbf{u} = -\frac{1}{\rho}\nabla p + \nu \nabla^2 \mathbf{u} + \mathbf{g}$$

**Energy (when heat transfer is enabled):**
$$\frac{\partial T}{\partial t} + \mathbf{u} \cdot \nabla T = \frac{k}{\rho c_p} \nabla^2 T + \frac{Q}{\rho c_p}$$

You don't need to understand these equations to use FlowStudio — the solver
handles everything — but understanding them helps you make better modelling choices.

### 6.3 Turbulence Models — When and Why

```
┌─────────────────────────────────────────────────────────────────┐
│                 TURBULENCE MODEL COMPARISON                     │
│                                                                 │
│  Model           │ Cost │ Accuracy │ Best For                  │
│  ─────────────── │ ──── │ ──────── │ ─────────────────────     │
│  k-ε             │ Low  │ Good     │ Fully turbulent, simple   │
│                  │      │          │ geometries                │
│  k-ω SST        │ Med  │ V.Good   │ General purpose,          │
│  (DEFAULT) ★     │      │          │ separation, heat transfer │
│  Spalart-        │ Low  │ Good     │ Aerospace, attached       │
│  Allmaras        │      │          │ boundary layers           │
│  LES-Smagorinsky│ High │ Excellent│ Unsteady, large eddies,   │
│                  │      │          │ acoustics                 │
│  LES-WALE       │ High │ Excellent│ Better wall behavior      │
│                  │      │          │ than Smagorinsky          │
│  LBM-Implicit   │ V.High│ Good    │ GPU-accelerated,          │
│  (FluidX3D)     │      │          │ real-time preview          │
└─────────────────────────────────────────────────────────────────┘
```

> **Recommendation:** Start with **k-ω SST**. It works well for 90% of cases.
> Only switch to a different model when you have a specific reason.

---

## 7. Meshing Deep-Dive

### 7.1 Mesh Quality Metrics

A good mesh is the foundation of an accurate simulation. Poor mesh quality
leads to convergence problems, inaccurate results, and wasted time.

**Key quality indicators:**

| Metric | Ideal | Acceptable | Bad |
|--------|-------|-----------|-----|
| Skewness | < 0.25 | < 0.75 | > 0.95 |
| Non-orthogonality | < 40° | < 65° | > 70° |
| Aspect ratio | < 5 | < 20 | > 100 |
| Volume ratio | < 3 | < 10 | > 20 |

### 7.2 Mesh Refinement Strategy

```
┌────────────────────────────────────────────────────────────────┐
│              WHERE TO REFINE YOUR MESH                         │
│                                                                │
│  ★ HIGH refinement (finest cells):                            │
│    • Wall surfaces (boundary layer mesh)                      │
│    • Heat sources (chips, hot components)                     │
│    • Leading/trailing edges (wings)                           │
│    • Inlets and outlets (flow transitions)                    │
│                                                                │
│  ◆ MEDIUM refinement:                                         │
│    • Wake regions behind obstacles                            │
│    • Recirculation zones                                      │
│    • Narrow gaps between components                           │
│                                                                │
│  ○ COARSE (save cells):                                       │
│    • Far-field bulk flow                                      │
│    • Regions with uniform flow                                │
│    • Areas far from surfaces of interest                      │
└────────────────────────────────────────────────────────────────┘
```

### 7.3 Mesh Refinement Regions

FlowStudio provides four types of refinement regions:

| Type | Shape | Use Case |
|------|-------|----------|
| **Surface** | Faces | Refine around specific walls, inlets, chip surfaces |
| **Volume (Box)** | Rectangular box | Wake region, recirculation zones |
| **Volume (Sphere)** | Sphere | Around small, complex obstacles |
| **Volume (Cylinder)** | Cylinder | Around pipes, rotating zones |

---

## Level 1 — Simple Box Cooling (Beginner)

> **Difficulty:** ★☆☆☆☆
> **Physics:** Steady, turbulent, incompressible, heat transfer
> **Solver:** OpenFOAM (buoyantSimpleFoam)
> **Time to complete:** 30-45 minutes
> **Cells:** ~200K

### Scenario Description

A sealed electronics enclosure (300mm × 200mm × 150mm) contains a single
heat-generating component (50mm × 50mm × 10mm chip) dissipating **25 W**.
Air enters through a vent on the left wall and exits through a vent on the right.
Goal: Determine the chip junction temperature and airflow pattern.

```
  ┌──────────────────────────────────────────────┐
  │                                              │  150mm
  │     ┌─────────┐                              │  height
  │     │  CHIP   │  25W                         │
  │     │ (50x50) │                              │
  ═══►  │         │                          ═══►│
 inlet  └─────────┘                         outlet
  │              300mm                           │
  └──────────────────────────────────────────────┘
                    200mm depth
```

### Step-by-Step Instructions

#### L1.1 — Create the Geometry

1. Switch to **Part** workbench
2. Create a **Box**: Length=300, Width=200, Height=150 (the enclosure)
3. Create another **Box**: Length=50, Width=50, Height=10 (the chip)
4. Position the chip: X=50, Y=75, Z=0 (sitting on the bottom wall)
5. The enclosure IS the fluid domain (air volume)

> **Note:** The chip is not subtracted — it is a separate solid that we
> reference when assigning wall boundary conditions with heat flux.

#### L1.2 — Create the Analysis

1. Switch to **FlowStudio** workbench
2. Click **New CFD Analysis** (or menu: FlowStudio → New CFD Analysis)
3. Observe: PhysicsModel, FluidMaterial, InitialConditions, Solver auto-created

#### L1.3 — Configure Physics

1. Double-click **PhysicsModel** in the model tree
2. Set:
   - **FlowRegime:** Turbulent
   - **TurbulenceModel:** kOmegaSST
   - **Compressibility:** Incompressible
   - **TimeModel:** Steady
   - **HeatTransfer:** ✓ Enabled
   - **Gravity:** ✓ Enabled (for buoyancy)
   - **Buoyancy:** ✓ Enabled
3. Click **OK**

#### L1.4 — Set Material

1. Double-click **FluidMaterial**
2. Select preset: **Air (20°C, 1atm)**
3. Verify: Density=1.225, DynamicViscosity=1.81e-5
4. Click **OK**

#### L1.5 — Define Boundary Conditions

**Inlet (left wall vent):**
1. Click **Inlet** in toolbar
2. Select the left face of the enclosure
3. Set:
   - **InletType:** Velocity
   - **VelocityMagnitude:** 2.0 m/s
   - **NormalToFace:** ✓
   - **TurbulenceIntensity:** 5%
   - **TurbulenceLengthScale:** 0.01 m
   - **InletTemperature:** 293.15 K (20°C)
4. Click **OK**

**Outlet (right wall vent):**
1. Click **Outlet** in toolbar
2. Select the right face of the enclosure
3. Set:
   - **OutletType:** Static Pressure
   - **StaticPressure:** 0 Pa (gauge)
4. Click **OK**

**Chip (heat source):**
1. Click **Wall** in toolbar
2. Select the top face of the chip
3. Set:
   - **WallType:** No-Slip
   - **ThermalType:** Fixed Heat Flux
   - **HeatFlux:** 10000.0 W/m² (= 25W / 0.0025m²)
4. Click **OK**

**Remaining walls (enclosure):**
1. Click **Wall** in toolbar
2. Select all other enclosure faces (top, bottom, front, back)
3. Set:
   - **WallType:** No-Slip
   - **ThermalType:** Adiabatic
4. Click **OK**

#### L1.6 — Generate Mesh

1. Click **CFD Mesh (GMSH)** in toolbar
2. Link to: Select the enclosure geometry
3. Set:
   - **CharacteristicLength:** 8.0 mm
   - **MinElementSize:** 2.0 mm
   - **MaxElementSize:** 20.0 mm
   - **Algorithm3D:** Delaunay
4. Click **Apply**

**Add surface refinement around chip:**
1. Click **Mesh Refinement Region** in toolbar
2. Select chip surfaces
3. Set **RefinementLevel:** 3.0 mm
4. Click **OK**

**Add boundary layer:**
1. Click **Boundary Layer Mesh** in toolbar
2. Select all wall faces
3. Set:
   - **Specification:** Target y+ (auto)
   - **TargetYPlus:** 30
   - **NumLayers:** 5
   - **ExpansionRatio:** 1.2
4. Click **OK**

5. Click **Run Mesh** (the gear icon on the mesh object)
6. Wait for meshing to complete (should show ~150K-250K cells)

#### L1.7 — Set Initial Conditions

1. Double-click **InitialConditions**
2. Set:
   - **Ux:** 2.0 m/s (matching inlet velocity for faster convergence)
   - **Temperature:** 293.15 K
3. Click **OK**

#### L1.8 — Configure and Run Solver

1. Double-click **Solver**
2. Set:
   - **SolverBackend:** OpenFOAM
   - **OpenFOAMSolver:** buoyantSimpleFoam
   - **MaxIterations:** 2000
   - **ConvergenceTolerance:** 1e-4
4. Click **OK**

5. Click **Run Solver** in toolbar
6. Monitor convergence — residuals should drop below 1e-4 within ~500-1000 iterations

#### L1.9 — Post-Process Results

1. Click **Post Pipeline** in toolbar
2. Click **Contour Plot** → Select variable: **Temperature** → Apply
3. Click **Streamlines** → Set seed point near inlet → Apply
4. Click **Point Probe** → Position at chip center (75, 100, 10) → Read temperature

**Expected results:**
- Chip surface temperature: ~45-55°C (318-328 K)
- Inlet velocity creates recirculation downstream of chip
- Temperature plume rises due to buoyancy

**Result interpretation diagram:**

```
  ┌──────────────────────────────────────────────┐
  │    Cool air (20°C)            Warm (25-30°C) │
  │     →→→→→→  ↗↗↗↗              →→→→→→→→→→→ → │
  │     →→→→→  ↗                  →→→→→→→→→→→ → │
  │     →→→  ╔══════╗  Hot plume ↗ →→→→→→→→→ → │
  │     →→→  ║ CHIP ║  (40-55°C)   →→→→→→→→ → │
  │     →→→  ║ 55°C ║  ↗↗↗↗↗       →→→→→→→ → │
  │     →→   ╚══════╝               →→→→→→→ → │
  │     →→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→ → │
  └──────────────────────────────────────────────┘
```

---

## Level 2 — Multi-Component PCB Cooling (Intermediate)

> **Difficulty:** ★★☆☆☆
> **Physics:** Steady, turbulent, heat transfer, natural + forced convection
> **Solver:** OpenFOAM (buoyantSimpleFoam)
> **Time to complete:** 1-2 hours
> **Cells:** ~500K-1M

### Scenario Description

A PCB board (200mm × 100mm) inside a ventilated enclosure (250mm × 150mm × 100mm)
carries four heat-generating components:

| Component | Size [mm] | Power [W] | Heat Flux [W/m²] |
|-----------|-----------|-----------|-------------------|
| CPU | 30×30×5 | 35 | 38,889 |
| GPU | 25×25×3 | 25 | 40,000 |
| Voltage Regulator | 15×10×3 | 8 | 53,333 |
| Memory Module | 40×10×3 | 5 | 12,500 |

A small fan drives air from the left (3 m/s) and warm air exits to the right.

```
  ┌────────────────────────────────────────────────┐
  │                                                │
  │   ┌─────┐  ┌────┐   ┌──┐  ┌──────────┐       │
  │   │ CPU │  │GPU │   │VR│  │  Memory  │       │
  │   │ 35W │  │25W │   │8W│  │   5W     │       │
      ══════════════════════════════════════ PCB
  FAN                                          EXIT
  3m/s                                         0 Pa
  ════►                                        ════►
  │                                                │
  └────────────────────────────────────────────────┘
```

### Key Differences from Level 1

1. **Multiple heat sources** — Each component gets its own wall BC with different heat flux
2. **Higher total power** — 73W total, need to verify outlet temperature rise
3. **Component interactions** — Downstream components receive pre-heated air
4. **Multiple refinement regions** — Each chip needs local mesh refinement

### Step-by-Step Instructions

#### L2.1 — Geometry

1. Create enclosure box: 250 × 150 × 100 mm
2. Create PCB board: 200 × 100 × 2 mm, positioned at Z=30 (raised)
3. Create four heat source boxes at their positions on the PCB
4. The fluid domain is the internal air volume (you can optionally Boolean-cut the components from the enclosure, but for simplicity treat them as internal obstacles)

#### L2.2 — Analysis & Physics

1. Create **New CFD Analysis**
2. Physics Model:
   - FlowRegime: **Turbulent**
   - TurbulenceModel: **kOmegaSST**
   - TimeModel: **Steady**
   - HeatTransfer: **✓ Enabled**
   - Gravity: **✓ Enabled**
   - Buoyancy: **✓ Enabled**

#### L2.3 — Material

Select preset: **Air (20°C, 1atm)**

#### L2.4 — Boundary Conditions

**Inlet (fan):**
- InletType: Velocity, VelocityMagnitude: 3.0 m/s
- InletTemperature: 293.15 K

**Outlet:**
- OutletType: Static Pressure, 0 Pa

**CPU top face:**
- WallType: No-Slip
- ThermalType: Fixed Heat Flux
- HeatFlux: 38889 W/m² (35W / 0.0009 m²)

**GPU top face:**
- WallType: No-Slip
- ThermalType: Fixed Heat Flux
- HeatFlux: 40000 W/m² (25W / 0.000625 m²)

**Voltage Regulator:**
- HeatFlux: 53333 W/m² (8W / 0.00015 m²)

**Memory Module:**
- HeatFlux: 12500 W/m² (5W / 0.0004 m²)

**Enclosure walls + PCB bottom:**
- ThermalType: Adiabatic

#### L2.5 — Mesh

- Base size: 5.0 mm
- Surface refinement on all chip faces: 2.0 mm
- Boundary layer: 5 layers, y+ target 30, expansion 1.2
- Add a box refinement region around the PCB area: 3.0 mm

**Expected cell count:** 500K-1M

#### L2.6 — Solver

- buoyantSimpleFoam
- MaxIterations: 3000 (more components = harder convergence)
- ConvergenceTolerance: 1e-4

#### L2.7 — Post-Processing

Key things to check:

1. **Temperature contour on PCB surface** — Shows hot spots
2. **Streamlines from inlet** — Shows if all components receive fresh air
3. **Point probes at each chip center** — Record junction temperatures
4. **Temperature contour on vertical cut plane** — Shows thermal plumes

**Expected results:**

| Component | Expected Temp [°C] | Risk Level |
|-----------|-------------------|------------|
| CPU | 55-70 | ⚠ Monitor |
| GPU | 50-65 | ⚠ Monitor |
| VR | 60-80 | ⚠ Highest flux |
| Memory | 35-45 | ✓ OK |

> **Key Insight:** The GPU, being downstream of the CPU, receives pre-heated
> air. Its temperature is higher than what the local heat flux alone would
> suggest. This is the **airflow stacking effect** — a critical design
> consideration in electronics cooling.

```
  Temperature [°C]:    20   30   40   50   60   70   80
                       ├────┼────┼────┼────┼────┼────┤
  Air flow →→→→→→→
  
  ┌────────────────────────────────────────────────┐
  │  ░░░░░░░░░░▒▒▒▒▒▒▒▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓██████  │
  │  ░ cool ░ ▒▒▒ warm ▒▒▒▓▓▓ hot ▓▓▓▓▓████████  │
  │  ░░░(CPU)░░▒▒(GPU)▒▒▒▓(VR)▓▓(Memory)██████  │
  │  ░░░░░░░░░░▒▒▒▒▒▒▒▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓██████  │
  └────────────────────────────────────────────────┘
```

---

## Level 2B — Electronics Cooling CHT + Radiation Benchmark (Intermediate-Advanced)

> **Difficulty:** ★★★☆☆
> **Physics:** Steady, turbulent, conjugate heat transfer with optional radiation
> **Solver:** OpenFOAM (`chtMultiRegionSimpleFoam`) or Elmer thermal/radiation workflow for partial parity
> **Time to complete:** 2-4 hours
> **Cells:** ~700K-1.5M across fluid + solid regions

### Scenario Description

This scenario mirrors the common SimFlow electronics-cooling tutorial pattern:
a **solid CPU and board** exchange heat with a forced-air **fluid region**, and a
second solve enables **surface-to-surface radiation** to quantify the thermal drop.

Unlike Level 2, this benchmark is intentionally **multi-region**:

- `solid` region contains the board, CPU, and fan housing solids
- `fluid` region contains the surrounding air domain
- a region interface couples conduction in the solids to convection in the air
- a second run toggles radiation to measure its effect on component temperature

Use this case when you want a workflow that is much closer to commercial
electronics-cooling GUIs and when wall heat-flux shortcuts are no longer enough.

### Benchmark Geometry

Import or create the following solids:

| Body | Role | Suggested source | Notes |
|------|------|------------------|-------|
| `board` | Main PCB solid | imported STL/STEP or Part box | Treated as solid conduction region |
| `cpu` | Heat-generating package | imported STL/STEP or Part box | Receives volumetric or equivalent heat source |
| `pins` | Secondary solid detail | optional imported STL/STEP | Helps test mesh refinement behavior |
| `fan` | Inlet plenum / fan body | Part box | Create a face group for the fan inlet |
| `outlet_tool` | Boundary extraction helper | Part box | Used to carve the outlet patch from the outer domain |
| `air_domain` | Outer enclosure / fluid box | Part box or Boolean result | Surrounds the board and CPU |

Suggested dimensions if you are building the benchmark from scratch instead of
reusing imported geometry:

- `fan`: origin `(0.05, 0.016, 0.0115) m`, size `(0.016, 0.016, 0.004) m`
- `outlet_tool`: origin `(0.0845, 0.0415, 0) m`, size `(0.0065, 0.009, 0.008) m`
- base domain min `(0, 0, 0) m`, max `(0.085, 0.056, 0.0155) m`

### FlowStudio Mapping

This is the closest FlowStudio mapping to the original commercial workflow:

| SimFlow concept | FlowStudio equivalent |
|-----------------|-----------------------|
| Case | `FlowStudio::CFDAnalysis` |
| Imported STL solids | FreeCAD Part bodies or imported STEP/STL geometry |
| Fan inlet face group | selected face + `FlowStudio_Fan` or inlet BC |
| Solid region | assigned `ThermalMaterial` objects on board/cpu solids |
| Fluid region | internal air volume with `FluidMaterial` |
| Region interface | touching fluid/solid boundary pair prepared for CHT backend |
| Cell-zone heat source | CPU heat source via fixed heat flux or solver-side volumetric source |
| Radiation panel | physics heat-transfer plus `FlowStudio_BC_Radiation` on exposed solids |
| ParaView temperature plots | `PostPipeline`, cut plots, surface plots, probes |

### Step-by-Step Instructions

#### L2B.1 — Geometry Preparation

1. Import `board`, `cpu`, and optional `pins` geometry or build them with Part primitives.
2. Create a `fan` box above the CPU.
3. Create an `outlet_tool` helper body on the far end of the enclosure.
4. Create an enclosing air box and derive the `air_domain` fluid volume.
5. Name bodies explicitly so later assignments stay readable: `board`, `cpu`, `pins`, `fan`, `air_domain`, `outlet_tool`.

#### L2B.2 — Analysis and Physics

1. Create **New CFD Analysis**.
2. In **PhysicsModel**, set:
   - `FlowRegime`: **Turbulent**
   - `TurbulenceModel`: **kEpsilon** or **kOmegaSST**
   - `Compressibility`: **Incompressible**
   - `TimeModel`: **Steady**
   - `HeatTransfer`: **✓ Enabled**
   - `Gravity`: **Optional** for this forced-flow benchmark
   - `Buoyancy`: **Off** unless you explicitly want mixed convection
3. For OpenFOAM-backed parity, set the solver app to **`chtMultiRegionSimpleFoam`**.
4. Keep **Radiation** disabled for the first pass; it will be enabled in the second run.

> **Implementation note:** FlowStudio already exposes heat transfer, thermal
> materials, and radiation BC objects. The fully guided CHT wizard is still a
> product target, so this benchmark documents the intended multi-region setup
> rather than claiming one-click automation.

#### L2B.3 — Materials

Assign materials by region:

**Fluid region:**
- `FluidMaterial`: **Air**
- If your backend exposes equation-of-state selection, prefer an incompressible ideal/perfect-gas style model for closer parity with the reference workflow.

**Solid regions:**
- `board`: **FR-4 (PCB)** or a custom thermal material
- `cpu`: **Aluminum** for the tutorial benchmark, or a package-specific custom material
- `pins`: **Copper** if included

For radiation-enabled runs, set reasonable emissivity values on the thermal materials:

| Region | Suggested emissivity |
|--------|----------------------|
| board / solder mask | 0.85-0.95 |
| CPU package top | 0.80-0.95 |
| bare aluminum surfaces | 0.05-0.20 unless coated |

#### L2B.4 — Boundary and Interface Setup

Configure the boundaries as follows:

**Fan inlet:**
- Select the fan bottom face and create a dedicated inlet face selection.
- Use either:
  - `FlowStudio_Fan` with an external-inlet or compact-fan style preset, or
  - `FlowStudio_BC_Inlet` with `VelocityMagnitude = 0.1 m/s`
- Set inlet temperature to `293.15 K`.

**Outlet:**
- Use the outer face or extracted outlet patch on the right side.
- `OutletType`: **Static Pressure**
- Pressure: `0 Pa`

**Outer enclosure walls:**
- `WallType`: **No-Slip**
- `ThermalType`: **Adiabatic** for the no-radiation baseline

**CPU heat source:**
- Preferred parity path: apply a **volumetric source** in the CPU region.
- Equivalent shortcut: apply a **Fixed Heat Flux** chosen to match `0.25 W` total power.
- If the CPU volume is approximately `200 mm^3`, the SimFlow-style volumetric source is:
  - `1.25e6 W/m^3`

**Fluid-solid interface:**
- Keep the CPU and board surfaces conformal with the surrounding fluid region.
- Mark the contacting fluid/solid surfaces as the CHT coupling interface for the selected backend.

#### L2B.5 — Mesh Strategy

Use a true multi-region mesh strategy rather than a single fluid-only mesh.

**Solid-region meshing:**
- `fan`: refinement `1-3`
- `board`: refinement `2-3`
- `cpu`: refinement `2-4`
- material point inside the solid region near `(0.058, 0.024, 0.0005) m`

**Fluid-region meshing:**
- move the material point into the air near `(0.058, 0.024, 0.005) m`
- keep the same base box extents as the geometry benchmark
- base divisions around `15 x 10 x 5` are acceptable for a first pass
- extract or explicitly define the outlet boundary before finalizing the fluid region

**Quality priorities:**
- maintain clean interface cells at CPU and board surfaces
- refine the fan and outlet path enough to avoid excessive numerical diffusion
- use boundary layers if your current backend path supports them cleanly

#### L2B.6 — Solver Controls

For the first run, target the no-radiation steady solution:

- Solver: `chtMultiRegionSimpleFoam`
- Turbulence: `realizable k-epsilon` for closer reference parity, `kOmegaSST` is also acceptable in FlowStudio tutorials
- Solid enthalpy tolerance: `1e-8` if exposed
- Non-orthogonal correctors: `2`
- Temperature limits: `290 K` to `600 K`
- Relaxation starting point:
  - `p_rgh`: `0.3`
  - `U`: `0.4`
  - `rho`, `k`, `epsilon`: `0.8`
  - `h` / solid enthalpy: `1.0`
- Initial run length: `800` iterations

#### L2B.7 — Radiation Pass

After the baseline converges:

1. Enable radiation in the active heat-transfer model.
2. Add `FlowStudio_BC_Radiation` to the exposed board, CPU, and fan-facing solid surfaces as needed.
3. Use surface-to-surface style assumptions where the backend supports it.
4. Keep the same mesh so the result delta is attributable to radiation rather than discretization changes.
5. Continue the run to roughly `2000` total iterations.

Expected benchmark behavior:

- baseline max temperature around the mid-`350 K` range
- with radiation enabled, peak temperature can drop by roughly `10-20 K`
- radiative heat flux should be visibly concentrated on the hotter package and nearby board surfaces

#### L2B.8 — Post-Processing Checklist

Create the following result views:

1. Temperature contour on board and CPU surfaces.
2. A cut plane through the fan, CPU, and outlet path.
3. Streamlines or flow trajectories from the inlet.
4. Point probes at CPU center, outlet, and a board hot spot.
5. A second temperature scene with the same color scale for the radiation-enabled rerun.
6. If supported, a radiative heat-flux plot on exposed solid surfaces.

#### L2B.9 — Validation Targets

Use these checks to judge whether the replication is behaving correctly:

| Check | Baseline expectation | Radiation run expectation |
|-------|----------------------|---------------------------|
| Residual trend | steady decay without oscillatory divergence | continued decay after restart |
| CPU peak temperature | hot spot on CPU and near-board contact | lower than baseline |
| Outlet air temperature | above inlet temperature | slightly cooler than baseline |
| Heat path | conduction into board + convection into air | same plus visible radiative redistribution |

### Why This Scenario Matters

This benchmark closes the gap between FlowStudio's existing beginner PCB example
and a workflow that thermal engineers expect from commercial electronics-cooling
tools:

1. It uses **fluid + solid regions** instead of only wall heat-flux surrogates.
2. It introduces **fan, outlet extraction, and interface coupling** as explicit setup tasks.
3. It makes **radiation** a measurable second-pass study instead of a theoretical checkbox.
4. It provides a reproducible benchmark for future FlowStudio workflow automation.

---

## Level 3 — NACA 2412 Wing (Intermediate-Advanced)

> **Difficulty:** ★★★☆☆
> **Physics:** Steady, turbulent, incompressible, external aerodynamics
> **Solver:** OpenFOAM (simpleFoam)
> **Time to complete:** 2-3 hours
> **Cells:** ~1M-2M

### Scenario Description

Simulate airflow around a **NACA 2412** airfoil in a wind tunnel at
different angles of attack. Compute lift and drag coefficients.

- Chord length: 1.0 m
- Span: 0.1 m (2D section with symmetry)
- Free-stream velocity: 30 m/s
- Angle of attack: 4°
- Reynolds number: Re ≈ 2,000,000

```
                    Wind tunnel domain
  ┌─────────────────────────────────────────────────┐
  │                                                 │
  │              5c upstream                        │
  │                                                 │
  │                    ╱═══════╲     4°             │
  │  Inlet ═══►      ╱  NACA   ╲    AoA    ═══► Outlet
  │  30 m/s          ╲  2412   ╱                   │
  │                    ╲═══════╱                    │
  │                                                 │
  │              10c downstream                     │
  │                                                 │
  └─────────────────────────────────────────────────┘
       Symmetry (front/back for 2D)

  Domain size:  15c × 10c × 0.1c
  (c = chord length = 1.0 m)
```

### Key Concepts for External Aerodynamics

**Wind tunnel sizing rules:**
- Upstream: 5× chord from wing leading edge to inlet
- Downstream: 10× chord from wing trailing edge to outlet
- Top/bottom: 5× chord from wing to top/bottom walls (or use open boundary)
- This prevents the domain boundaries from artificially influencing the flow

**Why this is different from internal flow:**
```
  Internal (box):                External (wing):
  ┌────────────────┐           ┌─────────────────────┐
  │                │           │  Fluid domain       │
  │  Fluid volume  │           │  ┌───────────┐      │
  │  = the box     │           │  │  SOLID     │      │
  │                │           │  │  (cut out) │      │
  └────────────────┘           │  └───────────┘      │
  Geometry = fluid             │                     │
                               └─────────────────────┘
                               Geometry = box − wing
```

### Step-by-Step Instructions

#### L3.1 — Create Wing Geometry

**Option A: Use FreeCAD's Part Workbench with Sketcher**
1. Create a Sketch on XZ plane
2. Import NACA 2412 coordinates (available from airfoiltools.com)
3. Create a closed BSpline through the coordinates
4. Pad/Extrude to span = 100 mm in Y direction

**Option B: Import a STEP file**
1. Download NACA 2412 STEP from airfoiltools.com or similar
2. File → Import → Select the .step file

**Create the wind tunnel:**
1. Create Box: 15000 × 1000 × 100 mm (15m × 1m × 0.1m)
2. Position wing at (5000, 500, 0) — 5m from inlet, centered vertically
3. Rotate wing 4° about Y-axis at its leading edge (angle of attack)
4. **Boolean Cut:** Tunnel − Wing = Fluid domain

#### L3.2 — Analysis & Physics

1. Create **New CFD Analysis**
2. Physics Model:
   - FlowRegime: **Turbulent** (Re ≈ 2M, clearly turbulent)
   - TurbulenceModel: **kOmegaSST** (best for boundary layer separation)
   - Compressibility: **Incompressible** (Ma ≈ 0.09, well below 0.3)
   - TimeModel: **Steady** (RANS approach)
   - HeatTransfer: OFF (pure aerodynamics)

#### L3.3 — Material

Select **Air (20°C, 1atm)**

#### L3.4 — Boundary Conditions

| Face | BC Type | Settings |
|------|---------|----------|
| **Inlet** (left) | Inlet: Velocity | U=30 m/s, normal to face, TI=1%, l=0.01m |
| **Outlet** (right) | Outlet: Static Pressure | P=0 Pa |
| **Wing surface** | Wall: No-Slip | Adiabatic |
| **Top & Bottom** | Open Boundary | FarFieldVelocity=(30,0,0), P=101325 Pa |
| **Front & Back** (span) | Symmetry | (makes it a 2D-like simulation) |

#### L3.5 — Mesh

This is the most critical step for wing simulations.

**Base mesh:**
- CharacteristicLength: 50 mm (large tunnel, coarse background)
- MinElementSize: 0.5 mm (near leading edge)
- MaxElementSize: 200 mm

**Surface refinement on wing:**
- Surface refinement: 2.0 mm on wing surface

**Leading edge refinement:**
- Volume sphere around leading edge: radius 50mm, size 1.0 mm

**Trailing edge refinement:**
- Volume sphere around trailing edge: radius 30mm, size 1.0 mm

**Wake refinement:**
- Volume box behind wing: 1000 × 200 × 100 mm, size 5.0 mm

**Boundary layer:**
- **Specification:** Target y+ (auto)
- **TargetYPlus:** 1.0 (wall-resolved for accurate lift/drag!)
- **NumLayers:** 15
- **ExpansionRatio:** 1.15

> **⚠ Important:** For lift and drag prediction, you MUST use y⁺ ≈ 1 on the
> wing surface. Wall functions (y⁺ ≈ 30) will significantly under-predict
> separation and give wrong drag values.

**Expected cell count:** 1M-2M

#### L3.6 — Initial Conditions

- Ux: 30.0 m/s (match free-stream)
- Pressure: 0 Pa
- **UsePotentialFlow:** ✓ Enabled (highly recommended for external flow!)

> **Why potential flow initialization?** Without it, the solver starts from
> a uniform field and takes hundreds of extra iterations to develop the flow
> around the wing. With potential flow, you get a good initial guess instantly.

#### L3.7 — Solver Settings

- SolverBackend: **OpenFOAM**
- OpenFOAMSolver: **simpleFoam** (steady incompressible)
- MaxIterations: 3000
- ConvergenceTolerance: 1e-5 (tighter for force coefficients)
- PressureSolver: GAMG
- ConvectionScheme: linearUpwind (2nd order, more accurate for aero)

#### L3.8 — Post-Processing

**Must-have visualisations:**

1. **Pressure coefficient contour on wing surface**
   - Shows suction peak on upper surface
   - Helps identify stall regions

2. **Streamlines** from inlet
   - Visualize flow attachment/separation on upper surface

3. **Force Report on wing surface**
   - Lift coefficient $C_L$
   - Drag coefficient $C_D$
   - Pitching moment $C_M$

**Expected results for NACA 2412 at 4° AoA, Re=2M:**

| Quantity | Expected Value | Your Result |
|----------|---------------|-------------|
| $C_L$ | ~0.65 | ______ |
| $C_D$ | ~0.008-0.012 | ______ |
| $C_L / C_D$ | ~55-80 | ______ |

```
  Pressure coefficient distribution (upper surface):

  Cp
  -2.0 ╷
       │  ╲
  -1.5 │   ╲  Suction peak
       │    ╲
  -1.0 │     ╲
       │      ╲──────────
  -0.5 │                 ╲──────
       │                        ──────────   Upper surface
   0.0 ├──────────────────────────────────── Leading edge
       │                                        Trailing edge
  +0.5 │  ──────────────────────────────── Lower surface
       │
  +1.0 ╵
       0.0          0.5          1.0  x/c
```

**Validation:** Compare your Cp distribution against published NACA 2412
data from Abbott & Von Doenhoff or XFOIL. The suction peak should be at
approximately x/c ≈ 0.15 on the upper surface.

---

## Level 4 — Server Rack Forced Cooling (Advanced)

> **Difficulty:** ★★★★☆
> **Physics:** Steady, turbulent, heat transfer, multiple heat sources, parallel
> **Solver:** OpenFOAM (buoyantSimpleFoam), parallel MPI
> **Time to complete:** 3-5 hours
> **Cells:** ~2M-5M

### Scenario Description

A 42U server rack (600mm × 1070mm × 2000mm) with:
- 6 servers at different power levels
- Front-to-back airflow (cold aisle / hot aisle architecture)
- Perforated floor tile supplying cold air at 18°C
- Target: Keep all inlet temperatures below 27°C

```
  Top View (looking down):
  ┌──────────────────────────────────────┐
  │ Server 1 (200W)  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  │
  │ Server 2 (350W)  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  │
  │ Server 3 (500W)  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  │
  │ (empty 3U)       ░░░░░░░░░░░░░░░░  │
  │ Server 4 (500W)  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  │
  │ Server 5 (350W)  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  │
  │ (empty 6U)       ░░░░░░░░░░░░░░░░  │
  │ Server 6 (800W)  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  │
  │ (empty 12U)      ░░░░░░░░░░░░░░░░  │
  └──────────────────────────────────────┘
       ↑ Cold aisle (front)    Hot aisle (rear) ↑
      18°C inlet              exhaust

  Side View:
  ┌────────────────────────────┐
  │  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  │ ← Server 1 (200W)
  │  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  │ ← Server 2 (350W)
  │  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  │ ← Server 3 (500W)
  │  ░░░░░░░░░░░░░░░░░░░░░░  │ ← Empty 3U (blanking panel?)
  │  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  │ ← Server 4 (500W)
  │  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  │ ← Server 5 (350W)
  │  ░░░░░░░░░░░░░░░░░░░░░░  │ ← Empty 6U
  │  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  │ ← Server 6 (800W)
  │  ░░░░░░░░░░░░░░░░░░░░░░  │ ← Empty 12U
  └────────────────────────────┘
       Front            Rear
       (cold)           (hot)
```

### Key Challenges (What Makes This Level 4)

1. **Multiple zones at different heights** — Air heats up as it rises
2. **Empty U-slots** — Hot air recirculation through gaps (must block or account for)
3. **Large power density** — Total 2700W in a confined space
4. **Parallel computation required** — 2M+ cells need MPI decomposition
5. **Convergence sensitivity** — Strong buoyancy + forced convection coupling

### Setup Highlight: Parallel Execution

For this case, serial execution would take hours. Use **parallel MPI**:

```python
# In Solver settings:
NumProcessors = 8       # Match your physical CPU cores
AutoParallel = False    # Manual specification for control

# This creates a decomposeParDict with Scotch method
# and runs decomposePar → mpirun -np 8 buoyantSimpleFoam → reconstructPar
```

**Decomposition visualization:**

```
  ┌──────┬──────┬──────┬──────┐
  │ Proc │ Proc │ Proc │ Proc │
  │  0   │  1   │  2   │  3   │
  │  ▓▓  │  ▓▓  │      │      │
  │  ▓▓  │  ▓▓  │  ▓▓  │  ▓▓  │
  │      │      │  ▓▓  │  ▓▓  │
  ├──────┼──────┼──────┼──────┤
  │ Proc │ Proc │ Proc │ Proc │
  │  4   │  5   │  6   │  7   │
  │  ▓▓  │  ▓▓  │      │      │
  │      │      │  ▓▓  │  ▓▓  │
  │      │      │  ▓▓  │  ▓▓  │
  └──────┴──────┴──────┴──────┘
  Scotch balances cell count per processor
```

### Boundary Conditions Summary

| Zone | BC | Thermal | Value |
|------|----|---------|-------|
| Front face (cold aisle) | Inlet: 3 m/s | T = 291.15 K (18°C) | — |
| Rear face (hot aisle) | Outlet: 0 Pa | — | — |
| Server 1 rear face | Wall | Heat Flux | 5556 W/m² (200W) |
| Server 2 rear face | Wall | Heat Flux | 9722 W/m² (350W) |
| Server 3 rear face | Wall | Heat Flux | 13889 W/m² (500W) |
| Server 4 rear face | Wall | Heat Flux | 13889 W/m² (500W) |
| Server 5 rear face | Wall | Heat Flux | 9722 W/m² (350W) |
| Server 6 rear face | Wall | Heat Flux | 22222 W/m² (800W) |
| Empty slots | Wall | Adiabatic | — |
| Rack sides/top/bottom | Wall | Adiabatic or HTC | h=5, T=22°C |

### Meshing Strategy

| Region | Cell Size | Note |
|--------|-----------|------|
| Bulk | 15 mm | Background |
| Near servers | 5 mm | Capture airflow past servers |
| Server faces | 3 mm | Surface refinement |
| Empty slots | 5 mm | Capture recirculation |
| Boundary layer (servers) | y+=30, 5 layers | Wall functions |

### Expected Results & Analysis

**Temperature distribution (side view):**

```
  Temperature [°C]: 18  22  26  30  34  38  42  46  50

  ┌────────────────────────────┐
  │░░░░▒▒▒▒▒▒▒▒▒▒▓▓▓▓▓▓▓▓▓▓▓│ S1: Exit ~28°C
  │░░░░▒▒▒▒▒▒▒▒▒▓▓▓▓████████│ S2: Exit ~35°C
  │░░░░▒▒▒▒▒▓▓▓▓▓████████████│ S3: Exit ~42°C
  │░░░░▒▒▒▒▒▒▒▒▒▒▓▓▓▓▓▓▓▓▓▓▓│ Gap: Recirculation
  │░░░░▒▒▒▒▒▓▓▓▓▓████████████│ S4: Exit ~42°C
  │░░░░▒▒▒▒▒▒▒▒▒▓▓▓▓████████│ S5: Exit ~35°C
  │░░░░░░░░░░░░░░░░░░░░░░░░░░│ Gap: Cool
  │░░░░▒▒▒▒▓▓▓▓█████████████│ S6: Exit ~48°C ⚠
  │░░░░░░░░░░░░░░░░░░░░░░░░░░│ Gap: Cool
  └────────────────────────────┘
  Front (18°C)         Rear (exhaust)
```

**Key engineering analysis:**
1. **Hot spot identification:** Server 6 (800W) has highest exhaust temperature
2. **Recirculation check:** Are empty slots causing hot air to recirculate to the front?
3. **If empty slots have no blanking panels:** Hot exhaust recirculates → servers above get hotter air
4. **Design improvement:** Add blanking panels to empty slots

> **Engineering Decision:**  If any server inlet temperature exceeds 27°C
> (ASHRAE A1 recommended), you need to either: increase airflow, reduce power,
> add blanking panels, or reposition high-power servers.

---

## Level 5 — CT Detector Rotating System (Expert)

> **Difficulty:** ★★★★★
> **Physics:** Transient, turbulent, rotating reference frame (MRF),
>              multi-physics (EM + Thermal + CFD), heat transfer
> **Solver:** OpenFOAM (pimpleFoam) for CFD, Elmer for EM+Thermal
> **Time to complete:** 1-2 days
> **Cells:** ~5M-10M

### Scenario Description

A CT (Computed Tomography) scanner gantry with:
- Rotating ring housing (∅ 800mm, width 300mm) at **2 rev/s (120 RPM)**
- X-ray tube generating **5 MW/m³** volumetric heat
- Two internal cooling fans (∅ 150mm, 3000 RPM)
- Multiple materials: air, tungsten (X-ray anode), copper PCB, ceramic
- Goal: Predict temperatures, validate cooling adequacy, visualize airflow

```
  Front View (looking along rotation axis):

                    ╔═══════════════╗
                ╔═══╝               ╚═══╗
              ╔═╝    Rotating Gantry     ╚═╗
            ╔═╝         (800mm ∅)          ╚═╗
           ║                                  ║
           ║   ┌──────┐        ┌──────┐      ║
           ║   │ FAN  │        │ FAN  │      ║
           ║   │3000  │  ╔══╗  │3000  │      ║
           ║   │ RPM  │  ║XT║  │ RPM  │      ║
           ║   └──────┘  ║  ║  └──────┘      ║
           ║             ╚══╝                 ║
           ║         X-ray tube               ║
           ║         5 MW/m³ heat             ║
            ╚═╗                            ╔═╝
              ╚═╗    ┌────────────┐     ╔═╝
                ╚═══╗│ Electronics│╔═══╝
                    ╚╧════════════╧╝
                      (PCB + copper)

  Side View (rotation axis is horizontal):

  ← 300mm →
  ┌────────────────────────────────────────────────┐
  │                                                │
  │   ┌────┐  ┌═══════╗  ┌────┐                  │
  │   │FAN │  ║ X-ray ║  │FAN │                  │   ↻ Rotates
  │   │    │  ║ tube  ║  │    │                  │   at 2 rev/s
  │   └────┘  ╚═══════╝  └────┘                  │   (12.57 rad/s)
  │                                                │
  │   ┌────────────────────────────────────┐      │
  │   │        Electronics (PCB)           │      │
  │   └────────────────────────────────────┘      │
  └────────────────────────────────────────────────┘
```

### Why This is Level 5

This simulation is the most complex because it combines:

1. **Rotating reference frames (MRF)** — The gantry rotates, creating centrifugal and Coriolis forces
2. **Multiple rotating zones** — Fans spin at different RPM than the gantry
3. **Multi-physics coupling** — EM fields (optional) + heat generation + forced convection
4. **Transient solver** — Rotation inherently requires time-dependent solution
5. **Very small time steps** — CFL condition with tip speeds >47 m/s requires Δt ≈ 34 μs
6. **Multiple materials** — Air, tungsten, copper, ceramic with very different properties
7. **Large cell count** — 5-10M cells for adequate resolution

### Step-by-Step Instructions

#### L5.1 — Understanding MRF (Multiple Reference Frame)

MRF is a technique for simulating rotating machinery **without physically moving the mesh**. Instead, source terms are added to the momentum equation to account for centrifugal and Coriolis forces.

```
  Inertial Frame                  Rotating Frame (MRF)
  (lab/stationary)               (co-rotating with gantry)

  Observer sees                   Observer rotates with gantry,
  gantry spinning                 sees gantry as stationary
  ┌──────────┐                    ┌──────────┐
  │    ↻     │                    │ (static) │
  │ rotating │      ══►           │ + source │
  │  mesh    │   Transform        │  terms:  │
  │          │                    │ Coriolis │
  └──────────┘                    │ Centrifugal
                                  └──────────┘

  Advantage:  Steady-state MRF is 100x cheaper than sliding mesh!
  Limitation: Assumes steady flow in the rotating frame (no strong
              rotor-stator interaction at this level)
```

**Key MRF parameters for this case:**

| Parameter | Gantry | Fan 1 | Fan 2 |
|-----------|--------|-------|-------|
| Zone | rotatingGantry | fan1Zone | fan2Zone |
| ω [rad/s] | 12.57 (2 rev/s) | 314.16 (3000 RPM) | 314.16 (3000 RPM) |
| Axis | (0, 0, 1) | (0, 0, 1) | (0, 0, 1) |
| Origin | (0, 0, 0) | (-150, 100, 0) | (150, 100, 0) |

**Fan blade tip speed:**
$$v_{tip} = \omega \cdot r = 314.16 \times 0.075 = 23.6 \text{ m/s}$$

**Courant number calculation:**
$$Co = \frac{v \cdot \Delta t}{\Delta x} < 1$$

For the fan zone: Δx ≈ 2mm, v ≈ 24 m/s
$$\Delta t_{max} = \frac{Co \cdot \Delta x}{v} = \frac{0.8 \times 0.002}{24} \approx 67 \mu s$$

#### L5.2 — Geometry

1. **Outer housing:** Cylinder, ∅800mm × 300mm
2. **X-ray tube:** Box 80×40×40 mm, positioned at (0, 200, 0)
3. **Fan zones:** Two cylinders ∅150mm × 30mm at (±150, 100, 0)
4. **Electronics PCB:** Box 200×100×2 mm at (0, -100, 0)
5. **Boolean cut:** Housing − (X-ray tube + PCB) = Air domain
6. **MRF zones:** Create named cell zones for gantry volume and each fan volume

#### L5.3 — Create Multi-Physics Analyses

This requires **two coupled analyses** or a single multi-physics analysis:

**Analysis 1: CFD (OpenFOAM)**
- Physics: Transient, Turbulent (kOmegaSST), Heat Transfer ON
- Handles: Airflow, fan forcing, temperature distribution

**Analysis 2: Thermal (Elmer)**
- Handles: Solid heat conduction in X-ray tube, PCB, housing
- Couples to CFD via: surface heat transfer coefficients

> **For this tutorial**, we simplify by using a single CFD analysis with wall
> heat flux BCs representing the heat sources. The full multi-physics coupling
> is described in the theory section below.

#### L5.4 — Material Properties

| Material | Usage | ρ [kg/m³] | k [W/(m·K)] | Cp [J/(kg·K)] |
|----------|-------|-----------|-------------|----------------|
| **Air (20°C)** | Cooling fluid | 1.225 | 0.025 | 1005 |
| **Tungsten** | X-ray anode | 19,300 | 173 | 134 |
| **Copper** | PCB/electronics | 8,960 | 401 | 385 |
| **Alumina (ceramic)** | X-ray tube insulation | 3,900 | 30 | 880 |

For the CFD analysis, use Air as the fluid material.

#### L5.5 — Boundary Conditions

| Surface | BC | Type | Values |
|---------|----|----|--------|
| X-ray tube surface | Wall | Fixed Heat Flux | Q = 5×10⁶ W/m³ × V_tube / A_tube |
| PCB surface | Wall | Fixed Heat Flux | 5000 W/m² |
| Fan inlets | Wall | Moving Wall (Rotational) | ω=314.16, axis=(0,0,1) |
| Housing inner wall | Wall | HTC | h=10 W/(m²·K), T_amb=25°C |
| Ventilation slots | Inlet/Outlet | Pressure | P=0 (natural ventilation) |

**The Moving Wall (Rotational) settings for fans:**
```
Property          │ Value
──────────────────┼──────────────────
WallType          │ Moving Wall (Rotational)
AngularVelocity   │ 314.16 rad/s
RotationAxis      │ (0, 0, 1)
RotationOrigin    │ (-150, 100, 0) mm   [for fan 1]
```

#### L5.6 — Mesh Strategy

This is the most demanding mesh in the tutorial:

| Region | Cell Size | Reason |
|--------|-----------|--------|
| Bulk (housing interior) | 10 mm | Background |
| Near X-ray tube | 3 mm | Hot surface |
| Fan zone | 2 mm | High velocity gradients |
| Fan blade surface | 1 mm | Capture blade forces |
| PCB surface | 3 mm | Heat source |
| Boundary layers (all walls) | y+=30, 5 layers | Wall functions |
| Fan blade BL | y+=1, 10 layers | Resolve blade flow |

**Expected cell count:** 5-10 million

#### L5.7 — Solver Configuration

```
SolverBackend:      OpenFOAM
OpenFOAMSolver:     pimpleFoam (transient, incompressible)
TimeStep:           5e-5 s (50 μs)
EndTime:            0.5 s (one full gantry revolution)
MaxCourantNumber:   0.8
WriteInterval:      100 (every 5ms → 100 frames)
NumProcessors:      8-16 (parallel required!)
```

**Convergence strategy:**
1. First, run 1000 iterations of simpleFoam (steady) to get an initial solution
2. Switch to pimpleFoam (transient) using the converged steady solution as IC
3. Run for ~5000 time steps (0.25s) to wash out startup transients
4. Collect statistics for the next 5000 steps (0.25s)

#### L5.8 — Elmer Multi-Physics (Optional Advanced)

For the complete CT detector simulation including EM fields, create a
separate Elmer analysis:

```python
from flow_studio.solvers.elmer_sif import SifBuilder, SifProcedure

b = SifBuilder()

# Header
b.set_header(mesh_db=".", mesh_dir="mesh", results_dir="results")

# Transient simulation (gantry rotates)
b.set_simulation(
    coord_system="Cartesian 3D",
    sim_type="Transient",
    Timestep_Sizes=1e-4,
    Timestep_Intervals=5000,
    Output_Intervals=100,
)

# Physical constants
b.set_constant("Permittivity Of Vacuum", 8.8542e-12)
b.set_constant("Stefan Boltzmann", 5.67e-8)

# Bodies
air = b.add_body("CoolingAir", equation=1, material=1, body_force=1)
tube = b.add_body("XRayTube", equation=2, material=2, body_force=2)
pcb = b.add_body("Electronics", equation=2, material=3)

# Materials
mat_air = b.add_material("Air")
mat_air["Density"] = 1.225
mat_air["Viscosity"] = 1.81e-5
mat_air["Heat Conductivity"] = 0.025
mat_air["Heat Capacity"] = 1005.0

mat_w = b.add_material("Tungsten")
mat_w["Density"] = 19300.0
mat_w["Heat Conductivity"] = 173.0
mat_w["Heat Capacity"] = 134.0

mat_cu = b.add_material("CopperPCB")
mat_cu["Density"] = 8960.0
mat_cu["Heat Conductivity"] = 401.0
mat_cu["Heat Capacity"] = 385.0

# Solvers
b.add_solver(
    "Navier-Stokes",
    SifProcedure("FlowSolve", "FlowSolver"),
    variable="Flow Solution",
    variable_dofs=4,
    Stabilize=True,
    Nonlinear_System_Max_Iterations=5,
    Linear_System_Solver="Iterative",
    Linear_System_Iterative_Method="BiCGStab",
    Linear_System_Max_Iterations=500,
    Linear_System_Preconditioning="ILU1",
)
b.add_solver(
    "Heat Equation",
    SifProcedure("HeatSolve", "HeatSolver"),
    variable="Temperature",
    variable_dofs=1,
    Linear_System_Solver="Iterative",
    Linear_System_Iterative_Method="BiCGStab",
)

# Equations
b.add_equation("FlowAndHeat", [1, 2])
b.add_equation("HeatOnly", [2])

# Body forces
bf_grav = b.add_body_force("Gravity")
bf_grav["Flow Bodyforce 3"] = -9.81
bf_heat = b.add_body_force("XRayHeatGen")
bf_heat["Heat Source"] = 5e6  # W/m³

# Boundary conditions
inlet_bc = b.add_boundary_condition("CoolAirInlet")
inlet_bc["Velocity 1"] = 5.0
inlet_bc["Velocity 2"] = 0.0
inlet_bc["Velocity 3"] = 0.0
inlet_bc["Temperature"] = 293.15

outlet_bc = b.add_boundary_condition("Exhaust")
outlet_bc["External Pressure"] = 0.0

wall_bc = b.add_boundary_condition("HousingWall")
wall_bc["Noslip Wall BC"] = True

ic = b.add_initial_condition("Uniform")
ic["Temperature"] = 293.15
ic["Velocity 1"] = 0.0
ic["Velocity 2"] = 0.0
ic["Velocity 3"] = 0.0
ic["Pressure"] = 0.0

# Generate the SIF file
sif_content = b.generate()
print(sif_content)
```

#### L5.9 — Post-Processing

For a CT detector simulation, key outputs are:

```
┌─────────────────────────────────────────────────────────────────┐
│                CT DETECTOR POST-PROCESSING CHECKLIST            │
│                                                                 │
│  ☐ Temperature contour on X-ray tube           → Max temp?     │
│  ☐ Temperature contour on PCB                   → Hot spots?    │
│  ☐ Velocity streamlines from fans               → Coverage?     │
│  ☐ Temperature vs. time at X-ray anode          → Thermal cycle │
│  ☐ Velocity magnitude on mid-plane cut          → Dead zones?   │
│  ☐ Air temperature at housing exhaust           → ΔT?           │
│  ☐ Force report on fan blades (optional)        → Fan loading   │
│  ☐ Generate ParaView script for publication     → pvpython      │
└─────────────────────────────────────────────────────────────────┘
```

**Measurement objects for automated data extraction:**

```python
# In FlowStudio, add measurement objects:
# 1. Measurement Point at X-ray tube center → Temperature vs time
# 2. Measurement Surface at housing exhaust → Average exit temperature
# 3. Measurement Volume around X-ray tube   → Max temperature in volume

# Then: FlowStudio → Generate ParaView Script
# This creates evaluate.py which can be run with:
#   pvpython evaluate.py
```

**Expected results:**

| Metric | Target | Expected |
|--------|--------|----------|
| X-ray anode temp | < 300°C | 150-200°C |
| PCB max temp | < 85°C | 45-65°C |
| Housing exhaust ΔT | < 30K | 15-25K |
| Fan blade loading | — | ~0.5-2 N |
| Time to thermal steady state | — | ~30-60s |

---

## 9. Post-Processing Deep-Dive

### 9.1 Built-in Post-Processing Pipeline

FlowStudio's built-in post-processing provides quick visualization without
leaving FreeCAD:

```
  Post Pipeline
    │
    ├── Contour Plot
    │     ├── Variable: Velocity / Pressure / Temperature / TurbulentKE
    │     ├── Display: Surface / Cut Plane / Iso-Surface
    │     └── Color Map: Rainbow / Blue-Red / Viridis
    │
    ├── Streamlines
    │     ├── Seed: Point / Line / Rake / Surface
    │     ├── Integration: Runge-Kutta 4
    │     └── Color by: Velocity / Temperature / Pressure
    │
    ├── Point Probe
    │     ├── Location: (x, y, z)
    │     └── Reports: All field values at that point
    │
    └── Force Report
          ├── Surface: Select faces
          └── Reports: Drag, Lift, Moment coefficients
```

### 9.2 ParaView Script Generation

For advanced post-processing, FlowStudio generates ParaView Python scripts:

1. Add **Measurement Points**, **Measurement Surfaces**, and/or **Measurement Volumes**
2. Click **Generate ParaView Script**
3. Run: `pvpython evaluate.py`

**Measurement types:**

| Type | Objects | Outputs |
|------|---------|---------|
| **Point** | Single point or line of points | Field values at locations |
| **Surface** | Cut plane, iso-surface, or face | Average, min, max, integral, mass flow |
| **Volume** | Box, sphere, cylinder, threshold | Volume average, max, min, statistics |

### 9.3 Interpreting Residuals

During the solver run, watch the residuals. They tell you if the solution
is converging:

```
  Residual
  1e+0 ╷
       │╲
  1e-1 │ ╲
       │  ╲
  1e-2 │   ╲───────  p (pressure)
       │    ╲
  1e-3 │     ╲────── Ux (velocity)
       │      ╲
  1e-4 │───────╲──── Target ← CONVERGED when below this line
       │        ────── k, ω (turbulence)
  1e-5 │
       │
  1e-6 ╵
       0    500   1000  1500  2000  Iterations
```

**What to look for:**

| Pattern | Meaning | Action |
|---------|---------|--------|
| All residuals drop to target | ✓ Converged | Stop, check results |
| Residuals oscillate but trend down | Slow convergence | Increase iterations or add relaxation |
| Residuals plateau above target | Partial convergence | Check mesh quality, BCs, physics model |
| Residuals blow up (increase) | ✗ Diverged | Reduce time step, add relaxation, check mesh |

---

## 10. Solver Backend Reference

### 10.1 OpenFOAM Solver Selection Matrix

| Application | Type | Compressibility | Heat | Transient |
|-------------|------|-----------------|------|-----------|
| **simpleFoam** | SIMPLE | Incompressible | No | Steady |
| **pimpleFoam** | PIMPLE | Incompressible | No | Transient |
| **pisoFoam** | PISO | Incompressible | No | Transient |
| **icoFoam** | — | Incompressible | No | Transient (laminar) |
| **rhoSimpleFoam** | SIMPLE | Compressible | Yes | Steady |
| **rhoPimpleFoam** | PIMPLE | Compressible | Yes | Transient |
| **buoyantSimpleFoam** | SIMPLE | Weakly-Comp. | Yes | Steady |
| **buoyantPimpleFoam** | PIMPLE | Weakly-Comp. | Yes | Transient |
| **interFoam** | VOF | Incompressible | No | Transient (2-phase) |
| **potentialFoam** | — | Incompressible | No | — (initial field) |

### 10.2 FluidX3D (GPU LBM)

| Property | Options | Description |
|----------|---------|-------------|
| Precision | FP32/FP32, FP32/FP16S, FP32/FP16C | Trade accuracy for speed |
| Resolution | 64-2048 | Grid points along longest axis |
| VRAM Budget | 512-24000 MB | GPU memory limit |
| Extensions | EQUILIBRIUM_BOUNDARIES, MOVING_BOUNDARIES, TEMPERATURE, etc. | Physics modules |
| Multi-GPU | True/False | Domain decomposition across GPUs |

**When to use FluidX3D:**
- Quick design iterations (10-100× faster than OpenFOAM)
- GPU available with sufficient VRAM
- Moderate accuracy requirements
- Real-time flow visualization during design

### 10.3 Elmer FEM

Elmer handles all non-CFD physics domains:

| Domain | Solver Procedure | Primary Variable |
|--------|-----------------|------------------|
| CFD (Navier-Stokes) | FlowSolve/FlowSolver | Flow Solution (4 DOF) |
| Heat Transfer | HeatSolve/HeatSolver | Temperature (1 DOF) |
| Electrostatics | StatElecSolve/StatElecSolver | Potential (1 DOF) |
| Electromagnetics | MagnetoDynamics/MagnetoDynamicsSolver | AV (4 DOF) |
| Structural | StressSolve/StressSolver | Displacement (3 DOF) |

---

## 11. Troubleshooting & FAQ

### Common Problems

| Problem | Likely Cause | Solution |
|---------|-------------|----------|
| Solver diverges immediately | Mesh quality too poor | Check non-orthogonality (< 65°), skewness (< 0.9) |
| Solver diverges after 100 iterations | Turbulence initialization | Set initial k, ω to reasonable values; reduce relaxation |
| Temperature goes to infinity | Missing thermal BC | Ensure every wall has a thermal type (even if adiabatic) |
| Pressure oscillations | Checkerboard pattern | Enable pressure stabilisation; check mesh |
| Solution doesn't converge | Under-resolved mesh | Refine near walls, heat sources, shear layers |
| Parallel run crashes | Unbalanced decomposition | Use scotch method; ensure ≥50K cells per process |
| "GAMG: no convergence" | Difficult pressure field | Switch to PCG solver; add DIC preconditioner |
| Force coefficients oscillate | Mesh too coarse on surface | Refine wing surface mesh; use y+=1 |

### Performance Tuning

| Setting | Faster Convergence | Better Accuracy | 
|---------|-------------------|-----------------|
| ConvectionScheme | upwind (1st order) | linearUpwind (2nd order) |
| RelaxationFactorU | 0.5 (more stable) | 0.8 (faster, may oscillate) |
| RelaxationFactorP | 0.2 (more stable) | 0.4 (faster, may oscillate) |
| PressureSolver | GAMG (fast, robust) | PCG (slower, exact) |
| y+ target | 30 (wall functions) | 1 (wall-resolved, expensive) |

### FAQ

**Q: How many cells do I need?**
A: Start with a coarse mesh (~100K cells) to verify your setup runs.
Then refine until the result changes by less than 2% between refinements.
This is called a **mesh independence study**.

**Q: Which turbulence model should I use?**
A: k-ω SST for 90% of cases. Use Spalart-Allmaras for thin attached boundary
layers (aerospace). Use LES only when you need unsteady detail (noise, mixing).

**Q: Steady or transient?**
A: Start with steady-state (SIMPLE). Switch to transient (PIMPLE) only if:
- Flow is inherently unsteady (vortex shedding, rotating machines)
- Steady solver won't converge (indicates unsteady physics)
- You need time-accurate results (transient heat loads, startup)

**Q: How long should my simulation run?**
A: Steady: Until residuals are below your tolerance (typically 500-3000 iterations).
Transient: Long enough for statistics (typically 3-5× the *flow-through time*,
which is domain length / average velocity).

**Q: Can I use FluidX3D for my case?**
A: FluidX3D is excellent for quick previews but currently limited to:
- Incompressible flow
- Simple boundary conditions
- No heat transfer (without TEMPERATURE extension)
- Moderate Reynolds numbers

---

## 12. Appendix: Property Reference Tables

### A.1 — Physics Model Properties

| Property | Type | Default | Options |
|----------|------|---------|---------|
| FlowRegime | Enum | Turbulent | Laminar, Turbulent |
| TurbulenceModel | Enum | kOmegaSST | kEpsilon, kOmega, kOmegaSST, SpalartAllmaras, LES-Smagorinsky, LES-WALE, LBM-Implicit |
| Compressibility | Enum | Incompressible | Incompressible, Compressible, Weakly-Compressible |
| TimeModel | Enum | Steady | Steady, Transient |
| Gravity | Bool | False | — |
| HeatTransfer | Bool | False | — |
| Buoyancy | Bool | False | — |
| FreeSurface | Bool | False | — |
| PassiveScalar | Bool | False | — |

### A.2 — Inlet BC Properties

| Property | Type | Default | Unit |
|----------|------|---------|------|
| InletType | Enum | Velocity | Velocity, Mass Flow Rate, Volumetric Flow Rate, Total Pressure |
| Ux, Uy, Uz | Float | 0, 0, 1 | m/s |
| VelocityMagnitude | Float | 1.0 | m/s |
| NormalToFace | Bool | True | — |
| MassFlowRate | Float | 0.0 | kg/s |
| VolFlowRate | Float | 0.0 | m³/s |
| TotalPressure | Float | 0.0 | Pa |
| TurbulenceIntensity | Float | 5.0 | % |
| TurbulenceLengthScale | Float | 0.01 | m |
| InletTemperature | Float | 293.15 | K |

### A.3 — Outlet BC Properties

| Property | Type | Default | Unit |
|----------|------|---------|------|
| OutletType | Enum | Static Pressure | Static Pressure, Mass Flow Rate, Outflow (Zero Gradient) |
| StaticPressure | Float | 0.0 | Pa |
| OutletMassFlowRate | Float | 0.0 | kg/s |
| PreventBackflow | Bool | True | — |

### A.4 — Wall BC Properties

| Property | Type | Default | Unit |
|----------|------|---------|------|
| WallType | Enum | No-Slip | No-Slip, Slip, Moving Wall (Translational), Moving Wall (Rotational), Rough Wall |
| WallVelocityX/Y/Z | Float | 0.0 | m/s |
| AngularVelocity | Float | 0.0 | rad/s |
| RotationAxis | Vector | (0,0,1) | — |
| RotationOrigin | Vector | (0,0,0) | mm |
| RoughnessHeight | Float | 0.0 | m |
| RoughnessConstant | Float | 0.5 | — |
| ThermalType | Enum | Adiabatic | Adiabatic, Fixed Temperature, Fixed Heat Flux, Heat Transfer Coefficient |
| WallTemperature | Float | 293.15 | K |
| HeatFlux | Float | 0.0 | W/m² |
| HeatTransferCoeff | Float | 0.0 | W/(m²·K) |

### A.5 — Solver Properties

| Property | Type | Default | Unit/Options |
|----------|------|---------|--------------|
| SolverBackend | Enum | OpenFOAM | OpenFOAM, FluidX3D, SU2 |
| OpenFOAMSolver | Enum | simpleFoam | (see Section 10.1) |
| MaxIterations | Int | 2000 | — |
| ConvergenceTolerance | Float | 1e-4 | — |
| RelaxationFactorU | Float | 0.7 | — |
| RelaxationFactorP | Float | 0.3 | — |
| NumProcessors | Int | 1 | — |
| TimeStep | Float | 0.0 | s (0 = auto) |
| EndTime | Float | 1.0 | s |
| MaxCourantNumber | Float | 1.0 | — |

### A.6 — Mesh Properties

| Property | Type | Default | Unit/Options |
|----------|------|---------|--------------|
| CharacteristicLength | Float | 10.0 | mm |
| MinElementSize | Float | 1.0 | mm |
| MaxElementSize | Float | 50.0 | mm |
| Algorithm3D | Enum | Delaunay | Delaunay, Frontal, HXT, MMG3D |
| ElementOrder | Enum | 1st Order | 1st Order, 2nd Order |
| GrowthRate | Float | 1.3 | — |
| CellsInGap | Int | 3 | — |

### A.7 — Boundary Layer Properties

| Property | Type | Default | Unit/Options |
|----------|------|---------|--------------|
| NumLayers | Int | 5 | — |
| FirstLayerHeight | Float | 0.1 | mm |
| ExpansionRatio | Float | 1.2 | — |
| Specification | Enum | First Layer + Expansion | (4 options) |
| TargetYPlus | Float | 1.0 | — |

### A.8 — Material Presets (Full Data)

| Preset | ρ [kg/m³] | μ [Pa·s] | ν [m²/s] | Cp [J/(kg·K)] | k [W/(m·K)] | Pr |
|--------|-----------|----------|----------|----------------|-------------|-----|
| Air (20°C, 1atm) | 1.225 | 1.81e-5 | 1.48e-5 | 1005 | 0.0257 | 0.707 |
| Water (20°C) | 998.2 | 1.002e-3 | 1.004e-6 | 4182 | 0.60 | 7.01 |
| Oil (SAE 30) | 891.0 | 0.29 | 3.25e-4 | 1900 | 0.145 | 3800 |
| Glycerin | 1261.0 | 1.412 | 1.12e-3 | 2427 | 0.286 | 11970 |
| Mercury | 13534.0 | 1.526e-3 | 1.128e-7 | 139.3 | 8.514 | 0.025 |

---

## Quick Reference: Simulation Setup Decision Matrix

Use this matrix to quickly determine the right settings for your simulation:

```
START HERE
    │
    ├─── What type of flow?
    │     ├── Internal (box, pipe, channel) ──→ Geometry IS the fluid
    │     └── External (wing, car, building) ──→ Create wind tunnel, Boolean-subtract solid
    │
    ├─── Is heat transfer important?
    │     ├── Yes ──→ Enable HeatTransfer + set thermal BCs on walls
    │     └── No  ──→ Leave HeatTransfer OFF (saves computation)
    │
    ├─── Is the flow steady or unsteady?
    │     ├── Steady (most cases) ──→ TimeModel: Steady,  Solver: simpleFoam / buoyantSimpleFoam
    │     └── Unsteady (rotating, pulsating) ──→ TimeModel: Transient,  Solver: pimpleFoam
    │
    ├─── What Reynolds number?
    │     ├── Re < 2300 ──→ Laminar (no turbulence model)
    │     └── Re > 2300 ──→ Turbulent ──→ k-ω SST (default, best general choice)
    │
    ├─── Need y+ = 1 (wall-resolved)?
    │     ├── Yes (forces/heat transfer accuracy) ──→ 10-15 BL layers, fine mesh
    │     └── No (general flow features) ──→ y+=30, 5 BL layers (wall functions)
    │
    └─── How many cells?
          ├── < 500K ──→ Serial (NumProcessors = 1)
          └── > 500K ──→ Parallel (NumProcessors = physical CPU cores, ≥50K cells/proc)
```

---

*FlowStudio v0.2.0 — Multi-Physics Simulation Workbench for FreeCAD*
*Tutorial revision: April 2026*
*License: LGPL-2.1-or-later*
