# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Task panel for MeasurementSurface (cut-plane / iso-surface evaluation)."""

import FreeCAD
from PySide import QtGui
from flow_studio.taskpanels.base_taskpanel import BaseTaskPanel
from flow_studio.ui.measurement_surface_presenter import MeasurementSurfacePresenter, MeasurementSurfaceSettings


class TaskMeasurementSurface(BaseTaskPanel):

    SUMMARY_TITLE = "Surface Measurement"
    SUMMARY_DETAIL = (
        "Define a surface extraction for {label}, then choose sampled fields and evaluation outputs."
    )

    def __init__(self, obj):
        self._presenter = MeasurementSurfacePresenter()
        super().__init__(obj)

    def _build_task_validation(self):
        level, title, detail = self._presenter.build_validation(self._current_settings())
        if level:
            return level, title, detail
        return super()._build_task_validation()

    def _build_form(self):
        widget = QtGui.QWidget()
        layout = QtGui.QVBoxLayout(widget)
        layout.addWidget(QtGui.QLabel("<b>Surface Measurement</b>"))
        layout.addWidget(QtGui.QLabel(
            "Define a cut-plane, iso-surface, or clip region for evaluation."
        ))

        definition = self._section(layout, "Definition")
        self.le_desc = QtGui.QLineEdit(self.obj.Label2)
        self._add_row(definition, "Description:", self.le_desc)

        self.cb_type = self._combo(
            ["Cut Plane", "Iso-Surface", "Geometry Faces", "Clip (Half-Space)"],
            self.obj.SurfaceType,
        )
        self._add_row(definition, "Surface Type:", self.cb_type)

        # --- Cut Plane ---
        grp_plane = QtGui.QGroupBox("Cut Plane / Clip")
        pl_lay = QtGui.QVBoxLayout(grp_plane)
        o = self.obj.PlaneOrigin
        self.sp_ox = self._spin_float(o.x)
        self.sp_oy = self._spin_float(o.y)
        self.sp_oz = self._spin_float(o.z)
        self._add_row(pl_lay, "Origin X [mm]:", self.sp_ox)
        self._add_row(pl_lay, "Origin Y [mm]:", self.sp_oy)
        self._add_row(pl_lay, "Origin Z [mm]:", self.sp_oz)
        self.cb_normal = self._combo(["X", "Y", "Z", "Custom"], self.obj.PlaneNormal)
        self._add_row(pl_lay, "Normal Axis:", self.cb_normal)
        cn = self.obj.CustomNormal
        self.sp_nx = self._spin_float(cn.x, -1.0, 1.0, 4, 0.1)
        self.sp_ny = self._spin_float(cn.y, -1.0, 1.0, 4, 0.1)
        self.sp_nz = self._spin_float(cn.z, -1.0, 1.0, 4, 0.1)
        self._add_row(pl_lay, "Custom Nx:", self.sp_nx)
        self._add_row(pl_lay, "Custom Ny:", self.sp_ny)
        self._add_row(pl_lay, "Custom Nz:", self.sp_nz)
        layout.addWidget(grp_plane)

        # --- Iso-Surface ---
        grp_iso = QtGui.QGroupBox("Iso-Surface")
        iso_lay = QtGui.QVBoxLayout(grp_iso)
        self.le_isofield = QtGui.QLineEdit(self.obj.IsoField)
        self._add_row(iso_lay, "Field:", self.le_isofield)
        self.sp_isoval = self._spin_float(self.obj.IsoValue)
        self._add_row(iso_lay, "Value:", self.sp_isoval)
        layout.addWidget(grp_iso)

        sampling = self._section(layout, "Sampling")
        self.le_fields = QtGui.QLineEdit(
            ", ".join(self.obj.SampleFields) if self.obj.SampleFields else "U, p"
        )
        self._add_row(sampling, "Fields:", self.le_fields)

        # --- Evaluation options ---
        grp_eval = QtGui.QGroupBox("Evaluation")
        eval_lay = QtGui.QVBoxLayout(grp_eval)
        self.chk_avg = self._checkbox(self.obj.ComputeAverage)
        self._add_row(eval_lay, "Area-Weighted Average:", self.chk_avg)
        self.chk_integ = self._checkbox(self.obj.ComputeIntegral)
        self._add_row(eval_lay, "Surface Integral:", self.chk_integ)
        self.chk_mflow = self._checkbox(self.obj.ComputeMassFlow)
        self._add_row(eval_lay, "Mass Flow Rate:", self.chk_mflow)
        self.chk_force = self._checkbox(self.obj.ComputeForce)
        self._add_row(eval_lay, "Force / Moment:", self.chk_force)
        rp = self.obj.ForceRefPoint
        self.sp_rpx = self._spin_float(rp.x)
        self.sp_rpy = self._spin_float(rp.y)
        self.sp_rpz = self._spin_float(rp.z)
        self._add_row(eval_lay, "Ref Point X:", self.sp_rpx)
        self._add_row(eval_lay, "Ref Point Y:", self.sp_rpy)
        self._add_row(eval_lay, "Ref Point Z:", self.sp_rpz)
        layout.addWidget(grp_eval)

        grp_exp = QtGui.QGroupBox("Export")
        exp_lay = QtGui.QVBoxLayout(grp_exp)
        self.chk_csv = self._checkbox(self.obj.ExportCSV)
        self._add_row(exp_lay, "Export CSV:", self.chk_csv)
        self.chk_vtk = self._checkbox(self.obj.ExportVTK)
        self._add_row(exp_lay, "Export VTK:", self.chk_vtk)
        self.chk_ts = self._checkbox(self.obj.TimeSeries)
        self._add_row(exp_lay, "Time Series:", self.chk_ts)
        layout.addWidget(grp_exp)

        layout.addStretch()
        return widget

    def _current_settings(self):
        if not hasattr(self, "le_desc"):
            return self._presenter.read_settings(self.obj)

        fields = tuple(field.strip() for field in self.le_fields.text().split(",") if field.strip())
        return MeasurementSurfaceSettings(
            label2=self.le_desc.text(),
            surface_type=self.cb_type.currentText(),
            plane_origin=(self.sp_ox.value(), self.sp_oy.value(), self.sp_oz.value()),
            plane_normal=self.cb_normal.currentText(),
            custom_normal=(self.sp_nx.value(), self.sp_ny.value(), self.sp_nz.value()),
            iso_field=self.le_isofield.text(),
            iso_value=self.sp_isoval.value(),
            sample_fields=fields,
            compute_average=self.chk_avg.isChecked(),
            compute_integral=self.chk_integ.isChecked(),
            compute_mass_flow=self.chk_mflow.isChecked(),
            compute_force=self.chk_force.isChecked(),
            force_ref_point=(self.sp_rpx.value(), self.sp_rpy.value(), self.sp_rpz.value()),
            export_csv=self.chk_csv.isChecked(),
            export_vtk=self.chk_vtk.isChecked(),
            time_series=self.chk_ts.isChecked(),
            face_refs=tuple(getattr(self.obj, "FaceRefs", []) or []),
        )

    def _store(self):
        self._presenter.persist_settings(self.obj, self._current_settings(), FreeCAD.Vector)
