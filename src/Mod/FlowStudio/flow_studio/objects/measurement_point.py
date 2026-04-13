# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""MeasurementPoint – point probe for field sampling in Paraview scripts.

Defines a single point (or set of points) in 3D space where field values
(velocity, pressure, temperature, etc.) are extracted during post-processing.
These probes can be exported as Paraview Python script snippets.
"""

from flow_studio.objects.base_object import BaseFlowObject


class MeasurementPoint(BaseFlowObject):
    """Single-point or multi-point field probe."""

    Type = "FlowStudio::MeasurementPoint"

    def __init__(self, obj):
        super().__init__(obj)

        obj.addProperty(
            "App::PropertyString", "Label2", "Measurement",
            "Human-readable description for this probe"
        )
        obj.Label2 = ""

        # --- Single point ---
        obj.addProperty(
            "App::PropertyVector", "ProbeLocation", "Measurement",
            "Probe point coordinates [mm]"
        )
        obj.ProbeLocation = (0.0, 0.0, 0.0)

        # --- Multi-point (line of probes) ---
        obj.addProperty(
            "App::PropertyBool", "UseLine", "Line Probe",
            "Sample along a line instead of a single point"
        )
        obj.UseLine = False

        obj.addProperty(
            "App::PropertyVector", "LineStart", "Line Probe",
            "Start point of the probe line [mm]"
        )
        obj.LineStart = (0.0, 0.0, 0.0)

        obj.addProperty(
            "App::PropertyVector", "LineEnd", "Line Probe",
            "End point of the probe line [mm]"
        )
        obj.LineEnd = (100.0, 0.0, 0.0)

        obj.addProperty(
            "App::PropertyInteger", "LineResolution", "Line Probe",
            "Number of sample points along the line"
        )
        obj.LineResolution = 50

        # --- Fields to sample ---
        obj.addProperty(
            "App::PropertyStringList", "SampleFields", "Measurement",
            "Field names to extract (e.g. U, p, T)"
        )
        obj.SampleFields = ["U", "p"]

        # --- Export options ---
        obj.addProperty(
            "App::PropertyBool", "ExportCSV", "Export",
            "Write sampled values to CSV file"
        )
        obj.ExportCSV = True

        obj.addProperty(
            "App::PropertyBool", "TimeSeries", "Export",
            "Sample across all time steps (transient)"
        )
        obj.TimeSeries = False
