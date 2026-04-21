# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""FloEFD-style material assignment panels for non-fluid domains."""

from PySide import QtGui

from flow_studio.engineering_database import material_presets
from flow_studio.engineering_database_editor import show_engineering_database_editor
from flow_studio.taskpanels.task_flowefd_features import FloEFDTaskPanel


SOLID_PRESETS = {
    "Steel (Structural)": {
        "MaterialName": "Steel",
        "Density": 7850.0,
        "YoungsModulus": 2.1e11,
        "PoissonRatio": 0.30,
        "ThermalExpansionCoeff": 1.2e-5,
        "YieldStrength": 2.5e8,
    },
    "Aluminum 6061-T6": {
        "MaterialName": "Aluminum 6061-T6",
        "Density": 2700.0,
        "YoungsModulus": 6.9e10,
        "PoissonRatio": 0.33,
        "ThermalExpansionCoeff": 2.36e-5,
        "YieldStrength": 2.75e8,
    },
    "Copper": {
        "MaterialName": "Copper",
        "Density": 8960.0,
        "YoungsModulus": 1.1e11,
        "PoissonRatio": 0.34,
        "ThermalExpansionCoeff": 1.65e-5,
        "YieldStrength": 7.0e7,
    },
}

THERMAL_PRESETS = {
    "Steel": {"MaterialName": "Steel", "Density": 7850.0, "ThermalConductivity": 50.0, "SpecificHeat": 500.0, "Emissivity": 0.3},
    "Aluminum": {"MaterialName": "Aluminum", "Density": 2700.0, "ThermalConductivity": 205.0, "SpecificHeat": 900.0, "Emissivity": 0.09},
    "Copper": {"MaterialName": "Copper", "Density": 8960.0, "ThermalConductivity": 385.0, "SpecificHeat": 385.0, "Emissivity": 0.03},
    "Insulation (Mineral Wool)": {"MaterialName": "Mineral Wool", "Density": 80.0, "ThermalConductivity": 0.04, "SpecificHeat": 840.0, "Emissivity": 0.9},
}

ELECTROSTATIC_PRESETS = {
    "Vacuum": {"MaterialName": "Vacuum", "RelativePermittivity": 1.0, "ElectricConductivity": 0.0},
    "Air": {"MaterialName": "Air", "RelativePermittivity": 1.0006, "ElectricConductivity": 0.0},
    "PTFE (Teflon)": {"MaterialName": "PTFE", "RelativePermittivity": 2.1, "ElectricConductivity": 1e-18},
    "FR-4 (PCB)": {"MaterialName": "FR-4", "RelativePermittivity": 4.4, "ElectricConductivity": 1e-14},
    "Water": {"MaterialName": "Water", "RelativePermittivity": 80.0, "ElectricConductivity": 5e-6},
}

ELECTROMAGNETIC_PRESETS = {
    "Air / Vacuum": {"MaterialName": "Air", "RelativePermeability": 1.0, "RelativePermittivity": 1.0, "ElectricConductivity": 0.0, "Density": 1.225},
    "Copper": {"MaterialName": "Copper", "RelativePermeability": 0.999994, "RelativePermittivity": 1.0, "ElectricConductivity": 5.96e7, "Density": 8960.0},
    "Aluminum": {"MaterialName": "Aluminum", "RelativePermeability": 1.000022, "RelativePermittivity": 1.0, "ElectricConductivity": 3.5e7, "Density": 2700.0},
    "Iron (soft)": {"MaterialName": "Soft Iron", "RelativePermeability": 5000.0, "RelativePermittivity": 1.0, "ElectricConductivity": 1.0e7, "Density": 7870.0},
}

