// FlowStudio - Zero to Post-Processing Tutorial (Typst)
// Version 0.2.0

#set page(
  paper: "a4",
  margin: (top: 2.3cm, bottom: 2.2cm, left: 2.2cm, right: 2.2cm),
  numbering: "1",
  number-align: center,
)
#set text(font: "Segoe UI", size: 10pt, fill: rgb("#263238"))
#set par(justify: true, leading: 0.66em)
#set heading(numbering: "1.1.1")

#show heading.where(level: 1): it => {
  pagebreak(weak: true)
  v(0.35cm)
  block(width: 100%, below: 0.7cm)[
    #set text(18pt, weight: "bold", fill: rgb("#0D47A1"))
    #it
    #v(0.12cm)
    #line(length: 100%, stroke: 1.5pt + rgb("#1565C0"))
  ]
}
#show heading.where(level: 2): set text(13.5pt, weight: "bold", fill: rgb("#1565C0"))
#show heading.where(level: 3): set text(11.5pt, weight: "bold", fill: rgb("#37474F"))

#show raw.where(block: true): block.with(
  fill: rgb("#F5F5F5"),
  inset: 10pt,
  radius: 4pt,
  width: 100%,
  stroke: 0.5pt + rgb("#E0E0E0"),
)

#let note(body) = block(
  width: 100%, fill: rgb("#E3F2FD"), inset: 10pt, radius: 4pt,
  stroke: (left: 3pt + rgb("#1976D2")),
)[#text(weight: "bold", fill: rgb("#1565C0"))[Note] #parbreak() #body]

#let warning(body) = block(
  width: 100%, fill: rgb("#FFF3E0"), inset: 10pt, radius: 4pt,
  stroke: (left: 3pt + rgb("#F57C00")),
)[#text(weight: "bold", fill: rgb("#E65100"))[Warning] #parbreak() #body]

#let tip(body) = block(
  width: 100%, fill: rgb("#E8F5E9"), inset: 10pt, radius: 4pt,
  stroke: (left: 3pt + rgb("#2E7D32")),
)[#text(weight: "bold", fill: rgb("#1B5E20"))[Tip] #parbreak() #body]

#let hdr-fill(accent) = (x, y) => {
  if y == 0 { accent } else if calc.odd(y) { rgb("#FAFAFA") } else { white }
}

#let lvl(label, stars) = [*#label* #h(8pt) #text(fill: rgb("#546E7A"))[#stars]]

#page(numbering: none)[
  #v(2.8cm)
  #align(center)[
    #block(width: 84%)[
      #line(length: 100%, stroke: 2pt + rgb("#1565C0"))
      #v(0.8cm)
      #text(33pt, weight: "bold", fill: rgb("#0D47A1"))[FlowStudio]
      #v(0.15cm)
      #text(19pt, weight: "bold", fill: rgb("#1565C0"))[Zero to Post-Processing]
      #v(0.3cm)
      #text(13pt, fill: rgb("#546E7A"))[Complete step-by-step tutorial with 5 difficulty levels]
      #v(0.8cm)
      #line(length: 100%, stroke: 2pt + rgb("#1565C0"))
    ]
  ]

  #v(1.2cm)
  #align(center)[
    #block(width: 72%, fill: rgb("#F5F5F5"), inset: 16pt, radius: 8pt,
      stroke: 0.5pt + rgb("#E0E0E0"))[
      #table(
        columns: (1fr, 2fr),
        stroke: none,
        align: (right, left),
        row-gutter: 5pt,
        [*Version*], [0.2.0],
        [*Platform*], [FreeCAD 1.0+],
        [*Domains*], [CFD, Structural, Electrostatic, Electromagnetic, Thermal],
        [*Backends*], [OpenFOAM, FluidX3D, Elmer],
        [*Scenarios*], [5 levels: Beginner to Expert],
        [*Date*], [April 2026],
      )
    ]
  ]
]

#page(numbering: none)[
  #v(0.8cm)
  #text(24pt, weight: "bold", fill: rgb("#0D47A1"))[Contents]
  #v(0.6cm)
  #outline(title: none, indent: 1.5em, depth: 3)
]
#counter(page).update(1)

= Introduction and Learning Goals

FlowStudio is a multi-physics workbench for FreeCAD that provides a guided simulation pipeline from geometry to post-processing. This tutorial is built for practical engineering workflows and production-style cases.

