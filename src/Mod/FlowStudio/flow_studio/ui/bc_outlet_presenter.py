# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Presenter and view-state helpers for the FlowStudio outlet-boundary panel."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class OutletBoundarySettings:
    references: tuple
    outlet_type: str
    static_pressure: float
    mass_flow_rate: float
    prevent_backflow: bool


class OutletBoundaryPresenter:
    """Frontend-neutral presenter for outlet-boundary validation and persistence."""

    def __init__(self, service=None):
        if service is None:
            from flow_studio.app import FlowStudioOutletBoundaryService

            service = FlowStudioOutletBoundaryService()
        self._service = service

    def read_settings(self, obj):
        payload = self._service.read_settings(obj)
        return OutletBoundarySettings(
            references=tuple(payload["References"]),
            outlet_type=str(payload["OutletType"]),
            static_pressure=float(payload["StaticPressure"]),
            mass_flow_rate=float(payload["OutletMassFlowRate"]),
            prevent_backflow=bool(payload["PreventBackflow"]),
        )

    def persist_settings(self, obj, settings):
        self._service.persist_settings(
            obj,
            {
                "OutletType": settings.outlet_type,
                "StaticPressure": settings.static_pressure,
                "OutletMassFlowRate": settings.mass_flow_rate,
                "PreventBackflow": settings.prevent_backflow,
            },
        )

    def build_validation(self, settings):
        if not settings.references:
            return (
                "incomplete",
                "Assign outlet faces",
                "Select one or more outlet faces so the exit condition is attached to geometry.",
            )

        if settings.outlet_type == "Mass Flow Rate" and settings.mass_flow_rate <= 0.0:
            return (
                "incomplete",
                "Outlet mass flow rate required",
                "Enter a positive outlet mass flow rate before solving with this outlet mode.",
            )

        return ("", "", "")