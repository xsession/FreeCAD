# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Task panel for FluidMaterial – FloEFD-like fluid property editor."""

from flow_studio.app.fluid_material_service import MATERIALS_DB
from flow_studio.ui.fluid_material_presenter import FluidMaterialPresenter, FluidMaterialSettings

try:
    from PySide import QtGui  # noqa: E402
    from flow_studio.taskpanels.task_flowefd_features import FloEFDTaskPanel  # noqa: E402
    _HAS_GUI = True
except ImportError:
    _HAS_GUI = False


class TaskFluidMaterial(FloEFDTaskPanel if _HAS_GUI else object):

    SUMMARY_TITLE = "Fluid Material"
    SUMMARY_DETAIL = (
        "Assign a fluid preset or custom transport properties for {label}."
    )

    def __init__(self, obj):
        self._presenter = FluidMaterialPresenter()
        super().__init__(obj)

    def _build_task_validation(self):
        level, title, detail = self._presenter.build_validation(self._current_settings())
        if level:
            return level, title, detail
        return super()._build_task_validation()

    def _build_form(self):
        widget = QtGui.QWidget()
        layout = QtGui.QVBoxLayout(widget)

        layout.addWidget(QtGui.QLabel("<b>Fluid Material Properties</b>"))
        self._add_selection_section(layout, "Assigned Fluid Region")

        material = self._section(layout, "Material")

        presets = self._presenter.preset_names()
        self.cb_preset = self._combo(presets, self.obj.Preset)
        self._add_row(material, "Preset:", self.cb_preset)
        self.cb_preset.currentTextChanged.connect(self._on_preset_changed)

        btn_db = QtGui.QPushButton("Engineering Database...")
        btn_db.clicked.connect(self._open_database)
        material.addWidget(btn_db)

        properties = self._section(layout, "Properties")
        self.sp_rho = self._spin_float(self.obj.Density, 0.001, 20000, 4, 0.1)
        self._add_row(properties, "Density [kg/m³]:", self.sp_rho)

        self.sp_mu = self._spin_float(self.obj.DynamicViscosity, 1e-9, 100, 8, 1e-6)
        self._add_row(properties, "Dynamic Viscosity [Pa·s]:", self.sp_mu)

        self.sp_nu = self._spin_float(self.obj.KinematicViscosity, 1e-9, 1, 8, 1e-7)
        self._add_row(properties, "Kinematic Viscosity [m²/s]:", self.sp_nu)

        self.sp_cp = self._spin_float(self.obj.SpecificHeat, 1, 50000, 1, 10)
        self._add_row(properties, "Specific Heat [J/(kg·K)]:", self.sp_cp)

        self.sp_k = self._spin_float(self.obj.ThermalConductivity, 0, 500, 4, 0.01)
        self._add_row(properties, "Thermal Conductivity [W/(m·K)]:", self.sp_k)

        self.sp_pr = self._spin_float(self.obj.PrandtlNumber, 0.001, 100000, 3, 0.01)
        self._add_row(properties, "Prandtl Number:", self.sp_pr)

        layout.addStretch()
        return widget

    def _current_settings(self):
        if not _HAS_GUI or not hasattr(self, "cb_preset"):
            return self._presenter.read_settings(self.obj)
        return FluidMaterialSettings(
            references=tuple(self._refs()),
            preset=self.cb_preset.currentText(),
            density=self.sp_rho.value(),
            dynamic_viscosity=self.sp_mu.value(),
            kinematic_viscosity=self.sp_nu.value(),
            specific_heat=self.sp_cp.value(),
            thermal_conductivity=self.sp_k.value(),
            prandtl_number=self.sp_pr.value(),
        )

    def _on_preset_changed(self, text):
        settings = self._presenter.apply_preset(self._current_settings(), text)
        self.sp_rho.setValue(settings.density)
        self.sp_mu.setValue(settings.dynamic_viscosity)
        self.sp_nu.setValue(settings.kinematic_viscosity)
        self.sp_cp.setValue(settings.specific_heat)
        self.sp_k.setValue(settings.thermal_conductivity)
        self.sp_pr.setValue(settings.prandtl_number)

    def _open_database(self):
        from flow_studio.catalog.editor import show_engineering_database_editor
        show_engineering_database_editor()

    def _store(self):
        self._presenter.persist_settings(self.obj, self._current_settings())
