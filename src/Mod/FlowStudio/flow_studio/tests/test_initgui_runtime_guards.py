# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Static regression tests for FlowStudio InitGui runtime guards."""

import ast
import os
import unittest


class TestInitGuiRuntimeGuards(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        cls.initgui_path = os.path.join(root_dir, "InitGui.py")

        with open(cls.initgui_path, "r", encoding="utf-8") as handle:
            cls.source = handle.read()

        cls.module = ast.parse(cls.source)
        cls.workbench = next(
            node
            for node in cls.module.body
            if isinstance(node, ast.ClassDef) and node.name == "FlowStudioWorkbench"
        )

    def test_toolbar_layout_uses_qt_enum_helper(self):
        method_src = self._method_source("_save_classic_toolbar_layout")
        self.assertIn(
            '"area": self._qt_enum_value(main_window.toolBarArea(toolbar))',
            method_src,
        )
        self.assertIn(
            '"orientation": self._qt_enum_value(toolbar.orientation())',
            method_src,
        )

    def test_restore_uses_qt_enum_helper_defaults(self):
        method_src = self._method_source("_restore_classic_toolbar_layout")
        self.assertIn(
            'config.get("orientation", self._qt_enum_value(toolbar.orientation()))',
            method_src,
        )
        self.assertIn(
            'config.get("area", self._qt_enum_value(main_window.toolBarArea(toolbar)))',
            method_src,
        )

    def test_active_view_recovery_creates_3d_view(self):
        method_src = self._method_source("_ensure_active_3d_view")
        self.assertIn('gui_doc.createView("Gui::View3DInventor")', method_src)
        self.assertIn('view.viewIsometric()', method_src)
        self.assertIn('view.fitAll()', method_src)

    def test_activated_restores_complete_ui_state(self):
        activated_src = self._method_source("Activated")
        self.assertIn(
            'QtCore.QTimer.singleShot(0, self._restore_workbench_ui_state)',
            activated_src,
        )

        restore_src = self._method_source("_restore_workbench_ui_state")
        self.assertLess(
            restore_src.find('self._ensure_active_3d_view()'),
            restore_src.find('self._restore_classic_toolbar_layout()'),
        )

    def _method_source(self, name):
        for node in self.workbench.body:
            if isinstance(node, ast.FunctionDef) and node.name == name:
                return ast.get_source_segment(self.source, node)
        self.fail(f"Method not found: {name}")


if __name__ == "__main__":
    unittest.main()