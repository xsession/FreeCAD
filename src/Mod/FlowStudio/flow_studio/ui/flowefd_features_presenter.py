# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Presenters for FloEFD-style FlowStudio feature task panels."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class VolumeSourceSettings:
    references: tuple
    source_type: str
    heat_power_density: float
    mass_source: float
    create_associated_goals: bool


@dataclass(frozen=True)
class FanSettings:
    references: tuple
    fan_type: str
    fan_curve_preset: str
    reference_pressure: float
    create_associated_goals: bool


@dataclass(frozen=True)
class ResultPlotSettings:
    references: tuple
    plot_kind: str
    field: str
    contour_count: int
    contours: bool
    isolines: bool
    vectors: bool
    streamlines: bool
    cut_plane: str
    plane_offset: float
    use_cad_geometry: bool
    interpolate: bool
    export_excel: bool


@dataclass(frozen=True)
class ParticleStudySettings:
    injections: tuple
    accretion: bool
    erosion: bool
    gravity: bool
    gravity_vector: tuple
    particle_shape: str
    particle_diameter: float
    color_by_field: str
    track_length: float
    track_time: float
    max_particles: int


class VolumeSourcePresenter:
    def __init__(self, service=None):
        if service is None:
            from flow_studio.app import FlowStudioVolumeSourceService

            service = FlowStudioVolumeSourceService()
        self._service = service

    def read_settings(self, obj):
        payload = self._service.read_settings(obj)
        return VolumeSourceSettings(
            references=tuple(payload["References"]),
            source_type=str(payload["SourceType"]),
            heat_power_density=float(payload["HeatPowerDensity"]),
            mass_source=float(payload["MassSource"]),
            create_associated_goals=bool(payload["CreateAssociatedGoals"]),
        )

    def persist_settings(self, obj, settings):
        self._service.persist_settings(
            obj,
            {
                "SourceType": settings.source_type,
                "HeatPowerDensity": settings.heat_power_density,
                "MassSource": settings.mass_source,
                "CreateAssociatedGoals": settings.create_associated_goals,
            },
        )


class FanPresenter:
    def __init__(self, service=None):
        if service is None:
            from flow_studio.app import FlowStudioFanService

            service = FlowStudioFanService()
        self._service = service

    def read_settings(self, obj):
        payload = self._service.read_settings(obj)
        return FanSettings(
            references=tuple(payload["References"]),
            fan_type=str(payload["FanType"]),
            fan_curve_preset=str(payload["FanCurvePreset"]),
            reference_pressure=float(payload["ReferencePressure"]),
            create_associated_goals=bool(payload["CreateAssociatedGoals"]),
        )

    def persist_settings(self, obj, settings):
        self._service.persist_settings(
            obj,
            {
                "FanType": settings.fan_type,
                "FanCurvePreset": settings.fan_curve_preset,
                "ReferencePressure": settings.reference_pressure,
                "CreateAssociatedGoals": settings.create_associated_goals,
            },
        )

    def build_curve_state(self, name, fan_database):
        data = fan_database.get(name, {})
        return {
            "FanType": str(data.get("FanType", "")) if "FanType" in data else None,
            "ReferencePressure": float(data["ReferencePressure"]) if "ReferencePressure" in data else None,
            "Curve": [(str(flow), str(pressure)) for flow, pressure in data.get("curve", [])],
        }


