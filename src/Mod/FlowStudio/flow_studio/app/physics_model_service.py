# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Application service for FlowStudio physics model task panels."""

from __future__ import annotations


class FlowStudioPhysicsModelService:
    """Backend-facing service for physics model settings persistence."""

    FIELD_NAMES = (
        "FlowRegime",
        "TurbulenceModel",
        "Compressibility",
        "TimeModel",
        "Gravity",
        "HeatTransfer",
        "Buoyancy",
        "FreeSurface",
        "PassiveScalar",
    )

    def read_settings(self, obj):
        return {name: getattr(obj, name) for name in self.FIELD_NAMES}

    def persist_settings(self, obj, settings):
        for name in self.FIELD_NAMES:
            setattr(obj, name, settings[name])