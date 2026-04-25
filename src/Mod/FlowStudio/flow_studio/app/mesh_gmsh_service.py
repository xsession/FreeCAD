# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Application service for the FlowStudio Gmsh mesh task panel."""

from __future__ import annotations

from flow_studio.tools.geometry import generate_mesh_from_geometry


class FlowStudioMeshGmshService:
    """Backend-facing service for mesh settings persistence and execution."""

    FIELD_NAMES = (
        "CharacteristicLength",
        "MinElementSize",
        "MaxElementSize",
        "Algorithm3D",
        "ElementOrder",
        "ElementType",
        "GrowthRate",
        "CellsInGap",
        "MeshFormat",
    )

    def read_settings(self, obj):
        return {name: getattr(obj, name) for name in self.FIELD_NAMES}

    def persist_settings(self, obj, settings):
        for name in self.FIELD_NAMES:
            setattr(obj, name, settings[name])

    def generate_mesh(self, obj):
        return generate_mesh_from_geometry(obj)