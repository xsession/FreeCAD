# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""FluidMaterial – fluid properties (like FloEFD fluid definition)."""

from flow_studio.objects.base_object import BaseFlowObject


class FluidMaterial(BaseFlowObject):
    """Defines fluid properties for the CFD analysis."""

    Type = "FlowStudio::FluidMaterial"

    def __init__(self, obj):
        super().__init__(obj)

        # Material name
        obj.addProperty(
            "App::PropertyString", "MaterialName", "Material",
            "Name of the fluid material"
        )
        obj.MaterialName = "Air"

        # Density
        obj.addProperty(
            "App::PropertyFloat", "Density", "Material",
            "Fluid density [kg/m³]"
        )
        obj.Density = 1.225

        # Dynamic viscosity
        obj.addProperty(
            "App::PropertyFloat", "DynamicViscosity", "Material",
            "Dynamic viscosity [Pa·s]"
        )
        obj.DynamicViscosity = 1.81e-5

        # Kinematic viscosity (auto-computed)
        obj.addProperty(
            "App::PropertyFloat", "KinematicViscosity", "Material",
            "Kinematic viscosity [m²/s]"
        )
        obj.KinematicViscosity = 1.48e-5

        # Specific heat
        obj.addProperty(
            "App::PropertyFloat", "SpecificHeat", "Material",
            "Specific heat capacity at constant pressure [J/(kg·K)]"
        )
        obj.SpecificHeat = 1005.0

        # Thermal conductivity
        obj.addProperty(
            "App::PropertyFloat", "ThermalConductivity", "Material",
            "Thermal conductivity [W/(m·K)]"
        )
        obj.ThermalConductivity = 0.0257

        # Prandtl number
        obj.addProperty(
            "App::PropertyFloat", "PrandtlNumber", "Material",
            "Prandtl number"
        )
        obj.PrandtlNumber = 0.707

        # Reference temperature
        obj.addProperty(
            "App::PropertyFloat", "ReferenceTemperature", "Material",
            "Reference temperature [K]"
        )
        obj.ReferenceTemperature = 293.15

        # Thermal expansion coefficient
        obj.addProperty(
            "App::PropertyFloat", "ThermalExpansionCoeff", "Material",
            "Volumetric thermal expansion coefficient [1/K]"
        )
        obj.ThermalExpansionCoeff = 3.41e-3

        # Predefined materials list
        obj.addProperty(
            "App::PropertyEnumeration", "Preset", "Material",
            "Select a predefined fluid material"
        )
        obj.Preset = [
            "Custom",
            "Air (20°C, 1atm)",
            "Water (20°C)",
            "Oil (SAE 30)",
            "Glycerin",
            "Mercury",
            "R134a",
            "Nitrogen",
            "Oxygen",
        ]
        obj.Preset = "Air (20°C, 1atm)"
