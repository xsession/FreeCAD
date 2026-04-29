# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Application service for FlowStudio inlet boundary task panels."""

from __future__ import annotations


class FlowStudioInletBoundaryService:
    """Backend-facing service for inlet boundary settings persistence."""

    FIELD_NAMES = (
        "InletType",
        "Ux",
        "Uy",
        "Uz",
        "NormalToFace",
        "MassFlowRate",
        "VolFlowRate",
        "TurbulenceSpec",
        "TurbulenceIntensity",
        "InletTemperature",
    )

    def read_settings(self, obj):
        return {
            "References": tuple(getattr(obj, "References", []) or []),
            **{name: getattr(obj, name) for name in self.FIELD_NAMES},
        }

    def persist_settings(self, obj, settings):
        for name in self.FIELD_NAMES:
            setattr(obj, name, settings[name])