class ResultPlotPresenter:
    def __init__(self, service=None):
        if service is None:
            from flow_studio.app import FlowStudioResultPlotService

            service = FlowStudioResultPlotService()
        self._service = service

    def read_settings(self, obj):
        payload = self._service.read_settings(obj)
        return ResultPlotSettings(
            references=tuple(payload["References"]),
            plot_kind=str(payload["PlotKind"]),
            field=str(payload["Field"]),
            contour_count=int(payload["ContourCount"]),
            contours=bool(payload["Contours"]),
            isolines=bool(payload["Isolines"]),
            vectors=bool(payload["Vectors"]),
            streamlines=bool(payload["Streamlines"]),
            cut_plane=str(payload["CutPlane"]),
            plane_offset=float(payload["PlaneOffset"]),
            use_cad_geometry=bool(payload["UseCADGeometry"]),
            interpolate=bool(payload["Interpolate"]),
            export_excel=bool(payload["ExportExcel"]),
        )

    def persist_settings(self, obj, settings):
        self._service.persist_settings(
            obj,
            {
                "PlotKind": settings.plot_kind,
                "Field": settings.field,
                "ContourCount": settings.contour_count,
                "Contours": settings.contours,
                "Isolines": settings.isolines,
                "Vectors": settings.vectors,
                "Streamlines": settings.streamlines,
                "CutPlane": settings.cut_plane,
                "PlaneOffset": settings.plane_offset,
                "UseCADGeometry": settings.use_cad_geometry,
                "Interpolate": settings.interpolate,
                "ExportExcel": settings.export_excel,
            },
        )

    def build_validation(self, settings):
        if not settings.references:
            return (
                "incomplete",
                "Assign plot targets",
                "Select faces, parts, or seed locations before creating a result plot.",
            )

        if not settings.field.strip():
            return (
                "incomplete",
                "Result field required",
                "Choose the field this result plot should visualize.",
            )

        if not any((settings.contours, settings.isolines, settings.vectors, settings.streamlines)):
            return (
                "warning",
                "Enable a display mode",
                "Turn on at least one display style such as contours, isolines, vectors, or streamlines.",
            )

        return ("", "", "")


class ParticleStudyPresenter:
    def __init__(self, service=None):
        if service is None:
            from flow_studio.app import FlowStudioParticleStudyService

            service = FlowStudioParticleStudyService()
        self._service = service

    def read_settings(self, obj):
        payload = self._service.read_settings(obj)
        return ParticleStudySettings(
            injections=tuple(payload["Injections"]),
            accretion=bool(payload["Accretion"]),
            erosion=bool(payload["Erosion"]),
            gravity=bool(payload["Gravity"]),
            gravity_vector=tuple(payload["GravityVector"]),
            particle_shape=str(payload["ParticleShape"]),
            particle_diameter=float(payload["ParticleDiameter"]),
            color_by_field=str(payload["ColorByField"]),
            track_length=float(payload["TrackLength"]),
            track_time=float(payload["TrackTime"]),
            max_particles=int(payload["MaxParticles"]),
        )

    def persist_settings(self, obj, settings, vector_factory):
        self._service.persist_settings(
            obj,
            {
                "Accretion": settings.accretion,
                "Erosion": settings.erosion,
                "Gravity": settings.gravity,
                "GravityVector": settings.gravity_vector,
                "ParticleShape": settings.particle_shape,
                "ParticleDiameter": settings.particle_diameter,
                "ColorByField": settings.color_by_field,
                "TrackLength": settings.track_length,
                "TrackTime": settings.track_time,
                "MaxParticles": settings.max_particles,
            },
            vector_factory,
        )

    def build_validation(self, settings):
        if not settings.injections:
            return (
                "incomplete",
                "Assign particle injections",
                "Select one or more injection faces, edges, or seed regions before configuring a particle study.",
            )

        if settings.gravity and settings.gravity_vector == (0.0, 0.0, 0.0):
            return (
                "warning",
                "Gravity vector is zero",
                "Use a non-zero gravity vector or disable gravity for this particle study.",
            )

        if settings.particle_diameter <= 0.0:
            return (
                "warning",
                "Particle diameter required",
                "Enter a positive particle diameter before tracing particles.",
            )

        if settings.track_length <= 0.0 or settings.track_time <= 0.0:
            return (
                "warning",
                "Tracking limits required",
                "Set positive tracking length and time limits before running the particle study.",
            )

        return ("", "", "")