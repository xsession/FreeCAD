# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Unit tests for FlowStudio desktop taskpanel lifecycle adapters."""

import os
import sys
import types
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


class TestFreeCADTaskPanelDesktopLifecycle(unittest.TestCase):
    def test_accept_reject_and_close_delegate_to_freecad_desktop(self):
        fake_freecad = types.SimpleNamespace(ActiveDocument=types.SimpleNamespace(recompute=mock.Mock()))
        fake_gui = types.SimpleNamespace(
            ActiveDocument=types.SimpleNamespace(resetEdit=mock.Mock()),
            Control=types.SimpleNamespace(closeDialog=mock.Mock()),
        )

        with mock.patch.dict(sys.modules, {"FreeCAD": fake_freecad, "FreeCADGui": fake_gui}):
            from importlib import import_module

            module = import_module("flow_studio.taskpanels.taskpanel_desktop_lifecycle")
            lifecycle = module.FreeCADTaskPanelDesktopLifecycle()
            lifecycle.accept_edit()
            lifecycle.reject_edit()
            lifecycle.close_dialog()

        self.assertEqual(fake_gui.ActiveDocument.resetEdit.call_count, 2)
        fake_freecad.ActiveDocument.recompute.assert_called_once_with()
        fake_gui.Control.closeDialog.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()