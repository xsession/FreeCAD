# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Presenter and view-state helpers for the FlowStudio initial conditions panel."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class InitialConditionsSettings:
    references: tuple
    ux: float
    uy: float
    uz: float
    pressure: float
    temperature: float
    turbulent_kinetic_energy: float
    specific_dissipation_rate: float
    use_potential_flow: bool


class InitialConditionsPresenter:
    """Frontend-neutral presenter for initial conditions validation and persistence."""

    def __init__(self, service=None):
        if service is None:
            from flow_studio.app import FlowStudioInitialConditionsService

            service = FlowStudioInitialConditionsService()
        self._service = service

    def read_settings(self, obj):
        payload = self._service.read_settings(obj)
        return InitialConditionsSettings(
            references=tuple(payload["References"]),
            ux=float(payload["Ux"]),
            uy=float(payload["Uy"]),
            uz=float(payload["Uz"]),
            pressure=float(payload["Pressure"]),
            temperature=float(payload["Temperature"]),
            turbulent_kinetic_energy=float(payload["TurbulentKineticEnergy"]),
            specific_dissipation_rate=float(payload["SpecificDissipationRate"]),
            use_potential_flow=bool(payload["UsePotentialFlow"]),
        )

    def persist_settings(self, obj, settings):
        self._service.persist_settings(
            obj,
            {
                "Ux": settings.ux,
                "Uy": settings.uy,
                "Uz": settings.uz,
                "Pressure": settings.pressure,
                "Temperature": settings.temperature,
                "TurbulentKineticEnergy": settings.turbulent_kinetic_energy,
                "SpecificDissipationRate": settings.specific_dissipation_rate,
                "UsePotentialFlow": settings.use_potential_flow,
            },
        )

    def build_validation(self, settings):
        if not settings.references:
            return (
                "incomplete",
                "Assign target regions",
                "Select one or more bodies, faces, or regions so these initial conditions apply somewhere in the model.",
            )

        if settings.temperature <= 0.0:
            return (
                "incomplete",
                "Initial temperature required",
                "Enter a positive starting temperature in kelvin before solving.",
            )

        if settings.turbulent_kinetic_energy < 0.0:
            return (
                "warning",
                "Turbulent kinetic energy cannot be negative",
                "Use zero or a positive k value for turbulence initialization.",
            )

        if settings.specific_dissipation_rate < 0.0:
            return (
                "warning",
                "Specific dissipation rate cannot be negative",
                "Use zero or a positive omega value for turbulence initialization.",
            )

        return ("", "", "")