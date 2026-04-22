# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Task panel for PhysicsModel – FloEFD-like General Settings dialog."""

from PySide import QtGui
from flow_studio.taskpanels.base_taskpanel import BaseTaskPanel


class TaskPhysicsModel(BaseTaskPanel):

    SUMMARY_TITLE = "Physics Model"
    SUMMARY_DETAIL = (
        "Configure the governing flow model, turbulence, and coupling options for {label}."
    )

    def _build_task_validation(self):
        if self.chk_buoy.isChecked() and not self.chk_gravity.isChecked():
            return (
                "warning",
                "Buoyancy needs gravity",
                "Enable gravity when buoyancy is active so the body-force direction is defined.",
            )

        if self.chk_buoy.isChecked() and not self.chk_heat.isChecked():
            return (
                "warning",
                "Buoyancy usually needs heat transfer",
                "Enable heat transfer when buoyancy is active so density variation has a thermal driver.",
            )

        if self.cb_flow.currentText() == "Laminar" and self.cb_turb.currentText() != "kOmegaSST":
            return (
                "info",
                "Laminar flow selected",
                "The turbulence model is currently not driving the solve because the flow regime is laminar.",
            )

        return super()._build_task_validation()

    def _build_form(self):
        widget = QtGui.QWidget()
        layout = QtGui.QVBoxLayout(widget)

        layout.addWidget(QtGui.QLabel("<b>Physics Model Settings</b>"))
        layout.addWidget(self._separator())

        flow = self._section(layout, "Flow")
        self.cb_flow = self._combo(
            ["Laminar", "Turbulent"], self.obj.FlowRegime
        )
        self._add_row(flow, "Flow Regime:", self.cb_flow)

        self.cb_turb = self._combo(
            ["kEpsilon", "kOmega", "kOmegaSST", "SpalartAllmaras",
             "LES-Smagorinsky", "LES-WALE", "LBM-Implicit"],
            self.obj.TurbulenceModel,
        )
        self._add_row(flow, "Turbulence Model:", self.cb_turb)

        coupling = self._section(layout, "Compressibility & Time")
        self.cb_comp = self._combo(
            ["Incompressible", "Compressible", "Weakly-Compressible"],
            self.obj.Compressibility,
        )
        self._add_row(coupling, "Compressibility:", self.cb_comp)

        self.cb_time = self._combo(
            ["Steady", "Transient"], self.obj.TimeModel
        )
        self._add_row(coupling, "Time Model:", self.cb_time)

        layout.addWidget(self._separator())

        features = self._section(layout, "Physical Features")
        self.chk_gravity = self._checkbox(self.obj.Gravity)
        self._add_row(features, "Gravity:", self.chk_gravity)

        self.chk_heat = self._checkbox(self.obj.HeatTransfer)
        self._add_row(features, "Heat Transfer:", self.chk_heat)

        self.chk_buoy = self._checkbox(self.obj.Buoyancy)
        self._add_row(features, "Buoyancy:", self.chk_buoy)

        self.chk_vof = self._checkbox(self.obj.FreeSurface)
        self._add_row(features, "Free Surface (VoF):", self.chk_vof)

        self.chk_scalar = self._checkbox(self.obj.PassiveScalar)
        self._add_row(features, "Passive Scalar:", self.chk_scalar)

        layout.addStretch()
        return widget

    def _store(self):
        self.obj.FlowRegime = self.cb_flow.currentText()
        self.obj.TurbulenceModel = self.cb_turb.currentText()
        self.obj.Compressibility = self.cb_comp.currentText()
        self.obj.TimeModel = self.cb_time.currentText()
        self.obj.Gravity = self.chk_gravity.isChecked()
        self.obj.HeatTransfer = self.chk_heat.isChecked()
        self.obj.Buoyancy = self.chk_buoy.isChecked()
        self.obj.FreeSurface = self.chk_vof.isChecked()
        self.obj.PassiveScalar = self.chk_scalar.isChecked()

    @staticmethod
    def _separator():
        line = QtGui.QFrame()
        line.setFrameShape(QtGui.QFrame.HLine)
        line.setFrameShadow(QtGui.QFrame.Sunken)
        return line
