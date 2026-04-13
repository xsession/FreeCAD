# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Task panel for PhysicsModel – FloEFD-like General Settings dialog."""

from PySide import QtGui
from flow_studio.taskpanels.base_taskpanel import BaseTaskPanel


class TaskPhysicsModel(BaseTaskPanel):

    def _build_form(self):
        widget = QtGui.QWidget()
        layout = QtGui.QVBoxLayout(widget)

        layout.addWidget(QtGui.QLabel("<b>Physics Model Settings</b>"))
        layout.addWidget(self._separator())

        # Flow type
        self.cb_flow = self._combo(
            ["Laminar", "Turbulent"], self.obj.FlowRegime
        )
        self._add_row(layout, "Flow Regime:", self.cb_flow)

        # Turbulence model
        self.cb_turb = self._combo(
            ["kEpsilon", "kOmega", "kOmegaSST", "SpalartAllmaras",
             "LES-Smagorinsky", "LES-WALE", "LBM-Implicit"],
            self.obj.TurbulenceModel,
        )
        self._add_row(layout, "Turbulence Model:", self.cb_turb)

        # Compressibility
        self.cb_comp = self._combo(
            ["Incompressible", "Compressible", "Weakly-Compressible"],
            self.obj.Compressibility,
        )
        self._add_row(layout, "Compressibility:", self.cb_comp)

        # Time
        self.cb_time = self._combo(
            ["Steady", "Transient"], self.obj.TimeModel
        )
        self._add_row(layout, "Time Model:", self.cb_time)

        layout.addWidget(self._separator())

        # Toggle features
        self.chk_gravity = self._checkbox(self.obj.Gravity)
        self._add_row(layout, "Gravity:", self.chk_gravity)

        self.chk_heat = self._checkbox(self.obj.HeatTransfer)
        self._add_row(layout, "Heat Transfer:", self.chk_heat)

        self.chk_buoy = self._checkbox(self.obj.Buoyancy)
        self._add_row(layout, "Buoyancy:", self.chk_buoy)

        self.chk_vof = self._checkbox(self.obj.FreeSurface)
        self._add_row(layout, "Free Surface (VoF):", self.chk_vof)

        self.chk_scalar = self._checkbox(self.obj.PassiveScalar)
        self._add_row(layout, "Passive Scalar:", self.chk_scalar)

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
