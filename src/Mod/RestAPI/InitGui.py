# SPDX-License-Identifier: LGPL-2.1-or-later
# ***************************************************************************
# *   Copyright (c) 2026 FreeCAD contributors                              *
# *                                                                         *
# *   FreeCAD REST API – GUI initialization.                                *
# *   Starts the REST server in a background thread when GUI loads          *
# *   if enabled in preferences.                                            *
# ***************************************************************************

import FreeCAD


class RestAPIWorkbench:
    """Invisible workbench – only starts the API server."""
    MenuText = "REST API"
    ToolTip = "Lightweight REST API for external integration"

    def Initialize(self):
        pass

    def Activated(self):
        pass

    def Deactivated(self):
        pass

    def GetClassName(self):
        return "Gui::PythonWorkbench"


def _maybe_start_server():
    """Start the REST API server if the user has opted in."""
    grp = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/RestAPI")
    if not grp.GetBool("Enabled", False):
        return

    try:
        from . import RestAPIServer
        RestAPIServer.start()
        FreeCAD.Console.PrintMessage("[RestAPI] Server started\n")
    except Exception as e:
        FreeCAD.Console.PrintError(f"[RestAPI] Failed to start server: {e}\n")


_maybe_start_server()
