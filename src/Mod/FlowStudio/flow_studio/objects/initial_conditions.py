# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""InitialConditions – set starting field values."""

from flow_studio.objects.base_object import BaseFlowObject


class InitialConditions(BaseFlowObject):
    """Defines initial velocity, pressure and temperature fields."""

    Type = "FlowStudio::InitialConditions"

    def __init__(self, obj):
        super().__init__(obj)

        self.add_reference_property(
            obj,
            "Initial Conditions",
            "Referenced parts, bodies, faces, or regions using these initial conditions",
        )

        # Velocity
        obj.addProperty(
            "App::PropertyFloat", "Ux", "Velocity",
            "Initial velocity X component [m/s]"
        )
        obj.Ux = 0.0
        obj.addProperty(
            "App::PropertyFloat", "Uy", "Velocity",
            "Initial velocity Y component [m/s]"
        )
        obj.Uy = 0.0
        obj.addProperty(
            "App::PropertyFloat", "Uz", "Velocity",
            "Initial velocity Z component [m/s]"
        )
        obj.Uz = 0.0

        # Pressure
        obj.addProperty(
            "App::PropertyFloat", "Pressure", "Pressure",
            "Initial gauge pressure [Pa]"
        )
        obj.Pressure = 0.0

        # Temperature
        obj.addProperty(
            "App::PropertyFloat", "Temperature", "Thermal",
            "Initial temperature [K]"
        )
        obj.Temperature = 293.15

        # Turbulence quantities
        obj.addProperty(
            "App::PropertyFloat", "TurbulentKineticEnergy", "Turbulence",
            "Initial turbulent kinetic energy k [m²/s²]"
        )
        obj.TurbulentKineticEnergy = 0.001
        obj.addProperty(
            "App::PropertyFloat", "TurbulentDissipationRate", "Turbulence",
            "Initial turbulent dissipation rate ε [m²/s³]"
        )
        obj.TurbulentDissipationRate = 0.001
        obj.addProperty(
            "App::PropertyFloat", "SpecificDissipationRate", "Turbulence",
            "Initial specific dissipation rate ω [1/s]"
        )
        obj.SpecificDissipationRate = 1.0
        obj.addProperty(
            "App::PropertyFloat", "NuTilda", "Turbulence",
            "Initial modified kinematic viscosity ν̃ (Spalart-Allmaras) [m²/s]"
        )
        obj.NuTilda = 1.5e-4

        # Potential flow initialisation
        obj.addProperty(
            "App::PropertyBool", "UsePotentialFlow", "Initialisation",
            "Initialize velocity field with potential flow solution"
        )
        obj.UsePotentialFlow = False
