# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Task panel for Wall boundary condition."""

from PySide import QtGui
from flow_studio.taskpanels.task_flowefd_features import FloEFDTaskPanel
from flow_studio.ui.bc_wall_presenter import WallBoundaryPresenter, WallBoundarySettings


class TaskBCWall(FloEFDTaskPanel):

    SUMMARY_TITLE = "Wall Boundary Condition"
    SUMMARY_DETAIL = (
        "Set wall motion, thermal behavior, and surface roughness for {label}."
    )

    def __init__(self, obj):
        self._presenter = WallBoundaryPresenter()
        super().__init__(obj)

    def _build_task_validation(self):
        level, title, detail = self._presenter.build_validation(self._current_settings())
        if level:
            return level, title, detail
        return super()._build_task_validation()

    def _build_form(self):
        widget = QtGui.QWidget()
        layout = QtGui.QVBoxLayout(widget)
        layout.addWidget(QtGui.QLabel("<b>Wall Boundary Condition</b>"))
        self._add_selection_section(layout)

        wall = self._section(layout, "Wall Motion")
        self.cb_type = self._combo(
            ["No-Slip", "Slip", "Moving Wall (Translational)",
             "Moving Wall (Rotational)", "Rough Wall"],
            self.obj.WallType,
        )
        self._add_row(wall, "Wall Type:", self.cb_type)

        thermal = self._section(layout, "Thermal")
        self.cb_thermal = self._combo(
            ["Adiabatic", "Fixed Temperature", "Fixed Heat Flux",
             "Heat Transfer Coefficient"],
            self.obj.ThermalType,
        )
        self._add_row(thermal, "Thermal BC:", self.cb_thermal)

        self.sp_temp = self._spin_float(self.obj.WallTemperature, 0, 10000, 2, 1)
        self._add_row(thermal, "Temperature [K]:", self.sp_temp)

        self.sp_flux = self._spin_float(self.obj.HeatFlux, -1e9, 1e9, 2, 100)
        self._add_row(thermal, "Heat Flux [W/m²]:", self.sp_flux)

        self.sp_htc = self._spin_float(self.obj.HeatTransferCoeff, 0, 1e9, 2, 10)
        self._add_row(thermal, "Heat Transfer Coeff. [W/(m²·K)]:", self.sp_htc)

        roughness = self._section(layout, "Surface")
        self.sp_rough = self._spin_float(self.obj.RoughnessHeight, 0, 1, 6, 0.0001)
        self._add_row(roughness, "Roughness Ks [m]:", self.sp_rough)

        layout.addStretch()
        return widget

    def _current_settings(self):
        if not hasattr(self, "cb_type"):
            return self._presenter.read_settings(self.obj)
        return WallBoundarySettings(
            references=tuple(self._refs()),
            wall_type=self.cb_type.currentText(),
            thermal_type=self.cb_thermal.currentText(),
            wall_temperature=self.sp_temp.value(),
            heat_flux=self.sp_flux.value(),
            heat_transfer_coeff=self.sp_htc.value(),
            roughness_height=self.sp_rough.value(),
        )

    def _store(self):
        self._presenter.persist_settings(self.obj, self._current_settings())
