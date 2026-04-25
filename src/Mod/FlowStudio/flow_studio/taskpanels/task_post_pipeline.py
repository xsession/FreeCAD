# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Task panel for Post-Processing pipeline."""

import FreeCAD
from PySide import QtGui
from flow_studio.taskpanels.base_taskpanel import BaseTaskPanel
from flow_studio.ui.post_pipeline_presenter import PostPipelinePresenter, PostPipelineSettings


class TaskPostPipeline(BaseTaskPanel):

    SUMMARY_TITLE = "Post-Processing"
    SUMMARY_DETAIL = (
        "Choose how {label} should visualize fields, ranges, and loaded result data."
    )

    def __init__(self, obj):
        self._presenter = PostPipelinePresenter()
        super().__init__(obj)

    def _build_task_validation(self):
        level, title, detail = self._presenter.build_validation(self._current_settings())
        if level:
            return level, title, detail
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

    def _current_settings(self):
        if not hasattr(self, "cb_vis"):
            return self._presenter.read_settings(self.obj)
        return PostPipelineSettings(
            visualization_type=self.cb_vis.currentText(),
            active_field=self.cb_field.currentText(),
            auto_range=self.chk_auto.isChecked(),
            min_range=self.sp_min.value(),
            max_range=self.sp_max.value(),
            available_fields=tuple(str(field) for field in (getattr(self.obj, "AvailableFields", []) or [])),
            result_file=str(getattr(self.obj, "ResultFile", "") or ""),
        )

    def _load_results(self):
        FreeCAD.Console.PrintMessage(
            "FlowStudio: Loading results... (VTK pipeline pending)\n"
        )

    def _store(self):
        self._presenter.persist_settings(self.obj, self._current_settings())
