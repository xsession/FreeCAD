# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Open boundary condition (far-field / freestream)."""

from flow_studio.objects.base_bc import BaseBoundaryCondition


class BCOpenBoundary(BaseBoundaryCondition):
    """Open / far-field boundary – FloEFD equivalent of environment pressure."""

    Type = "FlowStudio::BCOpenBoundary"

    def __init__(self, obj):
        super().__init__(obj)
        obj.BoundaryType = "open"

        obj.addProperty(
            "App::PropertyFloat", "FarFieldPressure", "OpenBoundary",
            "Far-field static pressure [Pa]"
        )
        obj.FarFieldPressure = 101325.0

        obj.addProperty(
            "App::PropertyFloat", "FarFieldTemperature", "OpenBoundary",
            "Far-field temperature [K]"
        )
        obj.FarFieldTemperature = 293.15

        obj.addProperty(
            "App::PropertyFloat", "FarFieldVelocityX", "OpenBoundary",
            "Far-field velocity X [m/s]"
        )
        obj.FarFieldVelocityX = 0.0
        obj.addProperty(
            "App::PropertyFloat", "FarFieldVelocityY", "OpenBoundary",
            "Far-field velocity Y [m/s]"
        )
        obj.FarFieldVelocityY = 0.0
        obj.addProperty(
            "App::PropertyFloat", "FarFieldVelocityZ", "OpenBoundary",
            "Far-field velocity Z [m/s]"
        )
        obj.FarFieldVelocityZ = 0.0
