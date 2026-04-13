# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""ThermalMaterial – material properties for heat transfer analyses."""

from flow_studio.objects.base_object import BaseFlowObject


class ThermalMaterial(BaseFlowObject):
    """Thermal material properties for heat conduction/convection analyses."""

    Type = "FlowStudio::ThermalMaterial"

    def __init__(self, obj):
        super().__init__(obj)

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
            "App::PropertyFloat", "ThermalConductivity", "Material",
            "Thermal conductivity [W/(m·K)]"
        )
        obj.ThermalConductivity = 50.0

        obj.addProperty(
            "App::PropertyFloat", "SpecificHeat", "Material",
            "Specific heat capacity [J/(kg·K)]"
        )
        obj.SpecificHeat = 500.0

        obj.addProperty(
            "App::PropertyFloat", "Emissivity", "Material",
            "Surface emissivity for radiation [-]"
        )
        obj.Emissivity = 0.3

        obj.addProperty(
            "App::PropertyEnumeration", "MaterialPreset", "Material",
            "Select from predefined thermal materials"
        )
        obj.MaterialPreset = [
            "Custom",
            "Steel",
            "Aluminum",
            "Copper",
            "Glass",
            "Concrete",
            "Air",
            "Water",
            "Insulation (Mineral Wool)",
        ]
        obj.MaterialPreset = "Steel"
