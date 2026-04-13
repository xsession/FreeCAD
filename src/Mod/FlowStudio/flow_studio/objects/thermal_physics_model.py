# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""ThermalPhysicsModel – physics settings for heat transfer analyses."""

from flow_studio.objects.base_object import BaseFlowObject


class ThermalPhysicsModel(BaseFlowObject):
    """Defines thermal physics parameters."""

    Type = "FlowStudio::ThermalPhysicsModel"

    def __init__(self, obj):
        super().__init__(obj)

        obj.addProperty(
            "App::PropertyEnumeration", "TimeModel", "Physics",
            "Steady-state or transient heat transfer"
        )
        obj.TimeModel = ["Steady", "Transient"]
        obj.TimeModel = "Steady"

        obj.addProperty(
            "App::PropertyBool", "Radiation", "Physics",
            "Enable radiation heat transfer (Stefan-Boltzmann)"
        )
        obj.Radiation = False

        obj.addProperty(
            "App::PropertyBool", "Convection", "Physics",
            "Enable convection (requires flow solution)"
        )
        obj.Convection = False

        obj.addProperty(
            "App::PropertyBool", "InternalHeatGeneration", "Physics",
            "Enable volumetric heat generation source"
        )
        obj.InternalHeatGeneration = False

        obj.addProperty(
            "App::PropertyFloat", "ReferenceTemperature", "Physics",
            "Reference temperature [K]"
        )
        obj.ReferenceTemperature = 293.15