#table(
  columns: (auto, auto, 1fr, auto),
  stroke: 0.5pt + rgb("#E0E0E0"),
  fill: hdr-fill(rgb("#E3F2FD")),
  inset: 7pt,
  [*Backend*], [*Type*], [*Best Use*], [*Hardware*],
  [OpenFOAM], [Finite Volume], [Production CFD, broad industrial workflows], [CPU / MPI],
  [FluidX3D], [Lattice Boltzmann], [Fast GPU iteration and design previews], [GPU],
  [Elmer], [Finite Element], [Thermal, EM, structural, multiphysics], [CPU / MPI],
)

== What You Will Learn

- Full setup flow from analysis creation to reporting.
- Solver and turbulence model selection logic.
- Mesh and boundary-layer strategy for stable convergence.
- Post-processing using built-in objects and ParaView script export.
- Five complete scenarios:
  - Level 1: Simple electronics box cooling.
  - Level 2: Multi-component PCB thermal management.
  - Level 3: Wing external aerodynamics.
  - Level 4: Server rack forced cooling.
  - Level 5: CT detector rotating system.

== Prerequisites

#table(
  columns: (auto, 1fr, 1fr),
  stroke: 0.5pt + rgb("#E0E0E0"),
  fill: hdr-fill(rgb("#E3F2FD")),
  inset: 7pt,
  [*Level*], [*You Should Know*], [*You Will Learn Here*],
  [1], [Basic FreeCAD navigation], [Complete first CFD case],
  [2], [Simple 3D modeling], [Thermal interactions between components],
  [3], [Basic fluid dynamics], [External aero setup and force reporting],
  [4], [Reynolds number and turbulence basics], [Large parallel internal-flow setup],
  [5], [Rotating machinery fundamentals], [Transient rotating and multiphysics strategy],
)

= Architecture Overview

FlowStudio follows a layered architecture:

```text
GUI Layer (commands, task panels, visualization)
        ->
Document Objects (analysis, physics, BC, mesh, solver)
        ->
Solver Runners (OpenFOAM, FluidX3D, Elmer)
        ->
External Tools (GMSH, ParaView, solver binaries)
```

Domain support:

- CFD: OpenFOAM, FluidX3D, Elmer
- Structural: Elmer
- Electrostatic: Elmer
- Electromagnetic: Elmer
- Thermal: Elmer

#tip[
Use CFD + Thermal workflow for most electronics-cooling projects first. Add EM coupling only when electromagnetic losses materially affect thermal budget.
]

= Installation and First Launch

== Minimum Setup

#table(
  columns: (auto, auto, 1fr),
  stroke: 0.5pt + rgb("#E0E0E0"),
  fill: hdr-fill(rgb("#E3F2FD")),
  inset: 7pt,
  [*Component*], [*Minimum*], [*Notes*],
  [FreeCAD], [1.0+], [Host application],
  [GMSH], [4.11+], [Meshing],
  [OpenFOAM], [v2312+], [Primary CFD backend],
  [FluidX3D], [2.18+], [GPU backend],
  [Elmer], [9.0+], [Multiphysics],
  [ParaView], [5.11+], [Advanced post-processing],
)

== Dependency Check

Use FlowStudio workflow check or Python console:

```python
from flow_studio.solver_deps import check_all, recommend_parallel_settings

reports = check_all()
for name, report in reports.items():
    print(name, report.available)

print(recommend_parallel_settings())
```

= The 9-Step Simulation Workflow

1. Create Analysis
2. Import or Create Geometry
3. Configure Physics Model
4. Assign Material
5. Define Boundary Conditions
6. Generate Mesh
7. Set Initial Conditions
8. Run Solver
9. Post-process Results

#note[
This order is intentionally strict. If you skip step 5 or 6, the solver run will fail pre-flight checks.
]

== Workflow Diagram

```text
[1 Analysis] -> [2 Geometry] -> [3 Physics] -> [4 Material] -> [5 BCs]
                                              -> [6 Mesh] -> [7 IC]
                                              -> [8 Solve] -> [9 Post]
```

= Interface and Core Objects

Typical model tree:

```text
Document
  Geometry
  CFDAnalysis
    PhysicsModel
    FluidMaterial
    InitialConditions
    Solver
    MeshGmsh
      MeshRegion
      BoundaryLayer
    BCInlet
    BCOutlet
    BCWall
    PostPipeline
```

Important object groups:

- Physics: flow regime, turbulence, compressibility, time model.
- Material: density, viscosity, thermal properties.
- BCs: inlet, outlet, wall, symmetry, open boundary.
- Mesh: base size, local refinements, boundary layer.
- Solver: backend, numerics, parallel settings.

= Physics Primer

== Reynolds Number

$ R_e = (U L) / nu $

- Low Re: laminar tendency.
- High Re: turbulent tendency.
- For most practical electronics and aero cases in this tutorial, turbulent modeling is required.

