# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Task panel for PhysicsModel – FloEFD-like General Settings dialog."""

from PySide import QtGui
from flow_studio.taskpanels.base_taskpanel import BaseTaskPanel
from flow_studio.ui.physics_model_presenter import PhysicsModelPresenter, PhysicsModelSettings


class TaskPhysicsModel(BaseTaskPanel):

    SUMMARY_TITLE = "Physics Model"
    SUMMARY_DETAIL = (
        "Configure the governing flow model, turbulence, and coupling options for {label}."
    )

    def __init__(self, obj):
        self._presenter = PhysicsModelPresenter()
        super().__init__(obj)

    def _build_task_validation(self):
        level, title, detail = self._presenter.build_validation(self._current_settings())
        if level:
            return level, title, detail
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

    def _current_settings(self):
        if not hasattr(self, "cb_flow"):
            return self._presenter.read_settings(self.obj)
        return PhysicsModelSettings(
            flow_regime=self.cb_flow.currentText(),
            turbulence_model=self.cb_turb.currentText(),
            compressibility=self.cb_comp.currentText(),
            time_model=self.cb_time.currentText(),
            gravity=self.chk_gravity.isChecked(),
            heat_transfer=self.chk_heat.isChecked(),
            buoyancy=self.chk_buoy.isChecked(),
            free_surface=self.chk_vof.isChecked(),
            passive_scalar=self.chk_scalar.isChecked(),
        )

    def _store(self):
        self._presenter.persist_settings(self.obj, self._current_settings())

    @staticmethod
    def _separator():
        line = QtGui.QFrame()
        line.setFrameShape(QtGui.QFrame.HLine)
        line.setFrameShadow(QtGui.QFrame.Sunken)
        return line
