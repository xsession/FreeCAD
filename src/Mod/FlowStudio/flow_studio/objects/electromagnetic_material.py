# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""ElectromagneticMaterial – material for magnetostatic/magnetodynamic analyses."""

from flow_studio.objects.base_object import BaseFlowObject


class ElectromagneticMaterial(BaseFlowObject):
    """Electromagnetic material properties (permeability, conductivity, etc.)."""

    Type = "FlowStudio::ElectromagneticMaterial"

    def __init__(self, obj):
        super().__init__(obj)

        obj.addProperty(
            "App::PropertyString", "MaterialName", "Material",
            "Material name"
        )
        obj.MaterialName = "Air"

        obj.addProperty(
            "App::PropertyFloat", "RelativePermeability", "Material",
            "Relative permeability [-]"
        )
        obj.RelativePermeability = 1.0

        obj.addProperty(
            "App::PropertyFloat", "RelativePermittivity", "Material",
            "Relative permittivity [-]"
        )
        obj.RelativePermittivity = 1.0

        obj.addProperty(
            "App::PropertyFloat", "ElectricConductivity", "Material",
            "Electric conductivity [S/m]"
        )
        obj.ElectricConductivity = 0.0

        obj.addProperty(
            "App::PropertyFloat", "Density", "Material",
            "Density [kg/m³]"
        )
        obj.Density = 1.225

        obj.addProperty(
            "App::PropertyEnumeration", "MaterialPreset", "Material",
            "Select from predefined EM materials"
        )
        obj.MaterialPreset = [
            "Custom",
            "Air / Vacuum",
            "Copper",
            "Aluminum",
            "Iron (soft)",
            "Silicon Steel (M19)",
            "Ferrite (MnZn)",
            "NdFeB Magnet",
            "FR-4 (PCB)",
        ]
        obj.MaterialPreset = "Air / Vacuum"
