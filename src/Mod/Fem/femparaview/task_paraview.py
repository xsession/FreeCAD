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

"""Task panel for ParaView integration in FreeCAD FEM."""

__title__ = "FreeCAD FEM ParaView Task Panel"
__author__ = "FreeCAD contributors"
__url__ = "https://www.freecad.org"

import os

import FreeCAD
import FreeCADGui
from FreeCAD import Qt

from PySide import QtCore, QtGui, QtWidgets

from femparaview import paraview_bridge


class TaskParaView:
    """Task panel for ParaView integration.

    Provides buttons for:
    - Opening results in ParaView
    - Exporting VTK files
    - Generating ParaView screenshots
    - Configuring ParaView path
    """

    def __init__(self, analysis=None):
        self.analysis = analysis
        self.form = self._create_widget()
        self._update_status()

    def _create_widget(self):
        """Build the task panel widget."""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)

        # --- Status group ---
        status_group = QtWidgets.QGroupBox(
            Qt.QT_TRANSLATE_NOOP("FEM_ParaView", "ParaView Status")
        )
        status_layout = QtWidgets.QFormLayout(status_group)

        self.lbl_status = QtWidgets.QLabel("Checking...")
        status_layout.addRow(
            Qt.QT_TRANSLATE_NOOP("FEM_ParaView", "Status:"),
            self.lbl_status,
        )

        self.lbl_version = QtWidgets.QLabel("")
        status_layout.addRow(
            Qt.QT_TRANSLATE_NOOP("FEM_ParaView", "Version:"),
            self.lbl_version,
        )

        self.lbl_path = QtWidgets.QLabel("")
        self.lbl_path.setWordWrap(True)
        status_layout.addRow(
            Qt.QT_TRANSLATE_NOOP("FEM_ParaView", "Path:"),
            self.lbl_path,
        )

        layout.addWidget(status_group)

        # --- Actions group ---
        actions_group = QtWidgets.QGroupBox(
            Qt.QT_TRANSLATE_NOOP("FEM_ParaView", "Actions")
        )
        actions_layout = QtWidgets.QVBoxLayout(actions_group)

        self.btn_open = QtWidgets.QPushButton(
            Qt.QT_TRANSLATE_NOOP("FEM_ParaView", "Open Results in ParaView")
        )
        self.btn_open.setToolTip(
            Qt.QT_TRANSLATE_NOOP(
                "FEM_ParaView",
                "Export all analysis results and open them in ParaView "
                "with a pre-configured visualization pipeline"
            )
        )
        self.btn_open.clicked.connect(self._on_open_paraview)
        actions_layout.addWidget(self.btn_open)

        self.btn_export = QtWidgets.QPushButton(
            Qt.QT_TRANSLATE_NOOP("FEM_ParaView", "Export VTK Files")
        )
        self.btn_export.setToolTip(
            Qt.QT_TRANSLATE_NOOP(
                "FEM_ParaView",
                "Export analysis results and mesh to VTK format "
                "without launching ParaView"
            )
        )
        self.btn_export.clicked.connect(self._on_export_vtk)
        actions_layout.addWidget(self.btn_export)

        self.btn_screenshot = QtWidgets.QPushButton(
            Qt.QT_TRANSLATE_NOOP("FEM_ParaView", "Generate Screenshot")
        )
        self.btn_screenshot.setToolTip(
            Qt.QT_TRANSLATE_NOOP(
                "FEM_ParaView",
                "Use pvpython to render a high-quality screenshot "
                "of the results (requires pvpython)"
            )
        )
        self.btn_screenshot.clicked.connect(self._on_screenshot)
        actions_layout.addWidget(self.btn_screenshot)

        layout.addWidget(actions_group)

        # --- Settings group ---
        settings_group = QtWidgets.QGroupBox(
            Qt.QT_TRANSLATE_NOOP("FEM_ParaView", "Settings")
        )
        settings_layout = QtWidgets.QFormLayout(settings_group)

        # ParaView binary path
        pv_row = QtWidgets.QHBoxLayout()
        self.edit_pv_path = QtWidgets.QLineEdit()
        self.edit_pv_path.setPlaceholderText(
            Qt.QT_TRANSLATE_NOOP("FEM_ParaView", "Auto-detect")
        )
        pv_row.addWidget(self.edit_pv_path)
        self.btn_browse_pv = QtWidgets.QPushButton("...")
        self.btn_browse_pv.setFixedWidth(30)
        self.btn_browse_pv.clicked.connect(self._on_browse_paraview)
        pv_row.addWidget(self.btn_browse_pv)
        settings_layout.addRow(
            Qt.QT_TRANSLATE_NOOP("FEM_ParaView", "ParaView:"),
            pv_row,
        )

        # Export directory
        dir_row = QtWidgets.QHBoxLayout()
        self.edit_export_dir = QtWidgets.QLineEdit()
        self.edit_export_dir.setPlaceholderText(
            Qt.QT_TRANSLATE_NOOP("FEM_ParaView", "Auto (near document)")
        )
        dir_row.addWidget(self.edit_export_dir)
        self.btn_browse_dir = QtWidgets.QPushButton("...")
        self.btn_browse_dir.setFixedWidth(30)
        self.btn_browse_dir.clicked.connect(self._on_browse_export_dir)
        dir_row.addWidget(self.btn_browse_dir)
        settings_layout.addRow(
            Qt.QT_TRANSLATE_NOOP("FEM_ParaView", "Export dir:"),
            dir_row,
        )

        self.btn_apply_settings = QtWidgets.QPushButton(
            Qt.QT_TRANSLATE_NOOP("FEM_ParaView", "Apply Settings")
        )
        self.btn_apply_settings.clicked.connect(self._on_apply_settings)
        settings_layout.addRow("", self.btn_apply_settings)

        layout.addWidget(settings_group)

        # --- Export info ---
        self.lbl_export_info = QtWidgets.QLabel("")
        self.lbl_export_info.setWordWrap(True)
        self.lbl_export_info.setStyleSheet("QLabel { color: gray; }")
        layout.addWidget(self.lbl_export_info)

        layout.addStretch()

        widget.setWindowTitle(
            Qt.QT_TRANSLATE_NOOP("FEM_ParaView", "ParaView Integration")
        )

        # Load saved settings
        self._load_settings()

        return widget

    def _load_settings(self):
        """Load settings from FreeCAD preferences."""
        prefs = paraview_bridge._get_pref_group()
        self.edit_pv_path.setText(prefs.GetString("ParaViewBinary", ""))
        self.edit_export_dir.setText(prefs.GetString("ExportDirectory", ""))

    def _update_status(self):
        """Update the ParaView status display."""
        pv_bin = paraview_bridge.find_paraview_binary()
        if pv_bin:
            self.lbl_status.setText(
                '<span style="color: green;">Available</span>'
            )
            self.lbl_path.setText(pv_bin)
            self.btn_open.setEnabled(True)
            version = paraview_bridge.get_paraview_version()
            self.lbl_version.setText(version or "Unknown")
        else:
            self.lbl_status.setText(
                '<span style="color: red;">Not found</span>'
            )
            self.lbl_path.setText("Not found")
            self.lbl_version.setText("N/A")
            self.btn_open.setEnabled(False)

        pvpy = paraview_bridge.find_pvpython_binary()
        self.btn_screenshot.setEnabled(bool(pvpy))

        # Check if analysis has results
        has_results = False
        if self.analysis:
            for obj in self.analysis.Group:
                if obj.isDerivedFrom("Fem::FemPostPipeline") or \
                   obj.isDerivedFrom("Fem::FemResultObject") or \
                   obj.isDerivedFrom("Fem::FemMeshObject"):
                    has_results = True
                    break
        self.btn_export.setEnabled(has_results)
        if not has_results:
            self.lbl_export_info.setText(
                "No results or mesh found in the active analysis. "
                "Run a solver first to generate results."
            )

    def _on_open_paraview(self):
        """Open analysis results in ParaView."""
        if not self.analysis:
            QtWidgets.QMessageBox.warning(
                self.form,
                "No Analysis",
                "No active FEM analysis found.",
            )
            return

        self.lbl_export_info.setText("Exporting and launching ParaView...")
        QtCore.QCoreApplication.processEvents()

        success = paraview_bridge.open_analysis_in_paraview(self.analysis)
        if success:
            self.lbl_export_info.setText("ParaView launched successfully.")
        else:
            self.lbl_export_info.setText(
                "Failed to launch ParaView. Check the Report View for details."
            )

    def _on_export_vtk(self):
        """Export VTK files without launching ParaView."""
        if not self.analysis:
            return

        self.lbl_export_info.setText("Exporting...")
        QtCore.QCoreApplication.processEvents()

        exported = paraview_bridge.export_analysis_vtk(self.analysis)
        if exported:
            self.lbl_export_info.setText(
                f"Exported {len(exported)} file(s) to:\n"
                + "\n".join(exported)
            )
        else:
            self.lbl_export_info.setText("No files exported.")

    def _on_screenshot(self):
        """Generate a screenshot using pvpython."""
        if not self.analysis:
            return

        self.lbl_export_info.setText("Generating screenshot with pvpython...")
        QtCore.QCoreApplication.processEvents()

        # Export first
        exported = paraview_bridge.export_analysis_vtk(self.analysis)
        if not exported:
            self.lbl_export_info.setText("No results to screenshot.")
            return

        # Generate screenshot from first result
        export_dir = os.path.dirname(exported[0])
        output_image = os.path.join(export_dir, "fem_result_screenshot.png")

        result = paraview_bridge.generate_screenshot(
            exported[0], output_image
        )
        if result:
            self.lbl_export_info.setText(f"Screenshot saved: {result}")
        else:
            self.lbl_export_info.setText(
                "Screenshot generation failed. Check Report View."
            )

    def _on_browse_paraview(self):
        """Browse for ParaView binary."""
        if os.name == "nt":
            filter_str = "Executables (*.exe);;All files (*.*)"
        else:
            filter_str = "All files (*)"

        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self.form,
            "Select ParaView executable",
            "",
            filter_str,
        )
        if path:
            self.edit_pv_path.setText(path)

    def _on_browse_export_dir(self):
        """Browse for export directory."""
        path = QtWidgets.QFileDialog.getExistingDirectory(
            self.form,
            "Select export directory",
        )
        if path:
            self.edit_export_dir.setText(path)

    def _on_apply_settings(self):
        """Save settings to FreeCAD preferences."""
        prefs = paraview_bridge._get_pref_group()
        prefs.SetString("ParaViewBinary", self.edit_pv_path.text())
        prefs.SetString("ExportDirectory", self.edit_export_dir.text())
        self._update_status()
        self.lbl_export_info.setText("Settings saved.")

    def accept(self):
        """Called when OK is pressed."""
        self._on_apply_settings()
        FreeCADGui.Control.closeDialog()

    def reject(self):
        """Called when Cancel is pressed."""
        FreeCADGui.Control.closeDialog()

    def getStandardButtons(self):
        """Return standard buttons for the task panel."""
        return (
            QtWidgets.QDialogButtonBox.Ok
            | QtWidgets.QDialogButtonBox.Cancel
        )
