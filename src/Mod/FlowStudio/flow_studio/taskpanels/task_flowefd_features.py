# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""FloEFD-style task panels for setup and result feature objects."""

import FreeCAD
import FreeCADGui
from PySide import QtGui

from flow_studio.catalog.database import fan_presets
from flow_studio.catalog.editor import show_engineering_database_editor
from flow_studio.taskpanels.base_taskpanel import BaseTaskPanel


RESULT_FIELDS = [
    "Pressure",
    "Temperature",
    "Velocity",
    "Velocity (X)",
    "Velocity (Y)",
    "Velocity (Z)",
    "Density (Fluid)",
    "Density (Solid)",
    "Turbulent Kinetic Energy",
    "Wall Heat Flux",
]


def _selection_labels(refs):
    labels = []
    for ref_obj, sub_names in refs or []:
        base = getattr(ref_obj, "Label", getattr(ref_obj, "Name", "Object"))
        if isinstance(sub_names, str):
            sub_names = [sub_names]
        if sub_names:
            labels.extend(f"{base}:{sub}" for sub in sub_names)
        else:
            labels.append(base)
    return labels


class FloEFDTaskPanel(BaseTaskPanel):
    """Base panel with a Creo/FloEFD-like selection header."""

    reference_property = "References"

    def _add_selection_section(self, layout, title="Selection"):
        group = QtGui.QGroupBox(title)
        group_layout = QtGui.QVBoxLayout(group)
        self.selection_list = QtGui.QListWidget()
        self.selection_list.setMinimumHeight(72)
        group_layout.addWidget(self.selection_list)
        btn_row = QtGui.QHBoxLayout()
        self.btn_use_selection = QtGui.QPushButton("Use Current Selection")
        self.btn_clear_selection = QtGui.QPushButton("Clear")
        btn_row.addWidget(self.btn_use_selection)
        btn_row.addWidget(self.btn_clear_selection)
        group_layout.addLayout(btn_row)
        self.btn_use_selection.clicked.connect(self._use_current_selection)
        self.btn_clear_selection.clicked.connect(self._clear_selection)
        layout.addWidget(group)
        self._refresh_selection_list()
        return group

    def _refs(self):
        return getattr(self.obj, self.reference_property, []) or []

    def _set_refs(self, refs):
        if self.reference_property in getattr(self.obj, "PropertiesList", []):
            setattr(self.obj, self.reference_property, refs)

    def _refresh_selection_list(self):
        if not hasattr(self, "selection_list"):
            return
        self.selection_list.clear()
        labels = _selection_labels(self._refs())
        if not labels:
            self.selection_list.addItem("(no geometry assigned)")
            return
        for label in labels:
            self.selection_list.addItem(label)

    def _use_current_selection(self):
        refs = []
        try:
            selection = FreeCADGui.Selection.getSelectionEx()
        except Exception:
            selection = []
        for item in selection:
            obj = getattr(item, "Object", None)
            if obj is None:
                continue
            flow_type = getattr(obj, "FlowType", "")
            if isinstance(flow_type, str) and flow_type.startswith("FlowStudio::"):
                continue
            refs.append((obj, list(getattr(item, "SubElementNames", []) or [])))
        self._set_refs(refs)
        self._refresh_selection_list()

    def _clear_selection(self):
        self._set_refs([])
        self._refresh_selection_list()

    def _section(self, layout, title):
        group = QtGui.QGroupBox(title)
        group.setCheckable(False)
        group_layout = QtGui.QVBoxLayout(group)
        layout.addWidget(group)
        return group_layout

    def _field_checklist(self, parent_layout, selected_fields):
        group = QtGui.QGroupBox("Parameters")
        group_layout = QtGui.QVBoxLayout(group)
        checks = []
        selected = set(selected_fields or [])
        for field in RESULT_FIELDS:
            cb = QtGui.QCheckBox(field)
            cb.setChecked(field in selected or (not selected and field in ("Pressure", "Velocity")))
            group_layout.addWidget(cb)
            checks.append(cb)
        parent_layout.addWidget(group)
        return checks


