# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""ElectromagneticPhysicsModel – physics settings for magnetostatic/magnetodynamic."""

from flow_studio.objects.base_object import BaseFlowObject


class ElectromagneticPhysicsModel(BaseFlowObject):
    """Defines electromagnetic physics parameters.

    Supports three modes:
    - Magnetostatic: static magnetic field (DC currents / permanent magnets)
    - Magnetodynamic Harmonic: time-harmonic (AC) analysis at a single frequency
    - Magnetodynamic Transient: full time-domain electromagnetic analysis
    """

    Type = "FlowStudio::ElectromagneticPhysicsModel"

    def __init__(self, obj):
        super().__init__(obj)

        obj.addProperty(
            "App::PropertyEnumeration", "EMModel", "Physics",
            "Electromagnetic analysis model"
        )
        obj.EMModel = [
            "Magnetostatic",
            "Magnetodynamic Harmonic",
            "Magnetodynamic Transient",
        ]
        obj.EMModel = "Magnetostatic"

        obj.addProperty(
            "App::PropertyEnumeration", "TimeModel", "Physics",
            "Steady or transient"
        )
        obj.TimeModel = ["Steady", "Transient"]
        obj.TimeModel = "Steady"

        obj.addProperty(
            "App::PropertyFloat", "Frequency", "Physics",
            "Excitation frequency [Hz] (for harmonic analysis)"
        )
        obj.Frequency = 50.0

        obj.addProperty(
            "App::PropertyBool", "CalculateCurrentDensity", "Physics",
            "Calculate current density J"
        )
        obj.CalculateCurrentDensity = True

        obj.addProperty(
            "App::PropertyBool", "CalculateElectricField", "Physics",
            "Calculate electric field E"
        )
        obj.CalculateElectricField = True

        obj.addProperty(
            "App::PropertyBool", "CalculateMagneticFieldStrength", "Physics",
            "Calculate magnetic field strength H"
        )
        obj.CalculateMagneticFieldStrength = True

        obj.addProperty(
            "App::PropertyBool", "CalculateJouleHeating", "Physics",
            "Calculate Joule/resistive heating losses"
        )
        obj.CalculateJouleHeating = True

        obj.addProperty(
            "App::PropertyBool", "CalculateMagneticFluxDensity", "Physics",
            "Calculate magnetic flux density B"
        )
        obj.CalculateMagneticFluxDensity = True
