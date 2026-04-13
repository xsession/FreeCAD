# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Task panel for Outlet boundary condition."""

from PySide import QtGui
from flow_studio.taskpanels.base_taskpanel import BaseTaskPanel


class TaskBCOutlet(BaseTaskPanel):

    def _build_form(self):
        widget = QtGui.QWidget()
        layout = QtGui.QVBoxLayout(widget)
        layout.addWidget(QtGui.QLabel("<b>Outlet Boundary Condition</b>"))

        self.cb_type = self._combo(
            ["Static Pressure", "Mass Flow Rate", "Outflow (Zero Gradient)"],
            self.obj.OutletType,
        )
        self._add_row(layout, "Outlet Type:", self.cb_type)

        self.sp_p = self._spin_float(self.obj.StaticPressure, -1e9, 1e9, 2, 100)
        self._add_row(layout, "Pressure [Pa]:", self.sp_p)

        self.chk_backflow = self._checkbox(self.obj.PreventBackflow)
        self._add_row(layout, "Prevent Backflow:", self.chk_backflow)

        layout.addStretch()
        return widget

    def _store(self):
        self.obj.OutletType = self.cb_type.currentText()
        self.obj.StaticPressure = self.sp_p.value()
        self.obj.PreventBackflow = self.chk_backflow.isChecked()
