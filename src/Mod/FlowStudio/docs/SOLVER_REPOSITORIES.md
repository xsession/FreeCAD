# FlowStudio Solver Repositories

This note records the canonical upstream solver repositories vendored under `src/Mod/FlowStudio/solver_repos`.

These submodules are reference source trees for adapter development, case-export validation, and reproducible backend integration work.

They are still not compiled by the top-level FreeCAD build by default, but FlowStudio now treats their common build/install output directories as first-class executable artifact roots during local dependency checks and simulation launch.

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
- FlowStudio executable resolution now prefers, in order:
	- explicit absolute executable paths stored on solver objects
	- normal `PATH` resolution
	- directories listed in `FLOWSTUDIO_SOLVER_ARTIFACTS`
	- common build/install output folders under `src/Mod/FlowStudio/solver_repos/<backend>`
- This means local simulations can use solver binaries built from the vendored repositories without copying them into the system `PATH`, as long as they land in a supported artifact directory or `FLOWSTUDIO_SOLVER_ARTIFACTS` points at the build root.
- Windows build entry points are now exposed through `build.bat` and the matching VS Code tasks:
	- `build.bat solver-fluidx3d` builds the vendored FluidX3D Visual Studio solution
	- `build.bat solver-elmer` configures, builds, and installs the vendored ElmerFEM tree with CMake + Ninja + MinGW toolchains
	  - the current Windows path expects OpenBLAS/LAPACK to be installed for the MinGW toolchain, or `BLAS_LIBRARIES` and `LAPACK_LIBRARIES` to be preseeded for CMake
	- `build.bat solver-openfoam` dispatches the vendored OpenFOAM `Allwmake` flow through WSL
	  - because upstream startup scripts require a canonical `OpenFOAM-dev` layout, the wrapper stages the repo into a temporary WSL work tree, normalizes shell scripts to LF there, runs `Allwmake`, and syncs the resulting `platforms/` artifacts back into the vendored checkout
	  - the current WSL path also expects a Linux build toolchain including `bash`, `gcc`, `g++`, `make`, `flex`, and `rsync`
	- `build.bat solvers` runs the primary vendored solver builds in sequence
- Backend adapters should treat these repositories as upstream references, not as an excuse to hard-wire solver-specific assumptions into the frontend model.
- Some upstream repositories, notably OpenFOAM on Windows, can report local checkout noise because of filesystem and case-sensitivity differences even when the recorded submodule gitlink is correct.