# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""FlowStudio – Multi-Physics Simulation Workbench – App-level initialization.

This module is loaded by FreeCAD at startup (even in console mode).
It registers import/export file types and unit tests.
Supports CFD, Structural, Electrostatic, Electromagnetic, and Thermal domains.
"""

import FreeCAD

# ---------------------------------------------------------------------------
# File format registrations
# ---------------------------------------------------------------------------
FreeCAD.addImportType(
    "OpenFOAM case (*.foam)", "flow_studio.feminout.importFlowStudio"
)
FreeCAD.addImportType(
    "VTK result (*.vtk *.vtu *.vtp)", "flow_studio.feminout.importFlowStudio"
)
FreeCAD.addImportType(
    "Elmer SIF (*.sif)", "flow_studio.feminout.importFlowStudio"
)

# ---------------------------------------------------------------------------
# Unit tests
# ---------------------------------------------------------------------------
FreeCAD.__unit_test__ += ["flow_studio.tests.TestFlowStudio"]
