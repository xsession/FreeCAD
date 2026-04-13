# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""StructuralPhysicsModel – physics settings for structural mechanics."""

from flow_studio.objects.base_object import BaseFlowObject


class StructuralPhysicsModel(BaseFlowObject):
    """Defines structural mechanics physics parameters."""

    Type = "FlowStudio::StructuralPhysicsModel"

    def __init__(self, obj):
        super().__init__(obj)

        obj.addProperty(
            "App::PropertyEnumeration", "AnalysisModel", "Physics",
            "Type of structural analysis"
        )
        obj.AnalysisModel = [
            "Linear Elastic",
            "Nonlinear Elastic",
            "Plane Stress",
            "Plane Strain",
            "Axisymmetric",
        ]
        obj.AnalysisModel = "Linear Elastic"

        obj.addProperty(
            "App::PropertyEnumeration", "TimeModel", "Physics",
            "Steady-state or transient"
        )
        obj.TimeModel = ["Steady", "Transient"]
        obj.TimeModel = "Steady"

        obj.addProperty(
            "App::PropertyBool", "LargeDeformation", "Physics",
            "Enable geometric nonlinearity (large deformations)"
        )
        obj.LargeDeformation = False

        obj.addProperty(
            "App::PropertyBool", "Gravity", "Physics",
            "Include gravitational body force"
        )
        obj.Gravity = False

        obj.addProperty(
            "App::PropertyBool", "ThermalStress", "Physics",
            "Include thermal stress from temperature distribution"
        )
        obj.ThermalStress = False

        obj.addProperty(
            "App::PropertyBool", "CalculateStresses", "Physics",
            "Calculate stress tensor in output"
        )
        obj.CalculateStresses = True

        obj.addProperty(
            "App::PropertyBool", "CalculateStrains", "Physics",
            "Calculate strain tensor in output"
        )
        obj.CalculateStrains = True
