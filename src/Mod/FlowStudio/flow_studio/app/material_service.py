# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Application service for FlowStudio material task panels."""

from __future__ import annotations

from copy import deepcopy

from flow_studio.catalog.database import material_presets
from flow_studio.catalog.optics import OPTICAL_MATERIAL_PRESETS


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


class FlowStudioMaterialService:
    """Backend-facing service for material settings and preset data."""

    def read_state(self, obj):
        properties = tuple(getattr(obj, "PropertiesList", []) or [])
        state = {
            "FlowType": str(getattr(obj, "FlowType", "") or ""),
            "PropertiesList": properties,
            "References": tuple(getattr(obj, "References", []) or []),
        }
        for name in properties:
            state[name] = getattr(obj, name)
        return state

    def persist_state(self, obj, state):
        properties = set(getattr(obj, "PropertiesList", []) or [])
        if "MaterialPreset" in properties:
            try:
                obj.MaterialPreset = state["MaterialPreset"]
            except Exception:
                obj.MaterialPreset = "Custom"
        if "MaterialName" in properties:
            obj.MaterialName = state["MaterialName"]
        for name, value in state["Values"].items():
            if name in properties:
                setattr(obj, name, value)

    def preset_db(self, flow_type):
        if flow_type == "FlowStudio::SolidMaterial":
            presets = material_presets("Solids")
            presets.update(SOLID_PRESETS)
            return deepcopy(presets)
        if flow_type == "FlowStudio::ThermalMaterial":
            presets = material_presets("Solids", "Liquids", "Gases")
            presets.update(THERMAL_PRESETS)
            return deepcopy(presets)
        if flow_type == "FlowStudio::ElectrostaticMaterial":
            presets = material_presets("Dielectrics", "Solids", "Liquids", "Gases")
            presets.update(ELECTROSTATIC_PRESETS)
            return deepcopy(presets)
        if flow_type == "FlowStudio::ElectromagneticMaterial":
            presets = material_presets("Magnetic", "Dielectrics", "Solids")
            presets.update(ELECTROMAGNETIC_PRESETS)
            return deepcopy(presets)
        if flow_type == "FlowStudio::OpticalMaterial":
            presets = material_presets("Optical Glasses", "Optical Coatings", "Dielectrics")
            presets.update(OPTICAL_MATERIAL_PRESETS)
            return deepcopy(presets)
        return {}