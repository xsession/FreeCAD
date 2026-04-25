# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Application service for FlowStudio initial conditions task panels."""

from __future__ import annotations


class FlowStudioInitialConditionsService:
    """Backend-facing service for initial conditions settings persistence."""

    FIELD_NAMES = (
        "Ux",
        "Uy",
        "Uz",
        "Pressure",
        "Temperature",
        "TurbulentKineticEnergy",
        "SpecificDissipationRate",
        "UsePotentialFlow",
    )

    def read_settings(self, obj):
        return {
            "References": tuple(getattr(obj, "References", []) or []),
            **{name: getattr(obj, name) for name in self.FIELD_NAMES},
        }

    def persist_settings(self, obj, settings):
        for name in self.FIELD_NAMES:
            setattr(obj, name, settings[name])