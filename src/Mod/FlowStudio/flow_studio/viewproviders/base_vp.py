# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Base ViewProvider for FlowStudio objects."""

import os
import FreeCADGui

ICONS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Resources", "icons")


class BaseFlowVP:
    """Minimal ViewProvider proxy for FlowStudio objects."""

    icon_name = "FlowStudioGeneric.svg"

    def __init__(self, vobj):
        vobj.Proxy = self

    def getIcon(self):
        return os.path.join(ICONS_DIR, self.icon_name)

    def attach(self, vobj):
        self.Object = vobj.Object

    def claimChildren(self):
        return []

    def onDelete(self, vobj, sub_elements):
        return True

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        pass

    def setEdit(self, vobj, mode=0):
        """Open the task panel for editing."""
        # Subclasses override to show a task panel
        return False

    def unsetEdit(self, vobj, mode=0):
        FreeCADGui.Control.closeDialog()
        return True

    def doubleClicked(self, vobj):
        doc = FreeCADGui.getDocument(vobj.Object.Document)
        if not doc.getInEdit():
            doc.setEdit(vobj.Object.Name)
        else:
            FreeCAD.Console.PrintMessage(
                "FlowStudio: Task panel already open\n"
            )
        return True
