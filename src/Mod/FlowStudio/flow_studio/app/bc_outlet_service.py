# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Application service for FlowStudio outlet boundary task panels."""

from __future__ import annotations


class FlowStudioOutletBoundaryService:
    """Backend-facing service for outlet boundary settings persistence."""

    FIELD_NAMES = (
        "OutletType",
        "StaticPressure",
        "OutletMassFlowRate",
        "PreventBackflow",
    )

    def read_settings(self, obj):
        return {
            "References": tuple(getattr(obj, "References", []) or []),
            **{name: getattr(obj, name) for name in self.FIELD_NAMES},
        }

    def persist_settings(self, obj, settings):
        for name in self.FIELD_NAMES:
            setattr(obj, name, settings[name])