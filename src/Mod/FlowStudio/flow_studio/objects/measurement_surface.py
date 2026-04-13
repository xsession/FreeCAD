# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""MeasurementSurface – surface sampling/integration for Paraview scripts.

Defines a cut-plane, iso-surface, or geometry-face-based sampling surface
for extracting field data, computing averages, integrals, and fluxes.
Used to generate Paraview evaluation scripts.
"""

from flow_studio.objects.base_object import BaseFlowObject


class MeasurementSurface(BaseFlowObject):
    """Surface-based measurement region for post-processing."""

    Type = "FlowStudio::MeasurementSurface"

    def __init__(self, obj):
        super().__init__(obj)

        obj.addProperty(
            "App::PropertyString", "Label2", "Measurement",
            "Human-readable description"
        )
        obj.Label2 = ""

        # --- Surface definition ---
        obj.addProperty(
            "App::PropertyEnumeration", "SurfaceType", "Surface",
            "How the measurement surface is defined"
        )
        obj.SurfaceType = [
            "Cut Plane",
            "Iso-Surface",
            "Geometry Faces",
            "Clip (Half-Space)",
        ]
        obj.SurfaceType = "Cut Plane"

        # Cut Plane parameters
        obj.addProperty(
            "App::PropertyVector", "PlaneOrigin", "Cut Plane",
            "Origin of the cut plane [mm]"
        )
        obj.PlaneOrigin = (0.0, 0.0, 0.0)

        obj.addProperty(
            "App::PropertyEnumeration", "PlaneNormal", "Cut Plane",
            "Cut plane normal axis"
        )
        obj.PlaneNormal = ["X", "Y", "Z", "Custom"]
        obj.PlaneNormal = "X"

        obj.addProperty(
            "App::PropertyVector", "CustomNormal", "Cut Plane",
            "Custom normal vector (used when PlaneNormal = Custom)"
        )
        obj.CustomNormal = (1.0, 0.0, 0.0)

        # Iso-surface parameters
        obj.addProperty(
            "App::PropertyString", "IsoField", "Iso-Surface",
            "Field name for the iso-surface"
        )
        obj.IsoField = "p"

        obj.addProperty(
            "App::PropertyFloat", "IsoValue", "Iso-Surface",
            "Iso-surface contour value"
        )
        obj.IsoValue = 0.0

        # Geometry face reference
        obj.addProperty(
            "App::PropertyLinkSubList", "FaceRefs", "Geometry Faces",
            "References to specific geometry faces"
        )

        # --- Fields to evaluate ---
        obj.addProperty(
            "App::PropertyStringList", "SampleFields", "Measurement",
            "Field names to extract on the surface"
        )
        obj.SampleFields = ["U", "p"]

        # --- Computed quantities ---
        obj.addProperty(
            "App::PropertyBool", "ComputeAverage", "Evaluation",
            "Compute area-weighted average of fields"
        )
        obj.ComputeAverage = True

        obj.addProperty(
            "App::PropertyBool", "ComputeIntegral", "Evaluation",
            "Compute surface integral (flux)"
        )
        obj.ComputeIntegral = False

        obj.addProperty(
            "App::PropertyBool", "ComputeMassFlow", "Evaluation",
            "Compute mass flow rate through the surface"
        )
        obj.ComputeMassFlow = False

        obj.addProperty(
            "App::PropertyBool", "ComputeForce", "Evaluation",
            "Compute pressure + viscous force on the surface"
        )
        obj.ComputeForce = False

        obj.addProperty(
            "App::PropertyVector", "ForceRefPoint", "Evaluation",
            "Reference point for moment computation [mm]"
        )
        obj.ForceRefPoint = (0.0, 0.0, 0.0)

        # --- Export ---
        obj.addProperty(
            "App::PropertyBool", "ExportCSV", "Export",
            "Export surface data to CSV"
        )
        obj.ExportCSV = True

        obj.addProperty(
            "App::PropertyBool", "ExportVTK", "Export",
            "Export surface as VTK file for external visualization"
        )
        obj.ExportVTK = False

        obj.addProperty(
            "App::PropertyBool", "TimeSeries", "Export",
            "Evaluate across all time steps"
        )
        obj.TimeSeries = False
