# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Enterprise-facing FreeCAD commands for Flow Studio."""

from __future__ import annotations

import os
from datetime import datetime

import FreeCAD
import FreeCADGui

from flow_studio.enterprise import initialize_workbench
from flow_studio.enterprise.app.legacy_actions import (
    export_fcstd_sidecar,
    export_analysis_manifest,
    submit_analysis_to_runtime,
)
from flow_studio.workflow_guide import get_active_analysis

translate = FreeCAD.Qt.translate

ICONS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Resources", "icons")


def _icon(name: str) -> str:
    return os.path.join(ICONS_DIR, name)


def _project_id() -> str:
    doc = FreeCAD.ActiveDocument
    if doc is None:
        return "flowstudio-project"
    return getattr(doc, "Name", "flowstudio-project")


def _default_output_dir(analysis) -> str:
    case_dir = getattr(analysis, "CaseDir", "")
    if case_dir:
        return case_dir
    doc = FreeCAD.ActiveDocument
    if doc is not None and hasattr(doc, "TransientDir"):
        return os.path.join(doc.TransientDir, "FlowStudio", getattr(analysis, "Name", "Analysis"))
    return os.path.join(os.path.expanduser("~"), "FlowStudio")


def _timestamp_slug() -> str:
    return datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")


def _show_info(title: str, message: str) -> None:
    if FreeCAD.GuiUp:
        from PySide import QtWidgets

        QtWidgets.QMessageBox.information(None, title, message)


def _show_warning(title: str, message: str) -> None:
    if FreeCAD.GuiUp:
        from PySide import QtWidgets

        QtWidgets.QMessageBox.warning(None, title, message)


class _CmdExportEnterpriseManifest:
    """Export the active legacy analysis to the enterprise schema."""

    def GetResources(self):
        return {
            "Pixmap": _icon("FlowStudioGeneric.svg"),
            "MenuText": translate("FlowStudio", "Export Enterprise Manifest"),
            "ToolTip": translate(
                "FlowStudio",
                "Export the active analysis as a canonical enterprise project manifest.",
            ),
        }

    def IsActive(self):
        return get_active_analysis() is not None

    def Activated(self):
        analysis = get_active_analysis()
        if analysis is None:
            return

        output_dir = _default_output_dir(analysis)
        default_path = os.path.join(output_dir, f"{analysis.Name}.enterprise.json")

        if FreeCAD.GuiUp:
            from PySide import QtWidgets

            selected_path, _ = QtWidgets.QFileDialog.getSaveFileName(
                None,
                translate("FlowStudio", "Export Enterprise Manifest"),
                default_path,
                translate("FlowStudio", "JSON Files (*.json)"),
            )
            if not selected_path:
                return
            output_path = selected_path
        else:
            output_path = default_path

        path = export_analysis_manifest(
            analysis_object=analysis,
            project_id=_project_id(),
            output_path=output_path,
        )
        doc = FreeCAD.ActiveDocument
        doc_path = getattr(doc, "FileName", "") if doc is not None else ""
        sidecar_path = export_fcstd_sidecar(
            analysis_object=analysis,
            project_id=_project_id(),
            fcstd_path=doc_path or None,
            fallback_directory=os.path.dirname(path),
        )
        FreeCAD.Console.PrintMessage(f"FlowStudio: Enterprise manifest exported to {path}\n")
        FreeCAD.Console.PrintMessage(f"FlowStudio: Enterprise sidecar exported to {sidecar_path}\n")
        _show_info(
            translate("FlowStudio", "Enterprise Manifest Exported"),
            translate(
                "FlowStudio",
                f"Manifest saved to:\n{path}\n\nFCStd sidecar saved to:\n{sidecar_path}",
            ),
        )


class _CmdSubmitEnterpriseRun:
    """Submit the active legacy analysis through the enterprise runtime."""

    def GetResources(self):
        return {
            "Pixmap": _icon("FlowStudioRunSolver.svg"),
            "MenuText": translate("FlowStudio", "Submit Enterprise Run"),
            "ToolTip": translate(
                "FlowStudio",
                "Translate the active analysis into the enterprise model and submit it "
                "through the new orchestration facade.",
            ),
        }

    def IsActive(self):
        return get_active_analysis() is not None

    def Activated(self):
        analysis = get_active_analysis()
        if analysis is None:
            return

        runtime = initialize_workbench()
        run_id = f"{analysis.Name}-{_timestamp_slug()}"
        working_directory = _default_output_dir(analysis)

        try:
            record, manifest_hash = submit_analysis_to_runtime(
                runtime=runtime,
                analysis_object=analysis,
                project_id=_project_id(),
                run_id=run_id,
                working_directory=working_directory,
            )
        except KeyError as exc:
            adapter_id = str(exc).strip("'")
            available = ", ".join(runtime.job_service.adapter_ids())
            message = (
                f"No enterprise adapter is registered for '{adapter_id}'.\n\n"
                f"Available adapters: {available}"
            )
            FreeCAD.Console.PrintError(f"FlowStudio: {message}\n")
            _show_warning(translate("FlowStudio", "Enterprise Submit Failed"), message)
            return
        except Exception as exc:
            FreeCAD.Console.PrintError(f"FlowStudio: Enterprise submit failed: {exc}\n")
            _show_warning(
                translate("FlowStudio", "Enterprise Submit Failed"),
                translate("FlowStudio", f"Submission failed:\n{exc}"),
            )
            return

        message = (
            f"Run submitted.\n\n"
            f"Run ID: {record.run_id}\n"
            f"State: {record.state.value}\n"
            f"Adapter: {record.adapter_id}\n"
            f"Target: {record.target_ref or record.target or 'local'}\n"
            f"Execution Mode: {record.execution_mode or 'unknown'}\n"
            f"Manifest: {manifest_hash}\n"
            f"Run Directory: {runtime.job_service.run_directory(record.run_id) or working_directory}"
        )
        FreeCAD.Console.PrintMessage(f"FlowStudio: {message}\n")
        _show_info(translate("FlowStudio", "Enterprise Run Submitted"), message)