class TaskVolumeSource(FloEFDTaskPanel):
    def _build_form(self):
        widget = QtGui.QWidget()
        layout = QtGui.QVBoxLayout(widget)
        layout.addWidget(QtGui.QLabel("<b>Volume Source</b>"))
        self._add_selection_section(layout)

        params = self._section(layout, "Parameter")
        self.cb_type = self._combo(["Heat Generation", "Mass Source", "Momentum Source", "Species Source"], self.obj.SourceType)
        self._add_row(params, "Type:", self.cb_type)
        self.sp_q = self._spin_float(self.obj.HeatPowerDensity, -1e12, 1e12, 3, 100.0)
        self._add_row(params, "q [W/m^3]:", self.sp_q)
        self.sp_m = self._spin_float(self.obj.MassSource, -1e9, 1e9, 6, 0.001)
        self._add_row(params, "Mass [kg/(m^3 s)]:", self.sp_m)
        self.chk_goals = self._checkbox(self.obj.CreateAssociatedGoals)
        self._add_row(self._section(layout, "Options"), "Create associated goals:", self.chk_goals)
        layout.addStretch()
        return widget

    def _store(self):
        self.obj.SourceType = self.cb_type.currentText()
        self.obj.HeatPowerDensity = self.sp_q.value()
        self.obj.MassSource = self.sp_m.value()
        self.obj.CreateAssociatedGoals = self.chk_goals.isChecked()


class TaskFan(FloEFDTaskPanel):
    def _build_form(self):
        widget = QtGui.QWidget()
        layout = QtGui.QVBoxLayout(widget)
        layout.addWidget(QtGui.QLabel("<b>Fan</b>"))
        self._add_selection_section(layout, "Faces Fluid Enters / Exits the Fan")

        fan = self._section(layout, "Fan")
        self.cb_type = self._combo(["Internal Fan", "External Inlet Fan", "External Outlet Fan"], self.obj.FanType)
        self._add_row(fan, "Type:", self.cb_type)
        self.fan_database = fan_presets()
        self.cb_curve = self._combo(
            ["User Defined"] + sorted(self.fan_database),
            self.obj.FanCurvePreset,
        )
        self._add_row(fan, "Curve:", self.cb_curve)
        self.cb_curve.currentTextChanged.connect(self._on_curve_changed)
        btn_db = QtGui.QPushButton("Engineering Database...")
        btn_db.clicked.connect(show_engineering_database_editor)
        fan.addWidget(btn_db)
        self.curve_table = QtGui.QTableWidget(0, 2)
        self.curve_table.setHorizontalHeaderLabels(["Volume flow rate [m^3/s]", "Pressure difference [Pa]"])
        self.curve_table.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.curve_table.horizontalHeader().setStretchLastSection(True)
        fan.addWidget(self.curve_table)
        self.sp_p = self._spin_float(self.obj.ReferencePressure, 0, 1e9, 2, 100.0)
        self._add_row(self._section(layout, "Thermodynamic Parameters"), "Reference pressure [Pa]:", self.sp_p)
        self.chk_goals = self._checkbox(self.obj.CreateAssociatedGoals)
        self._add_row(self._section(layout, "Options"), "Create associated goals:", self.chk_goals)
        layout.addStretch()
        self._on_curve_changed(self.cb_curve.currentText())
        return widget

    def _on_curve_changed(self, name):
        data = self.fan_database.get(name, {})
        if "FanType" in data:
            idx = self.cb_type.findText(str(data["FanType"]))
            if idx >= 0:
                self.cb_type.setCurrentIndex(idx)
        if "ReferencePressure" in data:
            self.sp_p.setValue(float(data["ReferencePressure"]))
        self.curve_table.setRowCount(0)
        for flow, pressure in data.get("curve", []):
            row = self.curve_table.rowCount()
            self.curve_table.insertRow(row)
            self.curve_table.setItem(row, 0, QtGui.QTableWidgetItem(str(flow)))
            self.curve_table.setItem(row, 1, QtGui.QTableWidgetItem(str(pressure)))

    def _store(self):
        self.obj.FanType = self.cb_type.currentText()
        self.obj.FanCurvePreset = self.cb_curve.currentText()
        self.obj.ReferencePressure = self.sp_p.value()
        self.obj.CreateAssociatedGoals = self.chk_goals.isChecked()


