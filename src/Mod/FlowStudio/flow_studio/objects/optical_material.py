# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""OpticalMaterial - refractive, absorptive, and reflective material data."""

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
        obj.MaterialName = "BK7"

        obj.addProperty("App::PropertyEnumeration", "MaterialPreset", "Material", "Optical material preset")
        obj.MaterialPreset = [
            "Custom",
            "Vacuum",
            "Air",
            "BK7",
            "Fused Silica",
            "Sapphire",
            "Polycarbonate",
            "Mirror Aluminum",
        ]
        obj.MaterialPreset = "BK7"

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

