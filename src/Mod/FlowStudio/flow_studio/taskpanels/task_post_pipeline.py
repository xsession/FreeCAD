# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Task panel for Post-Processing pipeline."""

import FreeCAD
from PySide import QtGui
from flow_studio.taskpanels.base_taskpanel import BaseTaskPanel


class TaskPostPipeline(BaseTaskPanel):

    def _build_form(self):
        widget = QtGui.QWidget()
        layout = QtGui.QVBoxLayout(widget)
        layout.addWidget(QtGui.QLabel("<b>Post-Processing</b>"))

        # Visualization type
        self.cb_vis = self._combo(
            ["Contour (Surface)", "Contour (Slice)", "Streamlines",
             "Vectors", "Iso-Surface"],
            self.obj.VisualizationType,
        )
        self._add_row(layout, "Visualization:", self.cb_vis)

        # Active field
        fields = list(self.obj.AvailableFields) if self.obj.AvailableFields else [
            "U", "p", "k", "omega", "epsilon", "nuTilda", "T",
            "UMean", "pMean",
        ]
        self.cb_field = self._combo(fields, self.obj.ActiveField)
        self._add_row(layout, "Field:", self.cb_field)

        # Range
        self.chk_auto = self._checkbox(self.obj.AutoRange)
        self._add_row(layout, "Auto Range:", self.chk_auto)
        self.sp_min = self._spin_float(self.obj.MinRange)
        self._add_row(layout, "Min Value:", self.sp_min)
        self.sp_max = self._spin_float(self.obj.MaxRange)
        self._add_row(layout, "Max Value:", self.sp_max)

        # Load results button
        btn_load = QtGui.QPushButton("Load Results")
        btn_load.clicked.connect(self._load_results)
        layout.addWidget(btn_load)

        layout.addStretch()
        return widget

    def _load_results(self):
        FreeCAD.Console.PrintMessage(
            "FlowStudio: Loading results... (VTK pipeline pending)\n"
        )

    def _store(self):
        self.obj.VisualizationType = self.cb_vis.currentText()
        self.obj.ActiveField = self.cb_field.currentText()
        self.obj.AutoRange = self.chk_auto.isChecked()
        self.obj.MinRange = self.sp_min.value()
        self.obj.MaxRange = self.sp_max.value()
