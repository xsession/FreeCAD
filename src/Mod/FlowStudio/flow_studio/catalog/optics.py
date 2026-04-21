# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Curated optical presets shared by FlowStudio materials and optics workflows."""

from copy import deepcopy

from flow_studio.catalog.database import material_presets


_CURATED_OPTICAL_PRESETS = {
    "Vacuum": {
        "MaterialName": "Vacuum",
        "OpticalRole": "Vacuum",
        "DispersionModel": "Constant Index",
        "RefractiveIndex": 1.0,
        "AbbeNumber": 0.0,
        "ExtinctionCoefficient": 0.0,
        "Transmission": 1.0,
        "Reflectivity": 0.0,
        "ReferenceWavelength": 587.6,
        "WavelengthMin": 1.0,
        "WavelengthMax": 100000.0,
        "AbsorptionLength": 1.0e12,
        "SurfaceRoughness": 0.0,
        "SellmeierB1": 0.0,
        "SellmeierB2": 0.0,
        "SellmeierB3": 0.0,
        "SellmeierC1": 0.0,
        "SellmeierC2": 0.0,
        "SellmeierC3": 0.0,
    },
    "Air": {
        "MaterialName": "Air",
        "OpticalRole": "Gas",
        "DispersionModel": "Constant Index",
        "RefractiveIndex": 1.000293,
        "AbbeNumber": 0.0,
        "ExtinctionCoefficient": 0.0,
        "Transmission": 1.0,
        "Reflectivity": 0.0,
        "ReferenceWavelength": 587.6,
        "WavelengthMin": 200.0,
        "WavelengthMax": 2000.0,
        "AbsorptionLength": 1.0e9,
        "SurfaceRoughness": 0.0,
        "SellmeierB1": 0.05792105,
        "SellmeierB2": 0.00167917,
        "SellmeierB3": 0.0,
        "SellmeierC1": 238.0185,
        "SellmeierC2": 57.362,
        "SellmeierC3": 0.0,
    },
    "BK7": {
        "MaterialName": "BK7",
        "OpticalRole": "Glass",
        "DispersionModel": "Sellmeier",
        "RefractiveIndex": 1.5168,
        "AbbeNumber": 64.17,
        "ExtinctionCoefficient": 0.0,
        "Transmission": 0.92,
        "Reflectivity": 0.04,
        "ReferenceWavelength": 587.6,
        "WavelengthMin": 350.0,
        "WavelengthMax": 2000.0,
        "AbsorptionLength": 25000.0,
        "SurfaceRoughness": 0.01,
        "SellmeierB1": 1.03961212,
        "SellmeierB2": 0.231792344,
        "SellmeierB3": 1.01046945,
        "SellmeierC1": 0.00600069867,
        "SellmeierC2": 0.0200179144,
        "SellmeierC3": 103.560653,
    },
    "Fused Silica": {
        "MaterialName": "Fused Silica",
        "OpticalRole": "Glass",
        "DispersionModel": "Sellmeier",
        "RefractiveIndex": 1.4585,
        "AbbeNumber": 67.82,
        "ExtinctionCoefficient": 0.0,
        "Transmission": 0.94,
        "Reflectivity": 0.035,
        "ReferenceWavelength": 587.6,
        "WavelengthMin": 180.0,
        "WavelengthMax": 3500.0,
        "AbsorptionLength": 50000.0,
        "SurfaceRoughness": 0.005,
        "SellmeierB1": 0.6961663,
        "SellmeierB2": 0.4079426,
        "SellmeierB3": 0.8974794,
        "SellmeierC1": 0.00467914826,
        "SellmeierC2": 0.0135120631,
        "SellmeierC3": 97.9340025,
    },
    "Sapphire": {
        "MaterialName": "Sapphire",
        "OpticalRole": "Crystal",
        "DispersionModel": "Sellmeier",
        "RefractiveIndex": 1.7682,
        "AbbeNumber": 72.2,
        "ExtinctionCoefficient": 0.0,
        "Transmission": 0.86,
        "Reflectivity": 0.076,
        "ReferenceWavelength": 587.6,
        "WavelengthMin": 150.0,
        "WavelengthMax": 5500.0,
        "AbsorptionLength": 15000.0,
        "SurfaceRoughness": 0.005,
        "SellmeierB1": 1.4313493,
        "SellmeierB2": 0.65054713,
        "SellmeierB3": 5.3414021,
        "SellmeierC1": 0.0052799261,
        "SellmeierC2": 0.0142382647,
        "SellmeierC3": 325.017834,
    },
    "Polycarbonate": {
        "MaterialName": "Polycarbonate",
        "OpticalRole": "Polymer",
        "DispersionModel": "Abbe Approximation",
        "RefractiveIndex": 1.586,
        "AbbeNumber": 30.0,
        "ExtinctionCoefficient": 0.0,
        "Transmission": 0.88,
        "Reflectivity": 0.05,
        "ReferenceWavelength": 587.6,
        "WavelengthMin": 380.0,
        "WavelengthMax": 1100.0,
        "AbsorptionLength": 2000.0,
        "SurfaceRoughness": 0.05,
        "SellmeierB1": 0.0,
        "SellmeierB2": 0.0,
        "SellmeierB3": 0.0,
        "SellmeierC1": 0.0,
        "SellmeierC2": 0.0,
        "SellmeierC3": 0.0,
    },
    "Mirror Aluminum": {
        "MaterialName": "Aluminum Mirror",
        "OpticalRole": "Mirror",
        "DispersionModel": "Metal / Complex Index",
        "RefractiveIndex": 0.65,
        "AbbeNumber": 0.0,
        "ExtinctionCoefficient": 5.3,
        "Transmission": 0.0,
        "Reflectivity": 0.88,
        "ReferenceWavelength": 550.0,
        "WavelengthMin": 200.0,
        "WavelengthMax": 20000.0,
        "AbsorptionLength": 0.1,
        "SurfaceRoughness": 0.02,
        "SellmeierB1": 0.0,
        "SellmeierB2": 0.0,
        "SellmeierB3": 0.0,
        "SellmeierC1": 0.0,
        "SellmeierC2": 0.0,
        "SellmeierC3": 0.0,
    },
    "Ideal AR Coating": {
        "MaterialName": "Ideal AR Coating",
        "OpticalRole": "Coating",
        "DispersionModel": "Constant Index",
        "RefractiveIndex": 1.38,
        "AbbeNumber": 0.0,
        "ExtinctionCoefficient": 0.0,
        "Transmission": 0.995,
        "Reflectivity": 0.005,
        "ReferenceWavelength": 550.0,
        "WavelengthMin": 350.0,
        "WavelengthMax": 1100.0,
        "AbsorptionLength": 5000.0,
        "SurfaceRoughness": 0.005,
        "SellmeierB1": 0.0,
        "SellmeierB2": 0.0,
        "SellmeierB3": 0.0,
        "SellmeierC1": 0.0,
        "SellmeierC2": 0.0,
        "SellmeierC3": 0.0,
    },
}


def optical_material_presets():
    """Return merged optical presets from the engineering DB and curated optics data."""
    presets = material_presets("Optical Glasses", "Optical Coatings", "Dielectrics")
    merged = deepcopy(presets)
    for name, data in _CURATED_OPTICAL_PRESETS.items():
        merged.setdefault(name, {})
        merged[name].update(deepcopy(data))
    return merged


OPTICAL_MATERIAL_PRESETS = optical_material_presets()
DEFAULT_OPTICAL_PRESET = "BK7"


def get_optical_material_preset(name):
    """Return one optical preset by name."""
    return deepcopy(OPTICAL_MATERIAL_PRESETS.get(name, {}))


def get_optical_material_preset_names():
    """Return preset names including the synthetic Custom entry."""
    return ["Custom"] + sorted(OPTICAL_MATERIAL_PRESETS)