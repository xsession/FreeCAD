# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Desktop-specific action adapter for the FlowStudio project cockpit."""

from __future__ import annotations

import FreeCADGui


class FreeCADProjectCockpitActions:
    """Adapter that binds presenter intents to the current FreeCAD desktop UI."""

    def execute_command(self, command_name: str) -> None:
        FreeCADGui.runCommand(command_name)

    def activate_result_target(self, object_name: str) -> bool:
        try:
            FreeCADGui.ActiveDocument.setEdit(object_name)
            return True
        except Exception:
            return False