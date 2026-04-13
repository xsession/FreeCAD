# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""FlowStudio – Workbench command definitions.

All FreeCADGui.addCommand() registrations happen at module import time,
which is triggered by ``InitGui.py``'s ``Initialize()``.

Supports multi-physics domains: CFD, Structural, Electrostatic,
Electromagnetic, Thermal – each with domain-specific materials,
boundary conditions, and solver backends.
"""

import os
import FreeCAD
import FreeCADGui

from flow_studio.workflow_guide import (
    get_active_analysis,
    has_analysis,
    has_geometry,
    has_physics_model,
    has_material,
    has_boundary_conditions,
    has_mesh,
    has_mesh_completed,
    has_solver,
    WorkflowChecker,
)

translate = FreeCAD.Qt.translate

ICONS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                         "Resources", "icons")


def _icon(name):
    return os.path.join(ICONS_DIR, name)


def _get_active_analysis():
    """Return the first SimulationAnalysis in the active document, or None."""
    return get_active_analysis()


def _get_active_domain():
    """Return the PhysicsDomain string of the active analysis, or 'CFD'."""
    analysis = _get_active_analysis()
    if analysis is not None:
        return getattr(analysis, "PhysicsDomain", "CFD")
    return "CFD"


def _add_to_analysis(obj):
    """Add *obj* to the active analysis group."""
    analysis = _get_active_analysis()
    if analysis is not None:
        analysis.addObject(obj)


# ======================================================================
#  ANALYSIS commands
# ======================================================================

class _CmdAnalysis:
    """Create a new CFD analysis container."""

    def GetResources(self):
        return {
            "Pixmap": _icon("FlowStudioAnalysis.svg"),
            "MenuText": translate("FlowStudio", "New CFD Analysis"),
            "Accel": "C, A",
            "ToolTip": translate(
                "FlowStudio",
                "Create a new CFD analysis container (FloEFD-style workflow)"
            ),
        }

    def IsActive(self):
        return FreeCAD.ActiveDocument is not None

    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction("Create CFD Analysis")
        from flow_studio.ObjectsFlowStudio import makeAnalysis
        analysis = makeAnalysis()
        from flow_studio.ObjectsFlowStudio import (
            makePhysicsModel, makeFluidMaterial, makeInitialConditions,
            makeSolver,
        )
        for maker in (makePhysicsModel, makeFluidMaterial,
                      makeInitialConditions, makeSolver):
            child = maker()
            analysis.addObject(child)
        FreeCAD.ActiveDocument.commitTransaction()
        FreeCAD.ActiveDocument.recompute()


class _CmdStructuralAnalysis:
    """Create a new Structural Mechanics analysis."""

    def GetResources(self):
        return {
            "Pixmap": _icon("FlowStudioStructural.svg"),
            "MenuText": translate("FlowStudio", "New Structural Analysis"),
            "ToolTip": translate(
                "FlowStudio",
                "Create a structural mechanics (FEM) analysis"
            ),
        }

    def IsActive(self):
        return FreeCAD.ActiveDocument is not None

    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction("Create Structural Analysis")
        from flow_studio.ObjectsFlowStudio import (
            makeDomainAnalysis, makeStructuralPhysicsModel,
            makeSolidMaterial, makeSolver,
        )
        analysis = makeDomainAnalysis(domain_key="Structural")
        for maker in (makeStructuralPhysicsModel, makeSolidMaterial, makeSolver):
            analysis.addObject(maker())
        FreeCAD.ActiveDocument.commitTransaction()
        FreeCAD.ActiveDocument.recompute()


class _CmdElectrostaticAnalysis:
    """Create a new Electrostatic analysis."""

    def GetResources(self):
        return {
            "Pixmap": _icon("FlowStudioElectrostatic.svg"),
            "MenuText": translate("FlowStudio", "New Electrostatic Analysis"),
            "ToolTip": translate(
                "FlowStudio",
                "Create an electrostatic field analysis"
            ),
        }

    def IsActive(self):
        return FreeCAD.ActiveDocument is not None

    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction("Create Electrostatic Analysis")
        from flow_studio.ObjectsFlowStudio import (
            makeDomainAnalysis, makeElectrostaticPhysicsModel,
            makeElectrostaticMaterial, makeSolver,
        )
        analysis = makeDomainAnalysis(domain_key="Electrostatic")
        for maker in (makeElectrostaticPhysicsModel, makeElectrostaticMaterial, makeSolver):
            analysis.addObject(maker())
        FreeCAD.ActiveDocument.commitTransaction()
        FreeCAD.ActiveDocument.recompute()


class _CmdElectromagneticAnalysis:
    """Create a new Electromagnetic analysis."""

    def GetResources(self):
        return {
            "Pixmap": _icon("FlowStudioElectromagnetic.svg"),
            "MenuText": translate("FlowStudio", "New Electromagnetic Analysis"),
            "ToolTip": translate(
                "FlowStudio",
                "Create an electromagnetic field analysis"
            ),
        }

    def IsActive(self):
        return FreeCAD.ActiveDocument is not None

    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction("Create EM Analysis")
        from flow_studio.ObjectsFlowStudio import (
            makeDomainAnalysis, makeElectromagneticPhysicsModel,
            makeElectromagneticMaterial, makeSolver,
        )
        analysis = makeDomainAnalysis(domain_key="Electromagnetic")
        for maker in (makeElectromagneticPhysicsModel, makeElectromagneticMaterial, makeSolver):
            analysis.addObject(maker())
        FreeCAD.ActiveDocument.commitTransaction()
        FreeCAD.ActiveDocument.recompute()


class _CmdThermalAnalysis:
    """Create a new Thermal analysis."""

    def GetResources(self):
        return {
            "Pixmap": _icon("FlowStudioThermal.svg"),
            "MenuText": translate("FlowStudio", "New Thermal Analysis"),
            "ToolTip": translate(
                "FlowStudio",
                "Create a heat transfer / thermal analysis"
            ),
        }

    def IsActive(self):
        return FreeCAD.ActiveDocument is not None

    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction("Create Thermal Analysis")
        from flow_studio.ObjectsFlowStudio import (
            makeDomainAnalysis, makeThermalPhysicsModel,
            makeThermalMaterial, makeSolver,
        )
        analysis = makeDomainAnalysis(domain_key="Thermal")
        for maker in (makeThermalPhysicsModel, makeThermalMaterial, makeSolver):
            analysis.addObject(maker())
        FreeCAD.ActiveDocument.commitTransaction()
        FreeCAD.ActiveDocument.recompute()


class _CmdPhysicsModel:
    def GetResources(self):
        return {
            "Pixmap": _icon("FlowStudioPhysics.svg"),
            "MenuText": translate("FlowStudio", "Physics Model"),
            "ToolTip": translate(
                "FlowStudio",
                "Configure flow regime, turbulence, heat transfer, etc."
            ),
        }

    def IsActive(self):
        return _get_active_analysis() is not None

    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction("Add Physics Model")
        from flow_studio.ObjectsFlowStudio import makePhysicsModel
        obj = makePhysicsModel()
        _add_to_analysis(obj)
        FreeCAD.ActiveDocument.commitTransaction()
        FreeCAD.ActiveDocument.recompute()


class _CmdFluidMaterial:
    def GetResources(self):
        return {
            "Pixmap": _icon("FlowStudioMaterial.svg"),
            "MenuText": translate("FlowStudio", "Fluid Material"),
            "ToolTip": translate(
                "FlowStudio",
                "Define fluid properties (density, viscosity, etc.)"
            ),
        }

    def IsActive(self):
        return _get_active_analysis() is not None

    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction("Add Fluid Material")
        from flow_studio.ObjectsFlowStudio import makeFluidMaterial
        obj = makeFluidMaterial()
        _add_to_analysis(obj)
        FreeCAD.ActiveDocument.commitTransaction()
        FreeCAD.ActiveDocument.recompute()


class _CmdInitialConditions:
    def GetResources(self):
        return {
            "Pixmap": _icon("FlowStudioInitial.svg"),
            "MenuText": translate("FlowStudio", "Initial Conditions"),
            "ToolTip": translate(
                "FlowStudio",
                "Set initial velocity, pressure, temperature fields"
            ),
        }

    def IsActive(self):
        return _get_active_analysis() is not None

    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction("Add Initial Conditions")
        from flow_studio.ObjectsFlowStudio import makeInitialConditions
        obj = makeInitialConditions()
        _add_to_analysis(obj)
        FreeCAD.ActiveDocument.commitTransaction()
        FreeCAD.ActiveDocument.recompute()


# ======================================================================
#  BOUNDARY CONDITION commands
# ======================================================================

class _CmdBCWall:
    def GetResources(self):
        return {
            "Pixmap": _icon("FlowStudioWall.svg"),
            "MenuText": translate("FlowStudio", "Wall"),
            "ToolTip": translate(
                "FlowStudio",
                "Assign wall boundary (no-slip, slip, moving, rough)\n"
                "Requires: Analysis + Physics Model (Step 5)"
            ),
        }

    def IsActive(self):
        return has_analysis() and has_physics_model()

    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction("Add Wall BC")
        from flow_studio.ObjectsFlowStudio import makeBCWall
        obj = makeBCWall()
        _add_to_analysis(obj)
        FreeCAD.ActiveDocument.commitTransaction()
        FreeCAD.ActiveDocument.recompute()


class _CmdBCInlet:
    def GetResources(self):
        return {
            "Pixmap": _icon("FlowStudioInlet.svg"),
            "MenuText": translate("FlowStudio", "Inlet"),
            "ToolTip": translate(
                "FlowStudio",
                "Define velocity/mass-flow/pressure inlet\n"
                "Requires: Analysis + Physics Model (Step 5)"
            ),
        }

    def IsActive(self):
        return has_analysis() and has_physics_model()

    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction("Add Inlet BC")
        from flow_studio.ObjectsFlowStudio import makeBCInlet
        obj = makeBCInlet()
        _add_to_analysis(obj)
        FreeCAD.ActiveDocument.commitTransaction()
        FreeCAD.ActiveDocument.recompute()


class _CmdBCOutlet:
    def GetResources(self):
        return {
            "Pixmap": _icon("FlowStudioOutlet.svg"),
            "MenuText": translate("FlowStudio", "Outlet"),
            "ToolTip": translate(
                "FlowStudio",
                "Define pressure/outflow outlet\n"
                "Requires: Analysis + Physics Model (Step 5)"
            ),
        }

    def IsActive(self):
        return has_analysis() and has_physics_model()

    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction("Add Outlet BC")
        from flow_studio.ObjectsFlowStudio import makeBCOutlet
        obj = makeBCOutlet()
        _add_to_analysis(obj)
        FreeCAD.ActiveDocument.commitTransaction()
        FreeCAD.ActiveDocument.recompute()


class _CmdBCOpenBoundary:
    def GetResources(self):
        return {
            "Pixmap": _icon("FlowStudioOpen.svg"),
            "MenuText": translate("FlowStudio", "Open Boundary"),
            "ToolTip": translate(
                "FlowStudio",
                "Far-field / open boundary condition\n"
                "Requires: Analysis + Physics Model (Step 5)"
            ),
        }

    def IsActive(self):
        return has_analysis() and has_physics_model()

    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction("Add Open BC")
        from flow_studio.ObjectsFlowStudio import makeBCOpenBoundary
        obj = makeBCOpenBoundary()
        _add_to_analysis(obj)
        FreeCAD.ActiveDocument.commitTransaction()
        FreeCAD.ActiveDocument.recompute()


class _CmdBCSymmetry:
    def GetResources(self):
        return {
            "Pixmap": _icon("FlowStudioSymmetry.svg"),
            "MenuText": translate("FlowStudio", "Symmetry"),
            "ToolTip": translate(
                "FlowStudio",
                "Symmetry boundary condition (zero normal gradient)\n"
                "Requires: Analysis + Physics Model (Step 5)"
            ),
        }

    def IsActive(self):
        return has_analysis() and has_physics_model()

    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction("Add Symmetry BC")
        from flow_studio.ObjectsFlowStudio import makeBCSymmetry
        obj = makeBCSymmetry()
        _add_to_analysis(obj)
        FreeCAD.ActiveDocument.commitTransaction()
        FreeCAD.ActiveDocument.recompute()


# ======================================================================
#  MESH commands
# ======================================================================

class _CmdMeshGmsh:
    def GetResources(self):
        return {
            "Pixmap": _icon("FlowStudioMesh.svg"),
            "MenuText": translate("FlowStudio", "CFD Mesh (GMSH)"),
            "ToolTip": translate(
                "FlowStudio",
                "Generate a CFD mesh using GMSH\n"
                "Requires: Analysis + Geometry (Step 6)"
            ),
        }

    def IsActive(self):
        return has_analysis() and has_geometry()

    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction("Add CFD Mesh")
        from flow_studio.ObjectsFlowStudio import makeMeshGmsh
        obj = makeMeshGmsh()
        _add_to_analysis(obj)
        FreeCAD.ActiveDocument.commitTransaction()
        FreeCAD.ActiveDocument.recompute()


class _CmdMeshRegion:
    def GetResources(self):
        return {
            "Pixmap": _icon("FlowStudioMeshRegion.svg"),
            "MenuText": translate("FlowStudio", "Mesh Refinement Region"),
            "ToolTip": translate(
                "FlowStudio",
                "Add a local mesh refinement region (box, sphere, surface)\n"
                "Requires: Mesh object (Step 6)"
            ),
        }

    def IsActive(self):
        return has_analysis() and has_mesh()

    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction("Add Mesh Region")
        from flow_studio.ObjectsFlowStudio import makeMeshRegion
        obj = makeMeshRegion()
        _add_to_analysis(obj)
        FreeCAD.ActiveDocument.commitTransaction()
        FreeCAD.ActiveDocument.recompute()


class _CmdBoundaryLayer:
    def GetResources(self):
        return {
            "Pixmap": _icon("FlowStudioBoundaryLayer.svg"),
            "MenuText": translate("FlowStudio", "Boundary Layer Mesh"),
            "ToolTip": translate(
                "FlowStudio",
                "Define inflation / boundary-layer mesh parameters\n"
                "Requires: Mesh object (Step 6)"
            ),
        }

    def IsActive(self):
        return has_analysis() and has_mesh()

    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction("Add Boundary Layer")
        from flow_studio.ObjectsFlowStudio import makeBoundaryLayer
        obj = makeBoundaryLayer()
        _add_to_analysis(obj)
        FreeCAD.ActiveDocument.commitTransaction()
        FreeCAD.ActiveDocument.recompute()


# ======================================================================
#  SOLVE commands
# ======================================================================

class _CmdSolverSelect:
    def GetResources(self):
        return {
            "Pixmap": _icon("FlowStudioSolver.svg"),
            "MenuText": translate("FlowStudio", "Add Solver"),
            "ToolTip": translate(
                "FlowStudio",
                "Add a CFD solver object (OpenFOAM, FluidX3D, SU2)"
            ),
        }

    def IsActive(self):
        return _get_active_analysis() is not None

    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction("Add Solver")
        from flow_studio.ObjectsFlowStudio import makeSolver
        obj = makeSolver()
        _add_to_analysis(obj)
        FreeCAD.ActiveDocument.commitTransaction()
        FreeCAD.ActiveDocument.recompute()


class _CmdSolverSettings:
    """Open solver settings panel."""

    def GetResources(self):
        return {
            "Pixmap": _icon("FlowStudioSolverSettings.svg"),
            "MenuText": translate("FlowStudio", "Solver Settings"),
            "ToolTip": translate(
                "FlowStudio",
                "Edit solver parameters (numerics, convergence, etc.)"
            ),
        }

    def IsActive(self):
        return _get_active_analysis() is not None

    def Activated(self):
        # Find the solver in the analysis and open for editing
        analysis = _get_active_analysis()
        if analysis is None:
            return
        for obj in analysis.Group:
            if getattr(obj, "FlowType", "") == "FlowStudio::Solver":
                FreeCADGui.ActiveDocument.setEdit(obj, 0)
                return
        FreeCAD.Console.PrintWarning(
            "FlowStudio: No solver found in analysis. Add one first.\n"
        )


class _CmdRunSolver:
    """Write case & launch the solver – with CfdOF-style pre-flight checks."""

    def GetResources(self):
        return {
            "Pixmap": _icon("FlowStudioRunSolver.svg"),
            "MenuText": translate("FlowStudio", "Run Solver"),
            "Accel": "C, R",
            "ToolTip": translate(
                "FlowStudio",
                "Write case files and launch the selected CFD solver\n"
                "Requires: Physics + Material + BCs + Mesh (Step 8)"
            ),
        }

    def IsActive(self):
        # Only active when ALL prerequisites for running are met
        return (has_analysis() and has_physics_model() and has_material()
                and has_boundary_conditions() and has_mesh_completed()
                and has_solver())

    def Activated(self):
        analysis = _get_active_analysis()
        if analysis is None:
            return

        # Pre-flight validation (CfdOF-style)
        checker = WorkflowChecker(analysis)
        errors = checker.check_all()
        if errors:
            msg = "FlowStudio: Cannot run solver – the following issues " \
                  "were found:\n"
            for i, e in enumerate(errors, 1):
                msg += f"  {i}. {e}\n"
            FreeCAD.Console.PrintError(msg)
            # Also show a message box if GUI is available
            if FreeCAD.GuiUp:
                from PySide import QtWidgets
                QtWidgets.QMessageBox.warning(
                    None,
                    translate("FlowStudio", "Workflow Check Failed"),
                    translate("FlowStudio",
                              "Cannot run solver. Please fix the following "
                              "issues:\n\n" + "\n".join(errors)),
                )
            return

        # Find the solver object
        solver_obj = None
        for obj in analysis.Group:
            if getattr(obj, "FlowType", "") == "FlowStudio::Solver":
                solver_obj = obj
                break

        if solver_obj is None:
            FreeCAD.Console.PrintError(
                "FlowStudio: No solver in analysis.\n")
            return

        # Check dirty flags and warn
        needs_mesh = getattr(analysis, "NeedsMeshRewrite", False)
        needs_case = getattr(analysis, "NeedsCaseRewrite", False)
        if needs_mesh or needs_case:
            if FreeCAD.GuiUp:
                from PySide import QtWidgets
                parts = []
                if needs_mesh:
                    parts.append("- Mesh parameters have changed (re-mesh recommended)")
                if needs_case:
                    parts.append("- Case settings have changed (case rewrite needed)")
                reply = QtWidgets.QMessageBox.question(
                    None,
                    translate("FlowStudio", "Settings Changed"),
                    translate("FlowStudio",
                              "The following changes were detected:\n\n"
                              + "\n".join(parts)
                              + "\n\nProceed with writing case and running solver?"),
                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                    QtWidgets.QMessageBox.Yes,
                )
                if reply != QtWidgets.QMessageBox.Yes:
                    return

        backend = solver_obj.SolverBackend
        FreeCAD.Console.PrintMessage(
            f"FlowStudio: Running solver backend '{backend}'...\n"
        )

        from flow_studio.solvers.registry import get_runner
        runner_cls = get_runner(backend)
        if runner_cls is None:
            FreeCAD.Console.PrintError(
                f"FlowStudio: Unknown backend '{backend}'\n")
            return

        runner = runner_cls(analysis, solver_obj)
        run_errors = runner.check()
        if run_errors:
            for e in run_errors:
                FreeCAD.Console.PrintError(f"FlowStudio: {e}\n")
            return
        runner.write_case()
        runner.run()

        # Clear dirty flags after successful case write + run launch
        try:
            analysis.NeedsCaseRewrite = False
            analysis.NeedsMeshRewrite = False
            analysis.NeedsMeshRerun = False
        except AttributeError:
            pass


# ======================================================================
#  STRUCTURAL BC commands
# ======================================================================

class _CmdSolidMaterial:
    def GetResources(self):
        return {
            "Pixmap": _icon("FlowStudioSolidMaterial.svg"),
            "MenuText": translate("FlowStudio", "Solid Material"),
            "ToolTip": translate("FlowStudio",
                                 "Define solid material (Young's modulus, density, etc.)"),
        }

    def IsActive(self):
        return _get_active_analysis() is not None

    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction("Add Solid Material")
        from flow_studio.ObjectsFlowStudio import makeSolidMaterial
        _add_to_analysis(makeSolidMaterial())
        FreeCAD.ActiveDocument.commitTransaction()
        FreeCAD.ActiveDocument.recompute()


class _CmdStructuralPhysics:
    def GetResources(self):
        return {
            "Pixmap": _icon("FlowStudioStructuralPhysics.svg"),
            "MenuText": translate("FlowStudio", "Structural Physics"),
            "ToolTip": translate("FlowStudio",
                                 "Configure structural analysis model"),
        }

    def IsActive(self):
        return _get_active_analysis() is not None

    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction("Add Structural Physics")
        from flow_studio.ObjectsFlowStudio import makeStructuralPhysicsModel
        _add_to_analysis(makeStructuralPhysicsModel())
        FreeCAD.ActiveDocument.commitTransaction()
        FreeCAD.ActiveDocument.recompute()


class _CmdBCFixedDisplacement:
    def GetResources(self):
        return {
            "Pixmap": _icon("FlowStudioFixedDisplacement.svg"),
            "MenuText": translate("FlowStudio", "Fixed Displacement"),
            "ToolTip": translate("FlowStudio",
                                 "Prescribe displacement / fixed support\n"
                                 "Requires: Analysis + Physics Model"),
        }

    def IsActive(self):
        return has_analysis() and has_physics_model()

    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction("Add Fixed Displacement BC")
        from flow_studio.ObjectsFlowStudio import makeBCFixedDisplacement
        _add_to_analysis(makeBCFixedDisplacement())
        FreeCAD.ActiveDocument.commitTransaction()
        FreeCAD.ActiveDocument.recompute()


class _CmdBCForce:
    def GetResources(self):
        return {
            "Pixmap": _icon("FlowStudioForce.svg"),
            "MenuText": translate("FlowStudio", "Force / Pressure"),
            "ToolTip": translate("FlowStudio",
                                 "Apply force or pressure to faces\n"
                                 "Requires: Analysis + Physics Model"),
        }

    def IsActive(self):
        return has_analysis() and has_physics_model()

    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction("Add Force BC")
        from flow_studio.ObjectsFlowStudio import makeBCForce
        _add_to_analysis(makeBCForce())
        FreeCAD.ActiveDocument.commitTransaction()
        FreeCAD.ActiveDocument.recompute()


class _CmdBCPressureLoad:
    def GetResources(self):
        return {
            "Pixmap": _icon("FlowStudioPressureLoad.svg"),
            "MenuText": translate("FlowStudio", "Pressure Load"),
            "ToolTip": translate("FlowStudio",
                                 "Apply uniform pressure load\n"
                                 "Requires: Analysis + Physics Model"),
        }

    def IsActive(self):
        return has_analysis() and has_physics_model()

    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction("Add Pressure Load BC")
        from flow_studio.ObjectsFlowStudio import makeBCPressureLoad
        _add_to_analysis(makeBCPressureLoad())
        FreeCAD.ActiveDocument.commitTransaction()
        FreeCAD.ActiveDocument.recompute()


# ======================================================================
#  ELECTROSTATIC commands
# ======================================================================

class _CmdElectrostaticMaterial:
    def GetResources(self):
        return {
            "Pixmap": _icon("FlowStudioDielectricMaterial.svg"),
            "MenuText": translate("FlowStudio", "Dielectric Material"),
            "ToolTip": translate("FlowStudio",
                                 "Define dielectric material properties"),
        }

    def IsActive(self):
        return _get_active_analysis() is not None

    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction("Add Electrostatic Material")
        from flow_studio.ObjectsFlowStudio import makeElectrostaticMaterial
        _add_to_analysis(makeElectrostaticMaterial())
        FreeCAD.ActiveDocument.commitTransaction()
        FreeCAD.ActiveDocument.recompute()


class _CmdElectrostaticPhysics:
    def GetResources(self):
        return {
            "Pixmap": _icon("FlowStudioElectrostaticPhysics.svg"),
            "MenuText": translate("FlowStudio", "Electrostatic Physics"),
            "ToolTip": translate("FlowStudio",
                                 "Configure electrostatic solver settings"),
        }

    def IsActive(self):
        return _get_active_analysis() is not None

    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction("Add Electrostatic Physics")
        from flow_studio.ObjectsFlowStudio import makeElectrostaticPhysicsModel
        _add_to_analysis(makeElectrostaticPhysicsModel())
        FreeCAD.ActiveDocument.commitTransaction()
        FreeCAD.ActiveDocument.recompute()


class _CmdBCElectricPotential:
    def GetResources(self):
        return {
            "Pixmap": _icon("FlowStudioElectricPotential.svg"),
            "MenuText": translate("FlowStudio", "Electric Potential"),
            "ToolTip": translate("FlowStudio",
                                 "Prescribe electric potential (voltage) on boundary\n"
                                 "Requires: Analysis + Physics Model"),
        }

    def IsActive(self):
        return has_analysis() and has_physics_model()

    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction("Add Electric Potential BC")
        from flow_studio.ObjectsFlowStudio import makeBCElectricPotential
        _add_to_analysis(makeBCElectricPotential())
        FreeCAD.ActiveDocument.commitTransaction()
        FreeCAD.ActiveDocument.recompute()


class _CmdBCSurfaceCharge:
    def GetResources(self):
        return {
            "Pixmap": _icon("FlowStudioSurfaceCharge.svg"),
            "MenuText": translate("FlowStudio", "Surface Charge"),
            "ToolTip": translate("FlowStudio",
                                 "Apply surface charge density\n"
                                 "Requires: Analysis + Physics Model"),
        }

    def IsActive(self):
        return has_analysis() and has_physics_model()

    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction("Add Surface Charge BC")
        from flow_studio.ObjectsFlowStudio import makeBCSurfaceCharge
        _add_to_analysis(makeBCSurfaceCharge())
        FreeCAD.ActiveDocument.commitTransaction()
        FreeCAD.ActiveDocument.recompute()


# ======================================================================
#  ELECTROMAGNETIC commands
# ======================================================================

class _CmdElectromagneticMaterial:
    def GetResources(self):
        return {
            "Pixmap": _icon("FlowStudioEMMaterial.svg"),
            "MenuText": translate("FlowStudio", "Electromagnetic Material"),
            "ToolTip": translate("FlowStudio",
                                 "Define electromagnetic material (permeability, conductivity)"),
        }

    def IsActive(self):
        return _get_active_analysis() is not None

    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction("Add EM Material")
        from flow_studio.ObjectsFlowStudio import makeElectromagneticMaterial
        _add_to_analysis(makeElectromagneticMaterial())
        FreeCAD.ActiveDocument.commitTransaction()
        FreeCAD.ActiveDocument.recompute()


class _CmdElectromagneticPhysics:
    def GetResources(self):
        return {
            "Pixmap": _icon("FlowStudioElectromagneticPhysics.svg"),
            "MenuText": translate("FlowStudio", "Electromagnetic Physics"),
            "ToolTip": translate("FlowStudio",
                                 "Configure electromagnetic solver type"),
        }

    def IsActive(self):
        return _get_active_analysis() is not None

    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction("Add EM Physics")
        from flow_studio.ObjectsFlowStudio import makeElectromagneticPhysicsModel
        _add_to_analysis(makeElectromagneticPhysicsModel())
        FreeCAD.ActiveDocument.commitTransaction()
        FreeCAD.ActiveDocument.recompute()


class _CmdBCMagneticPotential:
    def GetResources(self):
        return {
            "Pixmap": _icon("FlowStudioMagneticPotential.svg"),
            "MenuText": translate("FlowStudio", "Magnetic Potential"),
            "ToolTip": translate("FlowStudio",
                                 "Prescribe magnetic vector potential (A)\n"
                                 "Requires: Analysis + Physics Model"),
        }

    def IsActive(self):
        return has_analysis() and has_physics_model()

    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction("Add Magnetic Potential BC")
        from flow_studio.ObjectsFlowStudio import makeBCMagneticPotential
        _add_to_analysis(makeBCMagneticPotential())
        FreeCAD.ActiveDocument.commitTransaction()
        FreeCAD.ActiveDocument.recompute()


class _CmdBCCurrentDensity:
    def GetResources(self):
        return {
            "Pixmap": _icon("FlowStudioCurrentDensity.svg"),
            "MenuText": translate("FlowStudio", "Current Density"),
            "ToolTip": translate("FlowStudio",
                                 "Prescribe current density source\n"
                                 "Requires: Analysis + Physics Model"),
        }

    def IsActive(self):
        return has_analysis() and has_physics_model()

    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction("Add Current Density BC")
        from flow_studio.ObjectsFlowStudio import makeBCCurrentDensity
        _add_to_analysis(makeBCCurrentDensity())
        FreeCAD.ActiveDocument.commitTransaction()
        FreeCAD.ActiveDocument.recompute()


# ======================================================================
#  THERMAL commands
# ======================================================================

class _CmdThermalMaterial:
    def GetResources(self):
        return {
            "Pixmap": _icon("FlowStudioThermalMaterial.svg"),
            "MenuText": translate("FlowStudio", "Thermal Material"),
            "ToolTip": translate("FlowStudio",
                                 "Define thermal material properties"),
        }

    def IsActive(self):
        return _get_active_analysis() is not None

    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction("Add Thermal Material")
        from flow_studio.ObjectsFlowStudio import makeThermalMaterial
        _add_to_analysis(makeThermalMaterial())
        FreeCAD.ActiveDocument.commitTransaction()
        FreeCAD.ActiveDocument.recompute()


class _CmdThermalPhysics:
    def GetResources(self):
        return {
            "Pixmap": _icon("FlowStudioThermalPhysics.svg"),
            "MenuText": translate("FlowStudio", "Thermal Physics"),
            "ToolTip": translate("FlowStudio",
                                 "Configure heat transfer settings"),
        }

    def IsActive(self):
        return _get_active_analysis() is not None

    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction("Add Thermal Physics")
        from flow_studio.ObjectsFlowStudio import makeThermalPhysicsModel
        _add_to_analysis(makeThermalPhysicsModel())
        FreeCAD.ActiveDocument.commitTransaction()
        FreeCAD.ActiveDocument.recompute()


class _CmdBCTemperature:
    def GetResources(self):
        return {
            "Pixmap": _icon("FlowStudioTemperature.svg"),
            "MenuText": translate("FlowStudio", "Temperature"),
            "ToolTip": translate("FlowStudio",
                                 "Prescribe fixed temperature on boundary\n"
                                 "Requires: Analysis + Physics Model"),
        }

    def IsActive(self):
        return has_analysis() and has_physics_model()

    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction("Add Temperature BC")
        from flow_studio.ObjectsFlowStudio import makeBCTemperature
        _add_to_analysis(makeBCTemperature())
        FreeCAD.ActiveDocument.commitTransaction()
        FreeCAD.ActiveDocument.recompute()


class _CmdBCHeatFlux:
    def GetResources(self):
        return {
            "Pixmap": _icon("FlowStudioHeatFlux.svg"),
            "MenuText": translate("FlowStudio", "Heat Flux"),
            "ToolTip": translate("FlowStudio",
                                 "Apply heat flux on boundary\n"
                                 "Requires: Analysis + Physics Model"),
        }

    def IsActive(self):
        return has_analysis() and has_physics_model()

    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction("Add Heat Flux BC")
        from flow_studio.ObjectsFlowStudio import makeBCHeatFlux
        _add_to_analysis(makeBCHeatFlux())
        FreeCAD.ActiveDocument.commitTransaction()
        FreeCAD.ActiveDocument.recompute()


class _CmdBCConvection:
    def GetResources(self):
        return {
            "Pixmap": _icon("FlowStudioConvection.svg"),
            "MenuText": translate("FlowStudio", "Convection"),
            "ToolTip": translate("FlowStudio",
                                 "Apply convective heat transfer BC\n"
                                 "Requires: Analysis + Physics Model"),
        }

    def IsActive(self):
        return has_analysis() and has_physics_model()

    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction("Add Convection BC")
        from flow_studio.ObjectsFlowStudio import makeBCConvection
        _add_to_analysis(makeBCConvection())
        FreeCAD.ActiveDocument.commitTransaction()
        FreeCAD.ActiveDocument.recompute()


class _CmdBCRadiation:
    def GetResources(self):
        return {
            "Pixmap": _icon("FlowStudioRadiation.svg"),
            "MenuText": translate("FlowStudio", "Radiation"),
            "ToolTip": translate("FlowStudio",
                                 "Apply surface radiation BC\n"
                                 "Requires: Analysis + Physics Model"),
        }

    def IsActive(self):
        return has_analysis() and has_physics_model()

    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction("Add Radiation BC")
        from flow_studio.ObjectsFlowStudio import makeBCRadiation
        _add_to_analysis(makeBCRadiation())
        FreeCAD.ActiveDocument.commitTransaction()
        FreeCAD.ActiveDocument.recompute()


# ======================================================================
#  POST-PROCESSING commands
# ======================================================================

class _CmdPostPipeline:
    def GetResources(self):
        return {
            "Pixmap": _icon("FlowStudioPost.svg"),
            "MenuText": translate("FlowStudio", "Post Pipeline"),
            "ToolTip": translate(
                "FlowStudio",
                "Create post-processing pipeline for result visualization"
            ),
        }

    def IsActive(self):
        return _get_active_analysis() is not None

    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction("Add Post Pipeline")
        from flow_studio.ObjectsFlowStudio import makePostPipeline
        obj = makePostPipeline()
        _add_to_analysis(obj)
        FreeCAD.ActiveDocument.commitTransaction()
        FreeCAD.ActiveDocument.recompute()


class _CmdPostContour:
    def GetResources(self):
        return {
            "Pixmap": _icon("FlowStudioPostContour.svg"),
            "MenuText": translate("FlowStudio", "Contour Plot"),
            "ToolTip": translate(
                "FlowStudio",
                "Create a contour plot on surfaces or cut planes"
            ),
        }

    def IsActive(self):
        return _get_active_analysis() is not None

    def Activated(self):
        FreeCAD.Console.PrintMessage(
            "FlowStudio: Contour plot filter – select a Post Pipeline first.\n"
        )


class _CmdPostStreamlines:
    def GetResources(self):
        return {
            "Pixmap": _icon("FlowStudioPostStreamlines.svg"),
            "MenuText": translate("FlowStudio", "Streamlines"),
            "ToolTip": translate(
                "FlowStudio",
                "Visualize flow using streamlines"
            ),
        }

    def IsActive(self):
        return _get_active_analysis() is not None

    def Activated(self):
        FreeCAD.Console.PrintMessage(
            "FlowStudio: Streamlines filter – select a Post Pipeline first.\n"
        )


class _CmdPostProbe:
    def GetResources(self):
        return {
            "Pixmap": _icon("FlowStudioPostProbe.svg"),
            "MenuText": translate("FlowStudio", "Point Probe"),
            "ToolTip": translate(
                "FlowStudio",
                "Probe field values at a specific point"
            ),
        }

    def IsActive(self):
        return _get_active_analysis() is not None

    def Activated(self):
        FreeCAD.Console.PrintMessage(
            "FlowStudio: Point probe – pick a location.\n"
        )


class _CmdPostForceReport:
    def GetResources(self):
        return {
            "Pixmap": _icon("FlowStudioPostForce.svg"),
            "MenuText": translate("FlowStudio", "Force Report"),
            "ToolTip": translate(
                "FlowStudio",
                "Compute drag, lift, moment on selected surfaces"
            ),
        }

    def IsActive(self):
        return _get_active_analysis() is not None

    def Activated(self):
        FreeCAD.Console.PrintMessage(
            "FlowStudio: Force report – select surfaces.\n"
        )


# ======================================================================
#  MEASUREMENT DEFINITION commands (Paraview script targets)
# ======================================================================

class _CmdMeasurementPoint:
    """Add a point or line probe for Paraview evaluation."""

    def GetResources(self):
        return {
            "Pixmap": _icon("FlowStudioPostProbe.svg"),
            "MenuText": translate("FlowStudio", "Measurement Point / Line"),
            "ToolTip": translate(
                "FlowStudio",
                "Add a point probe or line probe for field sampling.\n"
                "Used to generate Paraview evaluation scripts."
            ),
        }

    def IsActive(self):
        return has_analysis()

    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction("Add Measurement Point")
        from flow_studio.ObjectsFlowStudio import makeMeasurementPoint
        obj = makeMeasurementPoint()
        _add_to_analysis(obj)
        FreeCAD.ActiveDocument.commitTransaction()
        FreeCAD.ActiveDocument.recompute()


class _CmdMeasurementSurface:
    """Add a surface measurement (cut-plane, iso-surface, clip) for Paraview."""

    def GetResources(self):
        return {
            "Pixmap": _icon("FlowStudioPostContour.svg"),
            "MenuText": translate("FlowStudio", "Measurement Surface"),
            "ToolTip": translate(
                "FlowStudio",
                "Add a cut-plane, iso-surface, or face-based measurement.\n"
                "Computes averages, integrals, mass-flow, forces.\n"
                "Used to generate Paraview evaluation scripts."
            ),
        }

    def IsActive(self):
        return has_analysis()

    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction("Add Measurement Surface")
        from flow_studio.ObjectsFlowStudio import makeMeasurementSurface
        obj = makeMeasurementSurface()
        _add_to_analysis(obj)
        FreeCAD.ActiveDocument.commitTransaction()
        FreeCAD.ActiveDocument.recompute()


class _CmdMeasurementVolume:
    """Add a volume measurement region for Paraview."""

    def GetResources(self):
        return {
            "Pixmap": _icon("FlowStudioPost.svg"),
            "MenuText": translate("FlowStudio", "Measurement Volume"),
            "ToolTip": translate(
                "FlowStudio",
                "Add a box, sphere, cylinder, or threshold-based\n"
                "volume region for field statistics.\n"
                "Used to generate Paraview evaluation scripts."
            ),
        }

    def IsActive(self):
        return has_analysis()

    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction("Add Measurement Volume")
        from flow_studio.ObjectsFlowStudio import makeMeasurementVolume
        obj = makeMeasurementVolume()
        _add_to_analysis(obj)
        FreeCAD.ActiveDocument.commitTransaction()
        FreeCAD.ActiveDocument.recompute()


class _CmdGenerateParaviewScript:
    """Generate a Paraview Python evaluation script from all measurement objects."""

    def GetResources(self):
        return {
            "Pixmap": _icon("FlowStudioPost.svg"),
            "MenuText": translate("FlowStudio", "Generate Paraview Script"),
            "Accel": "C, P",
            "ToolTip": translate(
                "FlowStudio",
                "Generate a pvpython script that evaluates all\n"
                "measurement points, surfaces, and volumes.\n"
                "Run with: pvpython evaluate.py"
            ),
        }

    def IsActive(self):
        return has_analysis()

    def Activated(self):
        analysis = _get_active_analysis()
        if analysis is None:
            return

        from flow_studio.utils.paraview_script import ParaviewScriptBuilder
        builder = ParaviewScriptBuilder(analysis)

        if not builder.has_measurements():
            FreeCAD.Console.PrintWarning(
                "FlowStudio: No measurement objects found in the analysis.\n"
                "  Add Measurement Point / Surface / Volume first.\n"
            )
            if FreeCAD.GuiUp:
                from PySide import QtWidgets
                QtWidgets.QMessageBox.information(
                    None,
                    translate("FlowStudio", "No Measurements"),
                    translate("FlowStudio",
                              "No measurement objects found.\n\n"
                              "Add at least one Measurement Point, Surface, or "
                              "Volume before generating the Paraview script."),
                )
            return

        # Ask user where to save (or use CaseDir)
        case_dir = getattr(analysis, "CaseDir", "")
        if FreeCAD.GuiUp and not case_dir:
            from PySide import QtWidgets
            case_dir = QtWidgets.QFileDialog.getExistingDirectory(
                None,
                translate("FlowStudio", "Select output directory for Paraview script"),
                os.path.expanduser("~"),
            )
            if not case_dir:
                return

        path = builder.write("evaluate.py", directory=case_dir or None)

        # Show the generated script path
        FreeCAD.Console.PrintMessage(
            f"FlowStudio: ✅ Paraview script generated:\n  {path}\n"
            f"  Run with: pvpython \"{path}\"\n"
        )
        if FreeCAD.GuiUp:
            from PySide import QtWidgets
            QtWidgets.QMessageBox.information(
                None,
                translate("FlowStudio", "Paraview Script Generated"),
                translate("FlowStudio",
                          f"Script saved to:\n{path}\n\n"
                          f"Run with:\n  pvpython \"{path}\""),
            )


# ======================================================================
#  WORKFLOW GUIDE command
# ======================================================================

class _CmdWorkflowGuide:
    """Show the step-by-step simulation workflow guide panel.

    Displays a checklist of the 9 workflow steps with completion status,
    descriptions, and hints for what to do next.  Modelled after CfdOF's
    structured workflow approach.
    """

    def GetResources(self):
        return {
            "Pixmap": _icon("FlowStudioWorkflow.svg"),
            "MenuText": translate("FlowStudio", "Workflow Guide"),
            "Accel": "C, W",
            "ToolTip": translate(
                "FlowStudio",
                "Show step-by-step simulation workflow checklist"
            ),
        }

    def IsActive(self):
        return FreeCAD.ActiveDocument is not None

    def Activated(self):
        from flow_studio.workflow_guide import get_workflow_status
        steps = get_workflow_status()

        # Print a formatted workflow status report to the console
        FreeCAD.Console.PrintMessage(
            "\n"
            "╔══════════════════════════════════════════════════════════╗\n"
            "║          FlowStudio — Simulation Workflow Guide         ║\n"
            "╚══════════════════════════════════════════════════════════╝\n\n"
        )

        next_step = None
        for step in steps:
            if step.complete:
                mark = "  ✅"
            elif step.active:
                mark = "  🔲"
                if next_step is None:
                    next_step = step
            else:
                mark = "  ⬜"

            FreeCAD.Console.PrintMessage(
                f"{mark}  Step {step.number}: {step.name}\n"
            )
            FreeCAD.Console.PrintMessage(
                f"        {step.description}\n"
            )
            if step.hint:
                FreeCAD.Console.PrintMessage(
                    f"        → {step.hint}\n"
                )
            FreeCAD.Console.PrintMessage("\n")

        if next_step:
            FreeCAD.Console.PrintMessage(
                f"► NEXT ACTION: Step {next_step.number} – {next_step.name}\n"
                f"  {next_step.hint}\n\n"
            )
        else:
            all_done = all(s.complete for s in steps)
            if all_done:
                FreeCAD.Console.PrintMessage(
                    "► All workflow steps complete! Review your results.\n\n"
                )
            else:
                FreeCAD.Console.PrintMessage(
                    "► Complete the unchecked steps above to proceed.\n\n"
                )

        # If FreeCAD GUI is available, also show the task panel
        if FreeCAD.GuiUp:
            try:
                panel = _WorkflowGuidePanel(steps)
                FreeCADGui.Control.showDialog(panel)
            except Exception:
                pass  # Fall back to console-only output


class _WorkflowGuidePanel:
    """Task panel displaying the workflow checklist (Qt widget)."""

    def __init__(self, steps):
        from PySide import QtWidgets, QtCore, QtGui
        self.form = QtWidgets.QWidget()
        self.form.setWindowTitle("FlowStudio Workflow Guide")
        layout = QtWidgets.QVBoxLayout(self.form)

        # Header
        header = QtWidgets.QLabel(
            "<h3>Simulation Workflow</h3>"
            "<p>Follow these steps in order for a successful simulation. "
            "Greyed-out steps require earlier steps to be completed first.</p>"
        )
        header.setWordWrap(True)
        layout.addWidget(header)

        # Steps list
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QtWidgets.QWidget()
        scroll_layout = QtWidgets.QVBoxLayout(scroll_widget)

        for step in steps:
            step_frame = QtWidgets.QFrame()
            step_frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
            step_layout = QtWidgets.QHBoxLayout(step_frame)

            # Status icon
            if step.complete:
                icon_text = "✅"
                color = "#2e7d32"
            elif step.active:
                icon_text = "🔲"
                color = "#1565c0"
            else:
                icon_text = "⬜"
                color = "#9e9e9e"

            icon_label = QtWidgets.QLabel(icon_text)
            icon_label.setFixedWidth(30)
            icon_label.setAlignment(QtCore.Qt.AlignCenter)
            step_layout.addWidget(icon_label)

            # Step info
            info_layout = QtWidgets.QVBoxLayout()
            name_label = QtWidgets.QLabel(
                f"<b style='color:{color}'>Step {step.number}: {step.name}</b>"
            )
            info_layout.addWidget(name_label)

            desc_label = QtWidgets.QLabel(step.description)
            desc_label.setWordWrap(True)
            desc_label.setStyleSheet(f"color: {'#333' if step.active else '#999'}")
            info_layout.addWidget(desc_label)

            if step.hint and not step.complete:
                hint_label = QtWidgets.QLabel(f"<i>→ {step.hint}</i>")
                hint_label.setWordWrap(True)
                hint_label.setStyleSheet("color: #e65100")
                info_layout.addWidget(hint_label)

            step_layout.addLayout(info_layout)

            # Action button for incomplete active steps
            if not step.complete and step.active and step.command_name:
                btn = QtWidgets.QPushButton("Go")
                btn.setFixedWidth(50)
                btn.setToolTip(f"Execute: {step.command_name}")
                cmd_name = step.command_name
                btn.clicked.connect(
                    lambda checked=False, c=cmd_name: self._run_command(c))
                step_layout.addWidget(btn)

            scroll_layout.addWidget(step_frame)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)

    def _run_command(self, command_name):
        """Execute a FreeCAD command by name and close the panel."""
        FreeCADGui.Control.closeDialog()
        FreeCADGui.runCommand(command_name)

    def accept(self):
        FreeCADGui.Control.closeDialog()

    def reject(self):
        FreeCADGui.Control.closeDialog()


class _CmdCheckWorkflow:
    """Run the pre-flight workflow checker and report issues."""

    def GetResources(self):
        return {
            "Pixmap": _icon("FlowStudioCheck.svg"),
            "MenuText": translate("FlowStudio", "Check Workflow"),
            "Accel": "C, K",
            "ToolTip": translate(
                "FlowStudio",
                "Validate that all prerequisites for running the solver are met"
            ),
        }

    def IsActive(self):
        return has_analysis()

    def Activated(self):
        analysis = _get_active_analysis()
        checker = WorkflowChecker(analysis)
        errors = checker.check_all()

        if not errors:
            msg = "FlowStudio: ✅ All workflow checks passed – ready to run!\n"
            FreeCAD.Console.PrintMessage(msg)
            if FreeCAD.GuiUp:
                from PySide import QtWidgets
                QtWidgets.QMessageBox.information(
                    None,
                    translate("FlowStudio", "Workflow Check"),
                    translate("FlowStudio",
                              "All checks passed. The simulation is ready to run."),
                )
        else:
            msg = "FlowStudio: ❌ Workflow check found issues:\n"
            for i, e in enumerate(errors, 1):
                msg += f"  {i}. {e}\n"
            FreeCAD.Console.PrintWarning(msg)
            if FreeCAD.GuiUp:
                from PySide import QtWidgets
                QtWidgets.QMessageBox.warning(
                    None,
                    translate("FlowStudio", "Workflow Check"),
                    translate("FlowStudio",
                              "Issues found:\n\n" + "\n".join(errors)),
                )


# ======================================================================
# Register all commands
# ======================================================================

# --- Analysis creation (one per domain) ---
FreeCADGui.addCommand("FlowStudio_Analysis", _CmdAnalysis())
FreeCADGui.addCommand("FlowStudio_StructuralAnalysis", _CmdStructuralAnalysis())
FreeCADGui.addCommand("FlowStudio_ElectrostaticAnalysis", _CmdElectrostaticAnalysis())
FreeCADGui.addCommand("FlowStudio_ElectromagneticAnalysis", _CmdElectromagneticAnalysis())
FreeCADGui.addCommand("FlowStudio_ThermalAnalysis", _CmdThermalAnalysis())

# --- CFD setup ---
FreeCADGui.addCommand("FlowStudio_PhysicsModel", _CmdPhysicsModel())
FreeCADGui.addCommand("FlowStudio_FluidMaterial", _CmdFluidMaterial())
FreeCADGui.addCommand("FlowStudio_InitialConditions", _CmdInitialConditions())

# --- CFD BCs ---
FreeCADGui.addCommand("FlowStudio_BC_Wall", _CmdBCWall())
FreeCADGui.addCommand("FlowStudio_BC_Inlet", _CmdBCInlet())
FreeCADGui.addCommand("FlowStudio_BC_Outlet", _CmdBCOutlet())
FreeCADGui.addCommand("FlowStudio_BC_OpenBoundary", _CmdBCOpenBoundary())
FreeCADGui.addCommand("FlowStudio_BC_Symmetry", _CmdBCSymmetry())

# --- Structural ---
FreeCADGui.addCommand("FlowStudio_SolidMaterial", _CmdSolidMaterial())
FreeCADGui.addCommand("FlowStudio_StructuralPhysics", _CmdStructuralPhysics())
FreeCADGui.addCommand("FlowStudio_BC_FixedDisplacement", _CmdBCFixedDisplacement())
FreeCADGui.addCommand("FlowStudio_BC_Force", _CmdBCForce())
FreeCADGui.addCommand("FlowStudio_BC_PressureLoad", _CmdBCPressureLoad())

# --- Electrostatic ---
FreeCADGui.addCommand("FlowStudio_ElectrostaticMaterial", _CmdElectrostaticMaterial())
FreeCADGui.addCommand("FlowStudio_ElectrostaticPhysics", _CmdElectrostaticPhysics())
FreeCADGui.addCommand("FlowStudio_BC_ElectricPotential", _CmdBCElectricPotential())
FreeCADGui.addCommand("FlowStudio_BC_SurfaceCharge", _CmdBCSurfaceCharge())

# --- Electromagnetic ---
FreeCADGui.addCommand("FlowStudio_ElectromagneticMaterial", _CmdElectromagneticMaterial())
FreeCADGui.addCommand("FlowStudio_ElectromagneticPhysics", _CmdElectromagneticPhysics())
FreeCADGui.addCommand("FlowStudio_BC_MagneticPotential", _CmdBCMagneticPotential())
FreeCADGui.addCommand("FlowStudio_BC_CurrentDensity", _CmdBCCurrentDensity())

# --- Thermal ---
FreeCADGui.addCommand("FlowStudio_ThermalMaterial", _CmdThermalMaterial())
FreeCADGui.addCommand("FlowStudio_ThermalPhysics", _CmdThermalPhysics())
FreeCADGui.addCommand("FlowStudio_BC_Temperature", _CmdBCTemperature())
FreeCADGui.addCommand("FlowStudio_BC_HeatFlux", _CmdBCHeatFlux())
FreeCADGui.addCommand("FlowStudio_BC_Convection", _CmdBCConvection())
FreeCADGui.addCommand("FlowStudio_BC_Radiation", _CmdBCRadiation())

# --- Mesh ---
FreeCADGui.addCommand("FlowStudio_MeshGmsh", _CmdMeshGmsh())
FreeCADGui.addCommand("FlowStudio_MeshRegion", _CmdMeshRegion())
FreeCADGui.addCommand("FlowStudio_BoundaryLayer", _CmdBoundaryLayer())

# --- Solve ---
FreeCADGui.addCommand("FlowStudio_SolverSelect", _CmdSolverSelect())
FreeCADGui.addCommand("FlowStudio_SolverSettings", _CmdSolverSettings())
FreeCADGui.addCommand("FlowStudio_RunSolver", _CmdRunSolver())

# --- Post-processing ---
FreeCADGui.addCommand("FlowStudio_PostPipeline", _CmdPostPipeline())
FreeCADGui.addCommand("FlowStudio_PostContour", _CmdPostContour())
FreeCADGui.addCommand("FlowStudio_PostStreamlines", _CmdPostStreamlines())
FreeCADGui.addCommand("FlowStudio_PostProbe", _CmdPostProbe())
FreeCADGui.addCommand("FlowStudio_PostForceReport", _CmdPostForceReport())

# --- Measurement / Paraview ---
FreeCADGui.addCommand("FlowStudio_MeasurementPoint", _CmdMeasurementPoint())
FreeCADGui.addCommand("FlowStudio_MeasurementSurface", _CmdMeasurementSurface())
FreeCADGui.addCommand("FlowStudio_MeasurementVolume", _CmdMeasurementVolume())
FreeCADGui.addCommand("FlowStudio_GenerateParaviewScript", _CmdGenerateParaviewScript())

# --- Workflow ---
FreeCADGui.addCommand("FlowStudio_WorkflowGuide", _CmdWorkflowGuide())
FreeCADGui.addCommand("FlowStudio_CheckWorkflow", _CmdCheckWorkflow())
