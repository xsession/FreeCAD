# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""FloEFD-style material assignment panels for non-fluid domains."""

from PySide import QtGui

from flow_studio.catalog.editor import show_engineering_database_editor
from flow_studio.taskpanels.task_flowefd_features import FloEFDTaskPanel
from flow_studio.ui.material_presenter import MaterialPresenter, MaterialSettings


class TaskMaterial(FloEFDTaskPanel):
    """One material editor that adapts to available object properties."""

    SUMMARY_DETAIL = (
        "Assign a preset and edit the domain-specific material properties applied to {label}."
    )

    def __init__(self, obj):
        self._presenter = MaterialPresenter()
        super().__init__(obj)

    def _build_task_summary(self):
        return self._presenter.title(getattr(self.obj, "FlowType", "")), self.SUMMARY_DETAIL.format(
            label=getattr(self.obj, "Label", getattr(self.obj, "Name", "Object"))
        )

    def _build_task_validation(self):
        level, title, detail = self._presenter.build_validation(self._current_settings())
        if level:
            return level, title, detail
        return super()._build_task_validation()

    def _build_form(self):
        widget = QtGui.QWidget()
        layout = QtGui.QVBoxLayout(widget)
        layout.addWidget(QtGui.QLabel(f"<b>{self._presenter.title(getattr(self.obj, 'FlowType', ''))}</b>"))
        self._add_selection_section(layout, "Assigned Parts / Regions")

        material = self._section(layout, "Material")
        presets = self._presenter.preset_names(getattr(self.obj, "FlowType", ""))
        self.cb_preset = self._combo(presets, getattr(self.obj, "MaterialPreset", "Custom"))
        self._add_row(material, "Preset:", self.cb_preset)
        self.cb_preset.currentTextChanged.connect(self._on_preset_changed)
        btn_db = QtGui.QPushButton("Engineering Database...")
        btn_db.clicked.connect(show_engineering_database_editor)
        material.addWidget(btn_db)
        self.le_name = QtGui.QLineEdit(getattr(self.obj, "MaterialName", "Material"))
        self._add_row(material, "Name:", self.le_name)

        props = self._section(layout, "Properties")
        self._widgets = {}
        self._add_float_if_present(props, "Density", "Density [kg/m^3]", 0.0, 1e9, 4, 1.0)
        self._add_float_if_present(props, "YoungsModulus", "Young's modulus [Pa]", 0.0, 1e15, 3, 1e9)
        self._add_float_if_present(props, "PoissonRatio", "Poisson ratio [-]", -1.0, 0.5, 4, 0.01)
        self._add_float_if_present(props, "ThermalExpansionCoeff", "Thermal expansion [1/K]", -1e-3, 1e-3, 8, 1e-6)
        self._add_float_if_present(props, "YieldStrength", "Yield strength [Pa]", 0.0, 1e15, 3, 1e6)
        self._add_float_if_present(props, "ThermalConductivity", "Thermal conductivity [W/(m K)]", 0.0, 1e6, 6, 0.1)
        self._add_float_if_present(props, "SpecificHeat", "Specific heat [J/(kg K)]", 0.0, 1e7, 3, 10.0)
        self._add_float_if_present(props, "Emissivity", "Emissivity [-]", 0.0, 1.0, 4, 0.01)
        self._add_float_if_present(props, "RelativePermittivity", "Relative permittivity [-]", 0.0, 1e9, 6, 0.1)
        self._add_float_if_present(props, "RelativePermeability", "Relative permeability [-]", 0.0, 1e9, 6, 0.1)
        self._add_float_if_present(props, "ElectricConductivity", "Electric conductivity [S/m]", 0.0, 1e12, 6, 100.0)
        self._add_float_if_present(props, "RefractiveIndex", "Refractive index n [-]", 0.0, 10.0, 6, 0.01)
        self._add_float_if_present(props, "AbbeNumber", "Abbe number Vd [-]", 0.0, 200.0, 4, 1.0)
        self._add_float_if_present(props, "ExtinctionCoefficient", "Extinction coefficient k [-]", 0.0, 100.0, 6, 0.01)
        self._add_float_if_present(props, "Transmission", "Transmission [-]", 0.0, 1.0, 4, 0.01)
        self._add_float_if_present(props, "Reflectivity", "Reflectivity [-]", 0.0, 1.0, 4, 0.01)
        self._add_float_if_present(props, "ReferenceWavelength", "Reference wavelength [nm]", 1.0, 1e6, 3, 1.0)
        self._add_float_if_present(props, "WavelengthMin", "Wavelength min [nm]", 1.0, 1e6, 3, 1.0)
        self._add_float_if_present(props, "WavelengthMax", "Wavelength max [nm]", 1.0, 1e6, 3, 1.0)
        self._add_float_if_present(props, "AbsorptionLength", "Absorption length [mm]", 0.0, 1e12, 3, 1.0)
        self._add_float_if_present(props, "SurfaceRoughness", "Surface roughness [um]", 0.0, 1e6, 4, 0.01)
        self._add_float_if_present(props, "SellmeierB1", "Sellmeier B1 [-]", -1e6, 1e6, 8, 0.001)
        self._add_float_if_present(props, "SellmeierB2", "Sellmeier B2 [-]", -1e6, 1e6, 8, 0.001)
        self._add_float_if_present(props, "SellmeierB3", "Sellmeier B3 [-]", -1e6, 1e6, 8, 0.001)
        self._add_float_if_present(props, "SellmeierC1", "Sellmeier C1 [um^2]", -1e6, 1e6, 8, 0.001)
        self._add_float_if_present(props, "SellmeierC2", "Sellmeier C2 [um^2]", -1e6, 1e6, 8, 0.001)
        self._add_float_if_present(props, "SellmeierC3", "Sellmeier C3 [um^2]", -1e6, 1e6, 8, 0.001)

        layout.addStretch()
        return widget

    def _add_float_if_present(self, layout, prop, label, minimum, maximum, decimals, step):
        if prop not in getattr(self.obj, "PropertiesList", []):
            return
        widget = self._spin_float(getattr(self.obj, prop), minimum, maximum, decimals, step)
        self._add_row(layout, label + ":", widget)
        self._widgets[prop] = widget

    def _current_settings(self):
        if not hasattr(self, "_widgets"):
            return self._presenter.read_settings(self.obj)
        return MaterialSettings(
            flow_type=str(getattr(self.obj, "FlowType", "") or ""),
            properties=tuple(getattr(self.obj, "PropertiesList", []) or []),
            references=tuple(self._refs()),
            material_preset=self.cb_preset.currentText() if hasattr(self, "cb_preset") else str(getattr(self.obj, "MaterialPreset", "Custom") or "Custom"),
            material_name=self.le_name.text() if hasattr(self, "le_name") else str(getattr(self.obj, "MaterialName", "") or ""),
            values={prop: widget.value() for prop, widget in getattr(self, "_widgets", {}).items()},
        )

    def _on_preset_changed(self, text):
        settings = self._presenter.apply_preset(self._current_settings(), text)
        self.le_name.setText(settings.material_name)
        for prop, widget in self._widgets.items():
            if prop in settings.values:
                widget.setValue(float(settings.values[prop]))

    def _store(self):
        self._presenter.persist_settings(self.obj, self._current_settings())
