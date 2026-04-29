# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Task panel for Inlet boundary condition."""

from PySide import QtGui
from flow_studio.taskpanels.task_flowefd_features import FloEFDTaskPanel
from flow_studio.ui.bc_inlet_presenter import InletBoundaryPresenter, InletBoundarySettings


class TaskBCInlet(FloEFDTaskPanel):

    SUMMARY_TITLE = "Inlet Boundary Condition"
    SUMMARY_DETAIL = (
        "Define how fluid enters {label}, including flow specification, turbulence, and temperature."
    )

    def __init__(self, obj):
        self._presenter = InletBoundaryPresenter()
        super().__init__(obj)

    def _build_task_validation(self):
        level, title, detail = self._presenter.build_validation(self._current_settings())
        if level:
            return level, title, detail
        return super()._build_task_validation()

    def _build_form(self):
        widget = QtGui.QWidget()
        layout = QtGui.QVBoxLayout(widget)
        layout.addWidget(QtGui.QLabel("<b>Inlet Boundary Condition</b>"))
        self._add_selection_section(layout)

        inlet = self._section(layout, "Flow Specification")
        self.cb_type = self._combo(
            ["Velocity", "Mass Flow Rate", "Volumetric Flow Rate", "Total Pressure"],
            self.obj.InletType,
        )
        self._add_row(inlet, "Inlet Type:", self.cb_type)

        self.sp_ux = self._spin_float(self.obj.Ux)
        self._add_row(inlet, "Ux [m/s]:", self.sp_ux)
        self.sp_uy = self._spin_float(self.obj.Uy)
        self._add_row(inlet, "Uy [m/s]:", self.sp_uy)
        self.sp_uz = self._spin_float(self.obj.Uz)
        self._add_row(inlet, "Uz [m/s]:", self.sp_uz)

        self.chk_normal = self._checkbox(self.obj.NormalToFace)
        self._add_row(inlet, "Normal to Face:", self.chk_normal)

        self.sp_mfr = self._spin_float(self.obj.MassFlowRate, 0, 1e9, 6, 0.01)
        self._add_row(inlet, "Mass Flow Rate [kg/s]:", self.sp_mfr)

        self.sp_vfr = self._spin_float(self.obj.VolFlowRate, 0, 1e9, 6, 0.001)
        self._add_row(inlet, "Vol. Flow Rate [m³/s]:", self.sp_vfr)

        turbulence = self._section(layout, "Turbulence")
        self.cb_turb = self._combo(
            ["Intensity & Length Scale", "Intensity & Viscosity Ratio",
             "k & Epsilon", "k & Omega"],
            self.obj.TurbulenceSpec,
        )
        self._add_row(turbulence, "Turbulence Spec:", self.cb_turb)
        self.sp_ti = self._spin_float(self.obj.TurbulenceIntensity, 0, 100, 2, 1)
        self._add_row(turbulence, "Turb. Intensity [%]:", self.sp_ti)

        thermal = self._section(layout, "Thermal")
        self.sp_T = self._spin_float(self.obj.InletTemperature, 0, 10000, 2, 1)
        self._add_row(thermal, "Temperature [K]:", self.sp_T)

        layout.addStretch()
        return widget

    def _current_settings(self):
        if not hasattr(self, "cb_type"):
            return self._presenter.read_settings(self.obj)
        return InletBoundarySettings(
            references=tuple(self._refs()),
            inlet_type=self.cb_type.currentText(),
            velocity_x=self.sp_ux.value(),
            velocity_y=self.sp_uy.value(),
            velocity_z=self.sp_uz.value(),
            normal_to_face=self.chk_normal.isChecked(),
            mass_flow_rate=self.sp_mfr.value(),
            volumetric_flow_rate=self.sp_vfr.value(),
            turbulence_spec=self.cb_turb.currentText(),
            turbulence_intensity=self.sp_ti.value(),
            inlet_temperature=self.sp_T.value(),
        )

    def _store(self):
        self._presenter.persist_settings(self.obj, self._current_settings())
