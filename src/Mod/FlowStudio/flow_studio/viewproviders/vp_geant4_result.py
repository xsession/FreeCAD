# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""ViewProvider for Geant4Result."""

from flow_studio.viewproviders.base_vp import BaseFlowVP


class VPGeant4Result(BaseFlowVP):
    icon_name = "FlowStudioPost.svg"

    def claimChildren(self):
        if hasattr(self, "Object") and self.Object:
            children = []
            children.extend(list(getattr(self.Object, "ScoringResults", []) or []))
            children.extend(list(getattr(self.Object, "DetectorResults", []) or []))
            return children
        return []

    def onDelete(self, vobj, sub_elements):
        obj = vobj.Object
        if obj is None or getattr(obj, "Document", None) is None:
            return True

        doc = obj.Document
        children = []
        children.extend(list(getattr(obj, "ScoringResults", []) or []))
        children.extend(list(getattr(obj, "DetectorResults", []) or []))
        for child in children:
            try:
                doc.removeObject(child.Name)
            except Exception:
                pass
        return True

    def setEdit(self, vobj, mode=0):
        from flow_studio.taskpanels.task_geant4_result import TaskGeant4Result

        return self.show_task_panel(TaskGeant4Result, vobj.Object)