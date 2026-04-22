# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Task panel for Outlet boundary condition."""

from PySide import QtGui
from flow_studio.taskpanels.task_flowefd_features import FloEFDTaskPanel


class TaskBCOutlet(FloEFDTaskPanel):

    SUMMARY_TITLE = "Outlet Boundary Condition"
    SUMMARY_DETAIL = (
        "Define how flow exits {label}, including pressure and backflow behavior."
    )

    def _build_task_validation(self):
        if not self._refs():
            return (
                "incomplete",
                "Assign outlet faces",
                "Select one or more outlet faces so the exit condition is attached to geometry.",
            )

        if (
            str(getattr(self.obj, "OutletType", "Static Pressure")) == "Mass Flow Rate"
            and float(getattr(self.obj, "OutletMassFlowRate", 0.0)) <= 0.0
        ):
            return (
                "incomplete",
                "Outlet mass flow rate required",
                "Enter a positive outlet mass flow rate before solving with this outlet mode.",
            )

        return super()._build_task_validation()

    def _build_form(self):
        widget = QtGui.QWidget()
        layout = QtGui.QVBoxLayout(widget)
        layout.addWidget(QtGui.QLabel("<b>Outlet Boundary Condition</b>"))
        self._add_selection_section(layout)

        outlet = self._section(layout, "Outlet")
        self.cb_type = self._combo(
            ["Static Pressure", "Mass Flow Rate", "Outflow (Zero Gradient)"],
            self.obj.OutletType,
        )
        self._add_row(outlet, "Outlet Type:", self.cb_type)

        self.sp_p = self._spin_float(self.obj.StaticPressure, -1e9, 1e9, 2, 100)
        self._add_row(outlet, "Pressure [Pa]:", self.sp_p)

        self.sp_mfr = self._spin_float(self.obj.OutletMassFlowRate, 0, 1e9, 6, 0.01)
        self._add_row(outlet, "Mass Flow Rate [kg/s]:", self.sp_mfr)

        self.chk_backflow = self._checkbox(self.obj.PreventBackflow)
        self._add_row(outlet, "Prevent Backflow:", self.chk_backflow)

        layout.addStretch()
        return widget

    def _store(self):
        self.obj.OutletType = self.cb_type.currentText()
        self.obj.StaticPressure = self.sp_p.value()
        self.obj.OutletMassFlowRate = self.sp_mfr.value()
        self.obj.PreventBackflow = self.chk_backflow.isChecked()
