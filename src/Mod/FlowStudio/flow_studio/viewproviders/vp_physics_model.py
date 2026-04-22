# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""ViewProvider for PhysicsModel."""

import FreeCADGui
from flow_studio.viewproviders.base_vp import BaseFlowVP


class VPPhysicsModel(BaseFlowVP):
    icon_name = "FlowStudioPhysics.svg"

    def setEdit(self, vobj, mode=0):
        from flow_studio.taskpanels.task_physics_model import TaskPhysicsModel
        return self.show_task_panel(TaskPhysicsModel, vobj.Object)
