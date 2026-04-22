# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************
"""ViewProvider for BCWall."""
import FreeCADGui
from flow_studio.viewproviders.base_vp import BaseFlowVP

class VPBCWall(BaseFlowVP):
    icon_name = "FlowStudioWall.svg"
    def setEdit(self, vobj, mode=0):
        from flow_studio.taskpanels.task_bc_wall import TaskBCWall
        return self.show_task_panel(TaskBCWall, vobj.Object)
