# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************
"""ViewProvider for Solver."""
import FreeCADGui
from flow_studio.viewproviders.base_vp import BaseFlowVP

class VPSolver(BaseFlowVP):
    icon_name = "FlowStudioSolver.svg"
    def setEdit(self, vobj, mode=0):
        from flow_studio.taskpanels.task_solver import TaskSolver
        return self.show_task_panel(TaskSolver, vobj.Object)
