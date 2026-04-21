# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""SolidMaterial – material properties for structural mechanics analyses."""

from flow_studio.objects.base_object import BaseFlowObject


class SolidMaterial(BaseFlowObject):
    """Solid material properties (steel, aluminum, etc.)."""

    Type = "FlowStudio::SolidMaterial"

    def __init__(self, obj):
        super().__init__(obj)

        self.add_reference_property(
            obj,
            "Material Assignment",
            "Referenced parts, bodies, faces, or regions using this solid material",
        )

        obj.addProperty(
            "App::PropertyString", "MaterialName", "Material",
            "Material name"
        )
        obj.MaterialName = "Steel"

        obj.addProperty(
            "App::PropertyFloat", "Density", "Material",
            "Density [kg/m³]"
        )
        obj.Density = 7850.0

        obj.addProperty(
            "App::PropertyFloat", "YoungsModulus", "Material",
            "Young's modulus [Pa]"
        )
        obj.YoungsModulus = 2.1e11

        obj.addProperty(
            "App::PropertyFloat", "PoissonRatio", "Material",
            "Poisson's ratio [-]"
        )
        obj.PoissonRatio = 0.3

        obj.addProperty(
            "App::PropertyFloat", "ThermalExpansionCoeff", "Material",
            "Thermal expansion coefficient [1/K]"
        )
        obj.ThermalExpansionCoeff = 1.2e-5

        obj.addProperty(
            "App::PropertyFloat", "YieldStrength", "Material",
            "Yield strength [Pa]"
        )
        obj.YieldStrength = 2.5e8

        obj.addProperty(
            "App::PropertyEnumeration", "MaterialPreset", "Material",
            "Select from predefined materials"
        )
        obj.MaterialPreset = [
            "Custom",
            "Steel (Structural)",
            "Aluminum 6061-T6",
            "Copper",
            "Titanium Ti-6Al-4V",
            "Concrete",
            "Glass",
            "Nylon (PA6)",
        ]
        obj.MaterialPreset = "Steel (Structural)"
