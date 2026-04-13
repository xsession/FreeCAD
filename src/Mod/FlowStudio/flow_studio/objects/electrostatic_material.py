# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""ElectrostaticMaterial – material properties for electrostatic analyses."""

from flow_studio.objects.base_object import BaseFlowObject


class ElectrostaticMaterial(BaseFlowObject):
    """Dielectric material properties for electrostatic simulations."""

    Type = "FlowStudio::ElectrostaticMaterial"

    def __init__(self, obj):
        super().__init__(obj)

        obj.addProperty(
            "App::PropertyString", "MaterialName", "Material",
            "Material name"
        )
        obj.MaterialName = "Air"

        obj.addProperty(
            "App::PropertyFloat", "RelativePermittivity", "Material",
            "Relative permittivity (dielectric constant) [-]"
        )
        obj.RelativePermittivity = 1.0

        obj.addProperty(
            "App::PropertyFloat", "ElectricConductivity", "Material",
            "Electric conductivity [S/m]"
        )
        obj.ElectricConductivity = 0.0

        obj.addProperty(
            "App::PropertyEnumeration", "MaterialPreset", "Material",
            "Select from predefined dielectric materials"
        )
        obj.MaterialPreset = [
            "Custom",
            "Vacuum",
            "Air",
            "PTFE (Teflon)",
            "FR-4 (PCB)",
            "Silicon Dioxide",
            "Alumina (Al₂O₃)",
            "Barium Titanate",
            "Water",
        ]
        obj.MaterialPreset = "Air"
