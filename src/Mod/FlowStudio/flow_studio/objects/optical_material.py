# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""OpticalMaterial - refractive, absorptive, and reflective material data."""

from flow_studio.catalog.optics import (
    DEFAULT_OPTICAL_PRESET,
    get_optical_material_preset,
    get_optical_material_preset_names,
)
from flow_studio.objects.base_object import BaseFlowObject


class OpticalMaterial(BaseFlowObject):
    """Material properties for ray-optics and photonics simulations."""

    Type = "FlowStudio::OpticalMaterial"

    def __init__(self, obj):
        super().__init__(obj)

        self.add_reference_property(
            obj,
            "Material Assignment",
            "Referenced optical parts, bodies, faces, lenses, or regions",
        )

        obj.addProperty("App::PropertyString", "MaterialName", "Material", "Material name")
        obj.MaterialName = DEFAULT_OPTICAL_PRESET

        obj.addProperty("App::PropertyEnumeration", "MaterialPreset", "Material", "Optical material preset")
        obj.MaterialPreset = get_optical_material_preset_names()
        obj.MaterialPreset = DEFAULT_OPTICAL_PRESET

        obj.addProperty("App::PropertyEnumeration", "OpticalRole", "Material", "Optical role in the study")
        obj.OpticalRole = [
            "Glass",
            "Crystal",
            "Polymer",
            "Mirror",
            "Coating",
            "Absorber",
            "Gas",
            "Vacuum",
        ]
        obj.OpticalRole = "Glass"

        obj.addProperty("App::PropertyEnumeration", "DispersionModel", "Optical", "Dispersion model used by optical solvers")
        obj.DispersionModel = [
            "Constant Index",
            "Abbe Approximation",
            "Sellmeier",
            "Metal / Complex Index",
        ]
        obj.DispersionModel = "Sellmeier"

        obj.addProperty("App::PropertyFloat", "RefractiveIndex", "Optical", "Refractive index n at reference wavelength")
        obj.RefractiveIndex = 1.5168

        obj.addProperty("App::PropertyFloat", "AbbeNumber", "Optical", "Abbe number Vd")
        obj.AbbeNumber = 64.17

        obj.addProperty("App::PropertyFloat", "ExtinctionCoefficient", "Optical", "Extinction coefficient k")
        obj.ExtinctionCoefficient = 0.0

        obj.addProperty("App::PropertyFloat", "Transmission", "Optical", "Bulk or coating transmission fraction")
        obj.Transmission = 0.92

        obj.addProperty("App::PropertyFloat", "Reflectivity", "Optical", "Reflectivity fraction")
        obj.Reflectivity = 0.04

        obj.addProperty("App::PropertyFloat", "ReferenceWavelength", "Optical", "Reference wavelength [nm]")
        obj.ReferenceWavelength = 587.6

        obj.addProperty("App::PropertyFloat", "WavelengthMin", "Optical", "Valid wavelength minimum [nm]")
        obj.WavelengthMin = 380.0

        obj.addProperty("App::PropertyFloat", "WavelengthMax", "Optical", "Valid wavelength maximum [nm]")
        obj.WavelengthMax = 780.0

        obj.addProperty("App::PropertyFloat", "AbsorptionLength", "Optical", "Absorption length [mm]")
        obj.AbsorptionLength = 1000.0

        obj.addProperty("App::PropertyFloat", "SurfaceRoughness", "Optical", "Surface roughness [um]")
        obj.SurfaceRoughness = 0.01

        obj.addProperty("App::PropertyFloat", "SellmeierB1", "Dispersion", "Sellmeier coefficient B1")
        obj.SellmeierB1 = 0.0

        obj.addProperty("App::PropertyFloat", "SellmeierB2", "Dispersion", "Sellmeier coefficient B2")
        obj.SellmeierB2 = 0.0

        obj.addProperty("App::PropertyFloat", "SellmeierB3", "Dispersion", "Sellmeier coefficient B3")
        obj.SellmeierB3 = 0.0

        obj.addProperty("App::PropertyFloat", "SellmeierC1", "Dispersion", "Sellmeier coefficient C1 [um^2]")
        obj.SellmeierC1 = 0.0

        obj.addProperty("App::PropertyFloat", "SellmeierC2", "Dispersion", "Sellmeier coefficient C2 [um^2]")
        obj.SellmeierC2 = 0.0

        obj.addProperty("App::PropertyFloat", "SellmeierC3", "Dispersion", "Sellmeier coefficient C3 [um^2]")
        obj.SellmeierC3 = 0.0

        self._apply_preset(obj, DEFAULT_OPTICAL_PRESET)

    def onChanged(self, obj, prop):
        if prop == "MaterialPreset":
            self._apply_preset(obj, getattr(obj, "MaterialPreset", "Custom"))

    def _apply_preset(self, obj, preset_name):
        if preset_name == "Custom":
            return
        preset = get_optical_material_preset(preset_name)
        for key, value in preset.items():
            if key in getattr(obj, "PropertiesList", []):
                try:
                    setattr(obj, key, value)
                except Exception:
                    continue

