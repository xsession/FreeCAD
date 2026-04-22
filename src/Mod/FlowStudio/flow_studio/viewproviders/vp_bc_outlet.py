# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************
"""ViewProvider for BCOutlet."""
import FreeCADGui
from flow_studio.viewproviders.base_vp import BaseFlowVP

class VPBCOutlet(BaseFlowVP):
    icon_name = "FlowStudioOutlet.svg"
    def setEdit(self, vobj, mode=0):
        from flow_studio.taskpanels.task_bc_outlet import TaskBCOutlet
        return self.show_task_panel(TaskBCOutlet, vobj.Object)
