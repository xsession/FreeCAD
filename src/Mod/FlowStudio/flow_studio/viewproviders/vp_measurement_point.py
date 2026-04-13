# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************
"""ViewProvider for MeasurementPoint."""
import FreeCADGui
from flow_studio.viewproviders.base_vp import BaseFlowVP


class VPMeasurementPoint(BaseFlowVP):
    icon_name = "FlowStudioPostProbe.svg"

    def setEdit(self, vobj, mode=0):
        from flow_studio.taskpanels.task_measurement_point import TaskMeasurementPoint
        FreeCADGui.Control.showDialog(TaskMeasurementPoint(vobj.Object))
        return True
