# ***************************************************************************
# *   Copyright (c) 2026 FreeCAD contributors                              *
# *                                                                         *
# *   This file is part of the FreeCAD CAx development system.              *
# *                                                                         *
# *   This program is free software; you can redistribute it and/or modify  *
# *   it under the terms of the GNU Lesser General Public License (LGPL)    *
# *   as published by the Free Software Foundation; either version 2 of     *
# *   the License, or (at your option) any later version.                   *
# *   for detail see the LICENCE text file.                                 *
# *                                                                         *
# *   This program is distributed in the hope that it will be useful,       *
# *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
# *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
# *   GNU Library General Public License for more details.                  *
# *                                                                         *
# *   You should have received a copy of the GNU Library General Public     *
# *   License along with this program; if not, write to the Free Software   *
# *   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
# *   USA                                                                   *
# *                                                                         *
# ***************************************************************************

"""FreeCAD FEM ParaView command definitions."""

__title__ = "FreeCAD FEM ParaView commands"
__author__ = "FreeCAD contributors"
__url__ = "https://www.freecad.org"

import FreeCAD
import FreeCADGui
from FreeCAD import Qt

from femcommands.manager import CommandManager


class _ParaViewOpen(CommandManager):
    """The FEM_ParaViewOpen command definition.

    Exports the active analysis results to VTK and opens them in ParaView.
    """

    def __init__(self):
        super().__init__()
        self.menutext = Qt.QT_TRANSLATE_NOOP(
            "FEM_ParaViewOpen", "Open in ParaView"
        )
        self.tooltip = Qt.QT_TRANSLATE_NOOP(
            "FEM_ParaViewOpen",
            "Export analysis results and open them in ParaView "
            "with a pre-configured visualization pipeline",
        )
        self.is_active = "with_analysis"

    def Activated(self):
        from femparaview import paraview_bridge

        if not paraview_bridge.is_paraview_available():
            from PySide import QtWidgets

            QtWidgets.QMessageBox.warning(
                FreeCADGui.getMainWindow(),
                "ParaView Not Found",
                "ParaView could not be found on your system.\n"
                "Please install ParaView or set the path in\n"
                "FEM preferences (ParaView tab).",
            )
            return

        analysis = self.active_analysis
        if analysis is None:
            return

        FreeCAD.Console.PrintMessage("Exporting results and launching ParaView...\n")
        success = paraview_bridge.open_analysis_in_paraview(analysis)
        if success:
            FreeCAD.Console.PrintMessage("ParaView launched successfully.\n")
        else:
            FreeCAD.Console.PrintError(
                "Failed to launch ParaView. Check Report View for details.\n"
            )


class _ParaViewExport(CommandManager):
    """The FEM_ParaViewExport command definition.

    Exports all analysis results to VTK format.
    """

    def __init__(self):
        super().__init__()
        self.menutext = Qt.QT_TRANSLATE_NOOP(
            "FEM_ParaViewExport", "Export to VTK (ParaView)"
        )
        self.tooltip = Qt.QT_TRANSLATE_NOOP(
            "FEM_ParaViewExport",
            "Export all analysis results and meshes to VTK format "
            "for use with ParaView or other visualization tools",
        )
        self.is_active = "with_analysis"

    def Activated(self):
        from femparaview import paraview_bridge

        analysis = self.active_analysis
        if analysis is None:
            return

        FreeCAD.Console.PrintMessage("Exporting analysis results to VTK...\n")
        exported = paraview_bridge.export_analysis_vtk(analysis)
        if exported:
            FreeCAD.Console.PrintMessage(
                f"Exported {len(exported)} file(s):\n"
            )
            for f in exported:
                FreeCAD.Console.PrintMessage(f"  {f}\n")
        else:
            FreeCAD.Console.PrintWarning("No results found to export.\n")


class _ParaViewScreenshot(CommandManager):
    """The FEM_ParaViewScreenshot command definition.

    Uses pvpython to generate a high-quality screenshot of results.
    """

    def __init__(self):
        super().__init__()
        self.menutext = Qt.QT_TRANSLATE_NOOP(
            "FEM_ParaViewScreenshot", "ParaView Screenshot"
        )
        self.tooltip = Qt.QT_TRANSLATE_NOOP(
            "FEM_ParaViewScreenshot",
            "Generate a high-quality screenshot of analysis results "
            "using ParaView's pvpython rendering engine",
        )
        self.is_active = "with_analysis"

    def Activated(self):
        import os
        from femparaview import paraview_bridge

        if not paraview_bridge.find_pvpython_binary():
            from PySide import QtWidgets

            QtWidgets.QMessageBox.warning(
                FreeCADGui.getMainWindow(),
                "pvpython Not Found",
                "pvpython could not be found on your system.\n"
                "It is usually installed alongside ParaView.",
            )
            return

        analysis = self.active_analysis
        if analysis is None:
            return

        FreeCAD.Console.PrintMessage("Exporting results for screenshot...\n")
        exported = paraview_bridge.export_analysis_vtk(analysis)
        if not exported:
            FreeCAD.Console.PrintWarning("No results found to screenshot.\n")
            return

        export_dir = os.path.dirname(exported[0])
        output_image = os.path.join(export_dir, "fem_result_screenshot.png")

        FreeCAD.Console.PrintMessage("Generating screenshot with pvpython...\n")
        result = paraview_bridge.generate_screenshot(exported[0], output_image)
        if result:
            FreeCAD.Console.PrintMessage(f"Screenshot saved: {result}\n")
        else:
            FreeCAD.Console.PrintError("Screenshot generation failed.\n")


class _ParaViewPanel(CommandManager):
    """The FEM_ParaViewPanel command definition.

    Opens the ParaView integration task panel with all controls.
    """

    def __init__(self):
        super().__init__()
        self.menutext = Qt.QT_TRANSLATE_NOOP(
            "FEM_ParaViewPanel", "ParaView Panel"
        )
        self.tooltip = Qt.QT_TRANSLATE_NOOP(
            "FEM_ParaViewPanel",
            "Open the ParaView integration panel with export, "
            "launch, screenshot, and settings controls",
        )
        self.is_active = "with_analysis"

    def Activated(self):
        from femparaview.task_paraview import TaskParaView

        panel = TaskParaView(analysis=self.active_analysis)
        FreeCADGui.Control.showDialog(panel)


# Command registration
FreeCADGui.addCommand("FEM_ParaViewOpen", _ParaViewOpen())
FreeCADGui.addCommand("FEM_ParaViewExport", _ParaViewExport())
FreeCADGui.addCommand("FEM_ParaViewScreenshot", _ParaViewScreenshot())
FreeCADGui.addCommand("FEM_ParaViewPanel", _ParaViewPanel())
