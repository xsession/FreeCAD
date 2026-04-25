# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Application service for FlowStudio fluid material task panels."""

from __future__ import annotations

from copy import deepcopy


MATERIALS_DB = {
    "Air (20°C, 1atm)": {
        "Density": 1.225,
        "DynamicViscosity": 1.81e-5,
        "KinematicViscosity": 1.48e-5,
        "SpecificHeat": 1005.0,
        "ThermalConductivity": 0.0257,
        "PrandtlNumber": 0.707,
    },
    "Water (20°C)": {
        "Density": 998.2,
        "DynamicViscosity": 1.002e-3,
        "KinematicViscosity": 1.004e-6,
        "SpecificHeat": 4182.0,
        "ThermalConductivity": 0.6,
        "PrandtlNumber": 7.01,
    },
    "Oil (SAE 30)": {
        "Density": 891.0,
        "DynamicViscosity": 0.29,
        "KinematicViscosity": 3.25e-4,
        "SpecificHeat": 1900.0,
        "ThermalConductivity": 0.145,
        "PrandtlNumber": 3800.0,
    },
    "Glycerin": {
        "Density": 1261.0,
        "DynamicViscosity": 1.412,
        "KinematicViscosity": 1.12e-3,
        "SpecificHeat": 2427.0,
        "ThermalConductivity": 0.286,
        "PrandtlNumber": 11970.0,
    },
    "Mercury": {
        "Density": 13534.0,
        "DynamicViscosity": 1.526e-3,
        "KinematicViscosity": 1.128e-7,
        "SpecificHeat": 139.3,
        "ThermalConductivity": 8.514,
        "PrandtlNumber": 0.025,
    },
}

try:
    from flow_studio.catalog.database import material_presets as _material_presets

    MATERIALS_DB.update(
        {
            name: props
            for name, props in _material_presets("Gases", "Liquids").items()
            if all(
                key in props
                for key in (
                    "Density",
                    "DynamicViscosity",
                    "KinematicViscosity",
                    "SpecificHeat",
                    "ThermalConductivity",
                    "PrandtlNumber",
                )
            )
        }
    )
except Exception:
    pass


class FlowStudioFluidMaterialService:
    """Backend-facing service for fluid material settings and presets."""

    FIELD_NAMES = (
        "Preset",
        "Density",
        "DynamicViscosity",
        "KinematicViscosity",
        "SpecificHeat",
        "ThermalConductivity",
        "PrandtlNumber",
    )

    def read_settings(self, obj):
        return {
            "References": tuple(getattr(obj, "References", []) or []),
            **{name: getattr(obj, name) for name in self.FIELD_NAMES},
        }

    def persist_settings(self, obj, settings):
        for name in self.FIELD_NAMES:
            setattr(obj, name, settings[name])

    def material_db(self):
        return deepcopy(MATERIALS_DB)