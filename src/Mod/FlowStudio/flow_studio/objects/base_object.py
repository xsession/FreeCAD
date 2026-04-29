# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Base class for all FlowStudio FeaturePython objects."""


REFERENCE_PROPERTY_NAME = "References"
REFERENCE_PROPERTY_TYPE = "App::PropertyLinkSubListGlobal"
LEGACY_REFERENCE_PROPERTY_TYPE = "App::PropertyLinkSubList"


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
        if REFERENCE_PROPERTY_NAME in getattr(obj, "PropertiesList", []):
            self._migrate_reference_property(obj, group, description)
            return

        obj.addProperty(
            REFERENCE_PROPERTY_TYPE,
            REFERENCE_PROPERTY_NAME,
            group,
            description or "Referenced parts, faces, or regions used by this FlowStudio object",
        )

    def _migrate_reference_property(self, obj, group="Geometry", description=None):
        property_name = REFERENCE_PROPERTY_NAME
        if property_name not in getattr(obj, "PropertiesList", []):
            return

        if obj.getTypeIdOfProperty(property_name) != LEGACY_REFERENCE_PROPERTY_TYPE:
            return

        refs = list(getattr(obj, property_name, []) or [])
        group_name = obj.getGroupOfProperty(property_name) or group
        doc = obj.getDocumentationOfProperty(property_name) or (
            description or "Referenced parts, faces, or regions used by this FlowStudio object"
        )
        editor_mode = obj.getEditorMode(property_name)

        obj.removeProperty(property_name)
        obj.addProperty(REFERENCE_PROPERTY_TYPE, property_name, group_name, doc)
        if editor_mode:
            obj.setEditorMode(property_name, editor_mode)
        setattr(obj, property_name, refs)

    def onDocumentRestored(self, obj):
        """Re-attach proxy after file load."""
        obj.Proxy = self
        self._migrate_reference_property(obj)

    def execute(self, obj):
        """Recompute – override in subclasses."""
        pass

    def __getstate__(self):
        return self.Type

    def __setstate__(self, state):
        self.Type = state
