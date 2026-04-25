# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Task panel for Open/far-field boundary condition."""

from PySide import QtGui
from flow_studio.taskpanels.task_flowefd_features import FloEFDTaskPanel
from flow_studio.ui.bc_open_presenter import OpenBoundaryPresenter, OpenBoundarySettings


class TaskBCOpen(FloEFDTaskPanel):

    SUMMARY_TITLE = "Open Boundary"
    SUMMARY_DETAIL = (
        "Define far-field pressure, temperature, and freestream velocity for {label}."
    )

    def __init__(self, obj):
        self._presenter = OpenBoundaryPresenter()
        super().__init__(obj)

    def _build_task_validation(self):
        level, title, detail = self._presenter.build_validation(self._current_settings())
        if level:
            return level, title, detail
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

    def _current_settings(self):
        if not hasattr(self, "sp_p"):
            return self._presenter.read_settings(self.obj)
        return OpenBoundarySettings(
            references=tuple(self._refs()),
            far_field_pressure=self.sp_p.value(),
            far_field_temperature=self.sp_T.value(),
            far_field_velocity_x=self.sp_vx.value(),
            far_field_velocity_y=self.sp_vy.value(),
            far_field_velocity_z=self.sp_vz.value(),
        )

    def _store(self):
        self._presenter.persist_settings(self.obj, self._current_settings())
