# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""FloEFD-style geometry task panels for FlowStudio."""

import FreeCAD
import FreeCADGui
from PySide import QtCore, QtGui

from flow_studio.app import FlowStudioGeometryCheckService, FlowStudioLeakTrackingService
from flow_studio.taskpanels.geometry_tools_desktop_adapter import FreeCADGeometryToolsDesktopAdapter
from flow_studio.ui.geometry_tools_presenter import GeometryCheckPresenter, LeakTrackingPresenter

from flow_studio.tools.geometry import (
    GeometryCheckOptions,
)


_USER_ROLE = QtCore.Qt.UserRole
_CHECKED_STATE = QtCore.Qt.Checked


class _SimpleTaskPanel:
    """Task panel base for command-only dialogs."""

    SUMMARY_TITLE = ""
    SUMMARY_DETAIL = ""
    VALIDATION_LEVEL = ""
    VALIDATION_TITLE = ""
    VALIDATION_DETAIL = ""

    def _finalize_form(self):
        self._refresh_taskview_metadata()
        self._connect_taskview_metadata_signals()

    def accept(self):
        return True

    def reject(self):
        return True

    def _apply_task_summary(self):
        title, detail = self._build_task_summary()
        self.taskview_summary_title = title
        self.taskview_summary_detail = detail
        if hasattr(self, "form") and self.form is not None:
            self.form.setProperty("taskview_summary_title", title)
            self.form.setProperty("taskview_summary_detail", detail)

    def _apply_task_validation(self):
        level, title, detail = self._build_task_validation()
        self.taskview_validation_level = level
        self.taskview_validation_title = title
        self.taskview_validation_detail = detail
        if hasattr(self, "form") and self.form is not None:
            self.form.setProperty("taskview_validation_level", level)
            self.form.setProperty("taskview_validation_title", title)
            self.form.setProperty("taskview_validation_detail", detail)

    def _refresh_taskview_metadata(self, *_args):
        self._apply_task_summary()
        self._apply_task_validation()

    def _build_task_summary(self):
        return self.SUMMARY_TITLE or "Task", self.SUMMARY_DETAIL

    def _build_task_validation(self):
        return self.VALIDATION_LEVEL, self.VALIDATION_TITLE, self.VALIDATION_DETAIL

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
        elif isinstance(widget, QtGui.QTreeWidget):
            widget.itemChanged.connect(refresh)


class TaskCheckGeometry(_SimpleTaskPanel):
    """Check geometry, create/show fluid volume, and launch leak tracking."""

    SUMMARY_TITLE = "Geometry Check"
    SUMMARY_DETAIL = (
        "Review watertightness, fluid volume readiness, and leak-detection setup before meshing or solving."
    )

    def __init__(self):
        self.last_result = None
        self._service = FlowStudioGeometryCheckService()
        self._presenter = GeometryCheckPresenter()
        self._desktop = FreeCADGeometryToolsDesktopAdapter()
        self.form = self._build_form()
        self._reload_objects()
        self._update_volume_button()
        self._finalize_form()

    def _build_task_validation(self):
        checked_count = len(self._checked_objects()) if hasattr(self, "state_tree") else 0
        return self._presenter.build_validation(checked_count, self.last_result)

    def _build_form(self):
        widget = QtGui.QWidget()
        layout = QtGui.QVBoxLayout(widget)

        self.state_tree = QtGui.QTreeWidget()
        self.state_tree.setHeaderLabels(["State"])
        self.state_tree.setMinimumHeight(180)
        layout.addWidget(self._group("State", self.state_tree))

        apply_btn = QtGui.QPushButton("Apply to Project")
        apply_btn.clicked.connect(self._reload_objects)
        layout.addWidget(apply_btn)

        analysis = QtGui.QWidget()
        analysis_layout = QtGui.QVBoxLayout(analysis)
        self.chk_exclude = QtGui.QCheckBox("Exclude cavities without flow conditions")
        analysis_layout.addWidget(self.chk_exclude)
        layout.addWidget(self._group("Analysis Type", analysis))

        options = QtGui.QWidget()
        options_layout = QtGui.QVBoxLayout(options)
        self.chk_improved = QtGui.QCheckBox("Improved geometry handling")
        self.chk_materials = QtGui.QCheckBox("Advanced materials check")
        self.chk_solid = QtGui.QCheckBox("Create solid body assembly")
        self.chk_fluid = QtGui.QCheckBox("Create fluid body assembly")
        self.chk_solid.setChecked(True)
        self.chk_fluid.setChecked(True)
        for checkbox in (self.chk_improved, self.chk_materials, self.chk_solid, self.chk_fluid):
            options_layout.addWidget(checkbox)
        layout.addWidget(self._group("Options", options))

        self.btn_check = QtGui.QPushButton("Check")
        self.btn_volume = QtGui.QPushButton("Show Fluid Volume")
        self.btn_leak = QtGui.QPushButton("Leak Tracking...")
        self.btn_check.clicked.connect(self._check)
        self.btn_volume.clicked.connect(self._toggle_volume)
        self.btn_leak.clicked.connect(self._open_leak_tracking)
        layout.addWidget(self.btn_check)
        layout.addWidget(self.btn_volume)
        layout.addWidget(self.btn_leak)

        self.results = QtGui.QTextEdit()
        self.results.setReadOnly(True)
        self.results.setMinimumHeight(140)
        layout.addWidget(self._group("Results", self.results))
        return widget

    @staticmethod
    def _group(title, child):
        group = QtGui.QGroupBox(title)
        group_layout = QtGui.QVBoxLayout(group)
        group_layout.addWidget(child)
        return group

    def _options(self):
        return GeometryCheckOptions(
            exclude_cavities_without_flow_conditions=self.chk_exclude.isChecked(),
            improved_geometry_handling=self.chk_improved.isChecked(),
            advanced_materials_check=self.chk_materials.isChecked(),
            create_solid_body_assembly=self.chk_solid.isChecked(),
            create_fluid_body_assembly=self.chk_fluid.isChecked(),
        )

    def _checked_objects(self):
        objects = []
        for index in range(self.state_tree.topLevelItemCount()):
            item = self.state_tree.topLevelItem(index)
            obj_name = item.data(0, _USER_ROLE)
            if item.checkState(0) == _CHECKED_STATE and obj_name:
                obj = self._desktop.get_document_object(obj_name)
                if obj is not None:
                    objects.append(obj)
        return objects

    def _reload_objects(self):
        self.state_tree.clear()
        for obj in self._service.iter_geometry_objects():
            item = QtGui.QTreeWidgetItem([getattr(obj, "Label", obj.Name)])
            item.setData(0, _USER_ROLE, obj.Name)
            item.setCheckState(0, _CHECKED_STATE)
            shape = getattr(obj, "Shape", None)
            try:
                if shape is not None and shape.Solids:
                    item.setIcon(0, self.form.style().standardIcon(QtGui.QStyle.SP_DirIcon))
                else:
                    item.setIcon(0, self.form.style().standardIcon(QtGui.QStyle.SP_FileIcon))
            except Exception:
                pass
            self.state_tree.addTopLevelItem(item)
        self.state_tree.expandAll()

    def _check(self):
        self.last_result = self._service.run_check(self._checked_objects(), self._options())
        lines = self._presenter.build_results(self.last_result)
        self.results.setPlainText("\n".join(lines))
        self._desktop.report_check_completed(lines)

    def _toggle_volume(self):
        if self._service.is_fluid_volume_visible():
            self._service.hide_fluid_volume()
        else:
            if self.last_result is None:
                self.last_result = self._service.run_check(self._checked_objects(), self._options())
            self._service.show_fluid_volume(self.last_result)
        self._update_volume_button()

    def _update_volume_button(self):
        if hasattr(self, "btn_volume"):
            self.btn_volume.setText(self._presenter.volume_button_text(self._service.is_fluid_volume_visible()))

    def _open_leak_tracking(self):
        self._desktop.open_leak_tracking_dialog(TaskLeakTracking())


