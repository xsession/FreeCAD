# FlowStudio Solver Repositories

This note records the canonical upstream solver repositories vendored under `src/Mod/FlowStudio/solver_repos`.

These submodules are reference source trees for adapter development, case-export validation, and reproducible backend integration work. They are not linked directly into the FreeCAD build by default.

## Core CFD and Multiphysics

- `openfoam` -> `https://github.com/OpenFOAM/OpenFOAM-dev.git`
- `elmerfem` -> `https://github.com/ElmerCSC/elmerfem.git`

These are the commercially necessary first-class backends for FlowStudio v1.

## Experimental CFD

- `fluidx3d` -> `https://github.com/ProjectPhysX/FluidX3D.git`

This backend remains isolated behind an experimental adapter boundary.

## Optical and Photonics

- `raysect` -> `https://github.com/raysect/source.git`
- `meep` -> `https://github.com/NanoComp/meep.git`
- `openems` -> `https://github.com/thliebig/openEMS.git`
- `optiland` -> `https://github.com/HarrisonKramer/optiland.git`

These repositories cover the initial optical backend set described in `OPTICAL_SOLVER_DEEPSEARCH.md`:

- Raysect for CAD-adjacent non-sequential ray tracing and illumination.
- Meep for wave optics, FDTD, and photonics.
- openEMS for full-wave electromagnetic and overlapping photonics cases.
- Optiland for lens-system design and differentiable optical workflows.

## Radiation and Particle Transport

- `geant4` -> `https://github.com/Geant4/geant4.git`

Geant4 is the canonical radiation transport and particle-scoring backend for FlowStudio's particle and detector workflow.

## Operating Notes

- The source of truth for submodule registration is the top-level `.gitmodules` file.
- Backend adapters should treat these repositories as upstream references, not as an excuse to hard-wire solver-specific assumptions into the frontend model.
- Some upstream repositories, notably OpenFOAM on Windows, can report local checkout noise because of filesystem and case-sensitivity differences even when the recorded submodule gitlink is correct.