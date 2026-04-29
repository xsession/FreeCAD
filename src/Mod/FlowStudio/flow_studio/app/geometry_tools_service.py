# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Application services for FlowStudio geometry-tools task panels."""

from __future__ import annotations

from flow_studio.tools.geometry import (
    check_geometry,
    create_or_update_fluid_volume,
    describe_face_ref,
    fluid_volume_is_visible,
    hide_fluid_volume,
    iter_geometry_objects,
    run_leak_tracking,
    selected_face_refs,
)


class FlowStudioGeometryCheckService:
    """Backend-facing service for geometry check workflows."""

    def iter_geometry_objects(self):
        return iter_geometry_objects()

    def run_check(self, objects, options):
        return check_geometry(objects, options)

    def is_fluid_volume_visible(self):
        return fluid_volume_is_visible()

    def show_fluid_volume(self, result):
        create_or_update_fluid_volume(result)

    def hide_fluid_volume(self):
        hide_fluid_volume()


class FlowStudioLeakTrackingService:
    """Backend-facing service for leak-tracking workflows."""

    def selected_face_refs(self):
        return selected_face_refs()

    def describe_face_ref(self, face_ref):
        return describe_face_ref(face_ref)

    def run_leak_tracking(self, face_a, face_b):
        return run_leak_tracking(face_a, face_b)