# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Presenter and view-state helpers for the FlowStudio open-boundary panel."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class OpenBoundarySettings:
    references: tuple
    far_field_pressure: float
    far_field_temperature: float
    far_field_velocity_x: float
    far_field_velocity_y: float
    far_field_velocity_z: float


class OpenBoundaryPresenter:
    """Frontend-neutral presenter for open boundary validation and persistence."""

    def __init__(self, service=None):
        if service is None:
            from flow_studio.app import FlowStudioOpenBoundaryService

            service = FlowStudioOpenBoundaryService()
        self._service = service

    def read_settings(self, obj):
        payload = self._service.read_settings(obj)
        return OpenBoundarySettings(
            references=tuple(payload["References"]),
            far_field_pressure=float(payload["FarFieldPressure"]),
            far_field_temperature=float(payload["FarFieldTemperature"]),
            far_field_velocity_x=float(payload["FarFieldVelocityX"]),
            far_field_velocity_y=float(payload["FarFieldVelocityY"]),
            far_field_velocity_z=float(payload["FarFieldVelocityZ"]),
        )

    def persist_settings(self, obj, settings):
        self._service.persist_settings(
            obj,
            {
                "FarFieldPressure": settings.far_field_pressure,
                "FarFieldTemperature": settings.far_field_temperature,
                "FarFieldVelocityX": settings.far_field_velocity_x,
                "FarFieldVelocityY": settings.far_field_velocity_y,
                "FarFieldVelocityZ": settings.far_field_velocity_z,
            },
        )

    def build_validation(self, settings):
        if not settings.references:
            return (
                "incomplete",
                "Assign open-boundary faces",
                "Select one or more exterior faces so the far-field condition can be applied.",
            )

        if settings.far_field_temperature <= 0.0:
            return (
                "incomplete",
                "Far-field temperature required",
                "Enter a positive far-field temperature in kelvin before solving with this boundary.",
            )

        return ("", "", "")