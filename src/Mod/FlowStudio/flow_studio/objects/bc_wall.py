# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Wall boundary condition (no-slip, slip, moving wall, rough wall)."""

from flow_studio.objects.base_bc import BaseBoundaryCondition


class BCWall(BaseBoundaryCondition):
    """Wall boundary – like FloEFD's Real Wall / Ideal Wall options."""

    Type = "FlowStudio::BCWall"

    def __init__(self, obj):
        super().__init__(obj)
        obj.BoundaryType = "wall"

        obj.addProperty(
            "App::PropertyEnumeration", "WallType", "Wall",
            "Type of wall boundary"
        )
        obj.WallType = [
            "No-Slip",
            "Slip",
            "Moving Wall (Translational)",
            "Moving Wall (Rotational)",
            "Rough Wall",
        ]
        obj.WallType = "No-Slip"

        # Moving wall velocity
        obj.addProperty(
            "App::PropertyFloat", "WallVelocityX", "Wall",
            "Wall translational velocity X [m/s]"
        )
        obj.WallVelocityX = 0.0
        obj.addProperty(
            "App::PropertyFloat", "WallVelocityY", "Wall",
            "Wall translational velocity Y [m/s]"
        )
        obj.WallVelocityY = 0.0
        obj.addProperty(
            "App::PropertyFloat", "WallVelocityZ", "Wall",
            "Wall translational velocity Z [m/s]"
        )
        obj.WallVelocityZ = 0.0

        # Rotational wall
        obj.addProperty(
            "App::PropertyFloat", "AngularVelocity", "Wall",
            "Angular velocity for rotational wall [rad/s]"
        )
        obj.AngularVelocity = 0.0
        obj.addProperty(
            "App::PropertyVector", "RotationAxis", "Wall",
            "Rotation axis direction"
        )
        obj.RotationAxis = (0.0, 0.0, 1.0)
        obj.addProperty(
            "App::PropertyVector", "RotationOrigin", "Wall",
            "Rotation origin point [mm]"
        )
        obj.RotationOrigin = (0.0, 0.0, 0.0)

        # Roughness
        obj.addProperty(
            "App::PropertyFloat", "RoughnessHeight", "Wall",
            "Sand-grain roughness height Ks [m]"
        )
        obj.RoughnessHeight = 0.0
        obj.addProperty(
            "App::PropertyFloat", "RoughnessConstant", "Wall",
            "Roughness constant Cs"
        )
        obj.RoughnessConstant = 0.5

        # Thermal wall BC
        obj.addProperty(
            "App::PropertyEnumeration", "ThermalType", "Thermal",
            "Thermal boundary type on wall"
        )
        obj.ThermalType = [
            "Adiabatic",
            "Fixed Temperature",
            "Fixed Heat Flux",
            "Heat Transfer Coefficient",
        ]
        obj.ThermalType = "Adiabatic"

        obj.addProperty(
            "App::PropertyFloat", "WallTemperature", "Thermal",
            "Fixed wall temperature [K]"
        )
        obj.WallTemperature = 293.15

        obj.addProperty(
            "App::PropertyFloat", "HeatFlux", "Thermal",
            "Applied heat flux [W/m²]"
        )
        obj.HeatFlux = 0.0

        obj.addProperty(
            "App::PropertyFloat", "HeatTransferCoeff", "Thermal",
            "Heat transfer coefficient [W/(m²·K)]"
        )
        obj.HeatTransferCoeff = 0.0
