# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************
"""ViewProvider for BCOpenBoundary."""
import FreeCADGui
from flow_studio.viewproviders.base_vp import BaseFlowVP

class VPBCOpenBoundary(BaseFlowVP):
    icon_name = "FlowStudioOpen.svg"
    def setEdit(self, vobj, mode=0):
        from flow_studio.taskpanels.task_bc_open import TaskBCOpen
        FreeCADGui.Control.showDialog(TaskBCOpen(vobj.Object))
        return True
