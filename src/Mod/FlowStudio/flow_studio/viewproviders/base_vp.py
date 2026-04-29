# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Base ViewProvider for FlowStudio objects."""

import os
import tempfile
import FreeCAD
import FreeCADGui

ICONS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Resources", "icons")
ICON_CACHE_DIR = os.path.join(tempfile.gettempdir(), "flowstudio_icon_cache")


class BaseFlowVP:
    """Minimal ViewProvider proxy for FlowStudio objects."""

    icon_name = "FlowStudioGeneric.svg"

    _STATUS_BADGES = {
        "active": {
            "fill": "#0b5cad",
            "glyph": '<circle cx="52" cy="52" r="3.5" fill="#ffffff"/>',
        },
        "done": {
            "fill": "#2e7d32",
            "glyph": '<path d="M46 52 L50 56 L58 47" stroke="#ffffff" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round"/>',
        },
        "warning": {
            "fill": "#c65d00",
            "glyph": '<rect x="50.5" y="45" width="3" height="9" rx="1.5" fill="#ffffff"/><circle cx="52" cy="57" r="1.7" fill="#ffffff"/>',
        },
    }

    def __init__(self, vobj):
        vobj.Proxy = self

    def getIcon(self):
        icon_path = os.path.join(ICONS_DIR, self.icon_name)
        status = self._icon_status()
        if not status:
            return icon_path
        return self._status_icon_path(icon_path, status)

    def attach(self, vobj):
        self.Object = vobj.Object

    def claimChildren(self):
        return []

    def onDelete(self, vobj, sub_elements):
        return True

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        pass

    def setEdit(self, vobj, mode=0):
        """Open the task panel for editing."""
        # Subclasses override to show a task panel
        return False

    @staticmethod
    def show_task_panel(task_panel, obj=None):
        """Instantiate and show a task panel consistently across FlowStudio."""
        try:
            FreeCADGui.Control.closeDialog()
        except Exception:
            pass

        panel = task_panel(obj) if isinstance(task_panel, type) else task_panel
        FreeCADGui.Control.showDialog(panel)
        return True

    def unsetEdit(self, vobj, mode=0):
        FreeCADGui.Control.closeDialog()
        return True

    def doubleClicked(self, vobj):
        doc = FreeCADGui.getDocument(vobj.Object.Document)
        in_edit = doc.getInEdit()
        if in_edit:
            current = in_edit[0] if isinstance(in_edit, tuple) else in_edit
            current_name = getattr(current, "Name", None)
            if current_name == vobj.Object.Name:
                return True
            doc.resetEdit()

        doc.setEdit(vobj.Object.Name)
        return True

    def _icon_status(self):
        obj = getattr(self, "Object", None)
        if obj is None:
            return ""
        try:
            from flow_studio.core.workflow import get_tree_status

            return get_tree_status(obj)
        except Exception:
            return ""

    @classmethod
    def _status_icon_path(cls, base_icon_path, status):
        badge = cls._STATUS_BADGES.get(status)
        if badge is None:
            return base_icon_path

        os.makedirs(ICON_CACHE_DIR, exist_ok=True)
        base_name, _ext = os.path.splitext(os.path.basename(base_icon_path))
        cached_path = os.path.join(ICON_CACHE_DIR, f"{base_name}_{status}.svg")

        try:
            base_mtime = os.path.getmtime(base_icon_path)
            cache_mtime = os.path.getmtime(cached_path) if os.path.exists(cached_path) else -1
            if cache_mtime >= base_mtime:
                return cached_path

            with open(base_icon_path, "r", encoding="utf-8") as handle:
                svg = handle.read()

            overlay = (
                '<g id="flowstudio-status-badge">'
                f'<circle cx="52" cy="52" r="10" fill="{badge["fill"]}" stroke="#ffffff" stroke-width="2"/>'
                f'{badge["glyph"]}'
                '</g>'
            )
            svg = svg.replace("</svg>", f"  {overlay}\n</svg>")

            with open(cached_path, "w", encoding="utf-8") as handle:
                handle.write(svg)
            return cached_path
        except Exception:
            return base_icon_path
