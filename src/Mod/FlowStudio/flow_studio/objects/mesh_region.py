# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""MeshRegion – local mesh refinement zone."""

from flow_studio.objects.base_object import BaseFlowObject


class MeshRegion(BaseFlowObject):
    """Local mesh refinement region – like FloEFD local mesh settings."""

    Type = "FlowStudio::MeshRegion"

    def __init__(self, obj):
        super().__init__(obj)

        obj.addProperty(
            "App::PropertyLinkSubList", "References", "MeshRegion",
            "Geometry references for the refinement region"
        )
        obj.addProperty(
            "App::PropertyEnumeration", "RegionType", "MeshRegion",
            "Type of refinement region"
        )
        obj.RegionType = ["Surface", "Volume (Box)", "Volume (Sphere)", "Volume (Cylinder)"]
        obj.RegionType = "Surface"

        obj.addProperty(
            "App::PropertyFloat", "RefinementLevel", "MeshRegion",
            "Element size in this region [mm]"
        )
        obj.RefinementLevel = 5.0

        # Volume region dimensions
        obj.addProperty(
            "App::PropertyVector", "Center", "MeshRegion",
            "Center point for volume region [mm]"
        )
        obj.Center = (0.0, 0.0, 0.0)
        obj.addProperty(
            "App::PropertyFloat", "Radius", "MeshRegion",
            "Radius for spherical/cylindrical region [mm]"
        )
        obj.Radius = 50.0
        obj.addProperty(
            "App::PropertyVector", "BoxMin", "MeshRegion",
            "Minimum corner for box region [mm]"
        )
        obj.BoxMin = (-50.0, -50.0, -50.0)
        obj.addProperty(
            "App::PropertyVector", "BoxMax", "MeshRegion",
            "Maximum corner for box region [mm]"
        )
        obj.BoxMax = (50.0, 50.0, 50.0)
