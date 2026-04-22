# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Task panel for MeasurementVolume (box / sphere / threshold region)."""

import FreeCAD
from PySide import QtGui
from flow_studio.taskpanels.base_taskpanel import BaseTaskPanel


class TaskMeasurementVolume(BaseTaskPanel):

    SUMMARY_TITLE = "Volume Measurement"
    SUMMARY_DETAIL = (
        "Define a volume extraction for {label}, then choose sampled fields and statistics to compute."
    )

    def _build_task_validation(self):
        fields = [field.strip() for field in self.le_fields.text().split(",") if field.strip()]
        if not fields:
            return (
                "incomplete",
                "Select sampled fields",
                "Enter at least one field name so the volume measurement has data to evaluate.",
            )

        volume_type = self.cb_type.currentText()
        if volume_type == "Box":
            if not (
                self.sp_bx0.value() < self.sp_bx1.value()
                and self.sp_by0.value() < self.sp_by1.value()
                and self.sp_bz0.value() < self.sp_bz1.value()
            ):
                return (
                    "warning",
                    "Box limits are invalid",
                    "Set each minimum corner value below its corresponding maximum value.",
                )

        if volume_type == "Sphere" and self.sp_sr.value() <= 0.0:
            return (
                "warning",
                "Sphere radius required",
                "Enter a positive sphere radius before evaluating this volume measurement.",
            )

        if volume_type == "Cylinder":
            axis = (self.sp_cax.value(), self.sp_cay.value(), self.sp_caz.value())
            if axis == (0.0, 0.0, 0.0):
                return (
                    "warning",
                    "Cylinder axis cannot be zero",
                    "Set a non-zero cylinder axis vector so the volume orientation is defined.",
                )
            if self.sp_cr.value() <= 0.0 or self.sp_ch.value() <= 0.0:
                return (
                    "warning",
                    "Cylinder size required",
                    "Enter positive cylinder radius and height values before evaluating this region.",
                )

        if volume_type == "Threshold (field-based)":
            if not self.le_thrfield.text().strip():
                return (
                    "incomplete",
                    "Threshold field required",
                    "Choose the field used to create the threshold-based measurement region.",
                )
            if self.sp_thrmin.value() >= self.sp_thrmax.value():
                return (
                    "warning",
                    "Threshold range is invalid",
                    "Set a threshold minimum smaller than the threshold maximum.",
                )

        if not any((self.chk_avg.isChecked(), self.chk_minmax.isChecked(), self.chk_integ.isChecked())):
            return (
                "warning",
                "Select a statistic to compute",
                "Enable at least one evaluation output such as average, min/max, or integral.",
            )

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

    def _store(self):
        self.obj.Label2 = self.le_desc.text()
        self.obj.VolumeType = self.cb_type.currentText()

        self.obj.BoxMin = FreeCAD.Vector(
            self.sp_bx0.value(), self.sp_by0.value(), self.sp_bz0.value()
        )
        self.obj.BoxMax = FreeCAD.Vector(
            self.sp_bx1.value(), self.sp_by1.value(), self.sp_bz1.value()
        )

        self.obj.SphereCenter = FreeCAD.Vector(
            self.sp_scx.value(), self.sp_scy.value(), self.sp_scz.value()
        )
        self.obj.SphereRadius = self.sp_sr.value()

        self.obj.CylinderCenter = FreeCAD.Vector(
            self.sp_ccx.value(), self.sp_ccy.value(), self.sp_ccz.value()
        )
        self.obj.CylinderAxis = FreeCAD.Vector(
            self.sp_cax.value(), self.sp_cay.value(), self.sp_caz.value()
        )
        self.obj.CylinderRadius = self.sp_cr.value()
        self.obj.CylinderHeight = self.sp_ch.value()

        self.obj.ThresholdField = self.le_thrfield.text()
        self.obj.ThresholdMin = self.sp_thrmin.value()
        self.obj.ThresholdMax = self.sp_thrmax.value()

        fields = [f.strip() for f in self.le_fields.text().split(",") if f.strip()]
        self.obj.SampleFields = fields

        self.obj.ComputeAverage = self.chk_avg.isChecked()
        self.obj.ComputeMinMax = self.chk_minmax.isChecked()
        self.obj.ComputeIntegral = self.chk_integ.isChecked()

        self.obj.ExportCSV = self.chk_csv.isChecked()
        self.obj.TimeSeries = self.chk_ts.isChecked()
