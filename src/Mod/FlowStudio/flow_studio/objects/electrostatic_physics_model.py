# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""ElectrostaticPhysicsModel – physics settings for electrostatic analysis."""

from flow_studio.objects.base_object import BaseFlowObject


class ElectrostaticPhysicsModel(BaseFlowObject):
    """Defines electrostatic physics parameters."""

    Type = "FlowStudio::ElectrostaticPhysicsModel"

    def __init__(self, obj):
        super().__init__(obj)

        obj.addProperty(
            "App::PropertyEnumeration", "TimeModel", "Physics",
            "Steady-state analysis (electrostatics is always steady)"
        )
        obj.TimeModel = ["Steady"]
        obj.TimeModel = "Steady"

        obj.addProperty(
            "App::PropertyBool", "CalculateElectricField", "Physics",
            "Calculate electric field vector E = -∇V"
        )
        obj.CalculateElectricField = True

        obj.addProperty(
            "App::PropertyBool", "CalculateElectricFlux", "Physics",
            "Calculate electric flux density D = ε·E"
        )
        obj.CalculateElectricFlux = True

        obj.addProperty(
            "App::PropertyBool", "CalculateElectricEnergy", "Physics",
            "Calculate electric energy density"
        )
        obj.CalculateElectricEnergy = True

        obj.addProperty(
            "App::PropertyBool", "CalculateElectricForce", "Physics",
            "Calculate electric force on conductors"
        )
        obj.CalculateElectricForce = True

        obj.addProperty(
            "App::PropertyBool", "CalculateCapacitanceMatrix", "Physics",
            "Calculate capacitance matrix between electrodes"
        )
        obj.CalculateCapacitanceMatrix = False
