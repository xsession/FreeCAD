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
from datetime import datetime
import FreeCAD
import FreeCADGui

from flow_studio.enterprise import initialize_workbench
from flow_studio.enterprise.app.legacy_actions import prepare_runtime_submissions
from flow_studio.core.workflow import (
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


def _project_id():
    doc = FreeCAD.ActiveDocument
    if doc is None:
        return "flowstudio-project"
    return getattr(doc, "Name", "flowstudio-project")


def _default_output_dir(analysis):
    case_dir = getattr(analysis, "CaseDir", "")
    if case_dir:
        return case_dir
    doc = FreeCAD.ActiveDocument
    if doc is not None and hasattr(doc, "TransientDir"):
        return os.path.join(doc.TransientDir, "FlowStudio", getattr(analysis, "Name", "Analysis"))
    return os.path.join(os.path.expanduser("~"), "FlowStudio")


def _timestamp_slug():
    return datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")


def _show_warning_dialog(title, message):
    if FreeCAD.GuiUp:
        from PySide import QtWidgets

        QtWidgets.QMessageBox.warning(None, title, message)


def _show_info_dialog(title, message):
    if FreeCAD.GuiUp:
        from PySide import QtWidgets

        QtWidgets.QMessageBox.information(None, title, message)


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


def _selected_geometry_references():
    """Return current GUI selection as PropertyLinkSubList-compatible refs."""
    if not FreeCAD.GuiUp:
        return []

    refs = []
    try:
        selection = FreeCADGui.Selection.getSelectionEx()
    except Exception:
        return refs

    for item in selection:
        obj = getattr(item, "Object", None)
        if obj is None:
            continue

        flow_type = getattr(obj, "FlowType", "")
        if isinstance(flow_type, str) and flow_type.startswith("FlowStudio::"):
            continue

        sub_names = list(getattr(item, "SubElementNames", []) or [])
        refs.append((obj, sub_names))

    return refs


def _selected_geometry_objects():
    """Return selected non-FlowStudio geometry objects."""
    return [ref_obj for ref_obj, _sub_names in _selected_geometry_references()]


def _pick_primary_geometry_object():
    """Return a preferred geometry object for mesh/link workflows."""
    selected = _selected_geometry_objects()
    if selected:
        return selected[0]

    document = FreeCAD.ActiveDocument
    if document is None:
        return None

    for obj in getattr(document, "Objects", []):
        flow_type = getattr(obj, "FlowType", "")
        if isinstance(flow_type, str) and flow_type.startswith("FlowStudio::"):
            continue
        if hasattr(obj, "Shape"):
            return obj
    return None


def _assign_current_selection(obj, message_prefix="FlowStudio"):
    """Assign current part/face selection to a FlowStudio object if supported."""
    if obj is None:
        return False
    properties = getattr(obj, "PropertiesList", [])
    target_property = None
    if "References" in properties:
        target_property = "References"
    elif "FaceRefs" in properties:
        target_property = "FaceRefs"
    if target_property is None:
        return False

    refs = _selected_geometry_references()
    if not refs:
        return False

    setattr(obj, target_property, refs)
    assigned = []
    for ref_obj, sub_names in refs:
        label = getattr(ref_obj, "Label", getattr(ref_obj, "Name", "Object"))
        if sub_names:
            assigned.append(f"{label}:{','.join(sub_names)}")
        else:
            assigned.append(label)
    FreeCAD.Console.PrintMessage(
        f"{message_prefix}: assigned selection to {getattr(obj, 'Label', obj.Name)} "
        f"({'; '.join(assigned)})\n"
    )
    return True


def _open_task_panel(obj):
    """Open the object's task panel after command creation when available."""
    if not FreeCAD.GuiUp or obj is None:
        return
    try:
        FreeCADGui.ActiveDocument.setEdit(obj.Name)
    except Exception as exc:
        FreeCAD.Console.PrintLog(
            f"FlowStudio: task panel not available for {getattr(obj, 'Name', obj)} ({exc})\n"
        )


def _show_project_cockpit():
    if not FreeCAD.GuiUp:
        return
    try:
        from flow_studio.taskpanels.task_project_cockpit import ProjectCockpitPanel

        FreeCADGui.Control.showDialog(ProjectCockpitPanel())
    except Exception as exc:
        FreeCAD.Console.PrintWarning(
            f"FlowStudio: project cockpit could not be opened ({exc})\n"
        )


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


class _CmdElectronicsCoolingStudy:
    """Create a benchmark-oriented electronics cooling CFD study scaffold."""

    def GetResources(self):
        return {
            "Pixmap": _icon("FlowStudioAnalysis.svg"),
            "MenuText": translate("FlowStudio", "New Electronics Cooling Study"),
            "ToolTip": translate(
                "FlowStudio",
                "Create a conjugate heat-transfer electronics cooling study scaffold with benchmark defaults",
            ),
        }

    def IsActive(self):
        return FreeCAD.ActiveDocument is not None

    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction("Create Electronics Cooling Study")
        from flow_studio.ObjectsFlowStudio import (
            makeAnalysis,
            makePhysicsModel,
            makeFluidMaterial,
            makeSolidMaterial,
            makeInitialConditions,
            makeSolver,
            makeMeshGmsh,
            makePostPipeline,
            makeFan,
            makeVolumeSource,
            makeBCInlet,
            makeBCOutlet,
            makeBCWall,
            makeBCRadiation,
        )
        from flow_studio.workflows.studies import apply_electronics_cooling_defaults

        analysis = makeAnalysis(name="ElectronicsCoolingAnalysis")
        physics = makePhysicsModel(name="ElectronicsCoolingPhysics")
        fluid_material = makeFluidMaterial(name="CoolingAir")
        solid_material = makeSolidMaterial(name="ElectronicsSolid")
        initial_conditions = makeInitialConditions(name="CoolingInitialConditions")
        solver = makeSolver(name="ElectronicsCoolingSolver")
        mesh = makeMeshGmsh(name="ElectronicsCoolingMesh")
        post = makePostPipeline(name="ElectronicsCoolingPost")
        fan = makeFan(name="CoolingFan")
        heat_source = makeVolumeSource(name="CPUHeatSource")
        inlet = makeBCInlet(name="FanInlet")
        outlet = makeBCOutlet(name="Outlet")
        walls = makeBCWall(name="Walls")
        radiation = makeBCRadiation(name="Radiation")

        for child in (
            physics,
            fluid_material,
            solid_material,
            initial_conditions,
            solver,
            mesh,
            post,
            fan,
            heat_source,
            inlet,
            outlet,
            walls,
            radiation,
        ):
            analysis.addObject(child)

        apply_electronics_cooling_defaults(
            analysis,
            physics_model=physics,
            fluid_material=fluid_material,
            solid_material=solid_material,
            solver=solver,
            initial_conditions=initial_conditions,
            fan=fan,
            volume_source=heat_source,
            mesh=mesh,
            post_pipeline=post,
        )

        try:
            inlet.BCLabel = "fan_inlet"
            inlet.VelocityMagnitude = 0.1
            inlet.InletTemperature = 293.15
            outlet.BCLabel = "outlet"
            outlet.StaticPressure = 0.0
            walls.BCLabel = "walls"
            walls.ThermalType = "Adiabatic"
            radiation.BCLabel = "Radiation"
        except Exception:
            pass

        FreeCAD.ActiveDocument.commitTransaction()
        FreeCAD.ActiveDocument.recompute()
        _show_project_cockpit()


class _CmdCoolingChannelStudy:
    """Create a cooling-channel-focused CHT study scaffold."""

    def GetResources(self):
        return {
            "Pixmap": _icon("FlowStudioAnalysis.svg"),
            "MenuText": translate("FlowStudio", "New Cooling Channel Study"),
            "ToolTip": translate(
                "FlowStudio",
                "Create a steady cooling-channel conjugate heat transfer starter with multi-region defaults",
            ),
        }

    def IsActive(self):
        return FreeCAD.ActiveDocument is not None

    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction("Create Cooling Channel Study")
        from flow_studio.ObjectsFlowStudio import (
            makeAnalysis,
            makePhysicsModel,
            makeFluidMaterial,
            makeSolidMaterial,
            makeInitialConditions,
            makeSolver,
            makeMeshGmsh,
            makePostPipeline,
            makeBCInlet,
            makeBCOutlet,
            makeBCWall,
            makeResultPlot,
        )
        from flow_studio.workflows.studies import apply_cooling_channel_defaults

        analysis = makeAnalysis(name="CoolingChannelAnalysis")
        physics = makePhysicsModel(name="CoolingChannelPhysics")
        fluid_material = makeFluidMaterial(name="CoolingChannelFluid")
        solid_material = makeSolidMaterial(name="CoolingChannelSolid")
        initial_conditions = makeInitialConditions(name="CoolingChannelInitialConditions")
        solver = makeSolver(name="CoolingChannelSolver")
        mesh = makeMeshGmsh(name="CoolingChannelMesh")
        post = makePostPipeline(name="CoolingChannelPost")
        inlet = makeBCInlet(name="CoolingChannelInlet")
        outlet = makeBCOutlet(name="CoolingChannelOutlet")
        walls = makeBCWall(name="CoolingChannelWalls")
        result_plot = makeResultPlot(name="CoolingChannelTemperaturePlot", plot_kind="Cut Plot")

        for child in (
            physics,
            fluid_material,
            solid_material,
            initial_conditions,
            solver,
            mesh,
            post,
            inlet,
            outlet,
            walls,
            result_plot,
        ):
            analysis.addObject(child)

        apply_cooling_channel_defaults(
            analysis,
            physics_model=physics,
            fluid_material=fluid_material,
            solid_material=solid_material,
            solver=solver,
            initial_conditions=initial_conditions,
            mesh=mesh,
            inlet_bc=inlet,
            outlet_bc=outlet,
            wall_bc=walls,
            post_pipeline=post,
            result_plot=result_plot,
        )

        try:
            inlet.InletType = "Velocity"
            outlet.OutletType = "Static Pressure"
        except Exception:
            pass

        FreeCAD.ActiveDocument.commitTransaction()
        FreeCAD.ActiveDocument.recompute()
        _show_project_cockpit()


class _CmdExternalAeroStudy:
    """Create a reusable external-aerodynamics CFD study scaffold."""

    def GetResources(self):
        return {
            "Pixmap": _icon("FlowStudioAnalysis.svg"),
            "MenuText": translate("FlowStudio", "New External Aero Study"),
            "ToolTip": translate(
                "FlowStudio",
                "Create a generic external aerodynamics CFD study scaffold for wing, car, or building cases",
            ),
        }

    def IsActive(self):
        return FreeCAD.ActiveDocument is not None

    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction("Create External Aero Study")
        from flow_studio.ObjectsFlowStudio import (
            makeAnalysis,
            makePhysicsModel,
            makeFluidMaterial,
            makeInitialConditions,
            makeSolver,
            makeMeshGmsh,
            makePostPipeline,
            makeBCInlet,
            makeBCOutlet,
            makeBCWall,
            makeBCSymmetry,
        )
        from flow_studio.workflows.studies import apply_external_aero_defaults

        analysis = makeAnalysis(name="ExternalAeroAnalysis")
        physics = makePhysicsModel(name="ExternalAeroPhysics")
        fluid_material = makeFluidMaterial(name="ExternalAeroAir")
        initial_conditions = makeInitialConditions(name="ExternalAeroInitialConditions")
        solver = makeSolver(name="ExternalAeroSolver")
        mesh = makeMeshGmsh(name="ExternalAeroMesh")
        post = makePostPipeline(name="ExternalAeroPost")
        inlet = makeBCInlet(name="FarFieldInlet")
        outlet = makeBCOutlet(name="FarFieldOutlet")
        ground = makeBCWall(name="GroundWall")
        symmetry = makeBCSymmetry(name="FarFieldSymmetry")

        for child in (
            physics,
            fluid_material,
            initial_conditions,
            solver,
            mesh,
            post,
            inlet,
            outlet,
            ground,
            symmetry,
        ):
            analysis.addObject(child)

        apply_external_aero_defaults(
            analysis,
            physics_model=physics,
            fluid_material=fluid_material,
            solver=solver,
            initial_conditions=initial_conditions,
            mesh=mesh,
            post_pipeline=post,
        )

        try:
            inlet.BCLabel = "inlet"
            inlet.VelocityMagnitude = 20.0
            outlet.BCLabel = "outlet"
            outlet.StaticPressure = 0.0
            ground.BCLabel = "ground"
            ground.WallType = "Moving Wall"
            symmetry.BCLabel = "symmetry"
        except Exception:
            pass

        FreeCAD.ActiveDocument.commitTransaction()
        FreeCAD.ActiveDocument.recompute()
        _show_project_cockpit()


class _CmdBuildingsStudy:
    """Create a buildings-focused external-flow CFD study scaffold."""

    def GetResources(self):
        return {
            "Pixmap": _icon("FlowStudioAnalysis.svg"),
            "MenuText": translate("FlowStudio", "New Buildings Wind Study"),
            "ToolTip": translate(
                "FlowStudio",
                "Create a wind-around-buildings external-flow starter with atmospheric-style defaults and a primary wake plot",
            ),
        }

    def IsActive(self):
        return FreeCAD.ActiveDocument is not None

    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction("Create Buildings Wind Study")
        from flow_studio.ObjectsFlowStudio import (
            makeAnalysis,
            makePhysicsModel,
            makeFluidMaterial,
            makeInitialConditions,
            makeSolver,
            makeMeshGmsh,
            makePostPipeline,
            makeBCInlet,
            makeBCOutlet,
            makeBCWall,
            makeBCSymmetry,
            makeResultPlot,
        )
        from flow_studio.workflows.studies import apply_buildings_defaults

        analysis = makeAnalysis(name="BuildingsWindAnalysis")
        physics = makePhysicsModel(name="BuildingsWindPhysics")
        fluid_material = makeFluidMaterial(name="BuildingsAir")
        initial_conditions = makeInitialConditions(name="BuildingsInitialConditions")
        solver = makeSolver(name="BuildingsWindSolver")
        mesh = makeMeshGmsh(name="BuildingsWindMesh")
        post = makePostPipeline(name="BuildingsWindPost")
        inlet = makeBCInlet(name="AtmosphericInlet")
        outlet = makeBCOutlet(name="BuildingsOutlet")
        ground = makeBCWall(name="UrbanGround")
        symmetry = makeBCSymmetry(name="FarFieldSymmetry")
        result_plot = makeResultPlot(name="BuildingsWindPlot", plot_kind="Cut Plot")

        for child in (
            physics,
            fluid_material,
            initial_conditions,
            solver,
            mesh,
            post,
            inlet,
            outlet,
            ground,
            symmetry,
            result_plot,
        ):
            analysis.addObject(child)

        apply_buildings_defaults(
            analysis,
            physics_model=physics,
            fluid_material=fluid_material,
            solver=solver,
            initial_conditions=initial_conditions,
            mesh=mesh,
            post_pipeline=post,
            result_plot=result_plot,
        )

        try:
            inlet.BCLabel = "atmospheric_inlet"
            inlet.InletType = "Velocity"
            inlet.VelocityMagnitude = 8.0
            outlet.BCLabel = "outlet"
            outlet.OutletType = "Static Pressure"
            outlet.StaticPressure = 0.0
            ground.BCLabel = "ground"
            ground.WallType = "Stationary Wall"
            symmetry.BCLabel = "symmetry"
        except Exception:
            pass

        FreeCAD.ActiveDocument.commitTransaction()
        FreeCAD.ActiveDocument.recompute()
        _show_project_cockpit()


class _CmdAirfoilStudy:
    """Create an airfoil-focused external-flow CFD study scaffold."""

    def GetResources(self):
        return {
            "Pixmap": _icon("FlowStudioAnalysis.svg"),
            "MenuText": translate("FlowStudio", "New Airfoil Study"),
            "ToolTip": translate(
                "FlowStudio",
                "Create a NACA-style airfoil external-flow starter with pressure-coefficient-focused defaults",
            ),
        }

    def IsActive(self):
        return FreeCAD.ActiveDocument is not None

    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction("Create Airfoil Study")
        from flow_studio.ObjectsFlowStudio import (
            makeAnalysis,
            makePhysicsModel,
            makeFluidMaterial,
            makeInitialConditions,
            makeSolver,
            makeMeshGmsh,
            makePostPipeline,
            makeBCInlet,
            makeBCOutlet,
            makeBCWall,
            makeBCSymmetry,
            makeResultPlot,
        )
        from flow_studio.workflows.studies import apply_airfoil_defaults

        analysis = makeAnalysis(name="AirfoilAnalysis")
        physics = makePhysicsModel(name="AirfoilPhysics")
        fluid_material = makeFluidMaterial(name="AirfoilAir")
        initial_conditions = makeInitialConditions(name="AirfoilInitialConditions")
        solver = makeSolver(name="AirfoilSolver")
        mesh = makeMeshGmsh(name="AirfoilMesh")
        post = makePostPipeline(name="AirfoilPost")
        inlet = makeBCInlet(name="AirfoilInlet")
        outlet = makeBCOutlet(name="AirfoilOutlet")
        airfoil_wall = makeBCWall(name="AirfoilWall")
        symmetry = makeBCSymmetry(name="FarFieldSymmetry")
        result_plot = makeResultPlot(name="AirfoilCpPlot", plot_kind="Surface Plot")

        for child in (
            physics,
            fluid_material,
            initial_conditions,
            solver,
            mesh,
            post,
            inlet,
            outlet,
            airfoil_wall,
            symmetry,
            result_plot,
        ):
            analysis.addObject(child)

        apply_airfoil_defaults(
            analysis,
            physics_model=physics,
            fluid_material=fluid_material,
            solver=solver,
            initial_conditions=initial_conditions,
            mesh=mesh,
            post_pipeline=post,
            result_plot=result_plot,
        )

        try:
            inlet.BCLabel = "inlet"
            inlet.InletType = "Velocity"
            inlet.VelocityMagnitude = 30.0
            outlet.BCLabel = "outlet"
            outlet.OutletType = "Static Pressure"
            outlet.StaticPressure = 0.0
            airfoil_wall.BCLabel = "airfoil"
            airfoil_wall.WallType = "Stationary Wall"
            symmetry.BCLabel = "symmetry"
        except Exception:
            pass

        FreeCAD.ActiveDocument.commitTransaction()
        FreeCAD.ActiveDocument.recompute()
        _show_project_cockpit()


class _CmdTeslaValveStudy:
    """Create a Tesla-valve-focused internal-flow CFD study scaffold."""

    def GetResources(self):
        return {
            "Pixmap": _icon("FlowStudioAnalysis.svg"),
            "MenuText": translate("FlowStudio", "New Tesla Valve Study"),
            "ToolTip": translate(
                "FlowStudio",
                "Create a Tesla valve internal-flow starter with pressure-drop-focused defaults and a primary pressure plot",
            ),
        }

    def IsActive(self):
        return FreeCAD.ActiveDocument is not None

    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction("Create Tesla Valve Study")
        from flow_studio.ObjectsFlowStudio import (
            makeAnalysis,
            makePhysicsModel,
            makeFluidMaterial,
            makeInitialConditions,
            makeSolver,
            makeMeshGmsh,
            makePostPipeline,
            makeBCInlet,
            makeBCOutlet,
            makeBCWall,
            makeResultPlot,
        )
        from flow_studio.workflows.studies import apply_tesla_valve_defaults

        analysis = makeAnalysis(name="TeslaValveAnalysis")
        physics = makePhysicsModel(name="TeslaValvePhysics")
        fluid_material = makeFluidMaterial(name="TeslaValveFluid")
        initial_conditions = makeInitialConditions(name="TeslaValveInitialConditions")
        solver = makeSolver(name="TeslaValveSolver")
        mesh = makeMeshGmsh(name="TeslaValveMesh")
        post = makePostPipeline(name="TeslaValvePost")
        inlet = makeBCInlet(name="TeslaValveInlet")
        outlet = makeBCOutlet(name="TeslaValveOutlet")
        walls = makeBCWall(name="TeslaValveWalls")
        result_plot = makeResultPlot(name="TeslaValvePressurePlot", plot_kind="Cut Plot")

        for child in (
            physics,
            fluid_material,
            initial_conditions,
            solver,
            mesh,
            post,
            inlet,
            outlet,
            walls,
            result_plot,
        ):
            analysis.addObject(child)

        apply_tesla_valve_defaults(
            analysis,
            physics_model=physics,
            fluid_material=fluid_material,
            solver=solver,
            initial_conditions=initial_conditions,
            mesh=mesh,
            post_pipeline=post,
            result_plot=result_plot,
        )

        try:
            inlet.BCLabel = "forward_inlet"
            inlet.InletType = "Velocity"
            inlet.VelocityMagnitude = 1.5
            outlet.BCLabel = "outlet"
            outlet.OutletType = "Static Pressure"
            outlet.StaticPressure = 0.0
            walls.BCLabel = "walls"
            walls.ThermalType = "Adiabatic"
        except Exception:
            pass

        FreeCAD.ActiveDocument.commitTransaction()
        FreeCAD.ActiveDocument.recompute()
        _show_project_cockpit()


class _CmdVonKarmanStudy:
    """Create a Von-Karman-focused transient validation CFD study scaffold."""

    def GetResources(self):
        return {
            "Pixmap": _icon("FlowStudioAnalysis.svg"),
            "MenuText": translate("FlowStudio", "New Von Karman Study"),
            "ToolTip": translate(
                "FlowStudio",
                "Create a transient Von Karman validation starter with vorticity-focused defaults and a primary wake plot",
            ),
        }

    def IsActive(self):
        return FreeCAD.ActiveDocument is not None

    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction("Create Von Karman Study")
        from flow_studio.ObjectsFlowStudio import (
            makeAnalysis,
            makePhysicsModel,
            makeFluidMaterial,
            makeInitialConditions,
            makeSolver,
            makeMeshGmsh,
            makePostPipeline,
            makeBCInlet,
            makeBCOutlet,
            makeBCWall,
            makeBCSymmetry,
            makeResultPlot,
        )
        from flow_studio.workflows.studies import apply_von_karman_defaults

        analysis = makeAnalysis(name="VonKarmanAnalysis")
        physics = makePhysicsModel(name="VonKarmanPhysics")
        fluid_material = makeFluidMaterial(name="VonKarmanAir")
        initial_conditions = makeInitialConditions(name="VonKarmanInitialConditions")
        solver = makeSolver(name="VonKarmanSolver")
        mesh = makeMeshGmsh(name="VonKarmanMesh")
        post = makePostPipeline(name="VonKarmanPost")
        inlet = makeBCInlet(name="VonKarmanInlet")
        outlet = makeBCOutlet(name="VonKarmanOutlet")
        body_wall = makeBCWall(name="CylinderWall")
        symmetry = makeBCSymmetry(name="FarFieldSymmetry")
        result_plot = makeResultPlot(name="VonKarmanVorticityPlot", plot_kind="Cut Plot")

        for child in (
            physics,
            fluid_material,
            initial_conditions,
            solver,
            mesh,
            post,
            inlet,
            outlet,
            body_wall,
            symmetry,
            result_plot,
        ):
            analysis.addObject(child)

        apply_von_karman_defaults(
            analysis,
            physics_model=physics,
            fluid_material=fluid_material,
            solver=solver,
            initial_conditions=initial_conditions,
            mesh=mesh,
            post_pipeline=post,
            result_plot=result_plot,
        )

        try:
            inlet.BCLabel = "inlet"
            inlet.InletType = "Velocity"
            inlet.VelocityMagnitude = 2.0
            outlet.BCLabel = "outlet"
            outlet.OutletType = "Static Pressure"
            outlet.StaticPressure = 0.0
            body_wall.BCLabel = "cylinder"
            body_wall.WallType = "Stationary Wall"
            symmetry.BCLabel = "symmetry"
        except Exception:
            pass

        FreeCAD.ActiveDocument.commitTransaction()
        FreeCAD.ActiveDocument.recompute()
        _show_project_cockpit()


class _CmdPipeFlowStudy:
    """Create a reusable internal pipe-flow CFD study scaffold."""

    def GetResources(self):
        return {
            "Pixmap": _icon("FlowStudioAnalysis.svg"),
            "MenuText": translate("FlowStudio", "New Pipe Flow Study"),
            "ToolTip": translate(
                "FlowStudio",
                "Create a generic internal pipe-flow CFD study scaffold with mixed inlet conditions",
            ),
        }

    def IsActive(self):
        return FreeCAD.ActiveDocument is not None

    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction("Create Pipe Flow Study")
        from flow_studio.ObjectsFlowStudio import (
            makeAnalysis,
            makePhysicsModel,
            makeFluidMaterial,
            makeInitialConditions,
            makeSolver,
            makeMeshGmsh,
            makePostPipeline,
            makeBCInlet,
            makeBCOutlet,
            makeBCWall,
        )
        from flow_studio.workflows.studies import apply_pipe_flow_defaults

        analysis = makeAnalysis(name="PipeFlowAnalysis")
        physics = makePhysicsModel(name="PipeFlowPhysics")
        fluid_material = makeFluidMaterial(name="PipeFlowFluid")
        initial_conditions = makeInitialConditions(name="PipeFlowInitialConditions")
        solver = makeSolver(name="PipeFlowSolver")
        mesh = makeMeshGmsh(name="PipeFlowMesh")
        post = makePostPipeline(name="PipeFlowPost")
        inlet_velocity = makeBCInlet(name="VelocityInlet")
        inlet_pressure = makeBCInlet(name="PressureInlet")
        outlet = makeBCOutlet(name="PipeOutlet")
        walls = makeBCWall(name="PipeWalls")

        for child in (
            physics,
            fluid_material,
            initial_conditions,
            solver,
            mesh,
            post,
            inlet_velocity,
            inlet_pressure,
            outlet,
            walls,
        ):
            analysis.addObject(child)

        apply_pipe_flow_defaults(
            analysis,
            physics_model=physics,
            fluid_material=fluid_material,
            solver=solver,
            initial_conditions=initial_conditions,
            mesh=mesh,
            post_pipeline=post,
        )

        try:
            inlet_velocity.BCLabel = "inlet1"
            inlet_velocity.InletType = "Velocity"
            inlet_velocity.VelocityMagnitude = 1.0
            inlet_velocity.NormalToFace = True
            inlet_pressure.BCLabel = "inlet2"
            inlet_pressure.InletType = "Total Pressure"
            inlet_pressure.TotalPressure = 100.0
            outlet.BCLabel = "outlet"
            outlet.OutletType = "Static Pressure"
            outlet.StaticPressure = 0.0
            walls.BCLabel = "walls"
            walls.ThermalType = "Adiabatic"
        except Exception:
            pass

        FreeCAD.ActiveDocument.commitTransaction()
        FreeCAD.ActiveDocument.recompute()
        _show_project_cockpit()


class _CmdStaticMixerStudy:
    """Create a reusable static-mixer passive-scalar CFD study scaffold."""

    def GetResources(self):
        return {
            "Pixmap": _icon("FlowStudioAnalysis.svg"),
            "MenuText": translate("FlowStudio", "New Static Mixer Study"),
            "ToolTip": translate(
                "FlowStudio",
                "Create a transient passive-scalar static mixer scaffold with split inlets and scalar-focused post setup",
            ),
        }

    def IsActive(self):
        return FreeCAD.ActiveDocument is not None

    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction("Create Static Mixer Study")
        from flow_studio.ObjectsFlowStudio import (
            makeAnalysis,
            makePhysicsModel,
            makeFluidMaterial,
            makeInitialConditions,
            makeSolver,
            makeMeshGmsh,
            makePostPipeline,
            makeBCInlet,
            makeBCOutlet,
            makeBCWall,
            makeResultPlot,
        )
        from flow_studio.workflows.studies import apply_static_mixer_defaults

        analysis = makeAnalysis(name="StaticMixerAnalysis")
        physics = makePhysicsModel(name="StaticMixerPhysics")
        fluid_material = makeFluidMaterial(name="StaticMixerFluid")
        initial_conditions = makeInitialConditions(name="StaticMixerInitialConditions")
        solver = makeSolver(name="StaticMixerSolver")
        mesh = makeMeshGmsh(name="StaticMixerMesh")
        post = makePostPipeline(name="StaticMixerPost")
        inlet_scalar0 = makeBCInlet(name="Scalar0Inlet")
        inlet_scalar1 = makeBCInlet(name="Scalar1Inlet")
        outlet = makeBCOutlet(name="MixerOutlet")
        walls = makeBCWall(name="MixerWalls")
        result_plot = makeResultPlot(name="PassiveScalarCut", plot_kind="Cut Plot")

        for child in (
            physics,
            fluid_material,
            initial_conditions,
            solver,
            mesh,
            post,
            inlet_scalar0,
            inlet_scalar1,
            outlet,
            walls,
            result_plot,
        ):
            analysis.addObject(child)

        apply_static_mixer_defaults(
            analysis,
            physics_model=physics,
            fluid_material=fluid_material,
            solver=solver,
            initial_conditions=initial_conditions,
            mesh=mesh,
            post_pipeline=post,
        )

        try:
            inlet_scalar0.BCLabel = "scalar0_inlet"
            inlet_scalar0.InletType = "Velocity"
            inlet_scalar0.VelocityMagnitude = 0.8
            inlet_scalar1.BCLabel = "scalar1_inlet"
            inlet_scalar1.InletType = "Velocity"
            inlet_scalar1.VelocityMagnitude = 0.8
            outlet.BCLabel = "outlet"
            outlet.OutletType = "Static Pressure"
            outlet.StaticPressure = 0.0
            walls.BCLabel = "walls"
            walls.ThermalType = "Adiabatic"
            result_plot.Field = "Passive Scalar"
            result_plot.Streamlines = True
            result_plot.CutPlane = "YZ Plane"
        except Exception:
            pass

        FreeCAD.ActiveDocument.commitTransaction()
        FreeCAD.ActiveDocument.recompute()
        _show_project_cockpit()


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


class _CmdOpticalAnalysis:
    """Create a new Optical / Photonics analysis."""

    def GetResources(self):
        return {
            "Pixmap": _icon("FlowStudioElectromagnetic.svg"),
            "MenuText": translate("FlowStudio", "New Optical Analysis"),
            "ToolTip": translate(
                "FlowStudio",
                "Create an optical / photonics analysis for ray tracing, illumination, or wave optics",
            ),
        }

    def IsActive(self):
        return FreeCAD.ActiveDocument is not None

    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction("Create Optical Analysis")
        from flow_studio.ObjectsFlowStudio import (
            makeDomainAnalysis, makeOpticalPhysicsModel,
            makeOpticalMaterial, makeSolver,
        )
        analysis = makeDomainAnalysis(name="OpticalAnalysis", domain_key="Optical")
        for maker in (makeOpticalPhysicsModel, makeOpticalMaterial, makeSolver):
            child = maker()
            if getattr(child, "FlowType", "") == "FlowStudio::Solver":
                try:
                    child.SolverBackend = "Raysect"
                except Exception:
                    pass
            analysis.addObject(child)
        FreeCAD.ActiveDocument.commitTransaction()
        FreeCAD.ActiveDocument.recompute()


class _CmdStructuralBracketExample:
    """Create a structural bracket starter example."""

    def GetResources(self):
        return {
            "Pixmap": _icon("FlowStudioStructural.svg"),
            "MenuText": translate("FlowStudio", "Structural Bracket Example"),
            "ToolTip": translate(
                "FlowStudio",
                "Create a structural bracket example with aluminum material, a fixed support, and a tip load",
            ),
        }

    def IsActive(self):
        return FreeCAD.ActiveDocument is not None

    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction("Create Structural Bracket Example")
        from flow_studio.ObjectsFlowStudio import (
            makeDomainAnalysis,
            makeStructuralPhysicsModel,
            makeSolidMaterial,
            makeSolver,
            makeBCFixedDisplacement,
            makeBCForce,
            makePostPipeline,
            makeResultPlot,
        )
        from flow_studio.workflows.studies import apply_structural_bracket_defaults

        analysis = makeDomainAnalysis(name="StructuralBracketExample", domain_key="Structural")
        physics = makeStructuralPhysicsModel(name="BracketPhysics")
        material = makeSolidMaterial(name="BracketMaterial")
        solver = makeSolver(name="StructuralSolver")
        fixed = makeBCFixedDisplacement(name="SupportConstraint")
        force = makeBCForce(name="TipLoad")
        post = makePostPipeline(name="StructuralBracketPost")
        result_plot = makeResultPlot(name="BracketStressPlot", plot_kind="Surface Plot")

        for child in (physics, material, solver, fixed, force, post, result_plot):
            analysis.addObject(child)

        apply_structural_bracket_defaults(
            analysis,
            physics_model=physics,
            solid_material=material,
            solver=solver,
            fixed_constraint=fixed,
            force_constraint=force,
            post_pipeline=post,
            result_plot=result_plot,
        )

        FreeCAD.ActiveDocument.commitTransaction()
        FreeCAD.ActiveDocument.recompute()
        _show_project_cockpit()


class _CmdElectrostaticCapacitorExample:
    """Create a parallel-plate capacitor starter example."""

    def GetResources(self):
        return {
            "Pixmap": _icon("FlowStudioElectrostatic.svg"),
            "MenuText": translate("FlowStudio", "Electrostatic Capacitor Example"),
            "ToolTip": translate(
                "FlowStudio",
                "Create a capacitor example with dielectric material and paired voltage electrodes",
            ),
        }

    def IsActive(self):
        return FreeCAD.ActiveDocument is not None

    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction("Create Electrostatic Capacitor Example")
        from flow_studio.ObjectsFlowStudio import (
            makeDomainAnalysis,
            makeElectrostaticPhysicsModel,
            makeElectrostaticMaterial,
            makeSolver,
            makeBCElectricPotential,
            makePostPipeline,
            makeResultPlot,
        )
        from flow_studio.workflows.studies import apply_electrostatic_capacitor_defaults

        analysis = makeDomainAnalysis(name="ElectrostaticCapacitorExample", domain_key="Electrostatic")
        physics = makeElectrostaticPhysicsModel(name="CapacitorPhysics")
        material = makeElectrostaticMaterial(name="DielectricMaterial")
        solver = makeSolver(name="ElectrostaticSolver")
        positive = makeBCElectricPotential(name="PositivePlate")
        ground = makeBCElectricPotential(name="GroundPlate")
        post = makePostPipeline(name="ElectrostaticCapacitorPost")
        result_plot = makeResultPlot(name="PotentialCutPlot", plot_kind="Cut Plot")

        for child in (physics, material, solver, positive, ground, post, result_plot):
            analysis.addObject(child)

        apply_electrostatic_capacitor_defaults(
            analysis,
            physics_model=physics,
            material=material,
            solver=solver,
            positive_bc=positive,
            ground_bc=ground,
            post_pipeline=post,
            result_plot=result_plot,
        )

        FreeCAD.ActiveDocument.commitTransaction()
        FreeCAD.ActiveDocument.recompute()
        _show_project_cockpit()


class _CmdElectromagneticCoilExample:
    """Create a magnetostatic coil starter example."""

    def GetResources(self):
        return {
            "Pixmap": _icon("FlowStudioElectromagnetic.svg"),
            "MenuText": translate("FlowStudio", "Electromagnetic Coil Example"),
            "ToolTip": translate(
                "FlowStudio",
                "Create a magnetostatic coil example with current density excitation and far-field potential",
            ),
        }

    def IsActive(self):
        return FreeCAD.ActiveDocument is not None

    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction("Create Electromagnetic Coil Example")
        from flow_studio.ObjectsFlowStudio import (
            makeDomainAnalysis,
            makeElectromagneticPhysicsModel,
            makeElectromagneticMaterial,
            makeSolver,
            makeBCCurrentDensity,
            makeBCMagneticPotential,
            makePostPipeline,
            makeResultPlot,
        )
        from flow_studio.workflows.studies import apply_electromagnetic_coil_defaults

        analysis = makeDomainAnalysis(name="ElectromagneticCoilExample", domain_key="Electromagnetic")
        physics = makeElectromagneticPhysicsModel(name="CoilPhysics")
        material = makeElectromagneticMaterial(name="CoilMaterial")
        solver = makeSolver(name="ElectromagneticSolver")
        current = makeBCCurrentDensity(name="CoilCurrent")
        boundary = makeBCMagneticPotential(name="FarFieldBoundary")
        post = makePostPipeline(name="ElectromagneticCoilPost")
        result_plot = makeResultPlot(name="MagneticFluxPlot", plot_kind="Surface Plot")

        for child in (physics, material, solver, current, boundary, post, result_plot):
            analysis.addObject(child)

        apply_electromagnetic_coil_defaults(
            analysis,
            physics_model=physics,
            material=material,
            solver=solver,
            current_bc=current,
            boundary_bc=boundary,
            post_pipeline=post,
            result_plot=result_plot,
        )

        FreeCAD.ActiveDocument.commitTransaction()
        FreeCAD.ActiveDocument.recompute()
        _show_project_cockpit()


class _CmdThermalPlateExample:
    """Create a heated-plate thermal starter example."""

    def GetResources(self):
        return {
            "Pixmap": _icon("FlowStudioThermal.svg"),
            "MenuText": translate("FlowStudio", "Thermal Plate Example"),
            "ToolTip": translate(
                "FlowStudio",
                "Create a thermal conduction example with a heat-flux source and ambient convection",
            ),
        }

    def IsActive(self):
        return FreeCAD.ActiveDocument is not None

    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction("Create Thermal Plate Example")
        from flow_studio.ObjectsFlowStudio import (
            makeDomainAnalysis,
            makeThermalPhysicsModel,
            makeThermalMaterial,
            makeSolver,
            makeBCHeatFlux,
            makeBCConvection,
            makePostPipeline,
            makeResultPlot,
        )
        from flow_studio.workflows.studies import apply_thermal_plate_defaults

        analysis = makeDomainAnalysis(name="ThermalPlateExample", domain_key="Thermal")
        physics = makeThermalPhysicsModel(name="ThermalPlatePhysics")
        material = makeThermalMaterial(name="ThermalPlateMaterial")
        solver = makeSolver(name="ThermalSolver")
        heat_flux = makeBCHeatFlux(name="HeaterPad")
        convection = makeBCConvection(name="AmbientCooling")
        post = makePostPipeline(name="ThermalPlatePost")
        result_plot = makeResultPlot(name="TemperatureCutPlot", plot_kind="Cut Plot")

        for child in (physics, material, solver, heat_flux, convection, post, result_plot):
            analysis.addObject(child)

        apply_thermal_plate_defaults(
            analysis,
            physics_model=physics,
            material=material,
            solver=solver,
            heat_flux_bc=heat_flux,
            convection_bc=convection,
            post_pipeline=post,
            result_plot=result_plot,
        )

        FreeCAD.ActiveDocument.commitTransaction()
        FreeCAD.ActiveDocument.recompute()
        _show_project_cockpit()


class _CmdOpticalLensExample:
    """Create a lens illumination optical starter example."""

    def GetResources(self):
        return {
            "Pixmap": _icon("FlowStudioElectromagnetic.svg"),
            "MenuText": translate("FlowStudio", "Optical Lens Example"),
            "ToolTip": translate(
                "FlowStudio",
                "Create a non-sequential lens illumination example with a source, detector, and reflective boundary",
            ),
        }

    def IsActive(self):
        return FreeCAD.ActiveDocument is not None

    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction("Create Optical Lens Example")
        from flow_studio.ObjectsFlowStudio import (
            makeDomainAnalysis,
            makeOpticalPhysicsModel,
            makeOpticalMaterial,
            makeSolver,
            makeBCOpticalSource,
            makeBCOpticalDetector,
            makeBCOpticalBoundary,
            makePostPipeline,
            makeResultPlot,
        )
        from flow_studio.workflows.studies import apply_optical_lens_defaults

        analysis = makeDomainAnalysis(name="OpticalLensExample", domain_key="Optical")
        physics = makeOpticalPhysicsModel(name="LensPhysics")
        material = makeOpticalMaterial(name="LensMaterial")
        solver = makeSolver(name="OpticalSolver")
        source = makeBCOpticalSource(name="LEDSource")
        detector = makeBCOpticalDetector(name="TargetDetector")
        boundary = makeBCOpticalBoundary(name="MirrorHousing")
        post = makePostPipeline(name="OpticalLensPost")
        result_plot = makeResultPlot(name="IrradianceSurfacePlot", plot_kind="Surface Plot")

        for child in (physics, material, solver, source, detector, boundary, post, result_plot):
            analysis.addObject(child)

        apply_optical_lens_defaults(
            analysis,
            physics_model=physics,
            material=material,
            solver=solver,
            source_bc=source,
            detector_bc=detector,
            boundary_bc=boundary,
            post_pipeline=post,
            result_plot=result_plot,
        )

        FreeCAD.ActiveDocument.commitTransaction()
        FreeCAD.ActiveDocument.recompute()
        _show_project_cockpit()


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
        _assign_current_selection(obj, "FlowStudio Material")
        _add_to_analysis(obj)
        FreeCAD.ActiveDocument.commitTransaction()
        FreeCAD.ActiveDocument.recompute()
        _open_task_panel(obj)


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
        _assign_current_selection(obj, "FlowStudio Initial Conditions")
        _add_to_analysis(obj)
        FreeCAD.ActiveDocument.commitTransaction()
        FreeCAD.ActiveDocument.recompute()
        _open_task_panel(obj)


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
        _assign_current_selection(obj, "FlowStudio Wall BC")
        _add_to_analysis(obj)
        FreeCAD.ActiveDocument.commitTransaction()
        FreeCAD.ActiveDocument.recompute()
        _open_task_panel(obj)


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
        _assign_current_selection(obj, "FlowStudio Inlet BC")
        _add_to_analysis(obj)
        FreeCAD.ActiveDocument.commitTransaction()
        FreeCAD.ActiveDocument.recompute()
        _open_task_panel(obj)


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
        _assign_current_selection(obj, "FlowStudio Outlet BC")
        _add_to_analysis(obj)
        FreeCAD.ActiveDocument.commitTransaction()
        FreeCAD.ActiveDocument.recompute()
        _open_task_panel(obj)


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
        _assign_current_selection(obj, "FlowStudio Open BC")
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
        _assign_current_selection(obj, "FlowStudio Symmetry BC")
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
        geometry_obj = _pick_primary_geometry_object()
        if geometry_obj is not None:
            try:
                obj.Part = geometry_obj
                FreeCAD.Console.PrintMessage(
                    f"FlowStudio Mesh: linked geometry {getattr(geometry_obj, 'Label', geometry_obj.Name)}\n"
                )
            except Exception:
                pass
        _add_to_analysis(obj)
        FreeCAD.ActiveDocument.commitTransaction()
        FreeCAD.ActiveDocument.recompute()
        _open_task_panel(obj)


class _CmdImportStep:
    def GetResources(self):
        return {
            "Pixmap": _icon("FlowStudioMeshRegion.svg"),
            "MenuText": translate("FlowStudio", "Import STEP Geometry"),
            "ToolTip": translate(
                "FlowStudio",
                "Import a STEP model with FlowStudio topology analysis and optional auto-repair"
            ),
        }

    def IsActive(self):
        return FreeCAD.ActiveDocument is not None or FreeCAD.GuiUp

    def Activated(self):
        if not FreeCAD.GuiUp:
            FreeCAD.Console.PrintWarning(
                "FlowStudio: STEP import requires the GUI file picker.\n"
            )
            return

        from PySide import QtWidgets
        from flow_studio.geometry_tools import import_step_optimized

        selected_path, _filter = QtWidgets.QFileDialog.getOpenFileName(
            None,
            translate("FlowStudio", "Import STEP Geometry"),
            os.path.expanduser("~"),
            translate("FlowStudio", "STEP Files (*.step *.stp);;All Files (*)"),
        )
        if not selected_path:
            return

        document = FreeCAD.ActiveDocument
        if document is None:
            document = FreeCAD.newDocument("FlowStudio")

        document.openTransaction("Import STEP Geometry")
        try:
            result = import_step_optimized(selected_path, document=document, repair=True)
            document.commitTransaction()
        except Exception as exc:
            document.abortTransaction()
            _show_warning_dialog(
                translate("FlowStudio", "STEP Import"),
                translate("FlowStudio", f"Failed to import STEP file:\n\n{exc}"),
            )
            raise

        topology = result.topology
        summary_lines = [
            f"Imported: {os.path.basename(selected_path)}",
            f"Faces: {topology.face_count}",
            f"Solids: {topology.solid_count}",
            f"Free edges: {topology.free_edge_count}",
            f"Boundary loops: {len(topology.boundary_loops)}",
        ]
        if result.repair_applied:
            summary_lines.append(f"Automatic lids created: {result.created_lids}")
        if result.issues:
            summary_lines.append("Issues:")
            summary_lines.extend(f"- {issue}" for issue in result.issues)
        else:
            summary_lines.append("Topology analysis completed without blocking issues.")

        FreeCAD.Console.PrintMessage("[FlowStudio] STEP import completed.\n")
        for line in summary_lines:
            FreeCAD.Console.PrintMessage(f"{line}\n")

        _show_info_dialog(
            translate("FlowStudio", "STEP Import"),
            "\n".join(summary_lines),
        )


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

        if self._try_enterprise_run(analysis):
            return

        FreeCAD.Console.PrintMessage(
            f"FlowStudio: Running legacy solver backend '{backend}'...\n"
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
        launched = runner.run()
        if not launched:
            FreeCAD.Console.PrintError("FlowStudio: Solver launch failed.\n")
            return

        try:
            from flow_studio.runtime_monitor import register_run

            register_run(analysis, solver_obj, runner)
        except Exception as exc:
            FreeCAD.Console.PrintWarning(
                f"FlowStudio: live runtime monitor unavailable ({exc})\n"
            )

        # Clear dirty flags after successful case write + run launch
        try:
            analysis.NeedsCaseRewrite = False
            analysis.NeedsMeshRewrite = False
            analysis.NeedsMeshRerun = False
        except AttributeError:
            pass
        _show_project_cockpit()

    def _try_enterprise_run(self, analysis):
        """Submit supported backends through the enterprise runtime."""

        runtime = initialize_workbench()
        working_directory = _default_output_dir(analysis)
        run_id = f"{analysis.Name}-{_timestamp_slug()}"

        try:
            submissions = prepare_runtime_submissions(
                runtime=runtime,
                analysis_object=analysis,
                project_id=_project_id(),
                run_id=run_id,
                working_directory=working_directory,
                requested_by="flowstudio-run-command",
                reason="run-solver-command",
            )
        except Exception as exc:
            FreeCAD.Console.PrintWarning(
                f"FlowStudio: Enterprise submission preparation failed; falling back to legacy runner: {exc}\n"
            )
            return False

        is_multi_solver = len(submissions) > 1
        unavailable_adapters = [
            adapter_id for _, adapter_id, _, _, _ in submissions
            if adapter_id not in runtime.job_service.adapter_ids()
        ]
        if unavailable_adapters:
            if is_multi_solver:
                message = (
                    "Enterprise multi-solver submission requires registered adapters for all selected backends. Missing: "
                    + ", ".join(unavailable_adapters)
                )
                FreeCAD.Console.PrintError(f"FlowStudio: {message}\n")
                _show_info_dialog(translate("FlowStudio", "Enterprise Run Failed"), message)
                return True
            FreeCAD.Console.PrintMessage(
                f"FlowStudio: Backend for adapter '{unavailable_adapters[0]}' is not yet handled by the enterprise runtime; using legacy runner.\n"
            )
            return False

        try:
            records = runtime.legacy_execution.submit_many(tuple(item[3] for item in submissions))
        except Exception as exc:
            if is_multi_solver:
                FreeCAD.Console.PrintError(
                    f"FlowStudio: Enterprise multi-solver submission failed: {exc}\n"
                )
                _show_info_dialog(translate("FlowStudio", "Enterprise Run Failed"), str(exc))
                return True
            FreeCAD.Console.PrintWarning(
                f"FlowStudio: Enterprise submission failed; falling back to legacy runner: {exc}\n"
            )
            return False

        try:
            if not getattr(analysis, "CaseDir", ""):
                analysis.CaseDir = working_directory
            analysis.NeedsCaseRewrite = False
            analysis.NeedsMeshRewrite = False
            analysis.NeedsMeshRerun = False
        except AttributeError:
            pass

        if len(records) == 1:
            record = records[0]
            manifest_hash = submissions[0][4]
            message = (
                f"Enterprise run submitted.\n\n"
                f"Run ID: {record.run_id}\n"
                f"State: {record.state.value}\n"
                f"Adapter: {record.adapter_id}\n"
                f"Execution Mode: {record.execution_mode or 'unknown'}\n"
                f"Manifest: {manifest_hash}\n"
                f"Run Directory: {runtime.job_service.run_directory(record.run_id) or working_directory}"
            )
        else:
            message = "Enterprise multi-solver runs submitted.\n\n" + "\n".join(
                f"{submissions[index][0]}: {record.run_id} | {record.state.value} | {record.adapter_id} | {runtime.job_service.run_directory(record.run_id) or working_directory}"
                for index, record in enumerate(records)
            )
        FreeCAD.Console.PrintMessage(f"FlowStudio: {message}\n")
        _show_info_dialog(translate("FlowStudio", "Enterprise Run Submitted"), message)
        return True


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
        obj = makeSolidMaterial()
        _assign_current_selection(obj, "FlowStudio Solid Material")
        _add_to_analysis(obj)
        FreeCAD.ActiveDocument.commitTransaction()
        FreeCAD.ActiveDocument.recompute()
        _open_task_panel(obj)


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
        obj = makeBCFixedDisplacement()
        _assign_current_selection(obj, "FlowStudio Fixed Displacement BC")
        _add_to_analysis(obj)
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
        obj = makeBCForce()
        _assign_current_selection(obj, "FlowStudio Force BC")
        _add_to_analysis(obj)
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
        obj = makeBCPressureLoad()
        _assign_current_selection(obj, "FlowStudio Pressure Load BC")
        _add_to_analysis(obj)
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
        obj = makeElectrostaticMaterial()
        _assign_current_selection(obj, "FlowStudio Electrostatic Material")
        _add_to_analysis(obj)
        FreeCAD.ActiveDocument.commitTransaction()
        FreeCAD.ActiveDocument.recompute()
        _open_task_panel(obj)


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
        obj = makeBCElectricPotential()
        _assign_current_selection(obj, "FlowStudio Electric Potential BC")
        _add_to_analysis(obj)
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
        obj = makeBCSurfaceCharge()
        _assign_current_selection(obj, "FlowStudio Surface Charge BC")
        _add_to_analysis(obj)
        FreeCAD.ActiveDocument.commitTransaction()
        FreeCAD.ActiveDocument.recompute()


class _CmdBCElectricFlux:
    def GetResources(self):
        return {
            "Pixmap": _icon("FlowStudioElectricFlux.svg"),
            "MenuText": translate("FlowStudio", "Electric Flux"),
            "ToolTip": translate("FlowStudio",
                                 "Apply electric flux density (D) on boundary\n"
                                 "Requires: Analysis + Physics Model"),
        }

    def IsActive(self):
        return has_analysis() and has_physics_model()

    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction("Add Electric Flux BC")
        from flow_studio.ObjectsFlowStudio import makeBCElectricFlux
        obj = makeBCElectricFlux()
        _assign_current_selection(obj, "FlowStudio Electric Flux BC")
        _add_to_analysis(obj)
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
        obj = makeElectromagneticMaterial()
        _assign_current_selection(obj, "FlowStudio Electromagnetic Material")
        _add_to_analysis(obj)
        FreeCAD.ActiveDocument.commitTransaction()
        FreeCAD.ActiveDocument.recompute()
        _open_task_panel(obj)


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
        obj = makeBCMagneticPotential()
        _assign_current_selection(obj, "FlowStudio Magnetic Potential BC")
        _add_to_analysis(obj)
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
        obj = makeBCCurrentDensity()
        _assign_current_selection(obj, "FlowStudio Current Density BC")
        _add_to_analysis(obj)
        FreeCAD.ActiveDocument.commitTransaction()
        FreeCAD.ActiveDocument.recompute()


class _CmdBCMagneticFluxDensity:
    def GetResources(self):
        return {
            "Pixmap": _icon("FlowStudioMagneticFluxDensity.svg"),
            "MenuText": translate("FlowStudio", "Magnetic Flux Density"),
            "ToolTip": translate("FlowStudio",
                                 "Prescribe magnetic flux density (B) on boundary\n"
                                 "Requires: Analysis + Physics Model"),
        }

    def IsActive(self):
        return has_analysis() and has_physics_model()

    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction("Add Magnetic Flux Density BC")
        from flow_studio.ObjectsFlowStudio import makeBCMagneticFluxDensity
        obj = makeBCMagneticFluxDensity()
        _assign_current_selection(obj, "FlowStudio Magnetic Flux Density BC")
        _add_to_analysis(obj)
        FreeCAD.ActiveDocument.commitTransaction()
        FreeCAD.ActiveDocument.recompute()


class _CmdBCFarFieldEM:
    def GetResources(self):
        return {
            "Pixmap": _icon("FlowStudioFarFieldEM.svg"),
            "MenuText": translate("FlowStudio", "Far-Field EM"),
            "ToolTip": translate("FlowStudio",
                                 "Apply far-field / open-boundary condition for EM\n"
                                 "Requires: Analysis + Physics Model"),
        }

    def IsActive(self):
        return has_analysis() and has_physics_model()

    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction("Add Far-Field EM BC")
        from flow_studio.ObjectsFlowStudio import makeBCFarFieldEM
        obj = makeBCFarFieldEM()
        _assign_current_selection(obj, "FlowStudio Far-Field EM BC")
        _add_to_analysis(obj)
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
        obj = makeThermalMaterial()
        _assign_current_selection(obj, "FlowStudio Thermal Material")
        _add_to_analysis(obj)
        FreeCAD.ActiveDocument.commitTransaction()
        FreeCAD.ActiveDocument.recompute()
        _open_task_panel(obj)


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
        obj = makeBCTemperature()
        _assign_current_selection(obj, "FlowStudio Temperature BC")
        _add_to_analysis(obj)
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
        obj = makeBCHeatFlux()
        _assign_current_selection(obj, "FlowStudio Heat Flux BC")
        _add_to_analysis(obj)
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
        obj = makeBCConvection()
        _assign_current_selection(obj, "FlowStudio Convection BC")
        _add_to_analysis(obj)
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
        obj = makeBCRadiation()
        _assign_current_selection(obj, "FlowStudio Radiation BC")
        _add_to_analysis(obj)
        FreeCAD.ActiveDocument.commitTransaction()
        FreeCAD.ActiveDocument.recompute()


# ======================================================================
#  OPTICAL commands
# ======================================================================

class _CmdOpticalMaterial:
    def GetResources(self):
        return {
            "Pixmap": _icon("FlowStudioElectromagnetic.svg"),
            "MenuText": translate("FlowStudio", "Optical Material"),
            "ToolTip": translate("FlowStudio", "Assign glass, coating, mirror, or absorber optical properties"),
        }

    def IsActive(self):
        return has_analysis()

    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction("Add Optical Material")
        from flow_studio.ObjectsFlowStudio import makeOpticalMaterial
        obj = makeOpticalMaterial()
        _assign_current_selection(obj, "FlowStudio Optical Material")
        _add_to_analysis(obj)
        FreeCAD.ActiveDocument.commitTransaction()
        FreeCAD.ActiveDocument.recompute()
        _open_task_panel(obj)


class _CmdOpticalPhysics:
    def GetResources(self):
        return {
            "Pixmap": _icon("FlowStudioPhysics.svg"),
            "MenuText": translate("FlowStudio", "Optical Physics"),
            "ToolTip": translate("FlowStudio", "Configure ray optics, illumination, or wave-optics settings"),
        }

    def IsActive(self):
        return has_analysis()

    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction("Add Optical Physics")
        from flow_studio.ObjectsFlowStudio import makeOpticalPhysicsModel
        obj = makeOpticalPhysicsModel()
        _add_to_analysis(obj)
        FreeCAD.ActiveDocument.commitTransaction()
        FreeCAD.ActiveDocument.recompute()


class _CmdBCOpticalSource:
    def GetResources(self):
        return {
            "Pixmap": _icon("FlowStudioPostStreamlines.svg"),
            "MenuText": translate("FlowStudio", "Optical Source"),
            "ToolTip": translate("FlowStudio", "Add a collimated beam, LED, point source, Gaussian beam, or laser source"),
        }

    def IsActive(self):
        return has_analysis()

    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction("Add Optical Source")
        from flow_studio.ObjectsFlowStudio import makeBCOpticalSource
        obj = makeBCOpticalSource()
        _assign_current_selection(obj, "FlowStudio Optical Source")
        _add_to_analysis(obj)
        FreeCAD.ActiveDocument.commitTransaction()
        FreeCAD.ActiveDocument.recompute()
        _open_task_panel(obj)


class _CmdBCOpticalDetector:
    def GetResources(self):
        return {
            "Pixmap": _icon("FlowStudioPostProbe.svg"),
            "MenuText": translate("FlowStudio", "Optical Detector"),
            "ToolTip": translate("FlowStudio", "Add an irradiance, power, spot, phase, or spectrum detector"),
        }

    def IsActive(self):
        return has_analysis()

    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction("Add Optical Detector")
        from flow_studio.ObjectsFlowStudio import makeBCOpticalDetector
        obj = makeBCOpticalDetector()
        _assign_current_selection(obj, "FlowStudio Optical Detector")
        _add_to_analysis(obj)
        FreeCAD.ActiveDocument.commitTransaction()
        FreeCAD.ActiveDocument.recompute()
        _open_task_panel(obj)


class _CmdBCOpticalBoundary:
    def GetResources(self):
        return {
            "Pixmap": _icon("FlowStudioPostContour.svg"),
            "MenuText": translate("FlowStudio", "Optical Boundary"),
            "ToolTip": translate("FlowStudio", "Assign refractive, reflective, absorbing, scattering, periodic, or PML behavior"),
        }

    def IsActive(self):
        return has_analysis()

    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction("Add Optical Boundary")
        from flow_studio.ObjectsFlowStudio import makeBCOpticalBoundary
        obj = makeBCOpticalBoundary()
        _assign_current_selection(obj, "FlowStudio Optical Boundary")
        _add_to_analysis(obj)
        FreeCAD.ActiveDocument.commitTransaction()
        FreeCAD.ActiveDocument.recompute()
        _open_task_panel(obj)


class _CmdBCGeant4Source:
    def GetResources(self):
        return {
            "Pixmap": _icon("FlowStudioPostStreamlines.svg"),
            "MenuText": translate("FlowStudio", "Geant4 Source"),
            "ToolTip": translate("FlowStudio", "Add a Geant4 primary particle source for beam, point, surface, or volume emission"),
        }

    def IsActive(self):
        return has_analysis()

    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction("Add Geant4 Source")
        from flow_studio.ObjectsFlowStudio import makeBCGeant4Source
        obj = makeBCGeant4Source()
        _assign_current_selection(obj, "FlowStudio Geant4 Source")
        _add_to_analysis(obj)
        FreeCAD.ActiveDocument.commitTransaction()
        FreeCAD.ActiveDocument.recompute()
        _open_task_panel(obj)


class _CmdBCGeant4Detector:
    def GetResources(self):
        return {
            "Pixmap": _icon("FlowStudioPostProbe.svg"),
            "MenuText": translate("FlowStudio", "Geant4 Detector"),
            "ToolTip": translate("FlowStudio", "Add a Geant4 sensitive detector, calorimeter, tracker, or dose plane"),
        }

    def IsActive(self):
        return has_analysis()

    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction("Add Geant4 Detector")
        from flow_studio.ObjectsFlowStudio import makeBCGeant4Detector
        obj = makeBCGeant4Detector()
        _assign_current_selection(obj, "FlowStudio Geant4 Detector")
        _add_to_analysis(obj)
        FreeCAD.ActiveDocument.commitTransaction()
        FreeCAD.ActiveDocument.recompute()
        _open_task_panel(obj)


class _CmdBCGeant4Scoring:
    def GetResources(self):
        return {
            "Pixmap": _icon("FlowStudioPostContour.svg"),
            "MenuText": translate("FlowStudio", "Geant4 Scoring"),
            "ToolTip": translate("FlowStudio", "Add a Geant4 scoring request for dose, energy deposition, flux, track length, or cell hits"),
        }

    def IsActive(self):
        return has_analysis()

    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction("Add Geant4 Scoring")
        from flow_studio.ObjectsFlowStudio import makeBCGeant4Scoring
        obj = makeBCGeant4Scoring()
        _assign_current_selection(obj, "FlowStudio Geant4 Scoring")
        _add_to_analysis(obj)
        FreeCAD.ActiveDocument.commitTransaction()
        FreeCAD.ActiveDocument.recompute()
        _open_task_panel(obj)


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


class _CmdGeant4Result:
    def GetResources(self):
        return {
            "Pixmap": _icon("FlowStudioPost.svg"),
            "MenuText": translate("FlowStudio", "Geant4 Result"),
            "ToolTip": translate(
                "FlowStudio",
                "Create a native Geant4 result container for imported artifact metadata"
            ),
        }

    def IsActive(self):
        return _get_active_analysis() is not None

    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction("Add Geant4 Result")
        from flow_studio.ObjectsFlowStudio import makeGeant4Result
        obj = makeGeant4Result()
        _add_to_analysis(obj)
        FreeCAD.ActiveDocument.commitTransaction()
        FreeCAD.ActiveDocument.recompute()
        _open_task_panel(obj)


class _CmdImportGeant4Result:
    def GetResources(self):
        return {
            "Pixmap": _icon("FlowStudioPost.svg"),
            "MenuText": translate("FlowStudio", "Import Geant4 Result"),
            "ToolTip": translate(
                "FlowStudio",
                "Import a saved FlowStudio Geant4 result summary JSON into a native Geant4 result object"
            ),
        }

    def IsActive(self):
        return FreeCAD.ActiveDocument is not None or FreeCAD.GuiUp

    def Activated(self):
        if not FreeCAD.GuiUp:
            FreeCAD.Console.PrintWarning(
                "FlowStudio: Geant4 summary import requires the GUI file picker.\n"
            )
            return
        from PySide import QtWidgets

        selected_path, _filter = QtWidgets.QFileDialog.getOpenFileName(
            None,
            translate("FlowStudio", "Import Geant4 Result Summary"),
            os.path.expanduser("~"),
            translate("FlowStudio", "Geant4 Result Summary (*geant4_result_summary.json *.json)"),
        )
        if not selected_path:
            return

        from flow_studio.feminout.importFlowStudio import open_geant4_summary

        analysis = _get_active_analysis()
        obj = open_geant4_summary(selected_path, doc=FreeCAD.ActiveDocument, analysis=analysis)
        _open_task_panel(obj)


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
#  FloEFD-style setup/result feature commands
# ======================================================================

class _CmdVolumeSource:
    def GetResources(self):
        return {
            "Pixmap": _icon("FlowStudioThermal.svg"),
            "MenuText": translate("FlowStudio", "Volume Source"),
            "ToolTip": translate("FlowStudio", "Add a volumetric heat/mass/momentum source to selected parts."),
        }

    def IsActive(self):
        return has_analysis()

    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction("Add Volume Source")
        from flow_studio.ObjectsFlowStudio import makeVolumeSource
        obj = makeVolumeSource()
        _assign_current_selection(obj, "FlowStudio Volume Source")
        _add_to_analysis(obj)
        FreeCAD.ActiveDocument.commitTransaction()
        FreeCAD.ActiveDocument.recompute()
        _open_task_panel(obj)


class _CmdFan:
    def GetResources(self):
        return {
            "Pixmap": _icon("FlowStudioSolver.svg"),
            "MenuText": translate("FlowStudio", "Fan"),
            "ToolTip": translate("FlowStudio", "Add an internal, external inlet, or external outlet fan on selected faces."),
        }

    def IsActive(self):
        return has_analysis()

    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction("Add Fan")
        from flow_studio.ObjectsFlowStudio import makeFan
        obj = makeFan()
        _assign_current_selection(obj, "FlowStudio Fan")
        _add_to_analysis(obj)
        FreeCAD.ActiveDocument.commitTransaction()
        FreeCAD.ActiveDocument.recompute()
        _open_task_panel(obj)


class _CmdResultPlot:
    plot_kind = "Surface Plot"
    name = "Result Plot"

    def GetResources(self):
        icon = "FlowStudioPostContour.svg"
        if self.plot_kind == "Flow Trajectories":
            icon = "FlowStudioPostStreamlines.svg"
        elif self.plot_kind in ("XY Plot", "Point Parameters"):
            icon = "FlowStudioPostProbe.svg"
        return {
            "Pixmap": _icon(icon),
            "MenuText": translate("FlowStudio", self.name),
            "ToolTip": translate("FlowStudio", f"Create a {self.plot_kind} result definition."),
        }

    def IsActive(self):
        return has_analysis()

    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction(f"Add {self.plot_kind}")
        from flow_studio.ObjectsFlowStudio import makeResultPlot
        name = self.plot_kind.replace(" ", "")
        obj = makeResultPlot(name=name, plot_kind=self.plot_kind)
        _assign_current_selection(obj, f"FlowStudio {self.plot_kind}")
        _add_to_analysis(obj)
        FreeCAD.ActiveDocument.commitTransaction()
        FreeCAD.ActiveDocument.recompute()
        _open_task_panel(obj)


class _CmdSurfacePlot(_CmdResultPlot):
    plot_kind = "Surface Plot"
    name = "Surface Plot"


class _CmdCutPlot(_CmdResultPlot):
    plot_kind = "Cut Plot"
    name = "Cut Plot"


class _CmdXYPlot(_CmdResultPlot):
    plot_kind = "XY Plot"
    name = "XY Plot"


class _CmdFlowTrajectories(_CmdResultPlot):
    plot_kind = "Flow Trajectories"
    name = "Flow Trajectories"


class _CmdPointParameters(_CmdResultPlot):
    plot_kind = "Point Parameters"
    name = "Point Parameters"


class _CmdParticleStudy:
    def GetResources(self):
        return {
            "Pixmap": _icon("FlowStudioPostStreamlines.svg"),
            "MenuText": translate("FlowStudio", "Particle Study"),
            "ToolTip": translate("FlowStudio", "Create a particle tracing study with injection selections."),
        }

    def IsActive(self):
        return has_analysis()

    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction("Add Particle Study")
        from flow_studio.ObjectsFlowStudio import makeParticleStudy
        obj = makeParticleStudy()
        _assign_current_selection(obj, "FlowStudio Particle Study")
        _add_to_analysis(obj)
        FreeCAD.ActiveDocument.commitTransaction()
        FreeCAD.ActiveDocument.recompute()
        _open_task_panel(obj)


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
            "MenuText": translate("FlowStudio", "Project Cockpit"),
            "Accel": "C, W",
            "ToolTip": translate(
                "FlowStudio",
                "Open the color-coded project cockpit for the full simulation workflow"
            ),
        }

    def IsActive(self):
        return FreeCAD.ActiveDocument is not None

    def Activated(self):
        from flow_studio.workflow_guide import get_workflow_context, get_workflow_status
        context = get_workflow_context()
        steps = get_workflow_status()
        profile = context["profile"]
        layout_model = context["layout"]
        study_recipe = context.get("study_recipe")

        # Print a formatted workflow status report to the console
        FreeCAD.Console.PrintMessage(
            "\n"
            "╔══════════════════════════════════════════════════════════╗\n"
            "║          FlowStudio — Simulation Workflow Guide         ║\n"
            "╚══════════════════════════════════════════════════════════╝\n\n"
        )
        FreeCAD.Console.PrintMessage(
            f"Domain: {profile.label}\n"
            f"Workspace: {layout_model.name}\n"
            f"Primary workflows: {', '.join(profile.workflows)}\n\n"
        )

        if study_recipe is not None:
            FreeCAD.Console.PrintMessage(
                f"Study recipe: {study_recipe.label}\n"
                f"Reference: {study_recipe.reference_url}\n"
            )
            for item in study_recipe.key_parameters:
                FreeCAD.Console.PrintMessage(f"  - {item}\n")
            FreeCAD.Console.PrintMessage("\n")

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
                _show_project_cockpit()
            except Exception:
                pass  # Fall back to console-only output


class _CmdStopSolver:
    def GetResources(self):
        return {
            "Pixmap": _icon("FlowStudioRunSolver.svg"),
            "MenuText": translate("FlowStudio", "Stop Solver"),
            "ToolTip": translate(
                "FlowStudio",
                "Terminate the active legacy solver run from the project cockpit"
            ),
        }

    def IsActive(self):
        return has_analysis()

    def Activated(self):
        from flow_studio.runtime_monitor import terminate_run

        if terminate_run(_get_active_analysis()):
            FreeCAD.Console.PrintWarning("FlowStudio: Stop requested for active solver run.\n")
        else:
            FreeCAD.Console.PrintWarning("FlowStudio: No active solver run to stop.\n")


class _WorkflowGuidePanel:
    """Task panel displaying the workflow checklist (Qt widget)."""

    def __init__(self, steps, context):
        from PySide import QtWidgets, QtCore, QtGui
        self.form = QtWidgets.QWidget()
        self.form.setWindowTitle("FlowStudio Workflow Guide")
        layout = QtWidgets.QVBoxLayout(self.form)
        profile = context["profile"]
        workspace = context["layout"]
        study_recipe = context.get("study_recipe")

        # Header
        header = QtWidgets.QLabel(
            f"<h3>{profile.label} Workflow</h3>"
            f"<p><b>Workspace:</b> {workspace.name}<br>"
            f"<b>Focus:</b> {', '.join(workspace.primary_workflows)}<br>"
            "Follow these steps in order for a successful simulation. "
            "Greyed-out steps require earlier steps to be completed first.</p>"
        )
        header.setWordWrap(True)
        layout.addWidget(header)

        if study_recipe is not None:
            recipe = QtWidgets.QLabel(
                f"<p><b>Study recipe:</b> {study_recipe.label}<br>"
                f"{study_recipe.summary}<br>"
                f"<a href='{study_recipe.reference_url}'>{study_recipe.reference_url}</a></p>"
                "<p><b>Milestones:</b><ul>"
                + "".join(f"<li>{item}</li>" for item in study_recipe.milestones)
                + "</ul><b>Reference values:</b><ul>"
                + "".join(f"<li>{item}</li>" for item in study_recipe.key_parameters)
                + "</ul></p>"
            )
            recipe.setWordWrap(True)
            recipe.setOpenExternalLinks(True)
            recipe.setStyleSheet("background:#f7f9fc; border:1px solid #90a4ae; border-radius:6px; padding:8px;")
            layout.addWidget(recipe)

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


class _CmdEngineeringDatabase:
    def GetResources(self):
        return {
            "Pixmap": _icon("FlowStudioMaterial.svg"),
            "MenuText": translate("FlowStudio", "Engineering Database"),
            "ToolTip": translate(
                "FlowStudio",
                "Open the material, fan, heat sink, component, and unit engineering database editor",
            ),
        }

    def IsActive(self):
        return FreeCAD.GuiUp

    def Activated(self):
        from flow_studio.catalog.editor import show_engineering_database_editor
        show_engineering_database_editor()


class _CmdCheckGeometry:
    def GetResources(self):
        return {
            "Pixmap": _icon("FlowStudioMeshRegion.svg"),
            "MenuText": translate("FlowStudio", "Check Geometry"),
            "ToolTip": translate(
                "FlowStudio",
                "Open the FlowStudio geometry checker, fluid-volume preview, and leak tracking tools",
            ),
        }

    def IsActive(self):
        return FreeCAD.GuiUp and FreeCAD.ActiveDocument is not None

    def Activated(self):
        from flow_studio.taskpanels.task_geometry_tools import TaskCheckGeometry

        try:
            FreeCADGui.Control.closeDialog()
        except Exception:
            pass
        FreeCADGui.Control.showDialog(TaskCheckGeometry())


class _CmdShowFluidVolume:
    def GetResources(self):
        return {
            "Pixmap": _icon("FlowStudioMesh.svg"),
            "MenuText": translate("FlowStudio", "Show Fluid Volume"),
            "ToolTip": translate(
                "FlowStudio",
                "Create or toggle a translucent preview of the detected FlowStudio fluid volume envelope",
            ),
        }

    def IsActive(self):
        return FreeCAD.ActiveDocument is not None

    def Activated(self):
        from flow_studio.tools.geometry import (
            fluid_volume_is_visible,
            hide_fluid_volume,
            show_fluid_volume,
        )

        if fluid_volume_is_visible():
            hide_fluid_volume()
            FreeCAD.Console.PrintMessage("[FlowStudio] Fluid volume hidden.\n")
        else:
            obj = show_fluid_volume()
            if obj is None:
                FreeCAD.Console.PrintWarning(
                    "[FlowStudio] Fluid volume could not be created. Add or select geometry first.\n"
                )
            else:
                FreeCAD.Console.PrintMessage("[FlowStudio] Fluid volume shown.\n")


class _CmdLeakTracking:
    def GetResources(self):
        return {
            "Pixmap": _icon("FlowStudioPostStreamlines.svg"),
            "MenuText": translate("FlowStudio", "Leak Tracking"),
            "ToolTip": translate(
                "FlowStudio",
                "Track a possible leak or connection between one internal and one external selected face",
            ),
        }

    def IsActive(self):
        return FreeCAD.GuiUp and FreeCAD.ActiveDocument is not None

    def Activated(self):
        from flow_studio.taskpanels.task_geometry_tools import TaskLeakTracking

        try:
            FreeCADGui.Control.closeDialog()
        except Exception:
            pass
        FreeCADGui.Control.showDialog(TaskLeakTracking())


# ======================================================================
# Register all commands
# ======================================================================

# --- Analysis creation (one per domain) ---
FreeCADGui.addCommand("FlowStudio_Analysis", _CmdAnalysis())
FreeCADGui.addCommand("FlowStudio_ElectronicsCoolingStudy", _CmdElectronicsCoolingStudy())
FreeCADGui.addCommand("FlowStudio_CoolingChannelStudy", _CmdCoolingChannelStudy())
FreeCADGui.addCommand("FlowStudio_ExternalAeroStudy", _CmdExternalAeroStudy())
FreeCADGui.addCommand("FlowStudio_BuildingsStudy", _CmdBuildingsStudy())
FreeCADGui.addCommand("FlowStudio_AirfoilStudy", _CmdAirfoilStudy())
FreeCADGui.addCommand("FlowStudio_TeslaValveStudy", _CmdTeslaValveStudy())
FreeCADGui.addCommand("FlowStudio_VonKarmanStudy", _CmdVonKarmanStudy())
FreeCADGui.addCommand("FlowStudio_PipeFlowStudy", _CmdPipeFlowStudy())
FreeCADGui.addCommand("FlowStudio_StaticMixerStudy", _CmdStaticMixerStudy())
FreeCADGui.addCommand("FlowStudio_StructuralAnalysis", _CmdStructuralAnalysis())
FreeCADGui.addCommand("FlowStudio_StructuralBracketExample", _CmdStructuralBracketExample())
FreeCADGui.addCommand("FlowStudio_ElectrostaticAnalysis", _CmdElectrostaticAnalysis())
FreeCADGui.addCommand("FlowStudio_ElectrostaticCapacitorExample", _CmdElectrostaticCapacitorExample())
FreeCADGui.addCommand("FlowStudio_ElectromagneticAnalysis", _CmdElectromagneticAnalysis())
FreeCADGui.addCommand("FlowStudio_ElectromagneticCoilExample", _CmdElectromagneticCoilExample())
FreeCADGui.addCommand("FlowStudio_ThermalAnalysis", _CmdThermalAnalysis())
FreeCADGui.addCommand("FlowStudio_ThermalPlateExample", _CmdThermalPlateExample())
FreeCADGui.addCommand("FlowStudio_OpticalAnalysis", _CmdOpticalAnalysis())
FreeCADGui.addCommand("FlowStudio_OpticalLensExample", _CmdOpticalLensExample())

# --- CFD setup ---
FreeCADGui.addCommand("FlowStudio_PhysicsModel", _CmdPhysicsModel())
FreeCADGui.addCommand("FlowStudio_FluidMaterial", _CmdFluidMaterial())
FreeCADGui.addCommand("FlowStudio_InitialConditions", _CmdInitialConditions())
FreeCADGui.addCommand("FlowStudio_EngineeringDatabase", _CmdEngineeringDatabase())
FreeCADGui.addCommand("FlowStudio_CheckGeometry", _CmdCheckGeometry())
FreeCADGui.addCommand("FlowStudio_ShowFluidVolume", _CmdShowFluidVolume())
FreeCADGui.addCommand("FlowStudio_LeakTracking", _CmdLeakTracking())
FreeCADGui.addCommand("FlowStudio_ImportStep", _CmdImportStep())

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
FreeCADGui.addCommand("FlowStudio_BC_ElectricFlux", _CmdBCElectricFlux())

# --- Electromagnetic ---
FreeCADGui.addCommand("FlowStudio_ElectromagneticMaterial", _CmdElectromagneticMaterial())
FreeCADGui.addCommand("FlowStudio_ElectromagneticPhysics", _CmdElectromagneticPhysics())
FreeCADGui.addCommand("FlowStudio_BC_MagneticPotential", _CmdBCMagneticPotential())
FreeCADGui.addCommand("FlowStudio_BC_CurrentDensity", _CmdBCCurrentDensity())
FreeCADGui.addCommand("FlowStudio_BC_MagneticFluxDensity", _CmdBCMagneticFluxDensity())
FreeCADGui.addCommand("FlowStudio_BC_FarFieldEM", _CmdBCFarFieldEM())

# --- Thermal ---
FreeCADGui.addCommand("FlowStudio_ThermalMaterial", _CmdThermalMaterial())
FreeCADGui.addCommand("FlowStudio_ThermalPhysics", _CmdThermalPhysics())
FreeCADGui.addCommand("FlowStudio_BC_Temperature", _CmdBCTemperature())
FreeCADGui.addCommand("FlowStudio_BC_HeatFlux", _CmdBCHeatFlux())
FreeCADGui.addCommand("FlowStudio_BC_Convection", _CmdBCConvection())
FreeCADGui.addCommand("FlowStudio_BC_Radiation", _CmdBCRadiation())

# --- Optical ---
FreeCADGui.addCommand("FlowStudio_OpticalMaterial", _CmdOpticalMaterial())
FreeCADGui.addCommand("FlowStudio_OpticalPhysics", _CmdOpticalPhysics())
FreeCADGui.addCommand("FlowStudio_BC_OpticalSource", _CmdBCOpticalSource())
FreeCADGui.addCommand("FlowStudio_BC_OpticalDetector", _CmdBCOpticalDetector())
FreeCADGui.addCommand("FlowStudio_BC_OpticalBoundary", _CmdBCOpticalBoundary())
FreeCADGui.addCommand("FlowStudio_BC_Geant4Source", _CmdBCGeant4Source())
FreeCADGui.addCommand("FlowStudio_BC_Geant4Detector", _CmdBCGeant4Detector())
FreeCADGui.addCommand("FlowStudio_BC_Geant4Scoring", _CmdBCGeant4Scoring())

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
FreeCADGui.addCommand("FlowStudio_Geant4Result", _CmdGeant4Result())
FreeCADGui.addCommand("FlowStudio_ImportGeant4Result", _CmdImportGeant4Result())
FreeCADGui.addCommand("FlowStudio_PostContour", _CmdPostContour())
FreeCADGui.addCommand("FlowStudio_PostStreamlines", _CmdPostStreamlines())
FreeCADGui.addCommand("FlowStudio_PostProbe", _CmdPostProbe())
FreeCADGui.addCommand("FlowStudio_PostForceReport", _CmdPostForceReport())

# --- FloEFD-style setup/results ---
FreeCADGui.addCommand("FlowStudio_VolumeSource", _CmdVolumeSource())
FreeCADGui.addCommand("FlowStudio_Fan", _CmdFan())
FreeCADGui.addCommand("FlowStudio_SurfacePlot", _CmdSurfacePlot())
FreeCADGui.addCommand("FlowStudio_CutPlot", _CmdCutPlot())
FreeCADGui.addCommand("FlowStudio_XYPlot", _CmdXYPlot())
FreeCADGui.addCommand("FlowStudio_FlowTrajectories", _CmdFlowTrajectories())
FreeCADGui.addCommand("FlowStudio_PointParameters", _CmdPointParameters())
FreeCADGui.addCommand("FlowStudio_ParticleStudy", _CmdParticleStudy())

# --- Measurement / Paraview ---
FreeCADGui.addCommand("FlowStudio_MeasurementPoint", _CmdMeasurementPoint())
FreeCADGui.addCommand("FlowStudio_MeasurementSurface", _CmdMeasurementSurface())
FreeCADGui.addCommand("FlowStudio_MeasurementVolume", _CmdMeasurementVolume())
FreeCADGui.addCommand("FlowStudio_GenerateParaviewScript", _CmdGenerateParaviewScript())

# --- Workflow ---
FreeCADGui.addCommand("FlowStudio_WorkflowGuide", _CmdWorkflowGuide())
FreeCADGui.addCommand("FlowStudio_ProjectCockpit", _CmdWorkflowGuide())
FreeCADGui.addCommand("FlowStudio_CheckWorkflow", _CmdCheckWorkflow())
FreeCADGui.addCommand("FlowStudio_StopSolver", _CmdStopSolver())
