# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Machine-readable coverage catalog for public SimFlow tutorial examples."""

from dataclasses import dataclass


@dataclass(frozen=True)
class TutorialCoverageEntry:
    key: str
    title: str
    url: str
    family: str
    phase: str
    domain_key: str
    analysis_pattern: str
    current_posture: str
    capabilities: tuple[str, ...] = ()


_TUTORIAL_COVERAGE = (
    TutorialCoverageEntry("pipe-flow", "Internal Pipe Flow", "https://help.sim-flow.com/tutorials/pipe-flow", "Foundation CFD", "Phase 0", "CFD", "steady incompressible internal flow", "family-scaffold-implemented", ("study-recipe", "internal-flow", "basic-bcs", "slices", "streamlines")),
    TutorialCoverageEntry("wing", "Wing", "https://help.sim-flow.com/tutorials/wing", "Foundation CFD", "Phase 0", "CFD", "steady external aerodynamics", "family-scaffold-implemented", ("study-recipe", "external-flow", "force-monitors", "streamlines")),
    TutorialCoverageEntry("car", "Car", "https://help.sim-flow.com/tutorials/car", "Foundation CFD", "Phase 0", "CFD", "steady external aerodynamics with moving ground", "family-scaffold-implemented", ("study-recipe", "external-flow", "moving-ground", "force-monitors")),
    TutorialCoverageEntry("buildings", "Wind around Buildings", "https://help.sim-flow.com/tutorials/buildings", "Foundation CFD", "Phase 0", "CFD", "steady atmospheric external flow", "partial-capability", ("external-flow", "atmospheric-inlet", "clip-postprocessing")),
    TutorialCoverageEntry("airfoil-naca-0012", "Airfoil (NACA 0012)", "https://help.sim-flow.com/tutorials/airfoil-naca-0012", "Foundation CFD", "Phase 0", "CFD", "2D airfoil external flow", "partial-capability", ("airfoil-helper", "force-coefficients", "angle-of-attack")),
    TutorialCoverageEntry("static-mixer", "Static Mixer", "https://help.sim-flow.com/tutorials/static-mixer", "Foundation CFD", "Phase 0", "CFD", "transient single-phase flow with passive scalar", "family-scaffold-implemented", ("study-recipe", "passive-scalar", "internal-flow", "boundary-extraction")),
    TutorialCoverageEntry("tesla-valve", "Tesla Valve", "https://help.sim-flow.com/tutorials/tesla-valve", "Foundation CFD", "Phase 0", "CFD", "steady internal flow with periodic interface", "partial-capability", ("periodic-interface", "2d-plate", "pressure-jump")),
    TutorialCoverageEntry("von-karman-vortex-street", "Von Karman Vortex Street", "https://help.sim-flow.com/tutorials/von-karman-vortex-street", "Foundation CFD", "Phase 0", "CFD", "transient 2D validation case", "partial-capability", ("validation-case", "forces", "parameterized-geometry")),
    TutorialCoverageEntry("electronics-cooling", "Electronics Cooling", "https://help.sim-flow.com/tutorials/electronics-cooling", "Thermal / CHT", "Phase 1", "CFD", "steady conjugate heat transfer with radiation comparison", "pilot-scaffold-implemented", ("study-recipe", "cht", "fan", "volume-source", "radiation")),
    TutorialCoverageEntry("cooling-channel", "Cooling Channel", "https://help.sim-flow.com/tutorials/cooling-channel", "Thermal / CHT", "Phase 1", "CFD", "steady conjugate heat transfer multi-zone flow", "partial-capability", ("cht", "multi-region", "thermal-bcs")),
    TutorialCoverageEntry("heat-exchanger", "Heat Exchanger", "https://help.sim-flow.com/tutorials/heat-exchanger", "Thermal / CHT", "Phase 1", "CFD", "steady conjugate heat transfer with thermal resistance", "partial-capability", ("cht", "thermal-resistance", "multi-region")),
    TutorialCoverageEntry("cylinder-cooling", "Cylinder Cooling", "https://help.sim-flow.com/tutorials/cylinder-cooling", "Thermal / CHT", "Phase 1", "CFD", "transient conjugate heat transfer", "partial-capability", ("transient-cht", "2d-plate", "region-interface")),
    TutorialCoverageEntry("catalytic-converter", "Catalytic Converter", "https://help.sim-flow.com/tutorials/catalytic-converter", "Advanced Internal / Environmental", "Phase 2", "CFD", "porous internal flow", "partial-capability", ("porous-region", "formula-bc", "potential-init")),
    TutorialCoverageEntry("clean-room", "Clean Room Ventilation", "https://help.sim-flow.com/tutorials/clean-room", "Advanced Internal / Environmental", "Phase 2", "CFD", "steady HVAC with porous media and residence-time scalar", "partial-capability", ("porous-baffle", "passive-scalar", "cyclic-interface")),
    TutorialCoverageEntry("garage-ventilation", "Garage Ventilation", "https://help.sim-flow.com/tutorials/garage-ventilation", "Advanced Internal / Environmental", "Phase 2", "CFD", "transient buoyant ventilation with fan and fire source", "partial-capability", ("buoyancy", "fan", "source-term", "scalar-smoke")),
    TutorialCoverageEntry("blood-flow", "Blood Flow", "https://help.sim-flow.com/tutorials/blood-flow", "Advanced Internal / Environmental", "Phase 2", "CFD", "transient non-Newtonian internal flow", "backend-gap", ("bird-carreau", "time-profile-inlet", "wall-shear-stress")),
    TutorialCoverageEntry("droplet", "Droplet", "https://help.sim-flow.com/tutorials/droplet", "Free-Surface / Multiphase", "Phase 3", "CFD", "2D VOF droplet and water pool", "partial-capability", ("vof", "phase-patching", "2d-plate")),
    TutorialCoverageEntry("dam-break", "Dam Break", "https://help.sim-flow.com/tutorials/dam-break", "Free-Surface / Multiphase", "Phase 3", "CFD", "transient two-phase free-surface flow", "partial-capability", ("vof", "phase-patching", "slice-monitor")),
    TutorialCoverageEntry("turbidity-current", "Turbidity Current", "https://help.sim-flow.com/tutorials/turbidity-current", "Free-Surface / Multiphase", "Phase 3", "CFD", "three-phase immiscible free-surface flow", "major-backend-gap", ("three-phase", "vof", "validation-measurements")),
    TutorialCoverageEntry("injection-molding", "Injection Molding", "https://help.sim-flow.com/tutorials/injection-molding", "Free-Surface / Multiphase", "Phase 3", "CFD", "non-Newtonian mold filling with free surface", "major-backend-gap", ("non-newtonian", "vof", "patch-init")),
    TutorialCoverageEntry("propeller", "Marine Propeller", "https://help.sim-flow.com/tutorials/propeller", "Rotating / Moving Mesh", "Phase 4", "CFD", "steady rotating machinery with MRF and periodicity", "partial-capability", ("mrf", "periodic-interface", "q-criterion")),
    TutorialCoverageEntry("mixing-tank", "Mixing Tank", "https://help.sim-flow.com/tutorials/mixing-tank", "Rotating / Moving Mesh", "Phase 4", "CFD", "dynamic mesh rotating zone with free surface", "major-backend-gap", ("dynamic-mesh", "arbitrary-interface", "vof")),
    TutorialCoverageEntry("ship-hull", "Ship Hull", "https://help.sim-flow.com/tutorials/ship-hull", "Rotating / Moving Mesh", "Phase 4", "CFD", "free-surface flow with dynamic mesh and 6DoF", "major-backend-gap", ("dynamic-mesh", "6dof", "free-surface")),
    TutorialCoverageEntry("sloshing-tank", "Sloshing Tank", "https://help.sim-flow.com/tutorials/sloshing-tank", "Rotating / Moving Mesh", "Phase 4", "CFD", "rigid body motion with free surface and baffles", "major-backend-gap", ("rigid-motion", "vof", "comparison-runs")),
    TutorialCoverageEntry("gas-pollutant-dispersion", "Gas & Pollutant Dispersion", "https://help.sim-flow.com/tutorials/gas-pollutant-dispersion", "Reacting / Particle / Compressible", "Phase 5", "CFD", "transient species transport with particles", "major-backend-gap", ("species-transport", "lagrangian-particles", "thermal-particles")),
    TutorialCoverageEntry("cyclone-separator", "Cyclone Separator", "https://help.sim-flow.com/tutorials/cyclone-separator", "Reacting / Particle / Compressible", "Phase 5", "CFD", "MPPIC particle separation", "major-backend-gap", ("mppic", "les", "particle-injection")),
    TutorialCoverageEntry("spray-combustion", "Spray Combustion", "https://help.sim-flow.com/tutorials/spray-combustion", "Reacting / Particle / Compressible", "Phase 5", "CFD", "spray combustion with Lagrangian droplets", "major-backend-gap", ("combustion", "spray", "chemkin-import")),
    TutorialCoverageEntry("oblique-shock", "Oblique Shock", "https://help.sim-flow.com/tutorials/oblique-shock", "Reacting / Particle / Compressible", "Phase 5", "CFD", "density-based supersonic compressible flow", "major-backend-gap", ("compressible", "shock-capturing", "mach-post")),
)


def all_tutorial_coverage() -> tuple[TutorialCoverageEntry, ...]:
    """Return the complete tutorial coverage catalog."""
    return _TUTORIAL_COVERAGE


def get_tutorial_coverage(key: str | None) -> TutorialCoverageEntry | None:
    """Return one tutorial entry by its stable slug-like key."""
    if not key:
        return None
    for entry in _TUTORIAL_COVERAGE:
        if entry.key == key:
            return entry
    return None


def tutorial_coverage_by_phase(phase: str | None) -> tuple[TutorialCoverageEntry, ...]:
    """Return all tutorial entries assigned to one roadmap phase."""
    if not phase:
        return ()
    return tuple(entry for entry in _TUTORIAL_COVERAGE if entry.phase == phase)


def tutorial_coverage_by_family(family: str | None) -> tuple[TutorialCoverageEntry, ...]:
    """Return all tutorial entries grouped under one capability family."""
    if not family:
        return ()
    return tuple(entry for entry in _TUTORIAL_COVERAGE if entry.family == family)