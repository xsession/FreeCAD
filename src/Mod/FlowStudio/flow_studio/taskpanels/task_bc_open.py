# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Task panel for Open/far-field boundary condition."""

from PySide import QtGui
from flow_studio.taskpanels.task_flowefd_features import FloEFDTaskPanel


class TaskBCOpen(FloEFDTaskPanel):

    SUMMARY_TITLE = "Open Boundary"
    SUMMARY_DETAIL = (
        "Define far-field pressure, temperature, and freestream velocity for {label}."
    )

    def _build_task_validation(self):
        if not self._refs():
            return (
                "incomplete",
                "Assign open-boundary faces",
                "Select one or more exterior faces so the far-field condition can be applied.",
            )

        if float(getattr(self.obj, "FarFieldTemperature", 0.0)) <= 0.0:
            return (
                "incomplete",
                "Far-field temperature required",
                "Enter a positive far-field temperature in kelvin before solving with this boundary.",
            )

        return super()._build_task_validation()

    def _build_form(self):
        widget = QtGui.QWidget()
        layout = QtGui.QVBoxLayout(widget)
        layout.addWidget(QtGui.QLabel("<b>Open / Far-Field Boundary</b>"))
        self._add_selection_section(layout)

        far_field = self._section(layout, "Far-Field State")

        self.sp_p = self._spin_float(self.obj.FarFieldPressure, 0, 1e9, 1, 1000)
        self._add_row(far_field, "Pressure [Pa]:", self.sp_p)
        self.sp_T = self._spin_float(self.obj.FarFieldTemperature, 0, 10000, 2, 1)
        self._add_row(far_field, "Temperature [K]:", self.sp_T)

        self.sp_vx = self._spin_float(self.obj.FarFieldVelocityX)
        self._add_row(far_field, "Velocity X [m/s]:", self.sp_vx)
        self.sp_vy = self._spin_float(self.obj.FarFieldVelocityY)
        self._add_row(far_field, "Velocity Y [m/s]:", self.sp_vy)
        self.sp_vz = self._spin_float(self.obj.FarFieldVelocityZ)
        self._add_row(far_field, "Velocity Z [m/s]:", self.sp_vz)

        layout.addStretch()
        return widget

    def _store(self):
        self.obj.FarFieldPressure = self.sp_p.value()
        self.obj.FarFieldTemperature = self.sp_T.value()
        self.obj.FarFieldVelocityX = self.sp_vx.value()
        self.obj.FarFieldVelocityY = self.sp_vy.value()
        self.obj.FarFieldVelocityZ = self.sp_vz.value()
