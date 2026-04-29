# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Unit tests for FlowStudio geometry-tools desktop adapters."""

import os
import sys
import types
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


class TestFreeCADGeometryToolsDesktopAdapter(unittest.TestCase):
    def test_adapter_delegates_document_reporting_and_dialog_flow(self):
        fake_doc = types.SimpleNamespace(getObject=mock.Mock(return_value="OBJ"))
        fake_console = types.SimpleNamespace(PrintMessage=mock.Mock())
        fake_freecad = types.SimpleNamespace(ActiveDocument=fake_doc, Console=fake_console)
        fake_gui = types.SimpleNamespace(Control=types.SimpleNamespace(closeDialog=mock.Mock(), showDialog=mock.Mock()))

        with mock.patch.dict(sys.modules, {"FreeCAD": fake_freecad, "FreeCADGui": fake_gui}):
            from importlib import import_module

            module = import_module("flow_studio.taskpanels.geometry_tools_desktop_adapter")
            adapter = module.FreeCADGeometryToolsDesktopAdapter()
            self.assertEqual(adapter.get_document_object("Body001"), "OBJ")
            adapter.report_check_completed(["Status: SUCCESSFUL"])
            adapter.report_leak_tracking_completed(["Status: FOUND"])
            adapter.open_leak_tracking_dialog("PANEL")

        fake_doc.getObject.assert_called_once_with("Body001")
        self.assertEqual(fake_console.PrintMessage.call_count, 4)
        fake_gui.Control.closeDialog.assert_called_once_with()
        fake_gui.Control.showDialog.assert_called_once_with("PANEL")


if __name__ == "__main__":
    unittest.main()