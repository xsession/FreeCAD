# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Application service for FlowStudio point measurement task panels."""

from __future__ import annotations


def _vector_tuple(vector):
    return (float(vector.x), float(vector.y), float(vector.z))


class FlowStudioMeasurementPointService:
    """Backend-facing service for point measurement settings persistence."""

    def read_settings(self, obj):
        return {
            "Label2": getattr(obj, "Label2", ""),
            "ProbeLocation": _vector_tuple(getattr(obj, "ProbeLocation")),
            "UseLine": bool(getattr(obj, "UseLine", False)),
            "LineStart": _vector_tuple(getattr(obj, "LineStart")),
            "LineEnd": _vector_tuple(getattr(obj, "LineEnd")),
            "LineResolution": int(getattr(obj, "LineResolution", 2)),
            "SampleFields": tuple(getattr(obj, "SampleFields", []) or []),
            "ExportCSV": bool(getattr(obj, "ExportCSV", False)),
            "TimeSeries": bool(getattr(obj, "TimeSeries", False)),
        }

    def persist_settings(self, obj, settings, vector_factory):
        obj.Label2 = settings["Label2"]
        obj.ProbeLocation = vector_factory(*settings["ProbeLocation"])
        obj.UseLine = settings["UseLine"]
        obj.LineStart = vector_factory(*settings["LineStart"])
        obj.LineEnd = vector_factory(*settings["LineEnd"])
        obj.LineResolution = settings["LineResolution"]
        obj.SampleFields = list(settings["SampleFields"])
        obj.ExportCSV = settings["ExportCSV"]
        obj.TimeSeries = settings["TimeSeries"]