class TaskResultPlot(FloEFDTaskPanel):
    SUMMARY_TITLE = "Result Plot"
    SUMMARY_DETAIL = (
        "Define how {label} should visualize a result field across the selected geometry or seed locations."
    )

    def _build_task_validation(self):
        if not self._refs():
            return (
                "incomplete",
                "Assign plot targets",
                "Select faces, parts, or seed locations before creating a result plot.",
            )

        if not self.cb_field.currentText().strip():
            return (
                "incomplete",
                "Result field required",
                "Choose the field this result plot should visualize.",
            )

        if not any((
            self.chk_contours.isChecked(),
            self.chk_isolines.isChecked(),
            self.chk_vectors.isChecked(),
            self.chk_streamlines.isChecked(),
        )):
            return (
                "warning",
                "Enable a display mode",
                "Turn on at least one display style such as contours, isolines, vectors, or streamlines.",
            )

        return super()._build_task_validation()

    def _build_form(self):
        widget = QtGui.QWidget()
        layout = QtGui.QVBoxLayout(widget)
        layout.addWidget(QtGui.QLabel(f"<b>{self.obj.PlotKind}</b>"))
        self._add_selection_section(layout)

        plot = self._section(layout, "Display")
        self.cb_kind = self._combo(["Surface Plot", "Cut Plot", "XY Plot", "Flow Trajectories", "Point Parameters"], self.obj.PlotKind)
        self._add_row(plot, "Plot kind:", self.cb_kind)
        self.cb_field = self._combo(RESULT_FIELDS, self.obj.Field)
        self._add_row(plot, "Field:", self.cb_field)
        self.sp_contours = self._spin_int(self.obj.ContourCount, 2, 256)
        self._add_row(plot, "Contour levels:", self.sp_contours)
        self.chk_contours = self._checkbox(self.obj.Contours)
        self._add_row(plot, "Contours:", self.chk_contours)
        self.chk_isolines = self._checkbox(self.obj.Isolines)
        self._add_row(plot, "Isolines:", self.chk_isolines)
        self.chk_vectors = self._checkbox(self.obj.Vectors)
        self._add_row(plot, "Vectors:", self.chk_vectors)
        self.chk_streamlines = self._checkbox(self.obj.Streamlines)
        self._add_row(plot, "Streamlines:", self.chk_streamlines)

        cut = self._section(layout, "Cut / XY Parameters")
        self.cb_plane = self._combo(["XY Plane", "XZ Plane", "YZ Plane", "Custom"], self.obj.CutPlane)
        self._add_row(cut, "Plane:", self.cb_plane)
        self.sp_offset = self._spin_float(self.obj.PlaneOffset, -1e9, 1e9, 6, 0.001)
        self._add_row(cut, "Offset:", self.sp_offset)

        options = self._section(layout, "Options")
        self.chk_cad = self._checkbox(self.obj.UseCADGeometry)
        self._add_row(options, "Use CAD geometry:", self.chk_cad)
        self.chk_interp = self._checkbox(self.obj.Interpolate)
        self._add_row(options, "Interpolate:", self.chk_interp)
        self.chk_excel = self._checkbox(self.obj.ExportExcel)
        self._add_row(options, "Export to Excel/CSV:", self.chk_excel)
        layout.addStretch()
        return widget

    def _store(self):
        self.obj.PlotKind = self.cb_kind.currentText()
        self.obj.Field = self.cb_field.currentText()
        self.obj.ContourCount = self.sp_contours.value()
        self.obj.Contours = self.chk_contours.isChecked()
        self.obj.Isolines = self.chk_isolines.isChecked()
        self.obj.Vectors = self.chk_vectors.isChecked()
        self.obj.Streamlines = self.chk_streamlines.isChecked()
        self.obj.CutPlane = self.cb_plane.currentText()
        self.obj.PlaneOffset = self.sp_offset.value()
        self.obj.UseCADGeometry = self.chk_cad.isChecked()
        self.obj.Interpolate = self.chk_interp.isChecked()
        self.obj.ExportExcel = self.chk_excel.isChecked()


