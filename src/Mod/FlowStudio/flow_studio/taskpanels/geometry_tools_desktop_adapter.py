# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Desktop adapter for FlowStudio geometry tool dialogs and reporting."""

from __future__ import annotations

import FreeCAD
import FreeCADGui


class FreeCADGeometryToolsDesktopAdapter:
    """Adapter that binds geometry-tool UI intents to the active FreeCAD desktop."""

    def get_document_object(self, object_name):
        if not FreeCAD.ActiveDocument or not object_name:
            return None
        return FreeCAD.ActiveDocument.getObject(object_name)

    def report_check_completed(self, lines):
        FreeCAD.Console.PrintMessage("[FlowStudio] Check Geometry completed.\n")
        for line in lines:
            FreeCAD.Console.PrintMessage(f"{line}\n")

    def report_leak_tracking_completed(self, lines):
        FreeCAD.Console.PrintMessage("[FlowStudio] Leak Tracking completed.\n")
        for line in lines:
            FreeCAD.Console.PrintMessage(f"{line}\n")

    def open_leak_tracking_dialog(self, panel):
        try:
            FreeCADGui.Control.closeDialog()
        except Exception:
            pass
        FreeCADGui.Control.showDialog(panel)