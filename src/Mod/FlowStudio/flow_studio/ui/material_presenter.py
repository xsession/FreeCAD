# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Presenter and view-state helpers for FlowStudio material task panels."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MaterialSettings:
    flow_type: str
    properties: tuple[str, ...]
    references: tuple
    material_preset: str
    material_name: str
    values: dict[str, float]


class MaterialPresenter:
    """Frontend-neutral presenter for material task-panel behavior."""

    TITLES = {
        "FlowStudio::SolidMaterial": "Solid Material",
        "FlowStudio::ThermalMaterial": "Thermal Material",
        "FlowStudio::ElectrostaticMaterial": "Electrostatic Material",
        "FlowStudio::ElectromagneticMaterial": "Electromagnetic Material",
        "FlowStudio::OpticalMaterial": "Optical Material",
    }

    POSITIVE_REQUIRED = (
        ("Density", "Density must be positive"),
        ("YoungsModulus", "Young's modulus must be positive"),
        ("ThermalConductivity", "Thermal conductivity must be positive"),
        ("SpecificHeat", "Specific heat must be positive"),
        ("RelativePermittivity", "Relative permittivity must be positive"),
        ("RelativePermeability", "Relative permeability must be positive"),
        ("RefractiveIndex", "Refractive index must be positive"),
    )

    def __init__(self, service=None):
        if service is None:
            from flow_studio.app.material_service import FlowStudioMaterialService

            service = FlowStudioMaterialService()
        self._service = service

    def title(self, flow_type):
        return self.TITLES.get(flow_type, "Material")

    def read_settings(self, obj):
        return self._coerce_settings(self._service.read_state(obj))

    def preset_names(self, flow_type):
        return ["Custom"] + sorted(self._service.preset_db(flow_type))

    def apply_preset(self, settings, preset_name):
        preset = self._service.preset_db(settings.flow_type).get(preset_name)
        if not preset:
            return settings
        values = dict(settings.values)
        for name, value in preset.items():
            if name in values:
                values[name] = float(value)
        material_name = settings.material_name
        if "MaterialName" in preset:
            material_name = str(preset["MaterialName"])
        return MaterialSettings(
            flow_type=settings.flow_type,
            properties=settings.properties,
            references=settings.references,
            material_preset=settings.material_preset,
            material_name=material_name,
            values=values,
        )

    def persist_settings(self, obj, settings):
        self._service.persist_state(
            obj,
            {
                "MaterialPreset": settings.material_preset,
                "MaterialName": settings.material_name,
                "Values": dict(settings.values),
            },
        )

    def build_validation(self, settings):
        if not settings.references:
            return (
                "incomplete",
                "Assign material targets",
                "Select one or more parts or regions so this material applies to geometry.",
            )

        if not settings.material_name.strip():
            return (
                "incomplete",
                "Material name required",
                "Enter a material name or choose a preset before continuing.",
            )

        properties = set(settings.properties)
        for prop, title in self.POSITIVE_REQUIRED:
            if prop in properties and float(settings.values.get(prop, 0.0)) <= 0.0:
                return (
                    "warning",
                    title,
                    f"Set a positive {prop} value or choose a preset that provides a valid material property.",
                )

        return ("", "", "")

    def _coerce_settings(self, payload):
        properties = tuple(payload["PropertiesList"])
        values = {}
        for name in properties:
            if name in {"References", "MaterialPreset", "MaterialName"}:
                continue
            value = payload.get(name)
            if isinstance(value, (int, float)):
                values[name] = float(value)
        return MaterialSettings(
            flow_type=str(payload["FlowType"]),
            properties=properties,
            references=tuple(payload["References"]),
            material_preset=str(payload.get("MaterialPreset", "Custom") or "Custom"),
            material_name=str(payload.get("MaterialName", "") or ""),
            values=values,
        )