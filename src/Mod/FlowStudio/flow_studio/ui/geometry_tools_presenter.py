# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Presenter helpers for FlowStudio geometry-tools task panels."""

from __future__ import annotations


def _format_volume(value):
    return f"{value:.6g} m^3"


class GeometryCheckPresenter:
    """Frontend-neutral presenter for geometry-check validation and reporting."""

    def build_validation(self, checked_count, last_result):
        if checked_count == 0:
            return (
                "incomplete",
                "Select geometry to analyze",
                "Check at least one body before running geometry validation or generating a fluid volume.",
            )

        if last_result is None:
            return (
                "info",
                "Run geometry check",
                "Use Check to confirm the current model is closed enough for fluid setup.",
            )

        if getattr(last_result, "errors", None):
            return (
                "warning",
                "Geometry blocks meshing",
                "Resolve the reported topology errors before generating the mesh or starting the solver.",
            )

        if getattr(last_result, "issues", None):
            return (
                "warning",
                "Geometry issues detected",
                "Review the reported issues before creating the final fluid domain or starting meshing.",
            )

        return (
            "success",
            "Geometry looks ready",
            "The checked bodies appear closed enough to continue with fluid-volume creation or meshing.",
        )

    def build_results(self, result):
        lines = [
            f"Status: {result.status}. Geometry is "
            f"{'OK' if result.status == 'SUCCESSFUL' else 'not fully closed'}",
            f"Analysis type: {result.analysis_type}",
            f"Fluid volume: {_format_volume(result.fluid_volume)}",
            f"Solid volume: {_format_volume(result.solid_volume)}",
            f"Mesh readiness: {'ready' if getattr(result, 'mesh_ready', False) else 'blocked'}",
        ]
        for info in result.objects:
            lines.append(
                f"{info.label}: {info.solids} solids, {info.shells} shells, "
                f"{info.faces} faces, volume {_format_volume(info.volume)}"
            )
        if getattr(result, "errors", None):
            lines.append("Errors:")
            lines.extend(f"- {issue}" for issue in result.errors)
        if getattr(result, "warnings", None):
            lines.append("Warnings:")
            lines.extend(f"- {issue}" for issue in result.warnings)
        if result.issues:
            lines.append("Issues summary:")
            lines.extend(f"- {issue}" for issue in result.issues)
        else:
            lines.append("All checked bodies look closed enough for setup.")
        return lines

    def volume_button_text(self, visible):
        return "Hide Fluid Volume" if visible else "Show Fluid Volume"


class LeakTrackingPresenter:
    """Frontend-neutral presenter for leak-tracking validation and reporting."""

    def build_validation(self, face_a, face_b):
        if not face_a or not face_b:
            return (
                "incomplete",
                "Select internal and external faces",
                "Capture one internal face and one external face before searching for a connection.",
            )

        if face_a == face_b:
            return (
                "warning",
                "Faces must be different",
                "Use two different faces so leak tracking can evaluate a real path through the model.",
            )

        return (
            "info",
            "Ready to find connection",
            "Run Find Connection to trace a possible leak path between the selected faces.",
        )

    def build_results(self, report):
        return [f"Status: {report['status']}"] + list(report["messages"])