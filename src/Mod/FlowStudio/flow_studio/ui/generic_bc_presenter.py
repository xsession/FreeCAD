# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Presenter and view-state helpers for generic FlowStudio boundary panels."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GenericBoundarySettings:
    title: str
    flow_type: str
    references: tuple
    values: dict


class GenericBoundaryPresenter:
    """Frontend-neutral presenter for generic boundary validation and persistence."""

    def __init__(self, service=None):
        if service is None:
            from flow_studio.app import FlowStudioGenericBoundaryService

            service = FlowStudioGenericBoundaryService()
        self._service = service

    def read_settings(self, obj, field_names):
        payload = self._service.read_settings(obj, field_names)
        return GenericBoundarySettings(
            title=str(payload["Title"]),
            flow_type=str(payload["FlowType"]),
            references=tuple(payload["References"]),
            values=dict(payload["Values"]),
        )

    def persist_settings(self, obj, settings):
        self._service.persist_settings(obj, settings.values)

    def build_validation(self, settings):
        if not settings.references:
            return (
                "incomplete",
                "Assign boundary targets",
                "Select one or more faces, bodies, or regions so this boundary condition applies to geometry.",
            )

        title = settings.title
        values = settings.values

        if "Temperature" in values and float(values["Temperature"]) <= 0.0:
            return (
                "warning",
                f"{title} temperature required",
                "Enter a positive temperature in kelvin before using this thermal boundary condition.",
            )

        if "AmbientTemperature" in values and float(values["AmbientTemperature"]) <= 0.0:
            return (
                "warning",
                f"{title} ambient temperature required",
                "Enter a positive ambient temperature in kelvin before solving.",
            )

        if "HeatTransferCoefficient" in values and float(values["HeatTransferCoefficient"]) <= 0.0:
            return (
                "warning",
                f"{title} coefficient required",
                "Enter a positive heat-transfer coefficient for this convection boundary condition.",
            )

        if "Emissivity" in values and not 0.0 <= float(values["Emissivity"]) <= 1.0:
            return (
                "warning",
                f"{title} emissivity out of range",
                "Keep emissivity between 0 and 1 for this radiation boundary condition.",
            )

        return ("", "", "")