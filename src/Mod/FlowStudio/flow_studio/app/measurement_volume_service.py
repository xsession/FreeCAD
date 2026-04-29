# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Application service for FlowStudio volume measurement task panels."""

from __future__ import annotations


def _vector_tuple(vector):
    return (float(vector.x), float(vector.y), float(vector.z))


class FlowStudioMeasurementVolumeService:
    """Backend-facing service for volume measurement settings persistence."""

    def read_settings(self, obj):
        return {
            "Label2": getattr(obj, "Label2", ""),
            "VolumeType": getattr(obj, "VolumeType", "Box"),
            "BoxMin": _vector_tuple(getattr(obj, "BoxMin")),
            "BoxMax": _vector_tuple(getattr(obj, "BoxMax")),
            "SphereCenter": _vector_tuple(getattr(obj, "SphereCenter")),
            "SphereRadius": float(getattr(obj, "SphereRadius", 0.0)),
            "CylinderCenter": _vector_tuple(getattr(obj, "CylinderCenter")),
            "CylinderAxis": _vector_tuple(getattr(obj, "CylinderAxis")),
            "CylinderRadius": float(getattr(obj, "CylinderRadius", 0.0)),
            "CylinderHeight": float(getattr(obj, "CylinderHeight", 0.0)),
            "ThresholdField": getattr(obj, "ThresholdField", ""),
            "ThresholdMin": float(getattr(obj, "ThresholdMin", 0.0)),
            "ThresholdMax": float(getattr(obj, "ThresholdMax", 0.0)),
            "SampleFields": tuple(getattr(obj, "SampleFields", []) or []),
            "ComputeAverage": bool(getattr(obj, "ComputeAverage", False)),
            "ComputeMinMax": bool(getattr(obj, "ComputeMinMax", False)),
            "ComputeIntegral": bool(getattr(obj, "ComputeIntegral", False)),
            "ExportCSV": bool(getattr(obj, "ExportCSV", False)),
            "TimeSeries": bool(getattr(obj, "TimeSeries", False)),
        }

    def persist_settings(self, obj, settings, vector_factory):
        obj.Label2 = settings["Label2"]
        obj.VolumeType = settings["VolumeType"]
        obj.BoxMin = vector_factory(*settings["BoxMin"])
        obj.BoxMax = vector_factory(*settings["BoxMax"])
        obj.SphereCenter = vector_factory(*settings["SphereCenter"])
        obj.SphereRadius = settings["SphereRadius"]
        obj.CylinderCenter = vector_factory(*settings["CylinderCenter"])
        obj.CylinderAxis = vector_factory(*settings["CylinderAxis"])
        obj.CylinderRadius = settings["CylinderRadius"]
        obj.CylinderHeight = settings["CylinderHeight"]
        obj.ThresholdField = settings["ThresholdField"]
        obj.ThresholdMin = settings["ThresholdMin"]
        obj.ThresholdMax = settings["ThresholdMax"]
        obj.SampleFields = list(settings["SampleFields"])
        obj.ComputeAverage = settings["ComputeAverage"]
        obj.ComputeMinMax = settings["ComputeMinMax"]
        obj.ComputeIntegral = settings["ComputeIntegral"]
        obj.ExportCSV = settings["ExportCSV"]
        obj.TimeSeries = settings["TimeSeries"]