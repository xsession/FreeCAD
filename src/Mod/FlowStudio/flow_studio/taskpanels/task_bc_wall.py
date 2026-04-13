# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Task panel for Wall boundary condition."""

from PySide import QtGui
from flow_studio.taskpanels.base_taskpanel import BaseTaskPanel


class TaskBCWall(BaseTaskPanel):

    def _build_form(self):
        widget = QtGui.QWidget()
        layout = QtGui.QVBoxLayout(widget)
        layout.addWidget(QtGui.QLabel("<b>Wall Boundary Condition</b>"))

        self.cb_type = self._combo(
            ["No-Slip", "Slip", "Moving Wall (Translational)",
             "Moving Wall (Rotational)", "Rough Wall"],
            self.obj.WallType,
        )
        self._add_row(layout, "Wall Type:", self.cb_type)

        # Thermal
        self.cb_thermal = self._combo(
            ["Adiabatic", "Fixed Temperature", "Fixed Heat Flux",
             "Heat Transfer Coefficient"],
            self.obj.ThermalType,
        )
        self._add_row(layout, "Thermal BC:", self.cb_thermal)

        self.sp_temp = self._spin_float(self.obj.WallTemperature, 0, 10000, 2, 1)
        self._add_row(layout, "Temperature [K]:", self.sp_temp)

        self.sp_flux = self._spin_float(self.obj.HeatFlux, -1e9, 1e9, 2, 100)
        self._add_row(layout, "Heat Flux [W/m²]:", self.sp_flux)

        # Roughness
        self.sp_rough = self._spin_float(self.obj.RoughnessHeight, 0, 1, 6, 0.0001)
        self._add_row(layout, "Roughness Ks [m]:", self.sp_rough)

        layout.addStretch()
        return widget

    def _store(self):
        self.obj.WallType = self.cb_type.currentText()
        self.obj.ThermalType = self.cb_thermal.currentText()
        self.obj.WallTemperature = self.sp_temp.value()
        self.obj.HeatFlux = self.sp_flux.value()
        self.obj.RoughnessHeight = self.sp_rough.value()