== Core Equations

Continuity: $ nabla dot u = 0 $

Momentum: $ (partial u)/(partial t) + (u dot nabla) u = -(1/rho) nabla p + nu nabla^2 u + g $

Energy: $ (partial T)/(partial t) + u dot nabla T = (k/(rho c_p)) nabla^2 T + Q/(rho c_p) $

== Turbulence Model Guidance

#table(
  columns: (auto, auto, auto, 1fr),
  stroke: 0.5pt + rgb("#E0E0E0"),
  fill: hdr-fill(rgb("#E3F2FD")),
  inset: 7pt,
  [*Model*], [*Cost*], [*Accuracy*], [*Best Use*],
  [k-omega SST], [Medium], [High], [Default general-purpose industrial choice],
  [k-epsilon], [Low], [Medium], [Simple fully turbulent internal flows],
  [Spalart-Allmaras], [Low], [Medium-High], [Aerospace attached flows],
  [LES], [High], [Very High], [Unsteady resolved turbulence],
)

= Meshing Deep-Dive

== Practical Rules

- Start coarse to validate setup and BC logic.
- Refine around walls, inlets/outlets, heat sources, and wakes.
- Use boundary layers for any wall-driven accuracy goal.

== y-plus Targeting

- $ y^+ approx 1 $: wall-resolved (best force/heat transfer fidelity).
- $ y^+ approx 30 $: wall-function workflow (cheaper, common in production).

```python
from flow_studio.utils.mesh_utils import estimate_y_plus_height
h = estimate_y_plus_height(velocity=30.0, length=0.1, nu=1.5e-5, y_plus_target=1.0)
print(h)
```

#warning[
If residuals stall or diverge, check mesh quality first (skewness and non-orthogonality) before changing solver numerics.
]

= Scenario Tutorials

== Level 1 - Simple Box Cooling (Beginner)

#lvl("Difficulty", "*" )

- Physics: steady, turbulent, incompressible, heat transfer.
- Solver: OpenFOAM, typically buoyantSimpleFoam.
- Geometry: enclosure with one heat source.

=== Steps

1. Build enclosure and chip geometry.
2. Create CFD analysis.
3. Set physics: Turbulent, k-omega SST, HeatTransfer ON.
4. Select material preset Air.
5. Set BCs:
   - Inlet velocity (for example 2 m/s).
   - Outlet static pressure 0 Pa.
   - Chip wall fixed heat flux.
   - Other walls adiabatic.
6. Mesh with local refinement near chip and basic boundary layer.
7. Initial conditions near inlet state.
8. Run solver until residual targets are met.
9. Create contour, streamline, and point-probe outputs.

Expected outcome: chip temperature field, airflow pathlines, and stable residual trend.

== Level 2 - Multi-Component PCB Cooling (Intermediate)

#lvl("Difficulty", "* *" )

- Multiple heat sources with different powers.
- Airflow stacking effects and downstream pre-heating.
- Stronger need for local refinement around components.

=== Steps

1. Build enclosure, board, and all component solids.
2. Keep same physics base as Level 1.
3. Assign separate wall heat flux BC for each component.
4. Add mesh refinement on each hot component.
5. Run and compare component peak temperatures.
6. Post-process with cut-plane thermal map and per-chip probes.

Engineering check: identify hottest component and downstream interaction effects.

== Level 3 - Wing External Flow (Intermediate-Advanced)

#lvl("Difficulty", "* * *" )

- External flow setup with wind tunnel domain.
- Lift and drag post-processing.

=== Steps

1. Build/import wing and create fluid domain by boolean subtraction from wind-tunnel volume.
2. Physics: turbulent, incompressible, steady.
3. BCs:
   - Inlet velocity (for example 30 m/s).
   - Outlet static pressure.
   - Wing no-slip wall.
   - Side/top boundaries as open or symmetry depending strategy.
4. Use stronger near-wall mesh control on wing.
5. Target low y-plus for aerodynamic force fidelity.
6. Run solver and evaluate force report.

Key outputs: pressure contours, streamlines, lift/drag trends.

== Level 4 - Server Rack Forced Cooling (Advanced)

#lvl("Difficulty", "* * * *" )

- Large internal-flow case with many heat sources.
- Parallel decomposition and runtime scaling become important.

=== Steps

1. Build rack domain and server blocks with realistic power map.
2. Physics: turbulent + heat transfer + buoyancy.
3. BCs: cold-aisle inlet, hot-aisle outlet, per-server heat loading.
4. Mesh with refinement around server outlets and recirculation zones.
5. Enable parallel execution in solver object.
6. Run and inspect temperature stratification and hot spots.

