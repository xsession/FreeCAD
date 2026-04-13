# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************
"""ViewProvider for MeshGmsh."""
import FreeCADGui
from flow_studio.viewproviders.base_vp import BaseFlowVP

class VPMeshGmsh(BaseFlowVP):
    icon_name = "FlowStudioMesh.svg"
    def setEdit(self, vobj, mode=0):
        from flow_studio.taskpanels.task_mesh_gmsh import TaskMeshGmsh
        FreeCADGui.Control.showDialog(TaskMeshGmsh(vobj.Object))
        return True
