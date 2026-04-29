# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Base task panel for FlowStudio dialogs."""

import FreeCAD
import FreeCADGui
from PySide import QtGui, QtCore

from flow_studio.taskpanels.taskpanel_desktop_lifecycle import FreeCADTaskPanelDesktopLifecycle


class BaseTaskPanel:
    """Common task panel base with accept/reject."""

    CONTEXT_MODE = "Edit"
    CONTEXT_TITLE = ""
    CONTEXT_DETAIL = ""
    SUMMARY_TITLE = ""
    SUMMARY_DETAIL = ""
    VALIDATION_LEVEL = ""
    VALIDATION_TITLE = ""
    VALIDATION_DETAIL = ""

    _DOMAIN_THEME = {
        "CFD": {"accent": "#0b5cad", "surface": "#eaf4ff", "text": "#12324a"},
        "Thermal": {"accent": "#c65d00", "surface": "#fff1e4", "text": "#4a2a12"},
        "Structural": {"accent": "#6a1b9a", "surface": "#f4eaff", "text": "#3d2455"},
        "Electrostatic": {"accent": "#00838f", "surface": "#e5fbfd", "text": "#143f45"},
        "Electromagnetic": {"accent": "#2e7d32", "surface": "#e9f7ea", "text": "#1d4021"},
        "Optical": {"accent": "#ad1457", "surface": "#fdeaf2", "text": "#4c1e35"},
        "General": {"accent": "#455a64", "surface": "#eef3f5", "text": "#263238"},
    }

    _VALIDATION_THEME = {
        "": {"bg": "#f3f5f7", "fg": "#546e7a"},
        "incomplete": {"bg": "#fff8e1", "fg": "#8a6d3b"},
        "warning": {"bg": "#fff3cd", "fg": "#8a6d3b"},
        "done": {"bg": "#e8f5e9", "fg": "#1b5e20"},
        "running": {"bg": "#e0f7fa", "fg": "#006064"},
        "failed": {"bg": "#ffebee", "fg": "#b71c1c"},
    }

    def __init__(self, obj, lifecycle=None):
        self.obj = obj
        self._lifecycle = lifecycle or FreeCADTaskPanelDesktopLifecycle()
        self.form = self._build_form()
        self._decorate_form()
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
        self._lifecycle.accept_edit()
        return True

    def reject(self):
        self._lifecycle.reject_edit()
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

    def _apply_task_context(self):
        mode, title, detail = self._build_task_context()
        self.taskview_context_mode = mode
        self.taskview_context_title = title
        self.taskview_context_detail = detail
        self._publish_taskview_property("taskview_context_mode", mode)
        self._publish_taskview_property("taskview_context_title", title)
        self._publish_taskview_property("taskview_context_detail", detail)

    def _apply_task_validation(self):
        level, title, detail = self._build_task_validation()
        self.taskview_validation_level = level
        self.taskview_validation_title = title
        self.taskview_validation_detail = detail
        self._publish_taskview_property("taskview_validation_level", level)
        self._publish_taskview_property("taskview_validation_title", title)
        self._publish_taskview_property("taskview_validation_detail", detail)

    def _refresh_taskview_metadata(self, *_args):
        self._apply_task_context()
        self._apply_task_summary()
        self._apply_task_validation()
        self._refresh_header_state()

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

    def _build_task_context(self):
        title = self.CONTEXT_TITLE or getattr(self.obj, "Label", getattr(self.obj, "Name", "Object"))
        detail = self.CONTEXT_DETAIL or self._default_context_detail()
        return self.CONTEXT_MODE or "Edit", title, detail

    def _default_context_detail(self):
        flow_type = getattr(self.obj, "FlowType", "")
        if isinstance(flow_type, str) and flow_type.startswith("FlowStudio::"):
            return flow_type.split("::", 1)[1].replace("_", " ")

        summary_title = self.SUMMARY_TITLE or self._default_summary_title()
        object_title = getattr(self.obj, "Label", getattr(self.obj, "Name", "Object"))
        return "" if summary_title == object_title else summary_title

    def _build_task_validation(self):
        level = self.VALIDATION_LEVEL or ""
        title = self.VALIDATION_TITLE or ""
        detail = self.VALIDATION_DETAIL or ""
        return level, title, detail

    def _decorate_form(self):
        if not hasattr(self, "form") or self.form is None:
            return

        theme = self._theme_colors()
        self.form.setStyleSheet(
            "QWidget { color: %(text)s; }"
            "QGroupBox {"
            " border: 1px solid %(accent)s;"
            " border-radius: 8px;"
            " margin-top: 14px;"
            " padding-top: 10px;"
            " background: rgba(255,255,255,0.94);"
            "}"
            "QGroupBox::title {"
            " subcontrol-origin: margin;"
            " left: 10px;"
            " padding: 0 6px;"
            " color: %(accent)s;"
            " font-weight: bold;"
            "}"
            "QPushButton {"
            " background: %(surface)s;"
            " border: 1px solid %(accent)s;"
            " border-radius: 6px;"
            " padding: 6px 10px;"
            "}"
            "QPushButton:hover { background: white; }"
            "QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QPlainTextEdit, QTextEdit, QListWidget {"
            " border: 1px solid #b0bec5;"
            " border-radius: 4px;"
            " background: white;"
            " padding: 4px;"
            "}"
            "QLabel[role='taskHint'] { color: #607d8b; }"
            % theme
        )

        layout = self.form.layout()
        if layout is None:
            return

        header = QtGui.QFrame()
        header.setObjectName("flowstudioTaskHeader")
        header_layout = QtGui.QVBoxLayout(header)
        header_layout.setContentsMargins(10, 10, 10, 10)

        self._header_context = QtGui.QLabel("")
        self._header_context.setProperty("role", "taskHint")
        self._header_context.setWordWrap(True)
        header_layout.addWidget(self._header_context)

        self._header_title = QtGui.QLabel("")
        self._header_title.setWordWrap(True)
        header_layout.addWidget(self._header_title)

        self._header_detail = QtGui.QLabel("")
        self._header_detail.setWordWrap(True)
        header_layout.addWidget(self._header_detail)

        self._header_validation = QtGui.QLabel("")
        self._header_validation.setWordWrap(True)
        header_layout.addWidget(self._header_validation)

        header.setStyleSheet(
            "QFrame#flowstudioTaskHeader {"
            f" background: {theme['surface']};"
            f" border: 1px solid {theme['accent']};"
            " border-radius: 10px;"
            "}"
        )
        layout.insertWidget(0, header)

    def _refresh_header_state(self):
        if not hasattr(self, "_header_title"):
            return

        context_mode = getattr(self, "taskview_context_mode", "Edit")
        context_title = getattr(self, "taskview_context_title", "")
        context_detail = getattr(self, "taskview_context_detail", "")
        summary_title = getattr(self, "taskview_summary_title", self._default_summary_title())
        summary_detail = getattr(self, "taskview_summary_detail", "")
        validation_level = getattr(self, "taskview_validation_level", "")
        validation_title = getattr(self, "taskview_validation_title", "")
        validation_detail = getattr(self, "taskview_validation_detail", "")
        theme = self._theme_colors()
        validation_theme = self._VALIDATION_THEME.get(validation_level, self._VALIDATION_THEME[""])

        self._header_context.setText(
            f"<b>{context_mode}</b> · {context_title}" + (f"<br>{context_detail}" if context_detail else "")
        )
        self._header_title.setText(
            f"<span style='font-size:18px; color:{theme['accent']}'><b>{summary_title}</b></span>"
        )
        self._header_detail.setText(summary_detail)

        if validation_title or validation_detail:
            self._header_validation.setText(
                f"<span style='background:{validation_theme['bg']}; color:{validation_theme['fg']}; "
                "padding:4px 8px; border-radius:6px;'><b>"
                f"{validation_title or 'Status'}"
                "</b></span>"
                + (f"<br>{validation_detail}" if validation_detail else "")
            )
        else:
            self._header_validation.setText(
                f"<span style='background:{validation_theme['bg']}; color:{validation_theme['fg']}; "
                "padding:4px 8px; border-radius:6px;'><b>Ready</b></span><br>"
                "Review the settings below and confirm when they match the study intent."
            )

    def _theme_colors(self):
        flow_type = str(getattr(self.obj, "FlowType", "") or "")
        if "Optical" in flow_type or "Geant4" in flow_type:
            return self._DOMAIN_THEME["Optical"]
        if "Electromagnetic" in flow_type:
            return self._DOMAIN_THEME["Electromagnetic"]
        if "Electrostatic" in flow_type:
            return self._DOMAIN_THEME["Electrostatic"]
        if "Structural" in flow_type or "Solid" in flow_type:
            return self._DOMAIN_THEME["Structural"]
        if "Thermal" in flow_type:
            return self._DOMAIN_THEME["Thermal"]
        if any(token in flow_type for token in ("Fluid", "BC", "Mesh", "Physics", "InitialConditions", "Solver", "PostPipeline", "Measurement")):
            return self._DOMAIN_THEME["CFD"]
        return self._DOMAIN_THEME["General"]

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
