# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************
"""ViewProvider for PostPipeline."""
import FreeCADGui
from flow_studio.viewproviders.base_vp import BaseFlowVP

class VPPostPipeline(BaseFlowVP):
    icon_name = "FlowStudioPost.svg"
    def setEdit(self, vobj, mode=0):
        from flow_studio.taskpanels.task_post_pipeline import TaskPostPipeline
        FreeCADGui.Control.showDialog(TaskPostPipeline(vobj.Object))
        return True
