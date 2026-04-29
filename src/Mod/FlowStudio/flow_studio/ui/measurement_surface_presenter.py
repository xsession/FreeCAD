# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Presenter and view-state helpers for surface measurement panels."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MeasurementSurfaceSettings:
    label2: str
    surface_type: str
    plane_origin: tuple
    plane_normal: str
    custom_normal: tuple
    iso_field: str
    iso_value: float
    sample_fields: tuple
    compute_average: bool
    compute_integral: bool
    compute_mass_flow: bool
    compute_force: bool
    force_ref_point: tuple
    export_csv: bool
    export_vtk: bool
    time_series: bool
    face_refs: tuple


class MeasurementSurfacePresenter:
    """Frontend-neutral presenter for measurement-surface validation and persistence."""

    def __init__(self, service=None):
        if service is None:
            from flow_studio.app import FlowStudioMeasurementSurfaceService

            service = FlowStudioMeasurementSurfaceService()
        self._service = service

    def read_settings(self, obj):
        payload = self._service.read_settings(obj)
        return MeasurementSurfaceSettings(
            label2=str(payload["Label2"]),
            surface_type=str(payload["SurfaceType"]),
            plane_origin=tuple(payload["PlaneOrigin"]),
            plane_normal=str(payload["PlaneNormal"]),
            custom_normal=tuple(payload["CustomNormal"]),
            iso_field=str(payload["IsoField"]),
            iso_value=float(payload["IsoValue"]),
            sample_fields=tuple(payload["SampleFields"]),
            compute_average=bool(payload["ComputeAverage"]),
            compute_integral=bool(payload["ComputeIntegral"]),
            compute_mass_flow=bool(payload["ComputeMassFlow"]),
            compute_force=bool(payload["ComputeForce"]),
            force_ref_point=tuple(payload["ForceRefPoint"]),
            export_csv=bool(payload["ExportCSV"]),
            export_vtk=bool(payload["ExportVTK"]),
            time_series=bool(payload["TimeSeries"]),
            face_refs=tuple(payload["FaceRefs"]),
        )

    def persist_settings(self, obj, settings, vector_factory):
        self._service.persist_settings(
            obj,
            {
                "Label2": settings.label2,
                "SurfaceType": settings.surface_type,
                "PlaneOrigin": settings.plane_origin,
                "PlaneNormal": settings.plane_normal,
                "CustomNormal": settings.custom_normal,
                "IsoField": settings.iso_field,
                "IsoValue": settings.iso_value,
                "SampleFields": settings.sample_fields,
                "ComputeAverage": settings.compute_average,
                "ComputeIntegral": settings.compute_integral,
                "ComputeMassFlow": settings.compute_mass_flow,
                "ComputeForce": settings.compute_force,
                "ForceRefPoint": settings.force_ref_point,
                "ExportCSV": settings.export_csv,
                "ExportVTK": settings.export_vtk,
                "TimeSeries": settings.time_series,
            },
            vector_factory,
        )

    def build_validation(self, settings):
        if not settings.sample_fields:
            return (
                "incomplete",
                "Select sampled fields",
                "Enter at least one field name so the surface measurement produces useful results.",
            )

        if settings.surface_type == "Iso-Surface" and not settings.iso_field.strip():
            return (
                "incomplete",
                "Iso field required",
                "Choose the scalar field used to define the iso-surface before exporting or evaluating it.",
            )

        if settings.surface_type == "Geometry Faces" and not settings.face_refs:
            return (
                "incomplete",
                "Assign geometry faces",
                "Pick one or more geometry faces when using a face-based measurement surface.",
            )

        if settings.plane_normal == "Custom" and settings.custom_normal == (0.0, 0.0, 0.0):
            return (
                "warning",
                "Custom normal cannot be zero",
                "Set a non-zero custom normal vector so the cut or clip direction is defined.",
            )

        if not any((
            settings.compute_average,
            settings.compute_integral,
            settings.compute_mass_flow,
            settings.compute_force,
        )):
            return (
                "warning",
                "Select an evaluation output",
                "Enable at least one surface evaluation such as average, integral, mass flow, or force.",
            )

        return ("", "", "")