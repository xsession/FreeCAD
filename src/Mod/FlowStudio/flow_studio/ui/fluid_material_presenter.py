# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Presenter and view-state helpers for the FlowStudio fluid material panel."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FluidMaterialSettings:
    references: tuple
    preset: str
    density: float
    dynamic_viscosity: float
    kinematic_viscosity: float
    specific_heat: float
    thermal_conductivity: float
    prandtl_number: float


class FluidMaterialPresenter:
    """Frontend-neutral presenter for fluid material validation and persistence."""

    def __init__(self, service=None):
        if service is None:
            from flow_studio.app import FlowStudioFluidMaterialService

            service = FlowStudioFluidMaterialService()
        self._service = service

    def read_settings(self, obj):
        payload = self._service.read_settings(obj)
        return FluidMaterialSettings(
            references=tuple(payload["References"]),
            preset=str(payload["Preset"]),
            density=float(payload["Density"]),
            dynamic_viscosity=float(payload["DynamicViscosity"]),
            kinematic_viscosity=float(payload["KinematicViscosity"]),
            specific_heat=float(payload["SpecificHeat"]),
            thermal_conductivity=float(payload["ThermalConductivity"]),
            prandtl_number=float(payload["PrandtlNumber"]),
        )

    def preset_names(self):
        presets = sorted(set(self._service.material_db()))
        if "Custom" in presets:
            presets.remove("Custom")
        return ["Custom"] + presets

    def apply_preset(self, settings, preset_name):
        material = self._service.material_db().get(preset_name)
        if not material:
            return settings
        return FluidMaterialSettings(
            references=settings.references,
            preset=settings.preset,
            density=float(material["Density"]),
            dynamic_viscosity=float(material["DynamicViscosity"]),
            kinematic_viscosity=float(material["KinematicViscosity"]),
            specific_heat=float(material["SpecificHeat"]),
            thermal_conductivity=float(material["ThermalConductivity"]),
            prandtl_number=float(material["PrandtlNumber"]),
        )

    def persist_settings(self, obj, settings):
        self._service.persist_settings(
            obj,
            {
                "Preset": settings.preset,
                "Density": settings.density,
                "DynamicViscosity": settings.dynamic_viscosity,
                "KinematicViscosity": settings.kinematic_viscosity,
                "SpecificHeat": settings.specific_heat,
                "ThermalConductivity": settings.thermal_conductivity,
                "PrandtlNumber": settings.prandtl_number,
            },
        )

    def build_validation(self, settings):
        if not settings.references:
            return (
                "incomplete",
                "Assign fluid regions",
                "Select one or more fluid regions so this material assignment applies to geometry.",
            )

        if settings.density <= 0.0:
            return (
                "incomplete",
                "Fluid density required",
                "Enter a positive density before solving with this fluid material.",
            )

        if settings.dynamic_viscosity <= 0.0:
            return (
                "incomplete",
                "Dynamic viscosity required",
                "Enter a positive dynamic viscosity for this fluid material.",
            )

        if settings.specific_heat <= 0.0:
            return (
                "warning",
                "Specific heat should be positive",
                "Use a positive specific heat so thermal solves have a valid fluid heat capacity.",
            )

        return ("", "", "")