class _CmdSubmitEnterpriseRemoteRun:
    """Submit the active legacy analysis through the enterprise remote profile."""

    def GetResources(self):
        return {
            "Pixmap": _icon("FlowStudioRunSolver.svg"),
            "MenuText": translate("FlowStudio", "Submit Enterprise Remote Run"),
            "ToolTip": translate(
                "FlowStudio",
                "Submit the active analysis through the enterprise remote execution profile.",
            ),
        }

    def IsActive(self):
        return get_active_analysis() is not None

    def Activated(self):
        analysis = get_active_analysis()
        if analysis is None:
            return

        runtime = initialize_workbench()
        profile = runtime.profiles.get("remote-loopback")
        if profile is None:
            message = "No remote enterprise execution profile is configured."
            FreeCAD.Console.PrintError(f"FlowStudio: {message}\n")
            _show_warning(translate("FlowStudio", "Remote Submit Failed"), message)
            return

        run_id = f"{analysis.Name}-{_timestamp_slug()}-remote"
        working_directory = _default_output_dir(analysis)

        try:
            record, manifest_hash = submit_analysis_to_runtime(
                runtime=runtime,
                analysis_object=analysis,
                project_id=_project_id(),
                run_id=run_id,
                working_directory=working_directory,
                reason="remote-submit",
                execution_profile=profile,
            )
        except KeyError as exc:
            missing_key = str(exc).strip("'")
            available_targets = ", ".join(runtime.job_service.remote_target_ids()) or "none"
            message = (
                f"Remote enterprise target '{missing_key}' is not available.\n\n"
                f"Configured remote targets: {available_targets}"
            )
            FreeCAD.Console.PrintError(f"FlowStudio: {message}\n")
            _show_warning(translate("FlowStudio", "Remote Submit Failed"), message)
            return
        except Exception as exc:
            FreeCAD.Console.PrintError(f"FlowStudio: Remote enterprise submit failed: {exc}\n")
            _show_warning(
                translate("FlowStudio", "Remote Submit Failed"),
                translate("FlowStudio", f"Submission failed:\n{exc}"),
            )
            return

        message = (
            f"Remote run submitted.\n\n"
            f"Run ID: {record.run_id}\n"
            f"State: {record.state.value}\n"
            f"Adapter: {record.adapter_id}\n"
            f"Target: {record.target_ref or profile.name}\n"
            f"Remote Run ID: {record.remote_run_id or 'n/a'}\n"
            f"Execution Mode: {record.execution_mode or 'unknown'}\n"
            f"Manifest: {manifest_hash}\n"
            f"Run Directory: {runtime.job_service.run_directory(record.run_id) or working_directory}"
        )
        FreeCAD.Console.PrintMessage(f"FlowStudio: {message}\n")
        _show_info(translate("FlowStudio", "Enterprise Remote Run Submitted"), message)


class _CmdEnterpriseJobs:
    """Show persisted enterprise jobs and run history."""

    def GetResources(self):
        return {
            "Pixmap": _icon("FlowStudioPost.svg"),
            "MenuText": translate("FlowStudio", "Enterprise Jobs"),
            "ToolTip": translate(
                "FlowStudio",
                "Inspect persisted enterprise jobs, states, and artifact locations.",
            ),
        }

    def IsActive(self):
        return FreeCAD.ActiveDocument is not None

    def Activated(self):
        runtime = initialize_workbench()
        if FreeCAD.GuiUp:
            from flow_studio.enterprise.ui.jobs_panel import EnterpriseJobsPanel

            FreeCADGui.Control.showDialog(EnterpriseJobsPanel(runtime))
            return

        summaries = runtime.job_service.persisted_run_summaries()
        if not summaries:
            FreeCAD.Console.PrintMessage("FlowStudio: No persisted enterprise runs found.\n")
            return

        FreeCAD.Console.PrintMessage("FlowStudio: Enterprise jobs\n")
        for summary in summaries:
            FreeCAD.Console.PrintMessage(
                f"  {summary.get('run_id', '')} | {summary.get('state', '')} | "
                f"{summary.get('target_ref', '') or summary.get('target', '')} | "
                f"{summary.get('adapter_id', '')} | {summary.get('run_directory', '')}\n"
            )


FreeCADGui.addCommand("FlowStudio_ExportEnterpriseManifest", _CmdExportEnterpriseManifest())
FreeCADGui.addCommand("FlowStudio_SubmitEnterpriseRun", _CmdSubmitEnterpriseRun())
FreeCADGui.addCommand("FlowStudio_SubmitEnterpriseRemoteRun", _CmdSubmitEnterpriseRemoteRun())
FreeCADGui.addCommand("FlowStudio_EnterpriseJobs", _CmdEnterpriseJobs())
