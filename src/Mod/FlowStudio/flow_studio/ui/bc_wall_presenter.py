# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Presenter and view-state helpers for the FlowStudio wall-boundary panel."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WallBoundarySettings:
    references: tuple
    wall_type: str
    thermal_type: str
    wall_temperature: float
    heat_flux: float
    heat_transfer_coeff: float
    roughness_height: float


class WallBoundaryPresenter:
    """Frontend-neutral presenter for wall-boundary validation and persistence."""

    def __init__(self, service=None):
        if service is None:
            from flow_studio.app import FlowStudioWallBoundaryService

            service = FlowStudioWallBoundaryService()
        self._service = service

    def read_settings(self, obj):
        payload = self._service.read_settings(obj)
        return WallBoundarySettings(
            references=tuple(payload["References"]),
            wall_type=str(payload["WallType"]),
            thermal_type=str(payload["ThermalType"]),
            wall_temperature=float(payload["WallTemperature"]),
            heat_flux=float(payload["HeatFlux"]),
            heat_transfer_coeff=float(payload["HeatTransferCoeff"]),
            roughness_height=float(payload["RoughnessHeight"]),
        )

    def persist_settings(self, obj, settings):
        self._service.persist_settings(
            obj,
            {
                "WallType": settings.wall_type,
                "ThermalType": settings.thermal_type,
                "WallTemperature": settings.wall_temperature,
                "HeatFlux": settings.heat_flux,
                "HeatTransferCoeff": settings.heat_transfer_coeff,
                "RoughnessHeight": settings.roughness_height,
            },
        )

    def build_validation(self, settings):
        if not settings.references:
            return (
                "incomplete",
                "Assign wall faces",
                "Select one or more wall faces so this boundary condition applies to geometry.",
            )

        if settings.thermal_type == "Fixed Temperature" and settings.wall_temperature <= 0.0:
            return (
                "incomplete",
                "Wall temperature required",
                "Enter a positive wall temperature in kelvin for a fixed-temperature wall.",
            )

        if settings.thermal_type == "Heat Transfer Coefficient" and settings.heat_transfer_coeff <= 0.0:
            return (
                "incomplete",
                "Heat-transfer coefficient required",
                "Enter a positive heat-transfer coefficient before solving with this wall mode.",
            )

        if settings.wall_type == "Rough Wall" and settings.roughness_height <= 0.0:
            return (
                "incomplete",
                "Wall roughness required",
                "Enter a positive roughness height before solving with a rough-wall boundary.",
            )

        return ("", "", "")