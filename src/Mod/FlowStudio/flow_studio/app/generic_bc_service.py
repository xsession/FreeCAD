# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Application service for generic FlowStudio boundary task panels."""

from __future__ import annotations


class FlowStudioGenericBoundaryService:
    """Backend-facing service for generic boundary settings persistence."""

    def read_settings(self, obj, field_names):
        return {
            "Title": getattr(obj, "BCLabel", getattr(obj, "Label", "Boundary Condition")),
            "FlowType": getattr(obj, "FlowType", ""),
            "References": tuple(getattr(obj, "References", []) or []),
            "Values": {name: getattr(obj, name) for name in field_names},
        }

    def persist_settings(self, obj, values):
        for name, value in values.items():
            setattr(obj, name, value)