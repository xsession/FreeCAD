# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Desktop adapter for FlowStudio taskpanel selection capture."""

from __future__ import annotations

import FreeCADGui


class FreeCADSelectionDesktopAdapter:
    """Desktop adapter that converts FreeCAD GUI selection into reference tuples."""

    def get_selected_references(self):
        refs = []
        try:
            selection = FreeCADGui.Selection.getSelectionEx()
        except Exception:
            selection = []
        for item in selection:
            obj = getattr(item, "Object", None)
            if obj is None:
                continue
            flow_type = getattr(obj, "FlowType", "")
            if isinstance(flow_type, str) and flow_type.startswith("FlowStudio::"):
                continue
            refs.append((obj, list(getattr(item, "SubElementNames", []) or [])))
        return refs