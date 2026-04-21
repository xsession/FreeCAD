# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""View provider for non-fluid material objects."""

import FreeCADGui

from flow_studio.viewproviders.base_vp import BaseFlowVP


class VPMaterial(BaseFlowVP):
    icon_name = "FlowStudioMaterial.svg"

    def setEdit(self, vobj, mode=0):
        from flow_studio.taskpanels.task_materials import TaskMaterial
        FreeCADGui.Control.showDialog(TaskMaterial(vobj.Object))
        return True
