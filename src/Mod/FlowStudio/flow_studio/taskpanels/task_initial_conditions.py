# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Task panel for InitialConditions."""

from PySide import QtGui
from flow_studio.taskpanels.task_flowefd_features import FloEFDTaskPanel
from flow_studio.ui.initial_conditions_presenter import InitialConditionsPresenter, InitialConditionsSettings


class TaskInitialConditions(FloEFDTaskPanel):

    SUMMARY_TITLE = "Initial Conditions"
    SUMMARY_DETAIL = (
        "Set the starting field values and turbulence initialization for {label}."
    )

    def __init__(self, obj):
        self._presenter = InitialConditionsPresenter()
        super().__init__(obj)

    def _build_task_validation(self):
        level, title, detail = self._presenter.build_validation(self._current_settings())
        if level:
            return level, title, detail
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

    def _current_settings(self):
        if not hasattr(self, "sp_ux"):
            return self._presenter.read_settings(self.obj)
        return InitialConditionsSettings(
            references=tuple(self._refs()),
            ux=self.sp_ux.value(),
            uy=self.sp_uy.value(),
            uz=self.sp_uz.value(),
            pressure=self.sp_p.value(),
            temperature=self.sp_T.value(),
            turbulent_kinetic_energy=self.sp_k.value(),
            specific_dissipation_rate=self.sp_omega.value(),
            use_potential_flow=self.chk_pot.isChecked(),
        )

    def _store(self):
        self._presenter.persist_settings(self.obj, self._current_settings())
