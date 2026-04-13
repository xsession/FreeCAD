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
        pass  # Skeleton: load only the bare frame for now

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
