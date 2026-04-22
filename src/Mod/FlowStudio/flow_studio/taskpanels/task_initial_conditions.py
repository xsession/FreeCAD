# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Task panel for InitialConditions."""

from PySide import QtGui
from flow_studio.taskpanels.task_flowefd_features import FloEFDTaskPanel


class TaskInitialConditions(FloEFDTaskPanel):

    SUMMARY_TITLE = "Initial Conditions"
    SUMMARY_DETAIL = (
        "Set the starting field values and turbulence initialization for {label}."
    )

    def _build_task_validation(self):
        if not self._refs():
            return (
                "incomplete",
                "Assign target regions",
                "Select one or more bodies, faces, or regions so these initial conditions apply somewhere in the model.",
            )

        if float(getattr(self.obj, "Temperature", 0.0)) <= 0.0:
            return (
                "incomplete",
                "Initial temperature required",
                "Enter a positive starting temperature in kelvin before solving.",
            )

        if float(getattr(self.obj, "TurbulentKineticEnergy", 0.0)) < 0.0:
            return (
                "warning",
                "Turbulent kinetic energy cannot be negative",
                "Use zero or a positive k value for turbulence initialization.",
            )

        if float(getattr(self.obj, "SpecificDissipationRate", 0.0)) < 0.0:
            return (
                "warning",
                "Specific dissipation rate cannot be negative",
                "Use zero or a positive omega value for turbulence initialization.",
            )

        return super()._build_task_validation()

    def _build_form(self):
        widget = QtGui.QWidget()
        layout = QtGui.QVBoxLayout(widget)
        layout.addWidget(QtGui.QLabel("<b>Initial Conditions</b>"))
        self._add_selection_section(layout)

        velocity = self._section(layout, "Velocity")
        self.sp_ux = self._spin_float(self.obj.Ux)
        self._add_row(velocity, "Ux [m/s]:", self.sp_ux)
        self.sp_uy = self._spin_float(self.obj.Uy)
        self._add_row(velocity, "Uy [m/s]:", self.sp_uy)
        self.sp_uz = self._spin_float(self.obj.Uz)
        self._add_row(velocity, "Uz [m/s]:", self.sp_uz)

        pressure = self._section(layout, "Pressure & Temperature")
        self.sp_p = self._spin_float(self.obj.Pressure, -1e9, 1e9, 2, 100)
        self._add_row(pressure, "Pressure [Pa]:", self.sp_p)
        self.sp_T = self._spin_float(self.obj.Temperature, 0, 10000, 2, 1)
        self._add_row(pressure, "Temperature [K]:", self.sp_T)

        turbulence = self._section(layout, "Turbulence")
        self.sp_k = self._spin_float(self.obj.TurbulentKineticEnergy, 0, 1e6, 6, 0.001)
        self._add_row(turbulence, "k [m²/s²]:", self.sp_k)
        self.sp_omega = self._spin_float(self.obj.SpecificDissipationRate, 0, 1e9, 2, 1)
        self._add_row(turbulence, "ω [1/s]:", self.sp_omega)

        initialization = self._section(layout, "Initialization")
        self.chk_pot = self._checkbox(self.obj.UsePotentialFlow)
        self._add_row(initialization, "Potential Flow Init:", self.chk_pot)

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
