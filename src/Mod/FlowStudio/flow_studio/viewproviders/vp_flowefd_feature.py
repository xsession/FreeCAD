# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""View providers for FloEFD-style setup/result feature objects."""

import FreeCADGui

from flow_studio.viewproviders.base_vp import BaseFlowVP


class VPFlowEFDFeature(BaseFlowVP):
    icon_name = "FlowStudioPost.svg"

    def setEdit(self, vobj, mode=0):
        obj = vobj.Object
        flow_type = getattr(obj, "FlowType", "")
        from flow_studio.taskpanels.task_flowefd_features import (
            TaskFan,
            TaskParticleStudy,
            TaskResultPlot,
            TaskVolumeSource,
        )

        panel_map = {
            "FlowStudio::VolumeSource": TaskVolumeSource,
            "FlowStudio::Fan": TaskFan,
            "FlowStudio::ResultPlot": TaskResultPlot,
            "FlowStudio::ParticleStudy": TaskParticleStudy,
        }
        panel_cls = panel_map.get(flow_type)
        if panel_cls is None:
            return False
        return self.show_task_panel(panel_cls, obj)
