# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Unit tests for shared selection presenters and desktop adapters."""

import os
import sys
import types
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


class TestSelectionPresenter(unittest.TestCase):
    def test_build_labels_formats_object_and_subelement_refs(self):
        from flow_studio.ui.selection_presenter import SelectionPresenter

        presenter = SelectionPresenter()
        refs = [
            (types.SimpleNamespace(Label="Block"), ["Face1", "Face2"]),
            (types.SimpleNamespace(Name="Body002"), []),
            (types.SimpleNamespace(Label="EdgeSet"), "Edge3"),
        ]

        self.assertEqual(
            presenter.build_labels(refs),
            ["Block:Face1", "Block:Face2", "Body002", "EdgeSet:Edge3"],
        )


class TestFreeCADSelectionDesktopAdapter(unittest.TestCase):
    def test_adapter_filters_flowstudio_objects_and_collects_refs(self):
        fake_gui = types.SimpleNamespace(
            Selection=types.SimpleNamespace(
                getSelectionEx=lambda: [
                    types.SimpleNamespace(
                        Object=types.SimpleNamespace(Label="Wall", FlowType="Part::Feature"),
                        SubElementNames=["Face1"],
                    ),
                    types.SimpleNamespace(
                        Object=types.SimpleNamespace(Label="FlowBC", FlowType="FlowStudio::BCOpen"),
                        SubElementNames=["Face9"],
                    ),
                    types.SimpleNamespace(
                        Object=types.SimpleNamespace(Name="Solid001"),
                        SubElementNames=[],
                    ),
                ]
            )
        )

        with mock.patch.dict(sys.modules, {"FreeCADGui": fake_gui}):
            from importlib import import_module

            module = import_module("flow_studio.taskpanels.selection_desktop_adapter")
            adapter = module.FreeCADSelectionDesktopAdapter()
            refs = adapter.get_selected_references()

        self.assertEqual(len(refs), 2)
        self.assertEqual(getattr(refs[0][0], "Label", ""), "Wall")
        self.assertEqual(refs[0][1], ["Face1"])
        self.assertEqual(getattr(refs[1][0], "Name", ""), "Solid001")


if __name__ == "__main__":
    unittest.main()