Guideline: keep at least about 50k cells per MPI rank for practical scaling.

== Level 5 - CT Detector Rotating System (Expert)

#lvl("Difficulty", "* * * * *" )

- Rotating components, transient solver setup, high thermal load.
- Optional multiphysics coupling strategy with Elmer.

=== Concept Focus

MRF-style rotational modeling uses rotating-frame source terms instead of physically moving the mesh, reducing cost for many engineering workflows.

$ v_("tip") = omega r $

$ C_o = (v Delta t) / (Delta x) < 1 $

=== Steps

1. Build gantry, fan zones, and electronics volumes.
2. Set transient CFD physics and rotational BC strategy.
3. Apply thermal loads for tube and electronics.
4. Mesh fan and rotating regions with tighter local size control.
5. Choose stable transient step from Courant target.
6. Run transient and extract temporal metrics.
7. Post-process thermal and flow stability indicators.

Optional extension: coupled Elmer thermal or EM model for deeper design validation.

= Post-Processing Guide

Use Post Pipeline objects to generate:

- Contour plots: velocity, pressure, temperature.
- Streamlines: identify recirculation and bypassing.
- Point probes: monitor thermal safety points.
- Force report: lift/drag or loading surfaces.

For automated reporting, create measurement objects (point/surface/volume) and generate ParaView Python scripts.

= Solver Selection Cheat Sheet

#table(
  columns: (auto, auto, auto, auto),
  stroke: 0.5pt + rgb("#E0E0E0"),
  fill: hdr-fill(rgb("#E3F2FD")),
  inset: 7pt,
  [*Need*], [*Recommended*], [*Mode*], [*Notes*],
  [Steady incompressible CFD], [simpleFoam], [OpenFOAM], [Baseline industrial setup],
  [Transient incompressible CFD], [pimpleFoam], [OpenFOAM], [Robust transient strategy],
  [Buoyant thermal CFD], [buoyantSimpleFoam or buoyantPimpleFoam], [OpenFOAM], [Electronics and HVAC style cases],
  [Fast GPU preview], [FluidX3D], [LBM], [High throughput iteration],
  [Thermal/EM/Structural], [Elmer], [FEM], [Multiphysics workflows],
)

= Troubleshooting

#table(
  columns: (1fr, 1fr, 1fr),
  stroke: 0.5pt + rgb("#E0E0E0"),
  fill: hdr-fill(rgb("#E3F2FD")),
  inset: 7pt,
  [*Symptom*], [*Likely Cause*], [*Action*],
  [Early divergence], [Poor mesh or aggressive numerics], [Improve mesh quality, reduce aggressiveness],
  [Residual plateau], [Under-resolved regions or BC mismatch], [Refine critical regions, verify BC consistency],
  [Unphysical temperature rise], [Missing thermal BC context], [Review wall thermal definitions and source terms],
  [Parallel instability], [Imbalanced decomposition], [Adjust processor count and decomposition strategy],
)

= Appendix A: Core Property Sets

== Physics Model

- FlowRegime: Laminar or Turbulent
- TurbulenceModel: k-epsilon, k-omega, k-omega SST, Spalart-Allmaras, LES variants
- Compressibility: Incompressible, Compressible, Weakly-Compressible
- TimeModel: Steady or Transient
- HeatTransfer, Gravity, Buoyancy toggles

== Core BC Types

- Inlet: velocity, mass flow, volumetric flow, total pressure
- Outlet: static pressure, mass-flow, outflow
- Wall: no-slip, slip, moving translational, moving rotational, rough
- Thermal wall modes: adiabatic, fixed temperature, fixed heat flux, HTC
- Symmetry and Open Boundary for domain simplification and far-field handling

== Mesh and Boundary Layer

- CharacteristicLength, MinElementSize, MaxElementSize
- Local refinement regions: surface/box/sphere/cylinder
- Boundary layer: number of layers, first layer height, expansion ratio, target y-plus

= Appendix B: Suggested Validation Loop

1. Run coarse mesh baseline.
2. Refine targeted regions and repeat.
3. Compare key outputs (for example delta T, pressure drop, forces).
4. Stop when output change is within project tolerance (commonly 1-3%).

#tip[
Treat validation as a formal stage, not an optional cleanup step. It is the fastest way to avoid false confidence in visually good but numerically weak results.
]

= Closing Notes

This Typst edition is the production-ready tutorial format for FlowStudio training and internal simulation handoff. Use it as the canonical baseline, then clone and adapt per domain team (electronics, aero, thermal, rotating machinery).
