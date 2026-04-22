# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""ViewProvider for FluidMaterial."""

import FreeCADGui
from flow_studio.viewproviders.base_vp import BaseFlowVP


class VPFluidMaterial(BaseFlowVP):
    icon_name = "FlowStudioMaterial.svg"

    def setEdit(self, vobj, mode=0):
        from flow_studio.taskpanels.task_fluid_material import TaskFluidMaterial
        return self.show_task_panel(TaskFluidMaterial, vobj.Object)
