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

    ANALYSIS_COMMANDS = [
        "FlowStudio_Analysis",
        "FlowStudio_StructuralAnalysis",
        "FlowStudio_ElectrostaticAnalysis",
        "FlowStudio_ElectromagneticAnalysis",
        "FlowStudio_ThermalAnalysis",
    ]

    CFD_SETUP_COMMANDS = [
        "FlowStudio_PhysicsModel",
        "FlowStudio_FluidMaterial",
        "FlowStudio_InitialConditions",
        "FlowStudio_BC_Inlet",
        "FlowStudio_BC_Outlet",
        "FlowStudio_BC_Wall",
        "FlowStudio_BC_OpenBoundary",
        "FlowStudio_BC_Symmetry",
    ]

    MESH_SOLVE_COMMANDS = [
        "FlowStudio_MeshGmsh",
        "FlowStudio_MeshRegion",
        "FlowStudio_BoundaryLayer",
        "FlowStudio_SolverSettings",
        "FlowStudio_RunSolver",
    ]

    POST_COMMANDS = [
        "FlowStudio_PostPipeline",
        "FlowStudio_PostContour",
        "FlowStudio_PostStreamlines",
        "FlowStudio_PostProbe",
        "FlowStudio_PostForceReport",
        "FlowStudio_GenerateParaviewScript",
    ]

    PHYSICS_COMMANDS = [
        "FlowStudio_ElectrostaticMaterial",
        "FlowStudio_ElectrostaticPhysics",
        "FlowStudio_BC_ElectricPotential",
        "FlowStudio_BC_SurfaceCharge",
        "FlowStudio_BC_ElectricFlux",
        "Separator",
        "FlowStudio_ElectromagneticMaterial",
        "FlowStudio_ElectromagneticPhysics",
        "FlowStudio_BC_MagneticPotential",
        "FlowStudio_BC_CurrentDensity",
        "FlowStudio_BC_MagneticFluxDensity",
        "FlowStudio_BC_FarFieldEM",
    ]

    ENTERPRISE_COMMANDS = [
        "FlowStudio_ExportEnterpriseManifest",
        "FlowStudio_SubmitEnterpriseRun",
        "FlowStudio_SubmitEnterpriseRemoteRun",
        "FlowStudio_EnterpriseJobs",
    ]

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
        import flow_studio.commands  # noqa: F401
        import flow_studio.enterprise_commands  # noqa: F401
        from flow_studio.enterprise import initialize_workbench

        initialize_workbench()
        self.appendToolbar("FlowStudio Analysis", self.ANALYSIS_COMMANDS)
        self.appendToolbar("FlowStudio CFD Setup", self.CFD_SETUP_COMMANDS)
        self.appendToolbar("FlowStudio Solve", self.MESH_SOLVE_COMMANDS)
        self.appendToolbar("FlowStudio Enterprise", self.ENTERPRISE_COMMANDS)
        self.appendToolbar("FlowStudio Physics", self.PHYSICS_COMMANDS)

        self.appendMenu("FlowStudio", self.ANALYSIS_COMMANDS)
        self.appendMenu(["FlowStudio", "CFD Setup"], self.CFD_SETUP_COMMANDS)
        self.appendMenu(["FlowStudio", "Physics Setup"], self.PHYSICS_COMMANDS)
        self.appendMenu(["FlowStudio", "Solve"], self.MESH_SOLVE_COMMANDS)
        self.appendMenu(["FlowStudio", "Post-Processing"], self.POST_COMMANDS)
        self.appendMenu(["FlowStudio", "Enterprise"], self.ENTERPRISE_COMMANDS)

    def Activated(self):
        """Called every time the workbench becomes active."""
        from flow_studio.enterprise import on_workbench_activated

        on_workbench_activated()

    def Deactivated(self):
        """Called when switching away from this workbench."""
        pass

    def GetClassName(self):
        return "Gui::PythonWorkbench"


FreeCADGui.addWorkbench(FlowStudioWorkbench())
FreeCAD.Console.PrintLog("FlowStudio: Workbench registered successfully\n")
