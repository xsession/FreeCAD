# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Application services for Geant4 result task panels."""

from __future__ import annotations


class FlowStudioGeant4ResultService:
    def read_settings(self, obj):
        return {
            "ResultFile": str(getattr(obj, "ResultFile", "") or ""),
            "ArtifactFiles": tuple(getattr(obj, "ArtifactFiles", []) or []),
            "AvailableFields": tuple(getattr(obj, "AvailableFields", []) or []),
            "ActiveField": str(getattr(obj, "ActiveField", "") or ""),
        }

    def persist_settings(self, obj, settings):
        obj.ActiveField = settings["ActiveField"]


class FlowStudioGeant4ResultComponentService:
    def read_settings(self, obj):
        return {
            "ParentResult": getattr(obj, "ParentResult", None),
            "FlowType": getattr(obj, "FlowType", ""),
            "AvailableFields": tuple(getattr(obj, "AvailableFields", []) or []),
            "ActiveField": str(getattr(obj, "ActiveField", "") or ""),
            "ArtifactFiles": tuple(getattr(obj, "ArtifactFiles", []) or []),
        }

    def persist_settings(self, obj, settings):
        obj.ActiveField = settings["ActiveField"]