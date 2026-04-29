# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Presenter and view-state helpers for point measurement panels."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MeasurementPointSettings:
    label2: str
    probe_location: tuple
    use_line: bool
    line_start: tuple
    line_end: tuple
    line_resolution: int
    sample_fields: tuple
    export_csv: bool
    time_series: bool


class MeasurementPointPresenter:
    """Frontend-neutral presenter for measurement-point validation and persistence."""

    def __init__(self, service=None):
        if service is None:
            from flow_studio.app import FlowStudioMeasurementPointService

            service = FlowStudioMeasurementPointService()
        self._service = service

    def read_settings(self, obj):
        payload = self._service.read_settings(obj)
        return MeasurementPointSettings(
            label2=str(payload["Label2"]),
            probe_location=tuple(payload["ProbeLocation"]),
            use_line=bool(payload["UseLine"]),
            line_start=tuple(payload["LineStart"]),
            line_end=tuple(payload["LineEnd"]),
            line_resolution=int(payload["LineResolution"]),
            sample_fields=tuple(payload["SampleFields"]),
            export_csv=bool(payload["ExportCSV"]),
            time_series=bool(payload["TimeSeries"]),
        )

    def persist_settings(self, obj, settings, vector_factory):
        self._service.persist_settings(
            obj,
            {
                "Label2": settings.label2,
                "ProbeLocation": settings.probe_location,
                "UseLine": settings.use_line,
                "LineStart": settings.line_start,
                "LineEnd": settings.line_end,
                "LineResolution": settings.line_resolution,
                "SampleFields": settings.sample_fields,
                "ExportCSV": settings.export_csv,
                "TimeSeries": settings.time_series,
            },
            vector_factory,
        )

    def build_validation(self, settings):
        if not settings.sample_fields:
            return (
                "incomplete",
                "Select sampled fields",
                "Enter at least one field name such as U, p, or T so the probe captures useful data.",
            )

        if settings.use_line and settings.line_start == settings.line_end:
            return (
                "warning",
                "Line probe needs distinct endpoints",
                "Move the line end point away from the start point so the probe spans a real path.",
            )

        return ("", "", "")