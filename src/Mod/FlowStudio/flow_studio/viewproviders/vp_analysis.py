# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""ViewProvider for CFDAnalysis."""

import FreeCAD
from flow_studio.viewproviders.base_vp import BaseFlowVP


class VPCFDAnalysis(BaseFlowVP):
    icon_name = "FlowStudioAnalysis.svg"

    def claimChildren(self):
        if hasattr(self, "Object") and self.Object:
            return self.Object.Group
        return []

    def onDelete(self, vobj, sub_elements):
        """Cascade-delete all child objects when the analysis is removed.

        Without this, deleting an analysis leaves physics models, materials,
        boundary conditions, mesh objects, and solvers orphaned in the
        document tree.
        """
        obj = vobj.Object
        if obj is None:
            return True

        doc = obj.Document

        # Collect all children (iterate a copy — Group changes during removal)
        children = list(obj.Group) if hasattr(obj, "Group") else []

        # Remove children in reverse order (deepest first) so that any
        # sub-groups (e.g. mesh regions inside a mesh object) are handled.
        for child in reversed(children):
            # Recursively remove sub-group children first
            if hasattr(child, "Group"):
                for sub in reversed(list(child.Group)):
                    try:
                        doc.removeObject(sub.Name)
                    except Exception:
                        pass
            try:
                doc.removeObject(child.Name)
            except Exception:
                pass

        FreeCAD.Console.PrintMessage(
            f"FlowStudio: Removed {len(children)} child objects "
            f"from analysis '{obj.Label}'\n"
        )
        return True
