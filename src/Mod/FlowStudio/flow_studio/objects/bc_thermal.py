# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Thermal boundary conditions – temperature, heat flux, convection, radiation."""

from flow_studio.objects.base_bc import BaseBoundaryCondition


class BCTemperature(BaseBoundaryCondition):
    """Fixed temperature (Dirichlet) boundary condition."""

    Type = "FlowStudio::BCTemperature"

    def __init__(self, obj):
        super().__init__(obj)
        obj.BCLabel = "Temperature"

        obj.addProperty(
            "App::PropertyFloat", "Temperature", "Thermal",
            "Fixed temperature [K]"
        )
        obj.Temperature = 373.15  # 100°C


class BCHeatFlux(BaseBoundaryCondition):
    """Applied heat flux (Neumann) boundary condition."""

    Type = "FlowStudio::BCHeatFlux"

    def __init__(self, obj):
        super().__init__(obj)
        obj.BCLabel = "Heat Flux"

        obj.addProperty(
            "App::PropertyFloat", "HeatFlux", "Thermal",
            "Applied heat flux [W/m²]"
        )
        obj.HeatFlux = 1000.0


class BCConvection(BaseBoundaryCondition):
    """Convective heat transfer (Robin) boundary condition."""

    Type = "FlowStudio::BCConvection"

    def __init__(self, obj):
        super().__init__(obj)
        obj.BCLabel = "Convection"

        obj.addProperty(
            "App::PropertyFloat", "HeatTransferCoefficient", "Thermal",
            "Convective heat transfer coefficient [W/(m²·K)]"
        )
        obj.HeatTransferCoefficient = 10.0

        obj.addProperty(
            "App::PropertyFloat", "AmbientTemperature", "Thermal",
            "Ambient temperature [K]"
        )
        obj.AmbientTemperature = 293.15


class BCRadiation(BaseBoundaryCondition):
    """Radiation heat transfer boundary condition."""

    Type = "FlowStudio::BCRadiation"

    def __init__(self, obj):
        super().__init__(obj)
        obj.BCLabel = "Radiation"

        obj.addProperty(
            "App::PropertyFloat", "Emissivity", "Thermal",
            "Surface emissivity [-] (0..1)"
        )
        obj.Emissivity = 0.9

        obj.addProperty(
            "App::PropertyFloat", "AmbientTemperature", "Thermal",
            "Ambient radiation temperature [K]"
        )
        obj.AmbientTemperature = 293.15
