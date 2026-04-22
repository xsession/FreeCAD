# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Base task panel for FlowStudio dialogs."""

import FreeCAD
import FreeCADGui
from PySide import QtGui, QtCore


class BaseTaskPanel:
    """Common task panel base with accept/reject."""

    SUMMARY_TITLE = ""
    SUMMARY_DETAIL = ""
    VALIDATION_LEVEL = ""
    VALIDATION_TITLE = ""
    VALIDATION_DETAIL = ""

    def __init__(self, obj):
        self.obj = obj
        self.form = self._build_form()
        self._refresh_taskview_metadata()
        self._connect_taskview_metadata_signals()

    def _build_form(self):
        """Override to build the Qt widget. Return a QWidget."""
        widget = QtGui.QWidget()
        layout = QtGui.QVBoxLayout(widget)
        layout.addWidget(QtGui.QLabel("(no settings)"))
        return widget

    def accept(self):
        self._store()
        FreeCADGui.ActiveDocument.resetEdit()
        FreeCAD.ActiveDocument.recompute()
        return True

    def reject(self):
        FreeCADGui.ActiveDocument.resetEdit()
        return True

    def _store(self):
        """Override to write widget values back to the document object."""
        pass

    def _apply_task_summary(self):
        title, detail = self._build_task_summary()
        self.taskview_summary_title = title
        self.taskview_summary_detail = detail
        self._publish_taskview_property("taskview_summary_title", title)
        self._publish_taskview_property("taskview_summary_detail", detail)

    def _apply_task_validation(self):
        level, title, detail = self._build_task_validation()
        self.taskview_validation_level = level
        self.taskview_validation_title = title
        self.taskview_validation_detail = detail
        self._publish_taskview_property("taskview_validation_level", level)
        self._publish_taskview_property("taskview_validation_title", title)
        self._publish_taskview_property("taskview_validation_detail", detail)

    def _refresh_taskview_metadata(self, *_args):
        self._apply_task_summary()
        self._apply_task_validation()

    def _publish_taskview_property(self, name, value):
        if hasattr(self, "form") and self.form is not None:
            self.form.setProperty(name, value)

    def _connect_taskview_metadata_signals(self):
        if not hasattr(self, "form") or self.form is None:
            return

        self._connect_widget_metadata_signal(self.form)
        for widget in self.form.findChildren(QtGui.QWidget):
            self._connect_widget_metadata_signal(widget)

    def _connect_widget_metadata_signal(self, widget):
        refresh = self._refresh_taskview_metadata

        if isinstance(widget, QtGui.QLineEdit):
            widget.textChanged.connect(refresh)
        elif isinstance(widget, QtGui.QComboBox):
            widget.currentIndexChanged.connect(refresh)
        elif isinstance(widget, QtGui.QAbstractButton):
            widget.clicked.connect(refresh)
            if hasattr(widget, "toggled"):
                widget.toggled.connect(refresh)
        elif isinstance(widget, QtGui.QSpinBox):
            widget.valueChanged.connect(refresh)
        elif isinstance(widget, QtGui.QDoubleSpinBox):
            widget.valueChanged.connect(refresh)
        elif isinstance(widget, QtGui.QPlainTextEdit):
            widget.textChanged.connect(refresh)
        elif isinstance(widget, QtGui.QTextEdit):
            widget.textChanged.connect(refresh)
        elif isinstance(widget, QtGui.QListWidget):
            widget.itemSelectionChanged.connect(refresh)

    def _build_task_summary(self):
        title = self.SUMMARY_TITLE or self._default_summary_title()
        detail_template = self.SUMMARY_DETAIL or "Review settings for {label}, then confirm or cancel."
        detail = detail_template.format(
            label=getattr(self.obj, "Label", getattr(self.obj, "Name", "Object")),
            name=getattr(self.obj, "Name", "Object"),
            flow_type=getattr(self.obj, "FlowType", ""),
        )
        return title, detail

    def _default_summary_title(self):
        flow_type = getattr(self.obj, "FlowType", "")
        if isinstance(flow_type, str) and flow_type.startswith("FlowStudio::"):
            return flow_type.split("::", 1)[1].replace("_", " ")

        return getattr(self.obj, "Label", getattr(self.obj, "Name", "Task"))

    def _build_task_validation(self):
        level = self.VALIDATION_LEVEL or ""
        title = self.VALIDATION_TITLE or ""
        detail = self.VALIDATION_DETAIL or ""
        return level, title, detail

    # Convenience helpers -----------------------------------------------
    @staticmethod
    def _add_row(layout, label_text, widget):
        row = QtGui.QHBoxLayout()
        row.addWidget(QtGui.QLabel(label_text))
        row.addWidget(widget)
        layout.addLayout(row)
        return widget

    @staticmethod
    def _section(layout, title):
        group = QtGui.QGroupBox(title)
        group_layout = QtGui.QVBoxLayout(group)
        layout.addWidget(group)
        return group_layout

    @staticmethod
    def _spin_float(value, minimum=-1e9, maximum=1e9, decimals=6, step=0.1):
        sb = QtGui.QDoubleSpinBox()
        sb.setRange(minimum, maximum)
        sb.setDecimals(decimals)
        sb.setSingleStep(step)
        sb.setValue(value)
        return sb

    @staticmethod
    def _spin_int(value, minimum=0, maximum=999999999):
        sb = QtGui.QSpinBox()
        sb.setRange(minimum, maximum)
        sb.setValue(value)
        return sb

    @staticmethod
    def _combo(items, current):
        cb = QtGui.QComboBox()
        cb.addItems(items)
        idx = cb.findText(current)
        if idx >= 0:
            cb.setCurrentIndex(idx)
        return cb

    @staticmethod
    def _checkbox(checked):
        cb = QtGui.QCheckBox()
        cb.setChecked(checked)
        return cb
