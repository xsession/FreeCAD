# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Application service for FlowStudio post-pipeline task panels."""

from __future__ import annotations


class FlowStudioPostPipelineService:
    """Backend-facing service for post-pipeline settings persistence."""

    FIELD_NAMES = (
        "VisualizationType",
        "ActiveField",
        "AutoRange",
        "MinRange",
        "MaxRange",
        "AvailableFields",
        "ResultFile",
    )

    def read_settings(self, obj):
        return {name: getattr(obj, name) for name in self.FIELD_NAMES}

    def persist_settings(self, obj, settings):
        for name in ("VisualizationType", "ActiveField", "AutoRange", "MinRange", "MaxRange"):
            setattr(obj, name, settings[name])