# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Base class for boundary condition objects."""

from flow_studio.objects.base_object import BaseFlowObject


class BaseBoundaryCondition(BaseFlowObject):
    """Common properties shared by all boundary condition types."""

    Type = "FlowStudio::BaseBoundaryCondition"

    def __init__(self, obj):
        super().__init__(obj)

        self.add_reference_property(
            obj,
            "Boundary",
            "Referenced faces, surfaces, or parts for this boundary condition",
        )
        obj.addProperty(
            "App::PropertyString", "BoundaryType", "Boundary",
            "Type of boundary condition"
        )
        obj.BoundaryType = "undefined"
        obj.setPropertyStatus("BoundaryType", "ReadOnly")