class TaskLeakTracking(_SimpleTaskPanel):
    """Track a possible leak/connection between two selected faces."""

    SUMMARY_TITLE = "Leak Tracking"
    SUMMARY_DETAIL = (
        "Compare an internal and external face to find unintended flow connections through the model."
    )

    def __init__(self):
        self.face_a = None
        self.face_b = None
        self._service = FlowStudioLeakTrackingService()
        self._presenter = LeakTrackingPresenter()
        self._desktop = FreeCADGeometryToolsDesktopAdapter()
        self.form = self._build_form()
        self._load_selection()
        self._finalize_form()

    def _build_task_validation(self):
        return self._presenter.build_validation(self.face_a, self.face_b)

    def _build_form(self):
        widget = QtGui.QWidget()
        layout = QtGui.QVBoxLayout(widget)

        info = QtGui.QLabel(
            "Please select one internal face and one external face. "
            "Selected faces should belong to connected solid components."
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        self.face_a_list = QtGui.QListWidget()
        self.face_b_list = QtGui.QListWidget()
        self.face_a_list.setMinimumHeight(48)
        self.face_b_list.setMinimumHeight(48)
        layout.addWidget(self._group("Internal Face", self.face_a_list))
        layout.addWidget(self._group("External Face", self.face_b_list))

        btn_row = QtGui.QHBoxLayout()
        self.btn_use_a = QtGui.QPushButton("Use Selection as Internal")
        self.btn_use_b = QtGui.QPushButton("Use Selection as External")
        btn_row.addWidget(self.btn_use_a)
        btn_row.addWidget(self.btn_use_b)
        layout.addLayout(btn_row)

        self.btn_find = QtGui.QPushButton("Find Connection")
        self.btn_find.clicked.connect(self._find_connection)
        self.btn_use_a.clicked.connect(self._use_selection_a)
        self.btn_use_b.clicked.connect(self._use_selection_b)
        layout.addWidget(self.btn_find)

        self.results = QtGui.QTextEdit()
        self.results.setReadOnly(True)
        self.results.setMinimumHeight(140)
        layout.addWidget(self._group("Results", self.results))
        return widget

    @staticmethod
    def _group(title, child):
        group = QtGui.QGroupBox(title)
        group_layout = QtGui.QVBoxLayout(group)
        group_layout.addWidget(child)
        return group

    def _load_selection(self):
        refs = self._service.selected_face_refs()
        if refs:
            self.face_a = refs[0]
        if len(refs) > 1:
            self.face_b = refs[1]
        self._refresh()

    def _use_selection_a(self):
        refs = self._service.selected_face_refs()
        if refs:
            self.face_a = refs[0]
        self._refresh()

    def _use_selection_b(self):
        refs = self._service.selected_face_refs()
        if refs:
            self.face_b = refs[-1]
        self._refresh()

    def _refresh(self):
        self.face_a_list.clear()
        self.face_b_list.clear()
        self.face_a_list.addItem(self._service.describe_face_ref(self.face_a) if self.face_a else "(no internal face)")
        self.face_b_list.addItem(self._service.describe_face_ref(self.face_b) if self.face_b else "(no external face)")
        self._refresh_taskview_metadata()

    def _find_connection(self):
        report = self._service.run_leak_tracking(self.face_a, self.face_b)
        lines = self._presenter.build_results(report)
        self.results.setPlainText("\n".join(lines))
        self._refresh_taskview_metadata()
        self._desktop.report_leak_tracking_completed(lines)
