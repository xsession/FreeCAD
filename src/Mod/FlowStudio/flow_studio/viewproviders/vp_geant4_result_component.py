# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""ViewProvider for typed Geant4 result child objects."""

from flow_studio.viewproviders.base_vp import BaseFlowVP


class VPGeant4ResultComponent(BaseFlowVP):
    icon_name = "FlowStudioPost.svg"

    def setEdit(self, vobj, mode=0):
        from flow_studio.taskpanels.task_geant4_result_component import TaskGeant4ResultComponent

        return self.show_task_panel(TaskGeant4ResultComponent, vobj.Object)