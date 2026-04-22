# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Task panel for Wall boundary condition."""

from PySide import QtGui
from flow_studio.taskpanels.task_flowefd_features import FloEFDTaskPanel


class TaskBCWall(FloEFDTaskPanel):

    SUMMARY_TITLE = "Wall Boundary Condition"
    SUMMARY_DETAIL = (
        "Set wall motion, thermal behavior, and surface roughness for {label}."
    )

    def _build_task_validation(self):
        if not self._refs():
            return (
                "incomplete",
                "Assign wall faces",
                "Select one or more wall faces so this boundary condition applies to geometry.",
            )

        thermal_type = str(getattr(self.obj, "ThermalType", "Adiabatic"))
        if thermal_type == "Fixed Temperature" and float(getattr(self.obj, "WallTemperature", 0.0)) <= 0.0:
            return (
                "incomplete",
                "Wall temperature required",
                "Enter a positive wall temperature in kelvin for a fixed-temperature wall.",
            )
        if thermal_type == "Heat Transfer Coefficient" and float(getattr(self.obj, "HeatTransferCoeff", 0.0)) <= 0.0:
            return (
                "incomplete",
                "Heat-transfer coefficient required",
                "Enter a positive heat-transfer coefficient before solving with this wall mode.",
            )

        if (
            str(getattr(self.obj, "WallType", "No-Slip")) == "Rough Wall"
            and float(getattr(self.obj, "RoughnessHeight", 0.0)) <= 0.0
        ):
            return (
                "incomplete",
                "Wall roughness required",
                "Enter a positive roughness height before solving with a rough-wall boundary.",
            )

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

    def _store(self):
        self.obj.WallType = self.cb_type.currentText()
        self.obj.ThermalType = self.cb_thermal.currentText()
        self.obj.WallTemperature = self.sp_temp.value()
        self.obj.HeatFlux = self.sp_flux.value()
        self.obj.HeatTransferCoeff = self.sp_htc.value()
        self.obj.RoughnessHeight = self.sp_rough.value()
