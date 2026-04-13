# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""BoundaryLayer – prismatic inflation layer mesh settings."""

from flow_studio.objects.base_object import BaseFlowObject


class BoundaryLayer(BaseFlowObject):
    """Prismatic boundary layer mesh – like FloEFD's boundary layer resolution."""

    Type = "FlowStudio::BoundaryLayer"

    def __init__(self, obj):
        super().__init__(obj)

        obj.addProperty(
            "App::PropertyLinkSubList", "References", "BoundaryLayer",
            "Face references for boundary layer inflation"
        )
        obj.addProperty(
            "App::PropertyInteger", "NumLayers", "BoundaryLayer",
            "Number of prismatic layers"
        )
        obj.NumLayers = 5

        obj.addProperty(
            "App::PropertyFloat", "FirstLayerHeight", "BoundaryLayer",
            "First cell height [mm]"
        )
        obj.FirstLayerHeight = 0.1

        obj.addProperty(
            "App::PropertyFloat", "ExpansionRatio", "BoundaryLayer",
            "Growth ratio between successive layers"
        )
        obj.ExpansionRatio = 1.2

        obj.addProperty(
            "App::PropertyFloat", "TotalThickness", "BoundaryLayer",
            "Total boundary layer thickness [mm] (0 = auto)"
        )
        obj.TotalThickness = 0.0

        obj.addProperty(
            "App::PropertyEnumeration", "Specification", "BoundaryLayer",
            "How to specify the boundary layer"
        )
        obj.Specification = [
            "First Layer + Expansion",
            "First Layer + Total Thickness",
            "Overall Thickness + Expansion",
            "Target y+ (auto)",
        ]
        obj.Specification = "First Layer + Expansion"

        obj.addProperty(
            "App::PropertyFloat", "TargetYPlus", "BoundaryLayer",
            "Target y+ value for automatic first layer sizing"
        )
        obj.TargetYPlus = 1.0
