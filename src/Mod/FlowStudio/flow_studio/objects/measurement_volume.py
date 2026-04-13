# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""MeasurementVolume – volume region sampling for Paraview scripts.

Defines a box, sphere, or threshold-based volume region where field
statistics (min, max, average, integral) are computed during
post-processing.  Generates Paraview Python script snippets.
"""

from flow_studio.objects.base_object import BaseFlowObject


class MeasurementVolume(BaseFlowObject):
    """Volume-based measurement region for post-processing."""

    Type = "FlowStudio::MeasurementVolume"

    def __init__(self, obj):
        super().__init__(obj)

        obj.addProperty(
            "App::PropertyString", "Label2", "Measurement",
            "Human-readable description"
        )
        obj.Label2 = ""

        # --- Volume definition ---
        obj.addProperty(
            "App::PropertyEnumeration", "VolumeType", "Volume",
            "How the measurement volume is defined"
        )
        obj.VolumeType = [
            "Box",
            "Sphere",
            "Cylinder",
            "Threshold (field-based)",
            "Entire Domain",
        ]
        obj.VolumeType = "Box"

        # Box parameters
        obj.addProperty(
            "App::PropertyVector", "BoxMin", "Box",
            "Minimum corner of the box [mm]"
        )
        obj.BoxMin = (-50.0, -50.0, -50.0)

        obj.addProperty(
            "App::PropertyVector", "BoxMax", "Box",
            "Maximum corner of the box [mm]"
        )
        obj.BoxMax = (50.0, 50.0, 50.0)

        # Sphere parameters
        obj.addProperty(
            "App::PropertyVector", "SphereCenter", "Sphere",
            "Center of the sphere [mm]"
        )
        obj.SphereCenter = (0.0, 0.0, 0.0)

        obj.addProperty(
            "App::PropertyFloat", "SphereRadius", "Sphere",
            "Radius of the sphere [mm]"
        )
        obj.SphereRadius = 50.0

        # Cylinder parameters
        obj.addProperty(
            "App::PropertyVector", "CylinderCenter", "Cylinder",
            "Center of the cylinder base [mm]"
        )
        obj.CylinderCenter = (0.0, 0.0, 0.0)

        obj.addProperty(
            "App::PropertyVector", "CylinderAxis", "Cylinder",
            "Cylinder axis direction"
        )
        obj.CylinderAxis = (0.0, 0.0, 1.0)

        obj.addProperty(
            "App::PropertyFloat", "CylinderRadius", "Cylinder",
            "Cylinder radius [mm]"
        )
        obj.CylinderRadius = 25.0

        obj.addProperty(
            "App::PropertyFloat", "CylinderHeight", "Cylinder",
            "Cylinder height [mm]"
        )
        obj.CylinderHeight = 100.0

        # Threshold parameters
        obj.addProperty(
            "App::PropertyString", "ThresholdField", "Threshold",
            "Field name for thresholding"
        )
        obj.ThresholdField = "p"

        obj.addProperty(
            "App::PropertyFloat", "ThresholdMin", "Threshold",
            "Minimum threshold value"
        )
        obj.ThresholdMin = 0.0

        obj.addProperty(
            "App::PropertyFloat", "ThresholdMax", "Threshold",
            "Maximum threshold value"
        )
        obj.ThresholdMax = 1.0

        # --- Fields to evaluate ---
        obj.addProperty(
            "App::PropertyStringList", "SampleFields", "Measurement",
            "Field names to evaluate in the volume"
        )
        obj.SampleFields = ["U", "p"]

        # --- Computed quantities ---
        obj.addProperty(
            "App::PropertyBool", "ComputeAverage", "Evaluation",
            "Compute volume-weighted average"
        )
        obj.ComputeAverage = True

        obj.addProperty(
            "App::PropertyBool", "ComputeMinMax", "Evaluation",
            "Compute min/max field values in the region"
        )
        obj.ComputeMinMax = True

        obj.addProperty(
            "App::PropertyBool", "ComputeIntegral", "Evaluation",
            "Compute volume integral"
        )
        obj.ComputeIntegral = False

        # --- Export ---
        obj.addProperty(
            "App::PropertyBool", "ExportCSV", "Export",
            "Export statistics to CSV"
        )
        obj.ExportCSV = True

        obj.addProperty(
            "App::PropertyBool", "TimeSeries", "Export",
            "Evaluate across all time steps"
        )
        obj.TimeSeries = False
