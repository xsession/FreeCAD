# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Task panel for InitialConditions."""

from PySide import QtGui
from flow_studio.taskpanels.base_taskpanel import BaseTaskPanel


class TaskInitialConditions(BaseTaskPanel):

    def _build_form(self):
        widget = QtGui.QWidget()
        layout = QtGui.QVBoxLayout(widget)
        layout.addWidget(QtGui.QLabel("<b>Initial Conditions</b>"))

        # Velocity
        self.sp_ux = self._spin_float(self.obj.Ux)
        self._add_row(layout, "Ux [m/s]:", self.sp_ux)
        self.sp_uy = self._spin_float(self.obj.Uy)
        self._add_row(layout, "Uy [m/s]:", self.sp_uy)
        self.sp_uz = self._spin_float(self.obj.Uz)
        self._add_row(layout, "Uz [m/s]:", self.sp_uz)

        # Pressure
        self.sp_p = self._spin_float(self.obj.Pressure, -1e9, 1e9, 2, 100)
        self._add_row(layout, "Pressure [Pa]:", self.sp_p)

        # Temperature
        self.sp_T = self._spin_float(self.obj.Temperature, 0, 10000, 2, 1)
        self._add_row(layout, "Temperature [K]:", self.sp_T)

        # Turbulence
        self.sp_k = self._spin_float(self.obj.TurbulentKineticEnergy, 0, 1e6, 6, 0.001)
        self._add_row(layout, "k [m²/s²]:", self.sp_k)
        self.sp_omega = self._spin_float(self.obj.SpecificDissipationRate, 0, 1e9, 2, 1)
        self._add_row(layout, "ω [1/s]:", self.sp_omega)

        # Potential flow init
        self.chk_pot = self._checkbox(self.obj.UsePotentialFlow)
        self._add_row(layout, "Potential Flow Init:", self.chk_pot)

        layout.addStretch()
        return widget

    def _store(self):
        self.obj.Ux = self.sp_ux.value()
        self.obj.Uy = self.sp_uy.value()
        self.obj.Uz = self.sp_uz.value()
        self.obj.Pressure = self.sp_p.value()
        self.obj.Temperature = self.sp_T.value()
        self.obj.TurbulentKineticEnergy = self.sp_k.value()
        self.obj.SpecificDissipationRate = self.sp_omega.value()
        self.obj.UsePotentialFlow = self.chk_pot.isChecked()
