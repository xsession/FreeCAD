# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************
"""ViewProvider for MeasurementVolume."""
import FreeCADGui
from flow_studio.viewproviders.base_vp import BaseFlowVP


class VPMeasurementVolume(BaseFlowVP):
    icon_name = "FlowStudioPost.svg"

    def setEdit(self, vobj, mode=0):
        from flow_studio.taskpanels.task_measurement_volume import TaskMeasurementVolume
        return self.show_task_panel(TaskMeasurementVolume, vobj.Object)
