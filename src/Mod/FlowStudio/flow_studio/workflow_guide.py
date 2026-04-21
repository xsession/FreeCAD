# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Workflow Guide – enforces domain-aware simulation workflows.

Modelled after CfdOF's approach: each simulation must follow a defined
sequence of steps.  This module provides:
  - ``get_workflow_status()`` – returns the completion state of each step
  - Helper predicates used by command ``IsActive()`` guards
  - ``WorkflowChecker`` – pre-run validation akin to CfdOF's dirty-flag checks

The status engine stays generic, while step names, hints, and workspace focus
come from domain profiles. This keeps workflow guidance aligned with the active
physics domain without cloning the validation logic per workbench area.
"""

try:
    import FreeCAD
except Exception:  # pragma: no cover - keeps pure-Python imports working
    class _FreeCADStub:
        ActiveDocument = None

    FreeCAD = _FreeCADStub()

from flow_studio.ui.layouts import get_workspace_layout
from flow_studio.workflows.profiles import get_workflow_profile

# FlowType strings used to identify objects inside analysis groups
_PHYSICS_TYPES = {
    "FlowStudio::PhysicsModel",
    "FlowStudio::StructuralPhysicsModel",
    "FlowStudio::ElectrostaticPhysicsModel",
    "FlowStudio::ElectromagneticPhysicsModel",
    "FlowStudio::ThermalPhysicsModel",
    "FlowStudio::OpticalPhysicsModel",
}

_MATERIAL_TYPES = {
    "FlowStudio::FluidMaterial",
    "FlowStudio::SolidMaterial",
    "FlowStudio::ElectrostaticMaterial",
    "FlowStudio::ElectromagneticMaterial",
    "FlowStudio::ThermalMaterial",
    "FlowStudio::OpticalMaterial",
}

_BC_TYPES = {
    "FlowStudio::BCWall",
    "FlowStudio::BCInlet",
    "FlowStudio::BCOutlet",
    "FlowStudio::BCOpenBoundary",
    "FlowStudio::BCSymmetry",
    "FlowStudio::BCFixedDisplacement",
    "FlowStudio::BCForce",
    "FlowStudio::BCPressureLoad",
    "FlowStudio::BCElectricPotential",
    "FlowStudio::BCSurfaceCharge",
    "FlowStudio::BCMagneticPotential",
    "FlowStudio::BCCurrentDensity",
    "FlowStudio::BCTemperature",
    "FlowStudio::BCHeatFlux",
    "FlowStudio::BCConvection",
    "FlowStudio::BCRadiation",
    "FlowStudio::BCOpticalSource",
    "FlowStudio::BCOpticalDetector",
    "FlowStudio::BCOpticalBoundary",
}

_MESH_TYPES = {
    "FlowStudio::MeshGmsh",
}

_SOLVER_TYPES = {
    "FlowStudio::Solver",
}

_INITIAL_COND_TYPES = {
    "FlowStudio::InitialConditions",
}

_POST_TYPES = {
    "FlowStudio::PostPipeline",
    "FlowStudio::MeasurementPoint",
    "FlowStudio::MeasurementSurface",
    "FlowStudio::MeasurementVolume",
}

_ANALYSIS_TYPES = {
    "FlowStudio::CFDAnalysis",
    "FlowStudio::SimulationAnalysis",
    "FlowStudio::StructuralAnalysis",
    "FlowStudio::ElectrostaticAnalysis",
    "FlowStudio::ElectromagneticAnalysis",
    "FlowStudio::ThermalAnalysis",
    "FlowStudio::OpticalAnalysis",
}


# ======================================================================
# Helpers – retrieve objects from analysis
# ======================================================================

def get_active_analysis():
    """Return the first analysis object in the active document, or None."""
    doc = FreeCAD.ActiveDocument
    if doc is None:
        return None
    for obj in doc.Objects:
        if getattr(obj, "FlowType", "") in _ANALYSIS_TYPES:
            return obj
    return None


def _group_objects(analysis):
    """Return the list of children inside the analysis group."""
    if analysis is None:
        return []
    return getattr(analysis, "Group", [])


def _has_type(analysis, type_set):
    """True if the analysis group contains at least one object whose
    FlowType is in *type_set*."""
    for obj in _group_objects(analysis):
        if getattr(obj, "FlowType", "") in type_set:
            return True
    return False


def _get_of_type(analysis, type_set):
    """Return all objects matching *type_set* inside the analysis."""
    return [
        o for o in _group_objects(analysis)
        if getattr(o, "FlowType", "") in type_set
    ]


def get_physics_model(analysis=None):
    if analysis is None:
        analysis = get_active_analysis()
    objs = _get_of_type(analysis, _PHYSICS_TYPES)
    return objs[0] if objs else None


def get_materials(analysis=None):
    if analysis is None:
        analysis = get_active_analysis()
    return _get_of_type(analysis, _MATERIAL_TYPES)


def get_boundary_conditions(analysis=None):
    if analysis is None:
        analysis = get_active_analysis()
    return _get_of_type(analysis, _BC_TYPES)


def get_mesh(analysis=None):
    if analysis is None:
        analysis = get_active_analysis()
    objs = _get_of_type(analysis, _MESH_TYPES)
    return objs[0] if objs else None


def get_solver(analysis=None):
    if analysis is None:
        analysis = get_active_analysis()
    objs = _get_of_type(analysis, _SOLVER_TYPES)
    return objs[0] if objs else None


def get_initial_conditions(analysis=None):
    if analysis is None:
        analysis = get_active_analysis()
    objs = _get_of_type(analysis, _INITIAL_COND_TYPES)
    return objs[0] if objs else None


# ======================================================================
# Geometry detection
# ======================================================================

def get_geometry_shapes():
    """Return Part::Feature objects that are NOT inside any analysis group.
    These are the candidate geometry bodies for meshing."""
    doc = FreeCAD.ActiveDocument
    if doc is None:
        return []
    analysis_children = set()
    for obj in doc.Objects:
        if getattr(obj, "FlowType", "") in _ANALYSIS_TYPES:
            for child in getattr(obj, "Group", []):
                analysis_children.add(child.Name)

    shapes = []
    for obj in doc.Objects:
        if obj.Name in analysis_children:
            continue
        if obj.isDerivedFrom("Part::Feature") and hasattr(obj, "Shape"):
            if not obj.Shape.isNull():
                shapes.append(obj)
    return shapes


# ======================================================================
# Workflow predicates – used by IsActive() guards
# ======================================================================

def has_analysis():
    return get_active_analysis() is not None


def has_geometry():
    return len(get_geometry_shapes()) > 0


def has_physics_model():
    return get_physics_model() is not None


def has_material():
    return len(get_materials()) > 0


def has_boundary_conditions():
    return len(get_boundary_conditions()) > 0


def has_mesh():
    return get_mesh() is not None


def has_mesh_completed():
    """True if a mesh exists and has been generated (cells > 0)."""
    mesh = get_mesh()
    if mesh is None:
        return False
    return getattr(mesh, "NumCells", 0) > 0


def has_solver():
    return get_solver() is not None


def has_initial_conditions():
    return get_initial_conditions() is not None


# ======================================================================
# Workflow status – overall progress report
# ======================================================================

class WorkflowStep:
    """Describes one step in the simulation workflow."""
    __slots__ = ("number", "name", "description", "complete", "active",
                 "command_name", "hint")

    def __init__(self, number, name, description, complete, active,
                 command_name="", hint=""):
        self.number = number
        self.name = name
        self.description = description
        self.complete = complete
        self.active = active        # Whether the user can act on it now
        self.command_name = command_name
        self.hint = hint


def get_active_domain_key(analysis=None):
    """Return the FlowStudio domain key for the active analysis."""
    if analysis is None:
        analysis = get_active_analysis()
    if analysis is None:
        return "CFD"
    return getattr(analysis, "PhysicsDomain", "CFD") or "CFD"


def get_workflow_context(analysis=None):
    """Return the active domain profile and workspace layout."""
    if analysis is None:
        analysis = get_active_analysis()
    domain_key = get_active_domain_key(analysis)
    return {
        "analysis": analysis,
        "domain_key": domain_key,
        "profile": get_workflow_profile(domain_key),
        "layout": get_workspace_layout(domain_key),
    }


def _build_status_map(analysis):
    mesh_exists = has_mesh()
    mesh_done = has_mesh_completed()
    run_done = False
    results_done = False
    if analysis is not None:
        case_dir = getattr(analysis, "CaseDir", "")
        if case_dir:
            import os
            run_done = os.path.isdir(os.path.join(case_dir, "postProcessing")) or \
                os.path.isdir(os.path.join(case_dir, "processor0"))
        results_done = _has_type(analysis, _POST_TYPES)

    return {
        "analysis": {
            "complete": analysis is not None,
            "active": True,
        },
        "geometry": {
            "complete": has_geometry(),
            "active": analysis is not None,
        },
        "physics": {
            "complete": has_physics_model(),
            "active": analysis is not None,
        },
        "materials": {
            "complete": has_material(),
            "active": analysis is not None,
        },
        "boundaries": {
            "complete": has_boundary_conditions(),
            "active": analysis is not None and has_physics_model(),
        },
        "mesh": {
            "complete": mesh_done,
            "active": analysis is not None and has_geometry(),
        },
        "study_controls": {
            "complete": has_initial_conditions(),
            "active": analysis is not None,
        },
        "optical_controls": {
            "complete": get_physics_model(analysis) is not None and get_solver(analysis) is not None,
            "active": analysis is not None and get_active_domain_key(analysis) == "Optical",
        },
        "run": {
            "complete": run_done,
            "active": analysis is not None and has_physics_model() and has_material() and has_boundary_conditions() and (mesh_done or not mesh_exists),
        },
        "results": {
            "complete": results_done,
            "active": run_done,
        },
    }


def get_workflow_status():
    """Return a list of ``WorkflowStep`` describing current progress.

    This is the single source of truth for the UI workflow guide panel.
    """
    context = get_workflow_context()
    status_map = _build_status_map(context["analysis"])
    steps = []
    for step_profile in context["profile"].steps:
        status = status_map[step_profile.status_key]
        steps.append(WorkflowStep(
            step_profile.number,
            step_profile.name,
            step_profile.description,
            status["complete"],
            status["active"],
            step_profile.command_name,
            "" if status["complete"] else step_profile.hint,
        ))
    return steps


# ======================================================================
# Pre-run validation (CfdOF style)
# ======================================================================

class WorkflowChecker:
    """Validates the analysis is ready to run, returning a list of errors."""

    def __init__(self, analysis=None):
        self.analysis = analysis or get_active_analysis()

    def check_all(self):
        """Return list of human-readable error strings.  Empty list = OK."""
        errors = []
        if self.analysis is None:
            errors.append("No analysis container found. Create one first "
                          "(FlowStudio → New Analysis).")
            return errors

        if not has_physics_model():
            errors.append("Step 3: No physics model found. The analysis needs "
                          "a physics model to define the simulation type.")

        if not has_material():
            errors.append("Step 4: No material defined. Add and configure a "
                          "material (fluid, solid, or domain-specific).")

        if not has_boundary_conditions():
            errors.append("Step 5: No boundary conditions assigned. Add at "
                          "least one BC (Inlet, Outlet, Wall, etc.).")

        if not has_mesh():
            errors.append("Step 6: No mesh object found. Create a mesh using "
                          "FlowStudio → Mesh → CFD Mesh.")
        elif not has_mesh_completed():
            errors.append("Step 6: Mesh exists but has not been generated yet. "
                          "Double-click the mesh and run the mesher.")

        if not has_solver():
            errors.append("Step 8: No solver object found in the analysis.")

        # Check dirty flags
        needs_mesh = getattr(self.analysis, "NeedsMeshRewrite", False)
        needs_case = getattr(self.analysis, "NeedsCaseRewrite", False)
        needs_rerun = getattr(self.analysis, "NeedsMeshRerun", False)

        if needs_mesh:
            errors.append("Mesh parameters have changed since the last mesh "
                          "generation. Re-run the mesher before solving.")
        if needs_rerun and has_mesh() and not needs_mesh:
            errors.append("Mesh case files were written but the mesher has "
                          "not been run. Execute the mesher first.")

        return errors

    def check_mesh_ready(self):
        """Check prerequisites for meshing."""
        errors = []
        if self.analysis is None:
            errors.append("No analysis container found.")
            return errors
        if not has_geometry():
            errors.append("No geometry found. Import or create a "
                          "Part::Feature shape before meshing.")
        return errors
