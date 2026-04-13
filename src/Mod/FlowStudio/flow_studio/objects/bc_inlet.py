# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Inlet boundary condition."""

from flow_studio.objects.base_bc import BaseBoundaryCondition


class BCInlet(BaseBoundaryCondition):
    """Inlet boundary – velocity, mass flow, or total pressure."""

    Type = "FlowStudio::BCInlet"

    def __init__(self, obj):
        super().__init__(obj)
        obj.BoundaryType = "inlet"

        obj.addProperty(
            "App::PropertyEnumeration", "InletType", "Inlet",
            "Method for specifying inlet conditions"
        )
        obj.InletType = [
            "Velocity",
            "Mass Flow Rate",
            "Volumetric Flow Rate",
            "Total Pressure",
        ]
        obj.InletType = "Velocity"

        # Velocity components
        obj.addProperty("App::PropertyFloat", "Ux", "Inlet", "Velocity X [m/s]")
        obj.Ux = 0.0
        obj.addProperty("App::PropertyFloat", "Uy", "Inlet", "Velocity Y [m/s]")
        obj.Uy = 0.0
        obj.addProperty("App::PropertyFloat", "Uz", "Inlet", "Velocity Z [m/s]")
        obj.Uz = 1.0

        # Velocity magnitude + direction
        obj.addProperty(
            "App::PropertyFloat", "VelocityMagnitude", "Inlet",
            "Velocity magnitude [m/s]"
        )
        obj.VelocityMagnitude = 1.0
        obj.addProperty(
            "App::PropertyBool", "NormalToFace", "Inlet",
            "Velocity direction normal to face"
        )
        obj.NormalToFace = True

        # Mass / volumetric flow rate
        obj.addProperty(
            "App::PropertyFloat", "MassFlowRate", "Inlet",
            "Mass flow rate [kg/s]"
        )
        obj.MassFlowRate = 0.0
        obj.addProperty(
            "App::PropertyFloat", "VolFlowRate", "Inlet",
            "Volumetric flow rate [m³/s]"
        )
        obj.VolFlowRate = 0.0

        # Total pressure
        obj.addProperty(
            "App::PropertyFloat", "TotalPressure", "Inlet",
            "Total (stagnation) pressure [Pa]"
        )
        obj.TotalPressure = 0.0

        # Turbulence at inlet
        obj.addProperty(
            "App::PropertyEnumeration", "TurbulenceSpec", "Turbulence",
            "How to specify turbulence at inlet"
        )
        obj.TurbulenceSpec = [
            "Intensity & Length Scale",
            "Intensity & Viscosity Ratio",
            "k & Epsilon",
            "k & Omega",
        ]
        obj.TurbulenceSpec = "Intensity & Length Scale"

        obj.addProperty(
            "App::PropertyFloat", "TurbulenceIntensity", "Turbulence",
            "Turbulence intensity [%]"
        )
        obj.TurbulenceIntensity = 5.0
        obj.addProperty(
            "App::PropertyFloat", "TurbulenceLengthScale", "Turbulence",
            "Turbulence length scale [m]"
        )
        obj.TurbulenceLengthScale = 0.01

        # Thermal
        obj.addProperty(
            "App::PropertyFloat", "InletTemperature", "Thermal",
            "Inlet temperature [K]"
        )
        obj.InletTemperature = 293.15
