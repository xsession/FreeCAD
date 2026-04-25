# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Presenter and view-state helpers for the FlowStudio post-pipeline panel."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PostPipelineSettings:
    visualization_type: str
    active_field: str
    auto_range: bool
    min_range: float
    max_range: float
    available_fields: tuple[str, ...]
    result_file: str


class PostPipelinePresenter:
    """Frontend-neutral presenter for post-pipeline validation and persistence."""

    def __init__(self, service=None):
        if service is None:
            from flow_studio.app import FlowStudioPostPipelineService

            service = FlowStudioPostPipelineService()
        self._service = service

    def read_settings(self, obj):
        payload = self._service.read_settings(obj)
        return PostPipelineSettings(
            visualization_type=str(payload["VisualizationType"]),
            active_field=str(payload["ActiveField"]),
            auto_range=bool(payload["AutoRange"]),
            min_range=float(payload["MinRange"]),
            max_range=float(payload["MaxRange"]),
            available_fields=tuple(str(field) for field in (payload["AvailableFields"] or [])),
            result_file=str(payload["ResultFile"] or ""),
        )

    def persist_settings(self, obj, settings):
        self._service.persist_settings(
            obj,
            {
                "VisualizationType": settings.visualization_type,
                "ActiveField": settings.active_field,
                "AutoRange": settings.auto_range,
                "MinRange": settings.min_range,
                "MaxRange": settings.max_range,
            },
        )

    def build_validation(self, settings):
        if not settings.result_file.strip() and not settings.available_fields:
            return (
                "info",
                "Load results to begin post-processing",
                "Choose a result file or run the solver so fields become available for visualization.",
            )

        if settings.available_fields and settings.active_field not in settings.available_fields:
            return (
                "warning",
                "Active field is not available",
                "Select one of the loaded result fields before updating the post-processing view.",
            )

        if not settings.auto_range and settings.min_range >= settings.max_range:
            return (
                "warning",
                "Manual range is invalid",
                "Set a minimum value smaller than the maximum value or re-enable automatic range.",
            )

        return ("", "", "")