class TaskParticleStudy(FloEFDTaskPanel):
    SUMMARY_TITLE = "Particle Study"
    SUMMARY_DETAIL = (
        "Configure how {label} seeds, colors, and limits particle trajectories from the selected injections."
    )

    reference_property = "Injections"

    def _build_task_validation(self):
        if not self._refs():
            return (
                "incomplete",
                "Assign particle injections",
                "Select one or more injection faces, edges, or seed regions before configuring a particle study.",
            )

        gravity = (self.sp_gx.value(), self.sp_gy.value(), self.sp_gz.value())
        if self.chk_grav.isChecked() and gravity == (0.0, 0.0, 0.0):
            return (
                "warning",
                "Gravity vector is zero",
                "Use a non-zero gravity vector or disable gravity for this particle study.",
            )

        if self.sp_d.value() <= 0.0:
            return (
                "warning",
                "Particle diameter required",
                "Enter a positive particle diameter before tracing particles.",
            )

        if self.sp_len.value() <= 0.0 or self.sp_time.value() <= 0.0:
            return (
                "warning",
                "Tracking limits required",
                "Set positive tracking length and time limits before running the particle study.",
            )

        return super()._build_task_validation()

    def _build_form(self):
        widget = QtGui.QWidget()
        layout = QtGui.QVBoxLayout(widget)
        layout.addWidget(QtGui.QLabel("<b>Particle Study Settings</b>"))
        self._add_selection_section(layout, "Injections")

        features = self._section(layout, "Physical Features")
        self.chk_acc = self._checkbox(self.obj.Accretion)
        self._add_row(features, "Accretion:", self.chk_acc)
        self.chk_ero = self._checkbox(self.obj.Erosion)
        self._add_row(features, "Erosion:", self.chk_ero)
        self.chk_grav = self._checkbox(self.obj.Gravity)
        self._add_row(features, "Gravity:", self.chk_grav)
        gv = self.obj.GravityVector
        self.sp_gx = self._spin_float(gv.x, -1000, 1000, 3, 0.1)
        self.sp_gy = self._spin_float(gv.y, -1000, 1000, 3, 0.1)
        self.sp_gz = self._spin_float(gv.z, -1000, 1000, 3, 0.1)
        self._add_row(features, "Gx [m/s^2]:", self.sp_gx)
        self._add_row(features, "Gy [m/s^2]:", self.sp_gy)
        self._add_row(features, "Gz [m/s^2]:", self.sp_gz)

        app = self._section(layout, "Default Appearance")
        self.cb_shape = self._combo(["Spheres", "Dots", "Arrows"], self.obj.ParticleShape)
        self._add_row(app, "Shape:", self.cb_shape)
        self.sp_d = self._spin_float(self.obj.ParticleDiameter, 0, 1e6, 6, 0.001)
        self._add_row(app, "Diameter [m]:", self.sp_d)
        self.cb_color = self._combo(RESULT_FIELDS, self.obj.ColorByField)
        self._add_row(app, "Color by:", self.cb_color)

        limits = self._section(layout, "Constraints")
        self.sp_len = self._spin_float(self.obj.TrackLength, 0, 1e9, 3, 1.0)
        self._add_row(limits, "Length [m]:", self.sp_len)
        self.sp_time = self._spin_float(self.obj.TrackTime, 0, 1e12, 2, 10.0)
        self._add_row(limits, "Time [s]:", self.sp_time)
        self.sp_max = self._spin_int(self.obj.MaxParticles, 1, 100000000)
        self._add_row(limits, "Max particles:", self.sp_max)
        layout.addStretch()
        return widget

    def _store(self):
        self.obj.Accretion = self.chk_acc.isChecked()
        self.obj.Erosion = self.chk_ero.isChecked()
        self.obj.Gravity = self.chk_grav.isChecked()
        self.obj.GravityVector = FreeCAD.Vector(self.sp_gx.value(), self.sp_gy.value(), self.sp_gz.value())
        self.obj.ParticleShape = self.cb_shape.currentText()
        self.obj.ParticleDiameter = self.sp_d.value()
        self.obj.ColorByField = self.cb_color.currentText()
        self.obj.TrackLength = self.sp_len.value()
        self.obj.TrackTime = self.sp_time.value()
        self.obj.MaxParticles = self.sp_max.value()
