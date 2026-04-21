# FlowStudio Optical Solver Deep Search

This note captures the initial open-source solver targets for FlowStudio optical simulation.

## Recommended Integration Order

1. **Raysect** - best first target for CAD-adjacent geometric optics. It is an open-source Python framework for physically realistic geometrical optical simulations with scene graphs, lenses, meshes, CSG, observers, and material models.
2. **Meep** - best first wave-optics / photonics target. It is GPL open-source FDTD software with Python, Scheme, and C++ APIs, support for 1D/2D/3D/cylindrical coordinates, MPI, PML, anisotropic/dispersive/nonlinear materials, and optimization workflows.
3. **openEMS** - strong full-wave FDTD target for RF/microwave/EM and some photonics-style problems. It has C++ engine, Python/Matlab/Octave interfaces, and CSXCAD geometry handling.
4. **Optiland** - promising Python optical design platform for lens systems, optimization, tolerancing, and differentiable ray tracing.
5. **Astree / OpenRayTrace / OpenRT** - useful references or optional exporters for classic optical design/ray tracing, but less attractive as the first robust FreeCAD backend than Raysect or Meep.

## FlowStudio Backend Strategy

The first backend should write a neutral `optical_case.json` manifest containing geometry references, optical materials, sources, detectors, boundaries, and physics settings. Solver-specific launchers can then translate that manifest into Raysect scenes, Meep scripts, or openEMS CSXCAD/Python cases without forcing the frontend to know solver-specific details.

## Frontend Scope

The initial frontend should expose:

- Optical analysis container
- Optical physics model
- Optical material assignment with glass/coating presets
- Optical source assignment
- Optical detector assignment
- Optical boundary/coating assignment

## Notes

Raysect is the best user-workflow match for non-sequential ray tracing and illumination-style CAD simulation. Meep is the best open-source choice for wave optics, photonic crystals, and nanophotonics. openEMS overlaps with the existing electromagnetic domain and should remain available for full-wave use cases.

