# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""PostPipeline – post-processing container for CFD results."""

from flow_studio.objects.base_object import BaseFlowObject


class PostPipeline(BaseFlowObject):
    """Post-processing pipeline for visualising CFD results."""

    Type = "FlowStudio::PostPipeline"

    def __init__(self, obj):
        super().__init__(obj)

        obj.addProperty(
            "App::PropertyLink", "Analysis", "PostProcessing",
            "Link to the CFD analysis"
        )
        obj.addProperty(
            "App::PropertyPath", "ResultFile", "PostProcessing",
            "Path to result file (VTK / OpenFOAM)"
        )
        obj.addProperty(
            "App::PropertyEnumeration", "ResultFormat", "PostProcessing",
            "Format of results to load"
        )
        obj.ResultFormat = ["OpenFOAM", "VTK", "FluidX3D-VTK"]
        obj.ResultFormat = "OpenFOAM"

        obj.addProperty(
            "App::PropertyStringList", "AvailableFields", "PostProcessing",
            "List of available scalar/vector fields"
        )
        obj.addProperty(
            "App::PropertyString", "ActiveField", "PostProcessing",
            "Currently displayed field"
        )
        obj.ActiveField = "U"

        obj.addProperty(
            "App::PropertyEnumeration", "VisualizationType", "PostProcessing",
            "Type of visualization"
        )
        obj.VisualizationType = [
            "Contour (Surface)",
            "Contour (Slice)",
            "Streamlines",
            "Vectors",
            "Iso-Surface",
        ]
        obj.VisualizationType = "Contour (Surface)"

        obj.addProperty(
            "App::PropertyFloat", "MinRange", "ColorMap",
            "Minimum value for color map"
        )
        obj.MinRange = 0.0
        obj.addProperty(
            "App::PropertyFloat", "MaxRange", "ColorMap",
            "Maximum value for color map"
        )
        obj.MaxRange = 1.0
        obj.addProperty(
            "App::PropertyBool", "AutoRange", "ColorMap",
            "Automatically compute min/max range"
        )
        obj.AutoRange = True
