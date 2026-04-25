# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Presenter and view-state helpers for the FlowStudio physics model panel."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PhysicsModelSettings:
    flow_regime: str
    turbulence_model: str
    compressibility: str
    time_model: str
    gravity: bool
    heat_transfer: bool
    buoyancy: bool
    free_surface: bool
    passive_scalar: bool


class PhysicsModelPresenter:
    """Frontend-neutral presenter for physics model validation and persistence."""

    def __init__(self, service=None):
        if service is None:
            from flow_studio.app import FlowStudioPhysicsModelService

            service = FlowStudioPhysicsModelService()
        self._service = service

    def read_settings(self, obj):
        payload = self._service.read_settings(obj)
        return PhysicsModelSettings(
            flow_regime=str(payload["FlowRegime"]),
            turbulence_model=str(payload["TurbulenceModel"]),
            compressibility=str(payload["Compressibility"]),
            time_model=str(payload["TimeModel"]),
            gravity=bool(payload["Gravity"]),
            heat_transfer=bool(payload["HeatTransfer"]),
            buoyancy=bool(payload["Buoyancy"]),
            free_surface=bool(payload["FreeSurface"]),
            passive_scalar=bool(payload["PassiveScalar"]),
        )

    def persist_settings(self, obj, settings):
        self._service.persist_settings(
            obj,
            {
                "FlowRegime": settings.flow_regime,
                "TurbulenceModel": settings.turbulence_model,
                "Compressibility": settings.compressibility,
                "TimeModel": settings.time_model,
                "Gravity": settings.gravity,
                "HeatTransfer": settings.heat_transfer,
                "Buoyancy": settings.buoyancy,
                "FreeSurface": settings.free_surface,
                "PassiveScalar": settings.passive_scalar,
            },
        )

    def build_validation(self, settings):
        if settings.buoyancy and not settings.gravity:
            return (
                "warning",
                "Buoyancy needs gravity",
                "Enable gravity when buoyancy is active so the body-force direction is defined.",
            )

        if settings.buoyancy and not settings.heat_transfer:
            return (
                "warning",
                "Buoyancy usually needs heat transfer",
                "Enable heat transfer when buoyancy is active so density variation has a thermal driver.",
            )

        if settings.flow_regime == "Laminar" and settings.turbulence_model != "kOmegaSST":
            return (
                "info",
                "Laminar flow selected",
                "The turbulence model is currently not driving the solve because the flow regime is laminar.",
            )

        return ("", "", "")