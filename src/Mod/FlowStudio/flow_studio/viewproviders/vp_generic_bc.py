# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Generic view provider for non-CFD boundary condition objects."""

import FreeCADGui

from flow_studio.viewproviders.base_vp import BaseFlowVP


class VPGenericBC(BaseFlowVP):
    icon_name = "FlowStudioGeneric.svg"

    def setEdit(self, vobj, mode=0):
        from flow_studio.taskpanels.task_generic_bc import TaskGenericBC
        FreeCADGui.Control.showDialog(TaskGenericBC(vobj.Object))
        return True
