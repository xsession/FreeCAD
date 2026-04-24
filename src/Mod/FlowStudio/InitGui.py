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
from flow_studio.physics_domains import all_example_commands, example_command_groups
from RibbonMetadata import (
    build_contextual_ribbon_toolbar_name,
    build_ribbon_toolbar_name,
    register_contextual_ribbon_panel,
)

initialize_workbench = lambda: None  # noqa: E731
is_enterprise_enabled = lambda *_args, **_kwargs: False  # noqa: E731
on_workbench_activated = lambda: None  # noqa: E731

try:
    from flow_studio.enterprise import (
        initialize_workbench,
        is_enterprise_enabled,
        on_workbench_activated,
    )
except Exception as exc:  # pragma: no cover - startup resilience path
    FreeCAD.Console.PrintError(
        f"FlowStudio: enterprise layer unavailable ({exc}). Falling back to core mode.\n"
    )

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

    EXAMPLE_COMMAND_GROUPS = example_command_groups()
    EXAMPLE_COMMANDS = all_example_commands()

    ANALYSIS_COMMANDS = [
        "FlowStudio_Analysis",
        "FlowStudio_ProjectCockpit",
        "FlowStudio_StructuralAnalysis",
        "FlowStudio_ElectrostaticAnalysis",
        "FlowStudio_ElectromagneticAnalysis",
        "FlowStudio_ThermalAnalysis",
        "FlowStudio_OpticalAnalysis",
    ]

    CFD_SETUP_COMMANDS = [
        "FlowStudio_PhysicsModel",
        "FlowStudio_FluidMaterial",
        "FlowStudio_EngineeringDatabase",
        "FlowStudio_InitialConditions",
        "FlowStudio_ImportStep",
        "FlowStudio_CheckGeometry",
        "FlowStudio_ShowFluidVolume",
        "FlowStudio_LeakTracking",
        "FlowStudio_BC_Inlet",
        "FlowStudio_BC_Outlet",
        "FlowStudio_BC_Wall",
        "FlowStudio_BC_OpenBoundary",
        "FlowStudio_BC_Symmetry",
        "FlowStudio_Fan",
        "FlowStudio_VolumeSource",
    ]

    GEOMETRY_COMMANDS = [
        "FlowStudio_ImportStep",
        "FlowStudio_CheckGeometry",
        "FlowStudio_ShowFluidVolume",
        "FlowStudio_LeakTracking",
    ]

    MESH_SOLVE_COMMANDS = [
        "FlowStudio_MeshGmsh",
        "FlowStudio_MeshRegion",
        "FlowStudio_BoundaryLayer",
        "FlowStudio_SolverSettings",
        "FlowStudio_RunSolver",
        "FlowStudio_StopSolver",
    ]

    POST_COMMANDS = [
        "FlowStudio_PostPipeline",
        "FlowStudio_Geant4Result",
        "FlowStudio_ImportGeant4Result",
        "FlowStudio_PostContour",
        "FlowStudio_PostStreamlines",
        "FlowStudio_PostProbe",
        "FlowStudio_PostForceReport",
        "FlowStudio_SurfacePlot",
        "FlowStudio_CutPlot",
        "FlowStudio_XYPlot",
        "FlowStudio_FlowTrajectories",
        "FlowStudio_PointParameters",
        "FlowStudio_ParticleStudy",
        "FlowStudio_GenerateParaviewScript",
    ]

    ELECTROSTATIC_COMMANDS = [
        "FlowStudio_ElectrostaticMaterial",
        "FlowStudio_ElectrostaticPhysics",
        "FlowStudio_BC_ElectricPotential",
        "FlowStudio_BC_SurfaceCharge",
        "FlowStudio_BC_ElectricFlux",
    ]

    ELECTROMAGNETIC_COMMANDS = [
        "FlowStudio_ElectromagneticMaterial",
        "FlowStudio_ElectromagneticPhysics",
        "FlowStudio_BC_MagneticPotential",
        "FlowStudio_BC_CurrentDensity",
        "FlowStudio_BC_MagneticFluxDensity",
        "FlowStudio_BC_FarFieldEM",
    ]

    OPTICAL_COMMANDS = [
        "FlowStudio_OpticalMaterial",
        "FlowStudio_OpticalPhysics",
        "FlowStudio_BC_OpticalSource",
        "FlowStudio_BC_OpticalDetector",
        "FlowStudio_BC_OpticalBoundary",
        "FlowStudio_BC_Geant4Source",
        "FlowStudio_BC_Geant4Detector",
        "FlowStudio_BC_Geant4Scoring",
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
        "Separator",
        "FlowStudio_OpticalMaterial",
        "FlowStudio_OpticalPhysics",
        "FlowStudio_BC_OpticalSource",
        "FlowStudio_BC_OpticalDetector",
        "FlowStudio_BC_OpticalBoundary",
        "FlowStudio_BC_Geant4Source",
        "FlowStudio_BC_Geant4Detector",
        "FlowStudio_BC_Geant4Scoring",
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

    @staticmethod
    def _enterprise_disabled(*_args, **_kwargs):
        return False

    @staticmethod
    def _noop(*_args, **_kwargs):
        return None

    @staticmethod
    def _resolve_enterprise_callable(name, fallback):
        """Resolve enterprise hooks safely under FreeCAD's InitGui execution model."""
        candidate = globals().get(name, fallback)
        if callable(candidate):
            return candidate

        FreeCAD.Console.PrintError(
            f"FlowStudio: enterprise hook '{name}' unavailable at runtime. Falling back.\n"
        )
        return fallback

    # ------------------------------------------------------------------
    # Workbench lifecycle
    # ------------------------------------------------------------------
    def Initialize(self):
        """Called once when the workbench is first loaded."""
        import flow_studio.commands  # noqa: F401

        main_window_prefs = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/MainWindow")
        ribbon_enabled = bool(main_window_prefs.GetBool("UseRibbonBar", False))

        enterprise_enabled_fn = self._resolve_enterprise_callable(
            "is_enterprise_enabled", self._enterprise_disabled
        )
        initialize_workbench_fn = self._resolve_enterprise_callable(
            "initialize_workbench", self._noop
        )
        enterprise_enabled = enterprise_enabled_fn()
        if enterprise_enabled:
            import flow_studio.enterprise_commands  # noqa: F401

            initialize_workbench_fn()
        else:
            FreeCAD.Console.PrintLog(
                "FlowStudio: Enterprise feature set disabled by FLOWSTUDIO_ENTERPRISE_ENABLED.\n"
            )

        if ribbon_enabled:
            self.appendToolbar(
                build_ribbon_toolbar_name(
                    "Setup", "Analysis", "Home", order=10, home_priority="primary"
                ),
                self.ANALYSIS_COMMANDS,
            )
            for index, (group_key, _group_label, commands) in enumerate(self.EXAMPLE_COMMAND_GROUPS):
                self.appendToolbar(
                    build_ribbon_toolbar_name(
                        "Setup",
                        f"{group_key} Examples",
                        "Home",
                        order=20 + index,
                        home_priority="primary",
                    ),
                    list(commands),
                )
            self.appendToolbar(
                build_ribbon_toolbar_name(
                    "Setup", "Setup", "Home", order=40, home_priority="primary"
                ),
                [
                    "FlowStudio_PhysicsModel",
                    "FlowStudio_FluidMaterial",
                    "FlowStudio_EngineeringDatabase",
                    "FlowStudio_InitialConditions",
                ],
            )
            self.appendToolbar(
                build_ribbon_toolbar_name("Inspect", "Geometry", order=10), self.GEOMETRY_COMMANDS
            )
            self.appendToolbar(
                build_ribbon_toolbar_name("Setup", "Boundary Conditions", order=30),
                [
                    "FlowStudio_BC_Inlet",
                    "FlowStudio_BC_Outlet",
                    "FlowStudio_BC_Wall",
                    "FlowStudio_BC_OpenBoundary",
                    "FlowStudio_BC_Symmetry",
                    "FlowStudio_Fan",
                    "FlowStudio_VolumeSource",
                ],
            )
            self.appendToolbar(
                build_ribbon_toolbar_name("Setup", "Mesh", order=40),
                [
                    "FlowStudio_MeshGmsh",
                    "FlowStudio_MeshRegion",
                    "FlowStudio_BoundaryLayer",
                ],
            )
            self.appendToolbar(
                build_ribbon_toolbar_name(
                    "Solve", "Solve", "Home", order=10, home_priority="secondary"
                ),
                [
                    "FlowStudio_SolverSettings",
                    "FlowStudio_RunSolver",
                    "FlowStudio_StopSolver",
                ],
            )
            self.appendToolbar(
                build_ribbon_toolbar_name("Results", "Post-Processing", order=10),
                [
                    "FlowStudio_SurfacePlot",
                    "FlowStudio_CutPlot",
                    "FlowStudio_XYPlot",
                    "FlowStudio_FlowTrajectories",
                    "FlowStudio_PointParameters",
                    "FlowStudio_ParticleStudy",
                ],
            )
            if enterprise_enabled:
                self.appendToolbar(
                    build_ribbon_toolbar_name("Solve", "Enterprise", order=20),
                    self.ENTERPRISE_COMMANDS,
                )
            register_contextual_ribbon_panel(
                build_contextual_ribbon_toolbar_name(
                    "Simulation",
                    "Setup",
                    "Flow",
                    "CFD",
                    "Fem",
                    "Electro",
                    "Optical",
                    "Thermal",
                    "Structural",
                    workbench="FlowStudio",
                    color="#008b8b",
                    order=10,
                ),
                [
                    "FlowStudio_Analysis",
                    "FlowStudio_PhysicsModel",
                    "FlowStudio_FluidMaterial",
                    "FlowStudio_InitialConditions",
                ],
            )
            register_contextual_ribbon_panel(
                build_contextual_ribbon_toolbar_name(
                    "Simulation",
                    "Boundary Conditions",
                    "Flow",
                    "CFD",
                    "Fem",
                    "Electro",
                    "Optical",
                    "Thermal",
                    "Structural",
                    workbench="FlowStudio",
                    color="#008b8b",
                    order=20,
                ),
                [
                    "FlowStudio_BC_Inlet",
                    "FlowStudio_BC_Outlet",
                    "FlowStudio_BC_Wall",
                    "FlowStudio_BC_OpenBoundary",
                ],
            )
            register_contextual_ribbon_panel(
                build_contextual_ribbon_toolbar_name(
                    "Simulation",
                    "Mesh & Solve",
                    "Flow",
                    "CFD",
                    "Fem",
                    "Electro",
                    "Optical",
                    "Thermal",
                    "Structural",
                    workbench="FlowStudio",
                    color="#008b8b",
                    order=30,
                ),
                [
                    "FlowStudio_MeshGmsh",
                    "FlowStudio_MeshRegion",
                    "FlowStudio_SolverSettings",
                    "FlowStudio_RunSolver",
                    "FlowStudio_StopSolver",
                ],
            )
            register_contextual_ribbon_panel(
                build_contextual_ribbon_toolbar_name(
                    "Simulation",
                    "Results",
                    "Flow",
                    "CFD",
                    "Fem",
                    "Electro",
                    "Optical",
                    "Thermal",
                    "Structural",
                    workbench="FlowStudio",
                    color="#008b8b",
                    order=40,
                ),
                [
                    "FlowStudio_SurfacePlot",
                    "FlowStudio_CutPlot",
                    "FlowStudio_FlowTrajectories",
                    "FlowStudio_PointParameters",
                ],
            )
            register_contextual_ribbon_panel(
                build_contextual_ribbon_toolbar_name(
                    "Electrostatic",
                    "Electrostatic Setup",
                    "Electrostatic",
                    "Electric",
                    workbench="FlowStudio",
                    color="#1f6feb",
                    order=10,
                ),
                self.ELECTROSTATIC_COMMANDS,
            )
            register_contextual_ribbon_panel(
                build_contextual_ribbon_toolbar_name(
                    "Electromagnetic",
                    "Electromagnetic Setup",
                    "Electromagnetic",
                    "Magnetic",
                    workbench="FlowStudio",
                    color="#0e7490",
                    order=10,
                ),
                self.ELECTROMAGNETIC_COMMANDS,
            )
            register_contextual_ribbon_panel(
                build_contextual_ribbon_toolbar_name(
                    "Optical",
                    "Optical & Geant4",
                    "Optical",
                    "Geant4",
                    workbench="FlowStudio",
                    color="#7c3aed",
                    order=10,
                ),
                self.OPTICAL_COMMANDS,
            )
        else:
            self.appendToolbar("FlowStudio Analysis", self.ANALYSIS_COMMANDS)
            for group_key, _group_label, commands in self.EXAMPLE_COMMAND_GROUPS:
                self.appendToolbar(f"FlowStudio {group_key} Examples", list(commands))
            self.appendToolbar("FlowStudio CFD Setup", self.CFD_SETUP_COMMANDS)
            self.appendToolbar("FlowStudio Geometry Tools", self.GEOMETRY_COMMANDS)
            self.appendToolbar("FlowStudio Solve", self.MESH_SOLVE_COMMANDS)
            self.appendToolbar("FlowStudio Physics", self.PHYSICS_COMMANDS)
            if enterprise_enabled:
                self.appendToolbar("FlowStudio Enterprise", self.ENTERPRISE_COMMANDS)

        self.appendMenu("FlowStudio", self.ANALYSIS_COMMANDS)
        for _group_key, group_label, commands in self.EXAMPLE_COMMAND_GROUPS:
            self.appendMenu(["FlowStudio", "Examples", group_label], list(commands))
        self.appendMenu(["FlowStudio", "CFD Setup"], self.CFD_SETUP_COMMANDS)
        self.appendMenu(["FlowStudio", "Geometry Tools"], self.GEOMETRY_COMMANDS)
        self.appendMenu(["FlowStudio", "Physics Setup"], self.PHYSICS_COMMANDS)
        self.appendMenu(["FlowStudio", "Solve"], self.MESH_SOLVE_COMMANDS)
        self.appendMenu(["FlowStudio", "Post-Processing"], self.POST_COMMANDS)
        if enterprise_enabled:
            self.appendMenu(["FlowStudio", "Enterprise"], self.ENTERPRISE_COMMANDS)

    def Activated(self):
        """Called every time the workbench becomes active."""
        enterprise_enabled_fn = self._resolve_enterprise_callable(
            "is_enterprise_enabled", self._enterprise_disabled
        )
        on_workbench_activated_fn = self._resolve_enterprise_callable(
            "on_workbench_activated", self._noop
        )
        if enterprise_enabled_fn():
            on_workbench_activated_fn()

    def Deactivated(self):
        """Called when switching away from this workbench."""
        pass

    def GetClassName(self):
        return "Gui::PythonWorkbench"


FreeCADGui.addWorkbench(FlowStudioWorkbench())
FreeCAD.Console.PrintLog("FlowStudio: Workbench registered successfully\n")
