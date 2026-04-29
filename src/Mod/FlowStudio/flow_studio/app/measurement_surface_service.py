# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Application service for FlowStudio surface measurement task panels."""

from __future__ import annotations


def _vector_tuple(vector):
    return (float(vector.x), float(vector.y), float(vector.z))


class FlowStudioMeasurementSurfaceService:
    """Backend-facing service for surface measurement settings persistence."""

    def read_settings(self, obj):
        return {
            "Label2": getattr(obj, "Label2", ""),
            "SurfaceType": getattr(obj, "SurfaceType", "Cut Plane"),
            "PlaneOrigin": _vector_tuple(getattr(obj, "PlaneOrigin")),
            "PlaneNormal": getattr(obj, "PlaneNormal", "X"),
            "CustomNormal": _vector_tuple(getattr(obj, "CustomNormal")),
            "IsoField": getattr(obj, "IsoField", ""),
            "IsoValue": float(getattr(obj, "IsoValue", 0.0)),
            "SampleFields": tuple(getattr(obj, "SampleFields", []) or []),
            "ComputeAverage": bool(getattr(obj, "ComputeAverage", False)),
            "ComputeIntegral": bool(getattr(obj, "ComputeIntegral", False)),
            "ComputeMassFlow": bool(getattr(obj, "ComputeMassFlow", False)),
            "ComputeForce": bool(getattr(obj, "ComputeForce", False)),
            "ForceRefPoint": _vector_tuple(getattr(obj, "ForceRefPoint")),
            "ExportCSV": bool(getattr(obj, "ExportCSV", False)),
            "ExportVTK": bool(getattr(obj, "ExportVTK", False)),
            "TimeSeries": bool(getattr(obj, "TimeSeries", False)),
            "FaceRefs": tuple(getattr(obj, "FaceRefs", []) or []),
        }

    def persist_settings(self, obj, settings, vector_factory):
        obj.Label2 = settings["Label2"]
        obj.SurfaceType = settings["SurfaceType"]
        obj.PlaneOrigin = vector_factory(*settings["PlaneOrigin"])
        obj.PlaneNormal = settings["PlaneNormal"]
        obj.CustomNormal = vector_factory(*settings["CustomNormal"])
        obj.IsoField = settings["IsoField"]
        obj.IsoValue = settings["IsoValue"]
        obj.SampleFields = list(settings["SampleFields"])
        obj.ComputeAverage = settings["ComputeAverage"]
        obj.ComputeIntegral = settings["ComputeIntegral"]
        obj.ComputeMassFlow = settings["ComputeMassFlow"]
        obj.ComputeForce = settings["ComputeForce"]
        obj.ForceRefPoint = vector_factory(*settings["ForceRefPoint"])
        obj.ExportCSV = settings["ExportCSV"]
        obj.ExportVTK = settings["ExportVTK"]
        obj.TimeSeries = settings["TimeSeries"]