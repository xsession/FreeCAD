# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Base class for all FlowStudio FeaturePython objects."""


class BaseFlowObject:
    """Minimal FeaturePython proxy shared by every FlowStudio object."""

    Type = "FlowStudio::BaseObject"

    def __init__(self, obj):
        obj.Proxy = self
        obj.addProperty(
            "App::PropertyString", "FlowType", "FlowStudio",
            "Internal type identifier"
        )
        obj.FlowType = self.Type
        obj.setPropertyStatus("FlowType", "ReadOnly")

    def add_reference_property(self, obj, group="Geometry", description=None):
        """Add a reusable geometry/subelement reference property."""
        if "References" in getattr(obj, "PropertiesList", []):
            return
        obj.addProperty(
            "App::PropertyLinkSubList",
            "References",
            group,
            description or "Referenced parts, faces, or regions used by this FlowStudio object",
        )

    def onDocumentRestored(self, obj):
        """Re-attach proxy after file load."""
        obj.Proxy = self

    def execute(self, obj):
        """Recompute – override in subclasses."""
        pass

    def __getstate__(self):
        return self.Type

    def __setstate__(self, state):
        self.Type = state
