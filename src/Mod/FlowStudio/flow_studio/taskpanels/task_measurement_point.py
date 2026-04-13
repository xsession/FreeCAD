# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Task panel for MeasurementPoint (point / line probe)."""

import FreeCAD
from PySide import QtGui
from flow_studio.taskpanels.base_taskpanel import BaseTaskPanel


class TaskMeasurementPoint(BaseTaskPanel):

    def _build_form(self):
        widget = QtGui.QWidget()
        layout = QtGui.QVBoxLayout(widget)
        layout.addWidget(QtGui.QLabel("<b>Point / Line Probe</b>"))
        layout.addWidget(QtGui.QLabel(
            "Define measurement points for Paraview evaluation scripts."
        ))

        # Description
        self.le_desc = QtGui.QLineEdit(self.obj.Label2)
        self._add_row(layout, "Description:", self.le_desc)

        # --- Single Point ---
        grp_pt = QtGui.QGroupBox("Point Probe")
        pt_lay = QtGui.QVBoxLayout(grp_pt)
        v = self.obj.ProbeLocation
        self.sp_px = self._spin_float(v.x)
        self.sp_py = self._spin_float(v.y)
        self.sp_pz = self._spin_float(v.z)
        self._add_row(pt_lay, "X [mm]:", self.sp_px)
        self._add_row(pt_lay, "Y [mm]:", self.sp_py)
        self._add_row(pt_lay, "Z [mm]:", self.sp_pz)
        layout.addWidget(grp_pt)

        # --- Line Probe ---
        self.chk_line = self._checkbox(self.obj.UseLine)
        self._add_row(layout, "Use Line Probe:", self.chk_line)

        grp_line = QtGui.QGroupBox("Line Probe (Plot Over Line)")
        line_lay = QtGui.QVBoxLayout(grp_line)
        s = self.obj.LineStart
        e = self.obj.LineEnd
        self.sp_sx = self._spin_float(s.x)
        self.sp_sy = self._spin_float(s.y)
        self.sp_sz = self._spin_float(s.z)
        self.sp_ex = self._spin_float(e.x)
        self.sp_ey = self._spin_float(e.y)
        self.sp_ez = self._spin_float(e.z)
        self._add_row(line_lay, "Start X [mm]:", self.sp_sx)
        self._add_row(line_lay, "Start Y [mm]:", self.sp_sy)
        self._add_row(line_lay, "Start Z [mm]:", self.sp_sz)
        self._add_row(line_lay, "End X [mm]:", self.sp_ex)
        self._add_row(line_lay, "End Y [mm]:", self.sp_ey)
        self._add_row(line_lay, "End Z [mm]:", self.sp_ez)
        self.sp_res = self._spin_int(self.obj.LineResolution, 2, 10000)
        self._add_row(line_lay, "Resolution:", self.sp_res)
        layout.addWidget(grp_line)
        self.grp_line = grp_line
        grp_line.setEnabled(self.obj.UseLine)
        self.chk_line.toggled.connect(grp_line.setEnabled)

        # --- Fields ---
        self.le_fields = QtGui.QLineEdit(
            ", ".join(self.obj.SampleFields) if self.obj.SampleFields else "U, p"
        )
        self.le_fields.setToolTip("Comma-separated field names, e.g. U, p, T, k")
        self._add_row(layout, "Fields:", self.le_fields)

        # --- Export ---
        self.chk_csv = self._checkbox(self.obj.ExportCSV)
        self._add_row(layout, "Export CSV:", self.chk_csv)
        self.chk_ts = self._checkbox(self.obj.TimeSeries)
        self._add_row(layout, "Time Series:", self.chk_ts)

        layout.addStretch()
        return widget

    def _store(self):
        self.obj.Label2 = self.le_desc.text()

        self.obj.ProbeLocation = FreeCAD.Vector(
            self.sp_px.value(), self.sp_py.value(), self.sp_pz.value()
        )

        self.obj.UseLine = self.chk_line.isChecked()
        self.obj.LineStart = FreeCAD.Vector(
            self.sp_sx.value(), self.sp_sy.value(), self.sp_sz.value()
        )
        self.obj.LineEnd = FreeCAD.Vector(
            self.sp_ex.value(), self.sp_ey.value(), self.sp_ez.value()
        )
        self.obj.LineResolution = self.sp_res.value()

        fields = [f.strip() for f in self.le_fields.text().split(",") if f.strip()]
        self.obj.SampleFields = fields

        self.obj.ExportCSV = self.chk_csv.isChecked()
        self.obj.TimeSeries = self.chk_ts.isChecked()
