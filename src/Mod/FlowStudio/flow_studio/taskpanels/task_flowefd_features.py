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
from flow_studio.taskpanels.selection_desktop_adapter import FreeCADSelectionDesktopAdapter
from flow_studio.ui.flowefd_features_presenter import (
    FanPresenter,
    FanSettings,
    ParticleStudyPresenter,
    ParticleStudySettings,
    ResultPlotPresenter,
    ResultPlotSettings,
    VolumeSourcePresenter,
    VolumeSourceSettings,
)
from flow_studio.ui.selection_presenter import SelectionPresenter


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
class FloEFDTaskPanel(BaseTaskPanel):
    """Base panel with a Creo/FloEFD-like selection header."""

    reference_property = "References"
    selection_mode = "any"

    def __init__(self, obj):
        self._selection_presenter = SelectionPresenter()
        self._selection_adapter = FreeCADSelectionDesktopAdapter()
        super().__init__(obj)

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
        labels = self._selection_presenter.build_labels(self._refs())
        if not labels:
            self.selection_list.addItem("(no geometry assigned)")
            return
        for label in labels:
            self.selection_list.addItem(label)

    def _use_current_selection(self):
        refs = self._selection_adapter.get_selected_references(mode=self.selection_mode)
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
    def __init__(self, obj):
        self._presenter = VolumeSourcePresenter()
        super().__init__(obj)

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

    def _current_settings(self):
        if not hasattr(self, "cb_type"):
            return self._presenter.read_settings(self.obj)
        return VolumeSourceSettings(
            references=tuple(self._refs()),
            source_type=self.cb_type.currentText(),
            heat_power_density=self.sp_q.value(),
            mass_source=self.sp_m.value(),
            create_associated_goals=self.chk_goals.isChecked(),
        )

    def _store(self):
        self._presenter.persist_settings(self.obj, self._current_settings())


class TaskFan(FloEFDTaskPanel):
    def __init__(self, obj):
        self._presenter = FanPresenter()
        super().__init__(obj)

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
        curve_state = self._presenter.build_curve_state(name, self.fan_database)
        if curve_state["FanType"]:
            idx = self.cb_type.findText(curve_state["FanType"])
            if idx >= 0:
                self.cb_type.setCurrentIndex(idx)
        if curve_state["ReferencePressure"] is not None:
            self.sp_p.setValue(curve_state["ReferencePressure"])
        self.curve_table.setRowCount(0)
        for flow, pressure in curve_state["Curve"]:
            row = self.curve_table.rowCount()
            self.curve_table.insertRow(row)
            self.curve_table.setItem(row, 0, QtGui.QTableWidgetItem(flow))
            self.curve_table.setItem(row, 1, QtGui.QTableWidgetItem(pressure))

    def _current_settings(self):
        if not hasattr(self, "cb_type"):
            return self._presenter.read_settings(self.obj)
        return FanSettings(
            references=tuple(self._refs()),
            fan_type=self.cb_type.currentText(),
            fan_curve_preset=self.cb_curve.currentText(),
            reference_pressure=self.sp_p.value(),
            create_associated_goals=self.chk_goals.isChecked(),
        )

    def _store(self):
        self._presenter.persist_settings(self.obj, self._current_settings())


class TaskResultPlot(FloEFDTaskPanel):
    SUMMARY_TITLE = "Result Plot"
    SUMMARY_DETAIL = (
        "Define how {label} should visualize a result field across the selected geometry or seed locations."
    )

    def __init__(self, obj):
        self._presenter = ResultPlotPresenter()
        super().__init__(obj)

    def _build_task_validation(self):
        level, title, detail = self._presenter.build_validation(self._current_settings())
        if level:
            return level, title, detail
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

    def _current_settings(self):
        if not hasattr(self, "cb_kind"):
            return self._presenter.read_settings(self.obj)
        return ResultPlotSettings(
            references=tuple(self._refs()),
            plot_kind=self.cb_kind.currentText(),
            field=self.cb_field.currentText(),
            contour_count=self.sp_contours.value(),
            contours=self.chk_contours.isChecked(),
            isolines=self.chk_isolines.isChecked(),
            vectors=self.chk_vectors.isChecked(),
            streamlines=self.chk_streamlines.isChecked(),
            cut_plane=self.cb_plane.currentText(),
            plane_offset=self.sp_offset.value(),
            use_cad_geometry=self.chk_cad.isChecked(),
            interpolate=self.chk_interp.isChecked(),
            export_excel=self.chk_excel.isChecked(),
        )

    def _store(self):
        self._presenter.persist_settings(self.obj, self._current_settings())


class TaskParticleStudy(FloEFDTaskPanel):
    SUMMARY_TITLE = "Particle Study"
    SUMMARY_DETAIL = (
        "Configure how {label} seeds, colors, and limits particle trajectories from the selected injections."
    )

    reference_property = "Injections"

    def __init__(self, obj):
        self._presenter = ParticleStudyPresenter()
        super().__init__(obj)

    def _build_task_validation(self):
        level, title, detail = self._presenter.build_validation(self._current_settings())
        if level:
            return level, title, detail
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

    def _current_settings(self):
        if not hasattr(self, "chk_acc"):
            return self._presenter.read_settings(self.obj)
        return ParticleStudySettings(
            injections=tuple(self._refs()),
            accretion=self.chk_acc.isChecked(),
            erosion=self.chk_ero.isChecked(),
            gravity=self.chk_grav.isChecked(),
            gravity_vector=(self.sp_gx.value(), self.sp_gy.value(), self.sp_gz.value()),
            particle_shape=self.cb_shape.currentText(),
            particle_diameter=self.sp_d.value(),
            color_by_field=self.cb_color.currentText(),
            track_length=self.sp_len.value(),
            track_time=self.sp_time.value(),
            max_particles=self.sp_max.value(),
        )

    def _store(self):
        self._presenter.persist_settings(self.obj, self._current_settings(), FreeCAD.Vector)
