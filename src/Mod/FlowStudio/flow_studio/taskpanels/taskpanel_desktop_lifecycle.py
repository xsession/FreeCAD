# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Desktop lifecycle adapter for FlowStudio task panels."""

from __future__ import annotations

import FreeCAD
import FreeCADGui


class FreeCADTaskPanelDesktopLifecycle:
    """Adapter that binds taskpanel lifecycle events to the active FreeCAD desktop."""

    def accept_edit(self) -> None:
        FreeCADGui.ActiveDocument.resetEdit()
        FreeCAD.ActiveDocument.recompute()

    def reject_edit(self) -> None:
        FreeCADGui.ActiveDocument.resetEdit()

    def close_dialog(self) -> None:
        FreeCADGui.Control.closeDialog()