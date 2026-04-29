# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Task panel for MeasurementVolume (box / sphere / threshold region)."""

import FreeCAD
from PySide import QtGui
from flow_studio.taskpanels.base_taskpanel import BaseTaskPanel
from flow_studio.ui.measurement_volume_presenter import MeasurementVolumePresenter, MeasurementVolumeSettings


class TaskMeasurementVolume(BaseTaskPanel):

    SUMMARY_TITLE = "Volume Measurement"
    SUMMARY_DETAIL = (
        "Define a volume extraction for {label}, then choose sampled fields and statistics to compute."
    )

    def __init__(self, obj):
        self._presenter = MeasurementVolumePresenter()
        super().__init__(obj)

    def _build_task_validation(self):
        level, title, detail = self._presenter.build_validation(self._current_settings())
        if level:
            return level, title, detail
        return super()._build_task_validation()

    def _build_form(self):
        widget = QtGui.QWidget()
        layout = QtGui.QVBoxLayout(widget)
        layout.addWidget(QtGui.QLabel("<b>Volume Measurement</b>"))
        layout.addWidget(QtGui.QLabel(
            "Define a volume region for field statistics in Paraview."
        ))

        definition = self._section(layout, "Definition")
        self.le_desc = QtGui.QLineEdit(self.obj.Label2)
        self._add_row(definition, "Description:", self.le_desc)

        self.cb_type = self._combo(
            ["Box", "Sphere", "Cylinder", "Threshold (field-based)", "Entire Domain"],
            self.obj.VolumeType,
        )
        self._add_row(definition, "Volume Type:", self.cb_type)

        # --- Box ---
        grp_box = QtGui.QGroupBox("Box")
        box_lay = QtGui.QVBoxLayout(grp_box)
        bmin = self.obj.BoxMin
        bmax = self.obj.BoxMax
        self.sp_bx0 = self._spin_float(bmin.x)
        self.sp_by0 = self._spin_float(bmin.y)
        self.sp_bz0 = self._spin_float(bmin.z)
        self.sp_bx1 = self._spin_float(bmax.x)
        self.sp_by1 = self._spin_float(bmax.y)
        self.sp_bz1 = self._spin_float(bmax.z)
        self._add_row(box_lay, "Min X [mm]:", self.sp_bx0)
        self._add_row(box_lay, "Min Y [mm]:", self.sp_by0)
        self._add_row(box_lay, "Min Z [mm]:", self.sp_bz0)
        self._add_row(box_lay, "Max X [mm]:", self.sp_bx1)
        self._add_row(box_lay, "Max Y [mm]:", self.sp_by1)
        self._add_row(box_lay, "Max Z [mm]:", self.sp_bz1)
        layout.addWidget(grp_box)

        # --- Sphere ---
        grp_sph = QtGui.QGroupBox("Sphere")
        sph_lay = QtGui.QVBoxLayout(grp_sph)
        sc = self.obj.SphereCenter
        self.sp_scx = self._spin_float(sc.x)
        self.sp_scy = self._spin_float(sc.y)
        self.sp_scz = self._spin_float(sc.z)
        self.sp_sr = self._spin_float(self.obj.SphereRadius, 0.0)
        self._add_row(sph_lay, "Center X [mm]:", self.sp_scx)
        self._add_row(sph_lay, "Center Y [mm]:", self.sp_scy)
        self._add_row(sph_lay, "Center Z [mm]:", self.sp_scz)
        self._add_row(sph_lay, "Radius [mm]:", self.sp_sr)
        layout.addWidget(grp_sph)

        # --- Cylinder ---
        grp_cyl = QtGui.QGroupBox("Cylinder")
        cyl_lay = QtGui.QVBoxLayout(grp_cyl)
        cc = self.obj.CylinderCenter
        ca = self.obj.CylinderAxis
        self.sp_ccx = self._spin_float(cc.x)
        self.sp_ccy = self._spin_float(cc.y)
        self.sp_ccz = self._spin_float(cc.z)
        self.sp_cax = self._spin_float(ca.x, -1.0, 1.0, 4, 0.1)
        self.sp_cay = self._spin_float(ca.y, -1.0, 1.0, 4, 0.1)
        self.sp_caz = self._spin_float(ca.z, -1.0, 1.0, 4, 0.1)
        self.sp_cr = self._spin_float(self.obj.CylinderRadius, 0.0)
        self.sp_ch = self._spin_float(self.obj.CylinderHeight, 0.0)
        self._add_row(cyl_lay, "Center X [mm]:", self.sp_ccx)
        self._add_row(cyl_lay, "Center Y [mm]:", self.sp_ccy)
        self._add_row(cyl_lay, "Center Z [mm]:", self.sp_ccz)
        self._add_row(cyl_lay, "Axis X:", self.sp_cax)
        self._add_row(cyl_lay, "Axis Y:", self.sp_cay)
        self._add_row(cyl_lay, "Axis Z:", self.sp_caz)
        self._add_row(cyl_lay, "Radius [mm]:", self.sp_cr)
        self._add_row(cyl_lay, "Height [mm]:", self.sp_ch)
        layout.addWidget(grp_cyl)

        # --- Threshold ---
        grp_thr = QtGui.QGroupBox("Threshold")
        thr_lay = QtGui.QVBoxLayout(grp_thr)
        self.le_thrfield = QtGui.QLineEdit(self.obj.ThresholdField)
        self.sp_thrmin = self._spin_float(self.obj.ThresholdMin)
        self.sp_thrmax = self._spin_float(self.obj.ThresholdMax)
        self._add_row(thr_lay, "Field:", self.le_thrfield)
        self._add_row(thr_lay, "Min:", self.sp_thrmin)
        self._add_row(thr_lay, "Max:", self.sp_thrmax)
        layout.addWidget(grp_thr)

        sampling = self._section(layout, "Sampling")
        self.le_fields = QtGui.QLineEdit(
            ", ".join(self.obj.SampleFields) if self.obj.SampleFields else "U, p"
        )
        self._add_row(sampling, "Fields:", self.le_fields)

        # --- Evaluation ---
        grp_eval = QtGui.QGroupBox("Evaluation")
        eval_lay = QtGui.QVBoxLayout(grp_eval)
        self.chk_avg = self._checkbox(self.obj.ComputeAverage)
        self._add_row(eval_lay, "Volume Average:", self.chk_avg)
        self.chk_minmax = self._checkbox(self.obj.ComputeMinMax)
        self._add_row(eval_lay, "Min / Max:", self.chk_minmax)
        self.chk_integ = self._checkbox(self.obj.ComputeIntegral)
        self._add_row(eval_lay, "Volume Integral:", self.chk_integ)
        layout.addWidget(grp_eval)

        export = self._section(layout, "Export")
        self.chk_csv = self._checkbox(self.obj.ExportCSV)
        self._add_row(export, "Export CSV:", self.chk_csv)
        self.chk_ts = self._checkbox(self.obj.TimeSeries)
        self._add_row(export, "Time Series:", self.chk_ts)

        layout.addStretch()
        return widget

    def _current_settings(self):
        if not hasattr(self, "le_desc"):
            return self._presenter.read_settings(self.obj)

        fields = tuple(field.strip() for field in self.le_fields.text().split(",") if field.strip())
        return MeasurementVolumeSettings(
            label2=self.le_desc.text(),
            volume_type=self.cb_type.currentText(),
            box_min=(self.sp_bx0.value(), self.sp_by0.value(), self.sp_bz0.value()),
            box_max=(self.sp_bx1.value(), self.sp_by1.value(), self.sp_bz1.value()),
            sphere_center=(self.sp_scx.value(), self.sp_scy.value(), self.sp_scz.value()),
            sphere_radius=self.sp_sr.value(),
            cylinder_center=(self.sp_ccx.value(), self.sp_ccy.value(), self.sp_ccz.value()),
            cylinder_axis=(self.sp_cax.value(), self.sp_cay.value(), self.sp_caz.value()),
            cylinder_radius=self.sp_cr.value(),
            cylinder_height=self.sp_ch.value(),
            threshold_field=self.le_thrfield.text(),
            threshold_min=self.sp_thrmin.value(),
            threshold_max=self.sp_thrmax.value(),
            sample_fields=fields,
            compute_average=self.chk_avg.isChecked(),
            compute_min_max=self.chk_minmax.isChecked(),
            compute_integral=self.chk_integ.isChecked(),
            export_csv=self.chk_csv.isChecked(),
            time_series=self.chk_ts.isChecked(),
        )

    def _store(self):
        self._presenter.persist_settings(self.obj, self._current_settings(), FreeCAD.Vector)
