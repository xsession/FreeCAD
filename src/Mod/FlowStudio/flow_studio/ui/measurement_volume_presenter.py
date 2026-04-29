# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Presenter and view-state helpers for volume measurement panels."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MeasurementVolumeSettings:
    label2: str
    volume_type: str
    box_min: tuple
    box_max: tuple
    sphere_center: tuple
    sphere_radius: float
    cylinder_center: tuple
    cylinder_axis: tuple
    cylinder_radius: float
    cylinder_height: float
    threshold_field: str
    threshold_min: float
    threshold_max: float
    sample_fields: tuple
    compute_average: bool
    compute_min_max: bool
    compute_integral: bool
    export_csv: bool
    time_series: bool


class MeasurementVolumePresenter:
    """Frontend-neutral presenter for measurement-volume validation and persistence."""

    def __init__(self, service=None):
        if service is None:
            from flow_studio.app import FlowStudioMeasurementVolumeService

            service = FlowStudioMeasurementVolumeService()
        self._service = service

    def read_settings(self, obj):
        payload = self._service.read_settings(obj)
        return MeasurementVolumeSettings(
            label2=str(payload["Label2"]),
            volume_type=str(payload["VolumeType"]),
            box_min=tuple(payload["BoxMin"]),
            box_max=tuple(payload["BoxMax"]),
            sphere_center=tuple(payload["SphereCenter"]),
            sphere_radius=float(payload["SphereRadius"]),
            cylinder_center=tuple(payload["CylinderCenter"]),
            cylinder_axis=tuple(payload["CylinderAxis"]),
            cylinder_radius=float(payload["CylinderRadius"]),
            cylinder_height=float(payload["CylinderHeight"]),
            threshold_field=str(payload["ThresholdField"]),
            threshold_min=float(payload["ThresholdMin"]),
            threshold_max=float(payload["ThresholdMax"]),
            sample_fields=tuple(payload["SampleFields"]),
            compute_average=bool(payload["ComputeAverage"]),
            compute_min_max=bool(payload["ComputeMinMax"]),
            compute_integral=bool(payload["ComputeIntegral"]),
            export_csv=bool(payload["ExportCSV"]),
            time_series=bool(payload["TimeSeries"]),
        )

    def persist_settings(self, obj, settings, vector_factory):
        self._service.persist_settings(
            obj,
            {
                "Label2": settings.label2,
                "VolumeType": settings.volume_type,
                "BoxMin": settings.box_min,
                "BoxMax": settings.box_max,
                "SphereCenter": settings.sphere_center,
                "SphereRadius": settings.sphere_radius,
                "CylinderCenter": settings.cylinder_center,
                "CylinderAxis": settings.cylinder_axis,
                "CylinderRadius": settings.cylinder_radius,
                "CylinderHeight": settings.cylinder_height,
                "ThresholdField": settings.threshold_field,
                "ThresholdMin": settings.threshold_min,
                "ThresholdMax": settings.threshold_max,
                "SampleFields": settings.sample_fields,
                "ComputeAverage": settings.compute_average,
                "ComputeMinMax": settings.compute_min_max,
                "ComputeIntegral": settings.compute_integral,
                "ExportCSV": settings.export_csv,
                "TimeSeries": settings.time_series,
            },
            vector_factory,
        )

    def build_validation(self, settings):
        if not settings.sample_fields:
            return (
                "incomplete",
                "Select sampled fields",
                "Enter at least one field name so the volume measurement has data to evaluate.",
            )

        if settings.volume_type == "Box":
            if not (
                settings.box_min[0] < settings.box_max[0]
                and settings.box_min[1] < settings.box_max[1]
                and settings.box_min[2] < settings.box_max[2]
            ):
                return (
                    "warning",
                    "Box limits are invalid",
                    "Set each minimum corner value below its corresponding maximum value.",
                )

        if settings.volume_type == "Sphere" and settings.sphere_radius <= 0.0:
            return (
                "warning",
                "Sphere radius required",
                "Enter a positive sphere radius before evaluating this volume measurement.",
            )

        if settings.volume_type == "Cylinder":
            if settings.cylinder_axis == (0.0, 0.0, 0.0):
                return (
                    "warning",
                    "Cylinder axis cannot be zero",
                    "Set a non-zero cylinder axis vector so the volume orientation is defined.",
                )
            if settings.cylinder_radius <= 0.0 or settings.cylinder_height <= 0.0:
                return (
                    "warning",
                    "Cylinder size required",
                    "Enter positive cylinder radius and height values before evaluating this region.",
                )

        if settings.volume_type == "Threshold (field-based)":
            if not settings.threshold_field.strip():
                return (
                    "incomplete",
                    "Threshold field required",
                    "Choose the field used to create the threshold-based measurement region.",
                )
            if settings.threshold_min >= settings.threshold_max:
                return (
                    "warning",
                    "Threshold range is invalid",
                    "Set a threshold minimum smaller than the threshold maximum.",
                )

        if not any((settings.compute_average, settings.compute_min_max, settings.compute_integral)):
            return (
                "warning",
                "Select a statistic to compute",
                "Enable at least one evaluation output such as average, min/max, or integral.",
            )

        return ("", "", "")