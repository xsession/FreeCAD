# SPDX-License-Identifier: LGPL-2.1-or-later
"""SheetMetal workbench GUI init stub."""

import FreeCADGui


class SheetMetalWorkbench(FreeCADGui.Workbench):
    MenuText = "SheetMetal"
    ToolTip = "Sheet metal tools"
    Icon = ""

    def Initialize(self):
        pass

    def GetClassName(self):
        return "Gui::PythonWorkbench"


FreeCADGui.addWorkbench(SheetMetalWorkbench())
