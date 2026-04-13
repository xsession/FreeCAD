# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Structural boundary conditions – fixed displacement, force, pressure load."""

from flow_studio.objects.base_bc import BaseBoundaryCondition


class BCFixedDisplacement(BaseBoundaryCondition):
    """Fixed (zero displacement) constraint on selected faces."""

    Type = "FlowStudio::BCFixedDisplacement"

    def __init__(self, obj):
        super().__init__(obj)
        obj.BCLabel = "Fixed"

        obj.addProperty(
            "App::PropertyBool", "FixX", "Constraint",
            "Fix displacement in X direction"
        )
        obj.FixX = True

        obj.addProperty(
            "App::PropertyBool", "FixY", "Constraint",
            "Fix displacement in Y direction"
        )
        obj.FixY = True

        obj.addProperty(
            "App::PropertyBool", "FixZ", "Constraint",
            "Fix displacement in Z direction"
        )
        obj.FixZ = True

        obj.addProperty(
            "App::PropertyFloat", "DisplacementX", "Constraint",
            "Prescribed displacement in X [m] (if FixX)"
        )
        obj.DisplacementX = 0.0

        obj.addProperty(
            "App::PropertyFloat", "DisplacementY", "Constraint",
            "Prescribed displacement in Y [m] (if FixY)"
        )
        obj.DisplacementY = 0.0

        obj.addProperty(
            "App::PropertyFloat", "DisplacementZ", "Constraint",
            "Prescribed displacement in Z [m] (if FixZ)"
        )
        obj.DisplacementZ = 0.0


class BCForce(BaseBoundaryCondition):
    """Applied force on selected faces."""

    Type = "FlowStudio::BCForce"

    def __init__(self, obj):
        super().__init__(obj)
        obj.BCLabel = "Force"

        obj.addProperty(
            "App::PropertyFloat", "ForceX", "Force",
            "Force in X direction [N]"
        )
        obj.ForceX = 0.0

        obj.addProperty(
            "App::PropertyFloat", "ForceY", "Force",
            "Force in Y direction [N]"
        )
        obj.ForceY = 0.0

        obj.addProperty(
            "App::PropertyFloat", "ForceZ", "Force",
            "Force in Z direction [N]"
        )
        obj.ForceZ = -1000.0


class BCPressureLoad(BaseBoundaryCondition):
    """Pressure load (normal force) on selected faces."""

    Type = "FlowStudio::BCPressureLoad"

    def __init__(self, obj):
        super().__init__(obj)
        obj.BCLabel = "Pressure Load"

        obj.addProperty(
            "App::PropertyFloat", "Pressure", "Load",
            "Applied pressure [Pa] (positive = compression)"
        )
        obj.Pressure = 1e6
