# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************
"""ViewProvider for BCInlet."""
import FreeCADGui
from flow_studio.viewproviders.base_vp import BaseFlowVP

class VPBCInlet(BaseFlowVP):
    icon_name = "FlowStudioInlet.svg"
    def setEdit(self, vobj, mode=0):
        from flow_studio.taskpanels.task_bc_inlet import TaskBCInlet
        return self.show_task_panel(TaskBCInlet, vobj.Object)
