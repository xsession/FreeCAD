# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Task panel for Outlet boundary condition."""

from PySide import QtGui
from flow_studio.taskpanels.task_flowefd_features import FloEFDTaskPanel
from flow_studio.ui.bc_outlet_presenter import OutletBoundaryPresenter, OutletBoundarySettings


class TaskBCOutlet(FloEFDTaskPanel):

    SUMMARY_TITLE = "Outlet Boundary Condition"
    SUMMARY_DETAIL = (
        "Define how flow exits {label}, including pressure and backflow behavior."
    )

    def __init__(self, obj):
        self._presenter = OutletBoundaryPresenter()
        super().__init__(obj)

    def _build_task_validation(self):
        level, title, detail = self._presenter.build_validation(self._current_settings())
        if level:
            return level, title, detail
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

    def _current_settings(self):
        if not hasattr(self, "cb_type"):
            return self._presenter.read_settings(self.obj)
        return OutletBoundarySettings(
            references=tuple(self._refs()),
            outlet_type=self.cb_type.currentText(),
            static_pressure=self.sp_p.value(),
            mass_flow_rate=self.sp_mfr.value(),
            prevent_backflow=self.chk_backflow.isChecked(),
        )

    def _store(self):
        self._presenter.persist_settings(self.obj, self._current_settings())
