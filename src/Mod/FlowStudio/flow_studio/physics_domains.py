# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Physics domain definitions – CST-inspired multi-physics domain system.

Each domain defines a physics type (CFD, FEM, Electrostatic, etc.) and
the set of objects, boundary conditions, and solver backends available
for that domain.  Commands and UI elements query this registry to show
domain-appropriate options.

Inspired by CST Studio Suite's multi-solver, domain-driven architecture.
"""


class PhysicsDomain:
    """Descriptor for one physics discipline."""

    __slots__ = (
        "key", "label", "description", "icon",
        "analysis_types", "bc_types", "solver_backends",
        "material_type", "physics_model_type", "example_commands",
    )

    def __init__(
        self,
        key,
        label,
        description="",
        icon="",
        analysis_types=None,
        bc_types=None,
        solver_backends=None,
        material_type=None,
        physics_model_type=None,
        example_commands=None,
    ):
        self.key = key
        self.label = label
        self.description = description
        self.icon = icon
        self.analysis_types = analysis_types or []
        self.bc_types = bc_types or []
        self.solver_backends = solver_backends or []
        self.material_type = material_type
        self.physics_model_type = physics_model_type
        self.example_commands = example_commands or []


# ======================================================================
# Domain registry
# ======================================================================
_DOMAINS = {}


def register_domain(domain):
    """Register a physics domain."""
    _DOMAINS[domain.key] = domain


def get_domain(key):
    """Return a PhysicsDomain by key, or None."""
    return _DOMAINS.get(key)


def available_domains():
    """Return list of registered domain keys."""
    return list(_DOMAINS.keys())


def all_domains():
    """Return all registered PhysicsDomain objects."""
    return list(_DOMAINS.values())


def example_commands_for_domain(key):
    """Return the starter example commands registered for one domain key."""
    domain = get_domain(key)
    if domain is None:
        return []
    return list(domain.example_commands)


def all_example_commands():
    """Return all registered starter example commands in domain order."""
    commands = []
    seen = set()
    for domain in all_domains():
        for command in domain.example_commands:
            if command in seen:
                continue
            seen.add(command)
            commands.append(command)
    return commands


def example_command_groups():
    """Return grouped starter example commands by domain in registry order."""
    groups = []
    for domain in all_domains():
        if not domain.example_commands:
            continue
        groups.append((domain.key, domain.label, tuple(domain.example_commands)))
    return tuple(groups)


# ======================================================================
# Built-in domain definitions
# ======================================================================

CFD = PhysicsDomain(
    key="CFD",
    label="CFD (Fluid Dynamics)",
    description="Computational Fluid Dynamics – incompressible/compressible "
                "flow, turbulence, heat transfer, multiphase.",
    icon="FlowStudioAnalysis.svg",
    analysis_types=[
        "Internal Flow",
        "External Flow",
        "Free Surface",
        "Heat Transfer",
        "Conjugate Heat Transfer",
    ],
    bc_types=[
        "FlowStudio::BCWall",
        "FlowStudio::BCInlet",
        "FlowStudio::BCOutlet",
        "FlowStudio::BCOpenBoundary",
        "FlowStudio::BCSymmetry",
    ],
    solver_backends=["OpenFOAM", "FluidX3D", "Elmer"],
    material_type="FlowStudio::FluidMaterial",
    physics_model_type="FlowStudio::PhysicsModel",
    example_commands=[
        "FlowStudio_ElectronicsCoolingStudy",
        "FlowStudio_ExternalAeroStudy",
        "FlowStudio_PipeFlowStudy",
        "FlowStudio_StaticMixerStudy",
    ],
)

STRUCTURAL = PhysicsDomain(
    key="Structural",
    label="Structural Mechanics (FEM)",
    description="Linear/nonlinear elasticity, stress analysis, modal analysis, "
                "buckling – using Elmer ElasticSolve.",
    icon="FlowStudioStructural.svg",
    analysis_types=[
        "Static Linear Elastic",
        "Static Nonlinear",
        "Modal Analysis",
        "Transient Dynamic",
    ],
    bc_types=[
        "FlowStudio::BCFixedDisplacement",
        "FlowStudio::BCForce",
        "FlowStudio::BCPressureLoad",
        "FlowStudio::BCSymmetry",
    ],
    solver_backends=["Elmer"],
    material_type="FlowStudio::SolidMaterial",
    physics_model_type="FlowStudio::StructuralPhysicsModel",
    example_commands=["FlowStudio_StructuralBracketExample"],
)

ELECTROSTATIC = PhysicsDomain(
    key="Electrostatic",
    label="Electrostatic",
    description="Static electric field and potential analysis – "
                "capacitance, electric force, charge distribution. "
                "Uses Elmer StatElecSolve.",
    icon="FlowStudioElectrostatic.svg",
    analysis_types=[
        "Electrostatic Potential",
        "Capacitance Matrix",
    ],
    bc_types=[
        "FlowStudio::BCElectricPotential",
        "FlowStudio::BCSurfaceCharge",
        "FlowStudio::BCElectricSymmetry",
    ],
    solver_backends=["Elmer"],
    material_type="FlowStudio::ElectrostaticMaterial",
    physics_model_type="FlowStudio::ElectrostaticPhysicsModel",
    example_commands=["FlowStudio_ElectrostaticCapacitorExample"],
)

ELECTROMAGNETIC = PhysicsDomain(
    key="Electromagnetic",
    label="Electromagnetic",
    description="Static and time-harmonic magnetic field analysis – "
                "inductors, transformers, eddy currents. "
                "Uses Elmer MagnetoDynamics / WhitneyAV solvers.",
    icon="FlowStudioElectromagnetic.svg",
    analysis_types=[
        "Magnetostatic",
        "Magnetodynamic Harmonic",
        "Magnetodynamic Transient",
    ],
    bc_types=[
        "FlowStudio::BCMagneticPotential",
        "FlowStudio::BCCurrentDensity",
        "FlowStudio::BCMagneticFluxDensity",
        "FlowStudio::BCMagneticSymmetry",
    ],
    solver_backends=["Elmer"],
    material_type="FlowStudio::ElectromagneticMaterial",
    physics_model_type="FlowStudio::ElectromagneticPhysicsModel",
    example_commands=["FlowStudio_ElectromagneticCoilExample"],
)

THERMAL = PhysicsDomain(
    key="Thermal",
    label="Thermal (Heat Transfer)",
    description="Steady-state and transient heat conduction/convection – "
                "temperature distribution, thermal stress coupling. "
                "Uses Elmer HeatSolve.",
    icon="FlowStudioThermal.svg",
    analysis_types=[
        "Steady-State Heat Transfer",
        "Transient Heat Transfer",
    ],
    bc_types=[
        "FlowStudio::BCTemperature",
        "FlowStudio::BCHeatFlux",
        "FlowStudio::BCConvection",
        "FlowStudio::BCRadiation",
    ],
    solver_backends=["Elmer"],
    material_type="FlowStudio::ThermalMaterial",
    physics_model_type="FlowStudio::ThermalPhysicsModel",
    example_commands=["FlowStudio_ThermalPlateExample"],
)

OPTICAL = PhysicsDomain(
    key="Optical",
    label="Optical / Photonics",
    description="Geometrical optics, illumination, lens/source/detector setup, "
                "wave-optics photonics, and radiation transport scaffolding through "
                "open-source backends.",
    icon="FlowStudioElectromagnetic.svg",
    analysis_types=[
        "Sequential Ray Trace",
        "Non-Sequential Ray Trace",
        "Illumination",
        "Wave Optics FDTD",
        "Photonic Crystal",
    ],
    bc_types=[
        "FlowStudio::BCOpticalSource",
        "FlowStudio::BCOpticalDetector",
        "FlowStudio::BCOpticalBoundary",
        "FlowStudio::BCGeant4Source",
        "FlowStudio::BCGeant4Detector",
        "FlowStudio::BCGeant4Scoring",
    ],
    solver_backends=["Raysect", "Meep", "openEMS", "Optiland", "Geant4"],
    material_type="FlowStudio::OpticalMaterial",
    physics_model_type="FlowStudio::OpticalPhysicsModel",
    example_commands=["FlowStudio_OpticalLensExample"],
)


# Register all built-in domains
for _dom in (CFD, STRUCTURAL, ELECTROSTATIC, ELECTROMAGNETIC, THERMAL, OPTICAL):
    register_domain(_dom)