OPTICAL_PRESETS = {
    "Vacuum": {"MaterialName": "Vacuum", "RefractiveIndex": 1.0, "AbbeNumber": 0.0, "ExtinctionCoefficient": 0.0, "Transmission": 1.0, "Reflectivity": 0.0, "ReferenceWavelength": 587.6},
    "Air": {"MaterialName": "Air", "RefractiveIndex": 1.000293, "AbbeNumber": 0.0, "ExtinctionCoefficient": 0.0, "Transmission": 1.0, "Reflectivity": 0.0, "ReferenceWavelength": 587.6},
    "BK7": {"MaterialName": "BK7", "RefractiveIndex": 1.5168, "AbbeNumber": 64.17, "ExtinctionCoefficient": 0.0, "Transmission": 0.92, "Reflectivity": 0.04, "ReferenceWavelength": 587.6},
    "Fused Silica": {"MaterialName": "Fused Silica", "RefractiveIndex": 1.4585, "AbbeNumber": 67.82, "ExtinctionCoefficient": 0.0, "Transmission": 0.94, "Reflectivity": 0.035, "ReferenceWavelength": 587.6},
    "Sapphire": {"MaterialName": "Sapphire", "RefractiveIndex": 1.7682, "AbbeNumber": 72.2, "ExtinctionCoefficient": 0.0, "Transmission": 0.86, "Reflectivity": 0.076, "ReferenceWavelength": 587.6},
    "Mirror Aluminum": {"MaterialName": "Aluminum Mirror", "RefractiveIndex": 0.65, "AbbeNumber": 0.0, "ExtinctionCoefficient": 5.3, "Transmission": 0.0, "Reflectivity": 0.88, "ReferenceWavelength": 550.0},
}


class TaskMaterial(FloEFDTaskPanel):
    """One material editor that adapts to available object properties."""

    def _build_form(self):
        widget = QtGui.QWidget()
        layout = QtGui.QVBoxLayout(widget)
        layout.addWidget(QtGui.QLabel(f"<b>{self._title()}</b>"))
        self._add_selection_section(layout, "Assigned Parts / Regions")

        material = self._section(layout, "Material")
        presets = self._preset_names()
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

        layout.addStretch()
        return widget

    def _title(self):
        flow_type = getattr(self.obj, "FlowType", "")
        return {
            "FlowStudio::SolidMaterial": "Solid Material",
            "FlowStudio::ThermalMaterial": "Thermal Material",
            "FlowStudio::ElectrostaticMaterial": "Electrostatic Material",
            "FlowStudio::ElectromagneticMaterial": "Electromagnetic Material",
            "FlowStudio::OpticalMaterial": "Optical Material",
        }.get(flow_type, "Material")

    def _preset_db(self):
        flow_type = getattr(self.obj, "FlowType", "")
        if flow_type == "FlowStudio::SolidMaterial":
            presets = material_presets("Solids")
            presets.update(SOLID_PRESETS)
            return presets
        if flow_type == "FlowStudio::ThermalMaterial":
            presets = material_presets("Solids", "Liquids", "Gases")
            presets.update(THERMAL_PRESETS)
            return presets
        if flow_type == "FlowStudio::ElectrostaticMaterial":
            presets = material_presets("Dielectrics", "Solids", "Liquids", "Gases")
            presets.update(ELECTROSTATIC_PRESETS)
            return presets
        if flow_type == "FlowStudio::ElectromagneticMaterial":
            presets = material_presets("Magnetic", "Dielectrics", "Solids")
            presets.update(ELECTROMAGNETIC_PRESETS)
            return presets
        if flow_type == "FlowStudio::OpticalMaterial":
            presets = material_presets("Optical Glasses", "Optical Coatings", "Dielectrics")
            presets.update(OPTICAL_PRESETS)
            return presets
        return {}

    def _preset_names(self):
        return ["Custom"] + sorted(self._preset_db())

    def _add_float_if_present(self, layout, prop, label, minimum, maximum, decimals, step):
        if prop not in getattr(self.obj, "PropertiesList", []):
            return
        widget = self._spin_float(getattr(self.obj, prop), minimum, maximum, decimals, step)
        self._add_row(layout, label + ":", widget)
        self._widgets[prop] = widget

    def _on_preset_changed(self, text):
        data = self._preset_db().get(text)
        if not data:
            return
        if "MaterialName" in data:
            self.le_name.setText(str(data["MaterialName"]))
        for prop, widget in self._widgets.items():
            if prop in data:
                widget.setValue(float(data[prop]))

    def _store(self):
        if "MaterialPreset" in getattr(self.obj, "PropertiesList", []):
            try:
                self.obj.MaterialPreset = self.cb_preset.currentText()
            except Exception:
                self.obj.MaterialPreset = "Custom"
        if "MaterialName" in getattr(self.obj, "PropertiesList", []):
            self.obj.MaterialName = self.le_name.text()
        for prop, widget in self._widgets.items():
            setattr(self.obj, prop, widget.value())
