# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Outlet boundary condition."""

from flow_studio.objects.base_bc import BaseBoundaryCondition


class BCOutlet(BaseBoundaryCondition):
    """Outlet boundary – static pressure, outflow, etc."""

    Type = "FlowStudio::BCOutlet"

    def __init__(self, obj):
        super().__init__(obj)
        obj.BoundaryType = "outlet"

        obj.addProperty(
            "App::PropertyEnumeration", "OutletType", "Outlet",
            "Method for specifying outlet conditions"
        )
        obj.OutletType = [
            "Static Pressure",
            "Mass Flow Rate",
            "Outflow (Zero Gradient)",
        ]
        obj.OutletType = "Static Pressure"

        obj.addProperty(
            "App::PropertyFloat", "StaticPressure", "Outlet",
            "Static pressure at outlet [Pa]"
        )
        obj.StaticPressure = 0.0

        obj.addProperty(
            "App::PropertyFloat", "OutletMassFlowRate", "Outlet",
            "Mass flow rate at outlet [kg/s]"
        )
        obj.OutletMassFlowRate = 0.0

        # Backflow prevention
        obj.addProperty(
            "App::PropertyBool", "PreventBackflow", "Outlet",
            "Prevent reverse flow at outlet"
        )
        obj.PreventBackflow = True
