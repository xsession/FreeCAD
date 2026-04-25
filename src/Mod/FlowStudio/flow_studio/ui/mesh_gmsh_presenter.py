# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Presenter and view-state helpers for the Gmsh mesh task panel."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MeshGmshSettings:
    characteristic_length: float
    min_element_size: float
    max_element_size: float
    algorithm_3d: str
    element_order: str
    element_type: str
    growth_rate: float
    cells_in_gap: int
    mesh_format: str


@dataclass(frozen=True)
class MeshGmshRunState:
    status: str
    stats_text: str
    console_message: str = ""
    dialog_title: str = ""
    dialog_message: str = ""
    show_warning: bool = False


class MeshGmshPresenter:
    """Frontend-neutral presenter for mesh validation, persistence, and execution."""

    def __init__(self, service=None):
        if service is None:
            from flow_studio.app import FlowStudioMeshGmshService

            service = FlowStudioMeshGmshService()
        self._service = service

    def read_settings(self, obj):
        return self._coerce_settings(self._service.read_settings(obj))

    def persist_settings(self, obj, settings):
        self._service.persist_settings(obj, self._to_payload(settings))

    def build_validation(self, settings):
        if settings.characteristic_length <= 0.0:
            return (
                "error",
                "Base mesh size must be positive",
                "Set a positive base size before generating the mesh.",
            )

        if settings.min_element_size > settings.max_element_size:
            return (
                "warning",
                "Minimum size exceeds maximum size",
                "Reduce the minimum element size or increase the maximum element size before meshing.",
            )

        return ("", "", "")

    def run_mesh(self, obj, settings):
        self.persist_settings(obj, settings)
        result = self._service.generate_mesh(obj)
        if result.status != "SUCCESSFUL":
            issues = list(result.issues) or ["Unknown mesh generation error."]
            message = "FlowStudio: Mesh generation blocked:\n- " + "\n- ".join(issues)
            return MeshGmshRunState(
                status=result.status,
                stats_text="Mesh blocked by geometry issues",
                console_message=message,
                dialog_title="FlowStudio Mesh Generation",
                dialog_message=message,
                show_warning=True,
            )

        return MeshGmshRunState(
            status=result.status,
            stats_text=f"Cells: {result.num_cells} | Points: {result.num_points}",
            console_message=(
                "FlowStudio: Mesh generated successfully\n"
                f"  file: {result.mesh_file}\n"
                f"  cells: {result.num_cells}\n"
                f"  points: {result.num_points}\n"
            ),
        )

    def _coerce_settings(self, payload):
        return MeshGmshSettings(
            characteristic_length=float(payload["CharacteristicLength"]),
            min_element_size=float(payload["MinElementSize"]),
            max_element_size=float(payload["MaxElementSize"]),
            algorithm_3d=str(payload["Algorithm3D"]),
            element_order=str(payload["ElementOrder"]),
            element_type=str(payload["ElementType"]),
            growth_rate=float(payload["GrowthRate"]),
            cells_in_gap=int(payload["CellsInGap"]),
            mesh_format=str(payload["MeshFormat"]),
        )

    def _to_payload(self, settings):
        return {
            "CharacteristicLength": settings.characteristic_length,
            "MinElementSize": settings.min_element_size,
            "MaxElementSize": settings.max_element_size,
            "Algorithm3D": settings.algorithm_3d,
            "ElementOrder": settings.element_order,
            "ElementType": settings.element_type,
            "GrowthRate": settings.growth_rate,
            "CellsInGap": settings.cells_in_gap,
            "MeshFormat": settings.mesh_format,
        }