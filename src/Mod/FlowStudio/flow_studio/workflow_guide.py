# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Workflow Guide – enforces the step-by-step simulation workflow.

Modelled after CfdOF's approach: each simulation must follow a defined
sequence of steps.  This module provides:
  - ``get_workflow_status()`` – returns the completion state of each step
  - Helper predicates used by command ``IsActive()`` guards
  - ``WorkflowChecker`` – pre-run validation akin to CfdOF's dirty-flag checks

Workflow steps (applicable to every physics domain):
  1. Create Analysis   – container + auto-created physics/material/solver
  2. Import/Create Geometry – a Part::Feature shape in the document
  3. Configure Physics  – double-click the PhysicsModel child
  4. Assign Material    – configure fluid/solid/dielectric properties
  5. Set Boundary Conditions – at least one BC on a face
  6. Generate Mesh      – create and run the mesher
  7. Set Initial Conditions – optional but recommended
  8. Run Solver         – write case + execute
  9. Post-process       – visualize results
"""

import FreeCAD

# FlowType strings used to identify objects inside analysis groups
_PHYSICS_TYPES = {
    "FlowStudio::PhysicsModel",
    "FlowStudio::StructuralPhysicsModel",
    "FlowStudio::ElectrostaticPhysicsModel",
    "FlowStudio::ElectromagneticPhysicsModel",
    "FlowStudio::ThermalPhysicsModel",
}

_MATERIAL_TYPES = {
    "FlowStudio::FluidMaterial",
    "FlowStudio::SolidMaterial",
    "FlowStudio::ElectrostaticMaterial",
    "FlowStudio::ElectromagneticMaterial",
    "FlowStudio::ThermalMaterial",
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


def get_workflow_status():
    """Return a list of ``WorkflowStep`` describing current progress.

    This is the single source of truth for the UI workflow guide panel.
    """
    analysis = get_active_analysis()

    step1_ok = analysis is not None
    step2_ok = has_geometry()
    step3_ok = has_physics_model()
    step4_ok = has_material()
    step5_ok = has_boundary_conditions()
    step6_ok = has_mesh()
    step6b_ok = has_mesh_completed()
    step7_ok = has_initial_conditions()
    step8_ok = False  # solver ran successfully – checked via results
    step9_ok = False

    # Check if solver results exist
    if analysis is not None:
        case_dir = getattr(analysis, "CaseDir", "")
        if case_dir:
            import os
            # A simple heuristic: if postProcessing or log.* exists, solver ran
            step8_ok = os.path.isdir(os.path.join(case_dir, "postProcessing")) or \
                       os.path.isdir(os.path.join(case_dir, "processor0"))
        step9_ok = _has_type(analysis, _POST_TYPES)

    steps = [
        WorkflowStep(
            1, "Create Analysis",
            "Create a simulation analysis container. This automatically adds "
            "physics model, material, initial conditions, and solver objects.",
            step1_ok, True,
            "FlowStudio_Analysis",
            "Use FlowStudio → New Analysis → [domain]" if not step1_ok else ""
        ),
        WorkflowStep(
            2, "Import / Create Geometry",
            "Add or import a CAD geometry (Part::Feature) into the document. "
            "This is the shape that will be meshed for simulation.",
            step2_ok, step1_ok,
            "",
            "Use Part workbench or File → Import to add geometry" if not step2_ok else ""
        ),
        WorkflowStep(
            3, "Configure Physics Model",
            "Double-click the PhysicsModel to set flow regime (steady/transient), "
            "turbulence model, heat transfer, compressibility, etc.",
            step3_ok, step1_ok,
            "FlowStudio_PhysicsModel",
            "Double-click PhysicsModel in the model tree" if not step3_ok else ""
        ),
        WorkflowStep(
            4, "Assign Material Properties",
            "Double-click the Material object to set density, viscosity, "
            "conductivity, and other material-specific properties.",
            step4_ok, step1_ok,
            "FlowStudio_FluidMaterial",
            "Double-click the material object in the model tree" if not step4_ok else ""
        ),
        WorkflowStep(
            5, "Define Boundary Conditions",
            "Add boundary conditions (Wall, Inlet, Outlet, etc.) and assign "
            "them to geometry faces. At least one BC is required.",
            step5_ok, step1_ok and step3_ok,
            "FlowStudio_BC_Inlet",
            "Add at least Inlet + Outlet BCs via FlowStudio → CFD → Inlet/Outlet" if not step5_ok else ""
        ),
        WorkflowStep(
            6, "Generate Mesh",
            "Create a mesh object, link it to the geometry, and run the mesher. "
            "Check mesh quality before proceeding to the solver.",
            step6b_ok, step1_ok and step2_ok,
            "FlowStudio_MeshGmsh",
            "Add mesh via FlowStudio → Mesh → CFD Mesh, then run the mesher" if not step6b_ok else ""
        ),
        WorkflowStep(
            7, "Set Initial Conditions",
            "Configure initial field values (velocity, pressure, temperature). "
            "Good initial conditions improve solver convergence.",
            step7_ok, step1_ok,
            "FlowStudio_InitialConditions",
            "Double-click InitialConditions in the model tree" if not step7_ok else ""
        ),
        WorkflowStep(
            8, "Run Solver",
            "Write case files and launch the solver. The system will check that "
            "all prerequisites are satisfied before running.",
            step8_ok, step1_ok and step3_ok and step4_ok and step5_ok and step6b_ok,
            "FlowStudio_RunSolver",
            "Use FlowStudio → Solve → Run Solver" if not step8_ok else ""
        ),
        WorkflowStep(
            9, "Post-process Results",
            "Create post-processing pipelines to visualize velocity, pressure, "
            "temperature, or other result fields.",
            step9_ok, step8_ok,
            "FlowStudio_PostPipeline",
            "Add a Post Pipeline via FlowStudio → Post-Processing" if not step9_ok else ""
        ),
    ]
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
