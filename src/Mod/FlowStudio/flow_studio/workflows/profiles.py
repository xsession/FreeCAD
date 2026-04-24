# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Domain-aware workflow profiles for FlowStudio guided studies."""

from dataclasses import dataclass


@dataclass(frozen=True)
class WorkflowStepProfile:
    number: int
    status_key: str
    name: str
    description: str
    command_name: str
    hint: str


@dataclass(frozen=True)
class WorkflowProfile:
    domain_key: str
    label: str
    workspace_name: str
    description: str
    workflows: tuple[str, ...]
    steps: tuple[WorkflowStepProfile, ...]


def _base_steps() -> tuple[WorkflowStepProfile, ...]:
    return (
        WorkflowStepProfile(1, "analysis", "Create Analysis", "Create the study container and its default child objects.", "FlowStudio_Analysis", "Use FlowStudio → New Analysis to start the study."),
        WorkflowStepProfile(2, "geometry", "Import / Create Geometry", "Bring CAD bodies into the document and keep the model recompute-ready.", "FlowStudio_ImportStep", "Import or create the bodies that define the study geometry."),
        WorkflowStepProfile(3, "physics", "Configure Physics Model", "Choose the governing equations, time behavior, and solver-facing physics settings.", "FlowStudio_PhysicsModel", "Double-click the physics model to configure the study."),
        WorkflowStepProfile(4, "materials", "Assign Material Properties", "Attach the relevant material model to each participating body or region.", "FlowStudio_FluidMaterial", "Assign at least one material to the participating regions."),
        WorkflowStepProfile(5, "boundaries", "Define Boundary Conditions", "Add the sources, loads, ports, boundaries, or contacts that drive the study.", "FlowStudio_BC_Inlet", "Create the boundary and excitation objects needed by this study."),
        WorkflowStepProfile(6, "mesh", "Prepare Discretization", "Generate the mesh or study discretization used by the solver backends.", "FlowStudio_MeshGmsh", "Generate and review the mesh or discretized model before solving."),
        WorkflowStepProfile(7, "study_controls", "Review Study Controls", "Check solver controls, initial values, and result requests before execution.", "FlowStudio_InitialConditions", "Review the solver and study-control objects before launch."),
        WorkflowStepProfile(8, "run", "Run Solver", "Write the prepared case and execute the selected backend.", "FlowStudio_RunSolver", "Run the prepared case after all prerequisites are green."),
        WorkflowStepProfile(9, "results", "Post-process Results", "Inspect fields, plots, detector outputs, or reports from the completed run.", "FlowStudio_PostPipeline", "Create plots, probes, or post pipelines to review the results."),
    )


def _with_overrides(base_steps, overrides):
    updated = []
    for step in base_steps:
        override = overrides.get(step.number)
        if override:
            updated.append(WorkflowStepProfile(
                number=step.number,
                status_key=override.get("status_key", step.status_key),
                name=override.get("name", step.name),
                description=override.get("description", step.description),
                command_name=override.get("command_name", step.command_name),
                hint=override.get("hint", step.hint),
            ))
        else:
            updated.append(step)
    return tuple(updated)


def apply_workflow_profile_overrides(
    profile: WorkflowProfile,
    *,
    label: str | None = None,
    description: str | None = None,
    workflows: tuple[str, ...] | None = None,
    step_overrides: dict[int, dict] | None = None,
) -> WorkflowProfile:
    """Return one workflow profile with optional display and step overrides."""
    return WorkflowProfile(
        domain_key=profile.domain_key,
        label=label or profile.label,
        workspace_name=profile.workspace_name,
        description=description or profile.description,
        workflows=workflows or profile.workflows,
        steps=_with_overrides(profile.steps, step_overrides or {}),
    )


_BASE_STEPS = _base_steps()

