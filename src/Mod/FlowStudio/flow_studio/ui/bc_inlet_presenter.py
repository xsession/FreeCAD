# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Presenter and view-state helpers for the FlowStudio inlet-boundary panel."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class InletBoundarySettings:
    references: tuple
    inlet_type: str
    velocity_x: float
    velocity_y: float
    velocity_z: float
    normal_to_face: bool
    mass_flow_rate: float
    volumetric_flow_rate: float
    turbulence_spec: str
    turbulence_intensity: float
    inlet_temperature: float


class InletBoundaryPresenter:
    """Frontend-neutral presenter for inlet-boundary validation and persistence."""

    def __init__(self, service=None):
        if service is None:
            from flow_studio.app import FlowStudioInletBoundaryService

            service = FlowStudioInletBoundaryService()
        self._service = service

    def read_settings(self, obj):
        payload = self._service.read_settings(obj)
        return InletBoundarySettings(
            references=tuple(payload["References"]),
            inlet_type=str(payload["InletType"]),
            velocity_x=float(payload["Ux"]),
            velocity_y=float(payload["Uy"]),
            velocity_z=float(payload["Uz"]),
            normal_to_face=bool(payload["NormalToFace"]),
            mass_flow_rate=float(payload["MassFlowRate"]),
            volumetric_flow_rate=float(payload["VolFlowRate"]),
            turbulence_spec=str(payload["TurbulenceSpec"]),
            turbulence_intensity=float(payload["TurbulenceIntensity"]),
            inlet_temperature=float(payload["InletTemperature"]),
        )

    def persist_settings(self, obj, settings):
        self._service.persist_settings(
            obj,
            {
                "InletType": settings.inlet_type,
                "Ux": settings.velocity_x,
                "Uy": settings.velocity_y,
                "Uz": settings.velocity_z,
                "NormalToFace": settings.normal_to_face,
                "MassFlowRate": settings.mass_flow_rate,
                "VolFlowRate": settings.volumetric_flow_rate,
                "TurbulenceSpec": settings.turbulence_spec,
                "TurbulenceIntensity": settings.turbulence_intensity,
                "InletTemperature": settings.inlet_temperature,
            },
        )

    def build_validation(self, settings):
        if not settings.references:
            return (
                "incomplete",
                "Assign inlet faces",
                "Select one or more boundary faces so this inlet can be applied to geometry.",
            )

        if settings.inlet_type == "Mass Flow Rate" and settings.mass_flow_rate <= 0.0:
            return (
                "incomplete",
                "Mass flow rate required",
                "Enter a positive mass flow rate before solving with this inlet.",
            )

        if settings.inlet_type == "Volumetric Flow Rate" and settings.volumetric_flow_rate <= 0.0:
            return (
                "incomplete",
                "Volumetric flow rate required",
                "Enter a positive volumetric flow rate before solving with this inlet.",
            )

        return ("", "", "")