# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Task panel for Inlet boundary condition."""

from PySide import QtGui
from flow_studio.taskpanels.base_taskpanel import BaseTaskPanel


class TaskBCInlet(BaseTaskPanel):

    def _build_form(self):
        widget = QtGui.QWidget()
        layout = QtGui.QVBoxLayout(widget)
        layout.addWidget(QtGui.QLabel("<b>Inlet Boundary Condition</b>"))

        self.cb_type = self._combo(
            ["Velocity", "Mass Flow Rate", "Volumetric Flow Rate", "Total Pressure"],
            self.obj.InletType,
        )
        self._add_row(layout, "Inlet Type:", self.cb_type)

        self.sp_ux = self._spin_float(self.obj.Ux)
        self._add_row(layout, "Ux [m/s]:", self.sp_ux)
        self.sp_uy = self._spin_float(self.obj.Uy)
        self._add_row(layout, "Uy [m/s]:", self.sp_uy)
        self.sp_uz = self._spin_float(self.obj.Uz)
        self._add_row(layout, "Uz [m/s]:", self.sp_uz)

        self.chk_normal = self._checkbox(self.obj.NormalToFace)
        self._add_row(layout, "Normal to Face:", self.chk_normal)

        self.sp_mfr = self._spin_float(self.obj.MassFlowRate, 0, 1e9, 6, 0.01)
        self._add_row(layout, "Mass Flow Rate [kg/s]:", self.sp_mfr)

        self.sp_vfr = self._spin_float(self.obj.VolFlowRate, 0, 1e9, 6, 0.001)
        self._add_row(layout, "Vol. Flow Rate [m³/s]:", self.sp_vfr)

        # Turbulence
        self.cb_turb = self._combo(
            ["Intensity & Length Scale", "Intensity & Viscosity Ratio",
             "k & Epsilon", "k & Omega"],
            self.obj.TurbulenceSpec,
        )
        self._add_row(layout, "Turbulence Spec:", self.cb_turb)
        self.sp_ti = self._spin_float(self.obj.TurbulenceIntensity, 0, 100, 2, 1)
        self._add_row(layout, "Turb. Intensity [%]:", self.sp_ti)

        # Temperature
        self.sp_T = self._spin_float(self.obj.InletTemperature, 0, 10000, 2, 1)
        self._add_row(layout, "Temperature [K]:", self.sp_T)

        layout.addStretch()
        return widget

    def _store(self):
        self.obj.InletType = self.cb_type.currentText()
        self.obj.Ux = self.sp_ux.value()
        self.obj.Uy = self.sp_uy.value()
        self.obj.Uz = self.sp_uz.value()
        self.obj.NormalToFace = self.chk_normal.isChecked()
        self.obj.MassFlowRate = self.sp_mfr.value()
        self.obj.VolFlowRate = self.sp_vfr.value()
        self.obj.TurbulenceSpec = self.cb_turb.currentText()
        self.obj.TurbulenceIntensity = self.sp_ti.value()
        self.obj.InletTemperature = self.sp_T.value()