_PROFILES = {
    "CFD": WorkflowProfile(
        domain_key="CFD",
        label="CFD / Flow",
        workspace_name="CFD Project Cockpit",
        description="Geometry-to-mesh-to-run workflow for internal flow, external aerodynamics, and electronics-cooling CHT studies.",
        workflows=("Internal flow", "External aerodynamics", "Electronics cooling"),
        steps=_with_overrides(_BASE_STEPS, {
            5: {"name": "Define Boundary Conditions", "hint": "Add inlet, outlet, wall, symmetry, open, fan, or thermal boundaries for the active CFD study."},
            7: {"name": "Set Initial Conditions", "description": "Configure initial field values and solver controls to improve convergence.", "hint": "Review the InitialConditions object and any CHT or radiation control settings before running."},
        }),
    ),
    "Thermal": WorkflowProfile(
        domain_key="Thermal",
        label="Thermal",
        workspace_name="Thermal Study Layout",
        description="Heat-transfer workflow focused on material, thermal loads, and reports.",
        workflows=("Conduction", "Convection", "Radiation"),
        steps=_with_overrides(_BASE_STEPS, {
            5: {"name": "Define Thermal Loads and Boundaries", "hint": "Add temperature, heat flux, convection, or radiation boundaries."},
            7: {"name": "Review Initial Temperatures", "description": "Check starting temperatures and thermal control settings.", "hint": "Review initial temperatures and solver control values."},
        }),
    ),
    "Structural": WorkflowProfile(
        domain_key="Structural",
        label="Structural",
        workspace_name="Structural Analysis Layout",
        description="Constraint-driven workflow for stress, load, and deformation studies.",
        workflows=("Static structural", "Loaded assembly", "Thermo-mechanical prep"),
        steps=_with_overrides(_BASE_STEPS, {
            5: {"name": "Define Loads and Constraints", "hint": "Add fixtures, forces, pressures, or displacement constraints."},
            7: {"name": "Review Load Case Controls", "description": "Confirm solver controls and load-case assumptions before execution.", "hint": "Review the solver settings and structural assumptions before running."},
        }),
    ),
    "Electrostatic": WorkflowProfile(
        domain_key="Electrostatic",
        label="Electrostatic",
        workspace_name="Electrostatic Layout",
        description="Dielectric and potential setup workflow for field studies.",
        workflows=("Potential maps", "Capacitance", "Insulation studies"),
        steps=_with_overrides(_BASE_STEPS, {
            5: {"name": "Define Potentials and Charges", "hint": "Add potentials, charges, and grounded regions."},
            7: {"name": "Review Solver Controls", "description": "Check electrostatic solver controls and result requests.", "hint": "Review the electrostatic solver object before execution."},
        }),
    ),
    "Electromagnetic": WorkflowProfile(
        domain_key="Electromagnetic",
        label="Electromagnetic",
        workspace_name="EM Project Layout",
        description="Source, material, and field-monitor workflow for electromagnetic studies.",
        workflows=("Magnetostatics", "Low-frequency EM", "Device studies"),
        steps=_with_overrides(_BASE_STEPS, {
            5: {"name": "Define Excitations and Boundaries", "hint": "Add current, magnetic, or far-field boundary objects."},
            7: {"name": "Review Frequency and Solver Controls", "description": "Check frequency-domain and output control settings.", "hint": "Confirm solver, frequency, and requested outputs."},
        }),
    ),
    "Optical": WorkflowProfile(
        domain_key="Optical",
        label="Optical / Photonics",
        workspace_name="Optical Lab Layout",
        description="CST-inspired optical workflow for components, sources, detectors, particle transport scaffolds, and post-processing.",
        workflows=("Non-sequential ray trace", "Illumination", "Wave optics", "Radiation transport"),
        steps=_with_overrides(_BASE_STEPS, {
            3: {"name": "Configure Optical Model", "description": "Choose sequential, non-sequential, illumination, or wave-optics study mode.", "command_name": "FlowStudio_OpticalPhysics", "hint": "Choose the optical model and wavelength settings."},
            4: {"name": "Assign Optical Materials", "description": "Assign glasses, polymers, mirrors, coatings, or absorbers to optical parts.", "command_name": "FlowStudio_OpticalMaterial", "hint": "Assign material presets or custom optical constants."},
            5: {"name": "Define Sources, Detectors, and Boundaries", "description": "Place optical or Geant4 sources, detector planes, scoring objects, and boundaries on the selected geometry.", "command_name": "FlowStudio_BC_OpticalSource", "hint": "Add at least one optical or Geant4 source/detector and the needed boundaries or scoring objects."},
            6: {"name": "Prepare Mesh or Sampling", "description": "Prepare geometry sampling or mesh resolution for ray or wave-optics backends.", "hint": "Prepare discretization suitable for the chosen optical backend."},
            7: {"status_key": "optical_controls", "name": "Review Study Controls", "description": "Check ray count, wavelength span, Geant4 event counts, PML, and requested outputs.", "command_name": "FlowStudio_OpticalPhysics", "hint": "Review optical physics and solver controls before launch."},
            9: {"name": "Inspect Detector and Field Results", "description": "Review detector planes, irradiance, spot diagrams, or optical path results.", "hint": "Create post-processing objects and inspect detector outputs."},
        }),
    ),
}


def get_workflow_profile(domain_key: str | None = None) -> WorkflowProfile:
    """Return the workflow profile for one FlowStudio domain."""
    if not domain_key:
        domain_key = "CFD"
    return _PROFILES.get(domain_key, _PROFILES["CFD"])
