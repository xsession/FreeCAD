# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""ViewProvider for InitialConditions."""

import FreeCADGui
from flow_studio.viewproviders.base_vp import BaseFlowVP


class VPInitialConditions(BaseFlowVP):
    icon_name = "FlowStudioInitial.svg"

    def setEdit(self, vobj, mode=0):
        from flow_studio.taskpanels.task_initial_conditions import TaskInitialConditions
        panel = TaskInitialConditions(vobj.Object)
        FreeCADGui.Control.showDialog(panel)
        return True
