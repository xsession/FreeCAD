# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Task panel for Post-Processing pipeline."""

import FreeCAD
from PySide import QtGui
from flow_studio.taskpanels.base_taskpanel import BaseTaskPanel


class TaskPostPipeline(BaseTaskPanel):

    SUMMARY_TITLE = "Post-Processing"
    SUMMARY_DETAIL = (
        "Choose how {label} should visualize fields, ranges, and loaded result data."
    )

    def _build_task_validation(self):
        result_file = str(getattr(self.obj, "ResultFile", "") or "").strip()
        available_fields = list(getattr(self.obj, "AvailableFields", []) or [])

        if not result_file and not available_fields:
            return (
                "info",
                "Load results to begin post-processing",
                "Choose a result file or run the solver so fields become available for visualization.",
            )

        if available_fields and str(getattr(self.obj, "ActiveField", "") or "") not in available_fields:
            return (
                "warning",
                "Active field is not available",
                "Select one of the loaded result fields before updating the post-processing view.",
            )

        if not bool(getattr(self.obj, "AutoRange", True)) and float(getattr(self.obj, "MinRange", 0.0)) >= float(getattr(self.obj, "MaxRange", 0.0)):
            return (
                "warning",
                "Manual range is invalid",
                "Set a minimum value smaller than the maximum value or re-enable automatic range.",
            )

        return super()._build_task_validation()

    def _build_form(self):
        widget = QtGui.QWidget()
        layout = QtGui.QVBoxLayout(widget)
        layout.addWidget(QtGui.QLabel("<b>Post-Processing</b>"))

        display = self._section(layout, "Display")
        self.cb_vis = self._combo(
            ["Contour (Surface)", "Contour (Slice)", "Streamlines",
             "Vectors", "Iso-Surface"],
            self.obj.VisualizationType,
        )
        self._add_row(display, "Visualization:", self.cb_vis)

        fields = list(self.obj.AvailableFields) if self.obj.AvailableFields else [
            "U", "p", "k", "omega", "epsilon", "nuTilda", "T",
            "UMean", "pMean",
        ]
        self.cb_field = self._combo(fields, self.obj.ActiveField)
        self._add_row(display, "Field:", self.cb_field)

        range_section = self._section(layout, "Range")
        self.chk_auto = self._checkbox(self.obj.AutoRange)
        self._add_row(range_section, "Auto Range:", self.chk_auto)
        self.sp_min = self._spin_float(self.obj.MinRange)
        self._add_row(range_section, "Min Value:", self.sp_min)
        self.sp_max = self._spin_float(self.obj.MaxRange)
        self._add_row(range_section, "Max Value:", self.sp_max)

        actions = self._section(layout, "Actions")
        btn_load = QtGui.QPushButton("Load Results")
        btn_load.clicked.connect(self._load_results)
        actions.addWidget(btn_load)

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
