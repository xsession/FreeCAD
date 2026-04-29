# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Presenters for Geant4 result task panels."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Geant4ResultSettings:
    result_file: str
    artifact_files: tuple
    available_fields: tuple
    active_field: str


@dataclass(frozen=True)
class Geant4ResultComponentSettings:
    parent_result: object
    flow_type: str
    available_fields: tuple
    active_field: str
    artifact_files: tuple


class Geant4ResultPresenter:
    def __init__(self, service=None):
        if service is None:
            from flow_studio.app import FlowStudioGeant4ResultService

            service = FlowStudioGeant4ResultService()
        self._service = service

    def read_settings(self, obj):
        payload = self._service.read_settings(obj)
        return Geant4ResultSettings(
            result_file=str(payload["ResultFile"]),
            artifact_files=tuple(payload["ArtifactFiles"]),
            available_fields=tuple(payload["AvailableFields"]),
            active_field=str(payload["ActiveField"]),
        )

    def persist_settings(self, obj, settings):
        self._service.persist_settings(obj, {"ActiveField": settings.active_field})

    def build_validation(self, settings):
        if not settings.result_file and not settings.artifact_files:
            return (
                "info",
                "Import a Geant4 result",
                "Load a Geant4 summary or artifact set before inspecting fields and monitor data.",
            )

        if settings.available_fields and settings.active_field not in settings.available_fields:
            return (
                "warning",
                "Selected field is unavailable",
                "Choose an active field that exists in the imported Geant4 result set.",
            )

        if not settings.available_fields:
            return (
                "info",
                "No parsed fields available yet",
                "The result object is present, but no parsed Geant4 fields are available for inspection yet.",
            )

        return (
            "success",
            "Geant4 result ready",
            "Imported artifacts and parsed fields are available for inspection.",
        )


class Geant4ResultComponentPresenter:
    def __init__(self, service=None):
        if service is None:
            from flow_studio.app import FlowStudioGeant4ResultComponentService

            service = FlowStudioGeant4ResultComponentService()
        self._service = service

    def read_settings(self, obj):
        payload = self._service.read_settings(obj)
        return Geant4ResultComponentSettings(
            parent_result=payload["ParentResult"],
            flow_type=str(payload["FlowType"]),
            available_fields=tuple(payload["AvailableFields"]),
            active_field=str(payload["ActiveField"]),
            artifact_files=tuple(payload["ArtifactFiles"]),
        )

    def persist_settings(self, obj, settings):
        self._service.persist_settings(obj, {"ActiveField": settings.active_field})

    def build_validation(self, settings):
        if settings.parent_result is None:
            return (
                "info",
                "Parent Geant4 result missing",
                "Link this component back to a Geant4 result so its source context is clear.",
            )

        if settings.flow_type == "FlowStudio::Geant4ScoringResult":
            if settings.available_fields and settings.active_field not in settings.available_fields:
                return (
                    "warning",
                    "Selected field is unavailable",
                    "Choose an active field that exists in this scoring result.",
                )
            if not settings.available_fields:
                return (
                    "info",
                    "No scoring fields available",
                    "The scoring result is linked, but no imported fields are available yet.",
                )

        if not settings.artifact_files:
            return (
                "info",
                "No component artifacts recorded",
                "This result component has metadata, but no exported artifact files are attached yet.",
            )

        return (
            "success",
            "Geant4 component ready",
            "Imported metadata and artifacts are available for this Geant4 result component.",
        )