# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""FlowStudio CFD Workbench – GUI-level initialization.

Defines the FreeCAD Workbench class, menus, and toolbars.
Inspired by FloEFD's user-friendly workflow:
  1. Create Analysis  →  2. Select Fluid/Physics  →  3. Set BCs  →
  4. Generate Mesh    →  5. Run Solver            →  6. Post-process
"""

import os
import FreeCAD
import FreeCADGui

FreeCAD.Console.PrintLog("FlowStudio: InitGui.py loading...\n")

# __file__ is NOT defined when this script is exec'd by FreeCAD's init system.
# Derive the workbench root from FreeCAD's module directory list instead.
FLOW_STUDIO_DIR = ""
for _d in FreeCAD.__ModDirs__:
    if os.path.basename(_d) == "FlowStudio":
        FLOW_STUDIO_DIR = _d
        break
if not FLOW_STUDIO_DIR:
    # Fallback: assume Mod/FlowStudio under FreeCAD home
    FLOW_STUDIO_DIR = os.path.join(FreeCAD.getHomePath(), "Mod", "FlowStudio")
ICONS_DIR = os.path.join(FLOW_STUDIO_DIR, "Resources", "icons")
FreeCAD.Console.PrintLog(f"FlowStudio: FLOW_STUDIO_DIR={FLOW_STUDIO_DIR}\n")


class FlowStudioWorkbench(FreeCADGui.Workbench):
    """FlowStudio – Multi-Physics Simulation Environment for FreeCAD.

    CST-inspired multi-domain workbench supporting CFD, Structural,
    Electrostatic, Electromagnetic, and Thermal simulation with
    multiple solver backends (OpenFOAM, FluidX3D, Elmer FEM).
    """

    MenuText = "FlowStudio"
    ToolTip = "Multi-physics simulation workbench (CFD, FEM, EM, Thermal) with multi-solver support."

    def __init__(self):
        import os as _os
        import FreeCAD as _fc
        _flow_dir = ""
        for _d in _fc.__ModDirs__:
            if _os.path.basename(_d) == "FlowStudio":
                _flow_dir = _d
                break
        if not _flow_dir:
            _flow_dir = _os.path.join(_fc.getHomePath(), "Mod", "FlowStudio")
        self.__class__.Icon = _os.path.join(_flow_dir, "Resources", "icons", "FlowStudioWorkbench.svg")

    # ------------------------------------------------------------------
    # Workbench lifecycle
    # ------------------------------------------------------------------
    def Initialize(self):
        """Called once when the workbench is first loaded."""
        from flow_studio import commands  # noqa: F401

        # ---- Workflow Guide (always visible) ----
        workflow_cmds = [
            "FlowStudio_WorkflowGuide",
            "FlowStudio_CheckWorkflow",
        ]

        # ---- Analysis creation (all domains) ----
        analysis_cmds = [
            "FlowStudio_Analysis",
            "FlowStudio_StructuralAnalysis",
            "FlowStudio_ElectrostaticAnalysis",
            "FlowStudio_ElectromagneticAnalysis",
            "FlowStudio_ThermalAnalysis",
        ]

        # ---- CFD Setup ----
        cfd_setup_cmds = [
            "FlowStudio_PhysicsModel",
            "FlowStudio_FluidMaterial",
            "FlowStudio_InitialConditions",
        ]

        # ---- CFD Boundary Conditions ----
        cfd_bc_cmds = [
            "FlowStudio_BC_Wall",
            "FlowStudio_BC_Inlet",
            "FlowStudio_BC_Outlet",
            "FlowStudio_BC_OpenBoundary",
            "FlowStudio_BC_Symmetry",
        ]

        # ---- Structural ----
        structural_cmds = [
            "FlowStudio_StructuralPhysics",
            "FlowStudio_SolidMaterial",
            "FlowStudio_BC_FixedDisplacement",
            "FlowStudio_BC_Force",
            "FlowStudio_BC_PressureLoad",
        ]

        # ---- Electrostatic ----
        electrostatic_cmds = [
            "FlowStudio_ElectrostaticPhysics",
            "FlowStudio_ElectrostaticMaterial",
            "FlowStudio_BC_ElectricPotential",
            "FlowStudio_BC_SurfaceCharge",
        ]

        # ---- Electromagnetic ----
        electromagnetic_cmds = [
            "FlowStudio_ElectromagneticPhysics",
            "FlowStudio_ElectromagneticMaterial",
            "FlowStudio_BC_MagneticPotential",
            "FlowStudio_BC_CurrentDensity",
        ]

        # ---- Thermal ----
        thermal_cmds = [
            "FlowStudio_ThermalPhysics",
            "FlowStudio_ThermalMaterial",
            "FlowStudio_BC_Temperature",
            "FlowStudio_BC_HeatFlux",
            "FlowStudio_BC_Convection",
            "FlowStudio_BC_Radiation",
        ]

        # ---- Mesh ----
        mesh_cmds = [
            "FlowStudio_MeshGmsh",
            "FlowStudio_MeshRegion",
            "FlowStudio_BoundaryLayer",
        ]

        # ---- Solve ----
        solve_cmds = [
            "FlowStudio_SolverSelect",
            "FlowStudio_SolverSettings",
            "FlowStudio_RunSolver",
        ]

        # ---- Post-processing ----
        post_cmds = [
            "FlowStudio_PostPipeline",
            "FlowStudio_PostContour",
            "FlowStudio_PostStreamlines",
            "FlowStudio_PostProbe",
            "FlowStudio_PostForceReport",
        ]

        # ---- Measurement / Paraview evaluation ----
        measurement_cmds = [
            "FlowStudio_MeasurementPoint",
            "FlowStudio_MeasurementSurface",
            "FlowStudio_MeasurementVolume",
            "Separator",
            "FlowStudio_GenerateParaviewScript",
        ]

        # ---- Toolbars (workflow-ordered) ----
        self.appendToolbar("Workflow", workflow_cmds)
        self.appendToolbar("Step 1 — New Analysis", analysis_cmds)
        self.appendToolbar("Steps 3-4 — CFD Setup", cfd_setup_cmds)
        self.appendToolbar("Step 5 — CFD Boundaries", cfd_bc_cmds)
        self.appendToolbar("Steps 3-5 — Structural", structural_cmds)
        self.appendToolbar("Steps 3-5 — Electrostatic", electrostatic_cmds)
        self.appendToolbar("Steps 3-5 — Electromagnetic", electromagnetic_cmds)
        self.appendToolbar("Steps 3-5 — Thermal", thermal_cmds)
        self.appendToolbar("Step 6 — Mesh", mesh_cmds)
        self.appendToolbar("Step 8 — Solve", solve_cmds)
        self.appendToolbar("Step 9 — Post-Processing", post_cmds)
        self.appendToolbar("Step 10 — Evaluation", measurement_cmds)

        # ---- Menus ----
        self.appendMenu("&FlowStudio", workflow_cmds)
        self.appendMenu(["&FlowStudio", "New Analysis"], analysis_cmds)
        self.appendMenu(["&FlowStudio", "CFD"], cfd_setup_cmds + cfd_bc_cmds)
        self.appendMenu(["&FlowStudio", "Structural"], structural_cmds)
        self.appendMenu(["&FlowStudio", "Electrostatic"], electrostatic_cmds)
        self.appendMenu(["&FlowStudio", "Electromagnetic"], electromagnetic_cmds)
        self.appendMenu(["&FlowStudio", "Thermal"], thermal_cmds)
        self.appendMenu(["&FlowStudio", "Mesh"], mesh_cmds)
        self.appendMenu(["&FlowStudio", "Solve"], solve_cmds)
        self.appendMenu(["&FlowStudio", "Post-Processing"], post_cmds)
        self.appendMenu(["&FlowStudio", "Evaluation"], measurement_cmds)

    def Activated(self):
        """Called every time the workbench becomes active."""
        pass

    def Deactivated(self):
        """Called when switching away from this workbench."""
        pass

    def GetClassName(self):
        return "Gui::PythonWorkbench"


FreeCADGui.addWorkbench(FlowStudioWorkbench())
FreeCAD.Console.PrintLog("FlowStudio: Workbench registered successfully\n")
