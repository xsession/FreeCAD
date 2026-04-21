# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""FloEFD-style geometry task panels for FlowStudio."""

import FreeCAD
import FreeCADGui
from PySide import QtCore, QtGui

from flow_studio.tools.geometry import (
    GeometryCheckOptions,
    check_geometry,
    create_or_update_fluid_volume,
    describe_face_ref,
    fluid_volume_is_visible,
    hide_fluid_volume,
    iter_geometry_objects,
    run_leak_tracking,
    selected_face_refs,
)


def _format_volume(value):
    return f"{value:.6g} m^3"


_USER_ROLE = QtCore.Qt.UserRole
_CHECKED_STATE = QtCore.Qt.Checked


class _SimpleTaskPanel:
    """Task panel base for command-only dialogs."""

    def accept(self):
        return True

    def reject(self):
        return True


class TaskCheckGeometry(_SimpleTaskPanel):
    """Check geometry, create/show fluid volume, and launch leak tracking."""

    def __init__(self):
        self.last_result = None
        self.form = self._build_form()
        self._reload_objects()
        self._update_volume_button()

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
                obj = FreeCAD.ActiveDocument.getObject(obj_name) if FreeCAD.ActiveDocument else None
                if obj is not None:
                    objects.append(obj)
        return objects

    def _reload_objects(self):
        self.state_tree.clear()
        for obj in iter_geometry_objects():
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
        self.last_result = check_geometry(self._checked_objects(), self._options())
        lines = [
            f"Status: {self.last_result.status}. Geometry is "
            f"{'OK' if self.last_result.status == 'SUCCESSFUL' else 'not fully closed'}",
            f"Analysis type: {self.last_result.analysis_type}",
            f"Fluid volume: {_format_volume(self.last_result.fluid_volume)}",
            f"Solid volume: {_format_volume(self.last_result.solid_volume)}",
        ]
        for info in self.last_result.objects:
            lines.append(
                f"{info.label}: {info.solids} solids, {info.shells} shells, "
                f"{info.faces} faces, volume {_format_volume(info.volume)}"
            )
        if self.last_result.issues:
            lines.append("Issues:")
            lines.extend(f"- {issue}" for issue in self.last_result.issues)
        else:
            lines.append("All checked bodies look closed enough for setup.")
        self.results.setPlainText("\n".join(lines))
        FreeCAD.Console.PrintMessage("[FlowStudio] Check Geometry completed.\n")
        for line in lines:
            FreeCAD.Console.PrintMessage(f"{line}\n")

    def _toggle_volume(self):
        if fluid_volume_is_visible():
            hide_fluid_volume()
        else:
            if self.last_result is None:
                self.last_result = check_geometry(self._checked_objects(), self._options())
            create_or_update_fluid_volume(self.last_result)
        self._update_volume_button()

    def _update_volume_button(self):
        if hasattr(self, "btn_volume"):
            self.btn_volume.setText("Hide Fluid Volume" if fluid_volume_is_visible() else "Show Fluid Volume")

    def _open_leak_tracking(self):
        try:
            FreeCADGui.Control.closeDialog()
        except Exception:
            pass
        FreeCADGui.Control.showDialog(TaskLeakTracking())


class TaskLeakTracking(_SimpleTaskPanel):
    """Track a possible leak/connection between two selected faces."""

    def __init__(self):
        self.face_a = None
        self.face_b = None
        self.form = self._build_form()
        self._load_selection()

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
        refs = selected_face_refs()
        if refs:
            self.face_a = refs[0]
        if len(refs) > 1:
            self.face_b = refs[1]
        self._refresh()

    def _use_selection_a(self):
        refs = selected_face_refs()
        if refs:
            self.face_a = refs[0]
        self._refresh()

    def _use_selection_b(self):
        refs = selected_face_refs()
        if refs:
            self.face_b = refs[-1]
        self._refresh()

    def _refresh(self):
        self.face_a_list.clear()
        self.face_b_list.clear()
        self.face_a_list.addItem(describe_face_ref(self.face_a) if self.face_a else "(no internal face)")
        self.face_b_list.addItem(describe_face_ref(self.face_b) if self.face_b else "(no external face)")

    def _find_connection(self):
        report = run_leak_tracking(self.face_a, self.face_b)
        lines = [f"Status: {report['status']}"] + report["messages"]
        self.results.setPlainText("\n".join(lines))
        FreeCAD.Console.PrintMessage("[FlowStudio] Leak Tracking completed.\n")
        for line in lines:
            FreeCAD.Console.PrintMessage(f"{line}\n")

