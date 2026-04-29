# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Unit tests for shared ribbon metadata helpers."""

import importlib.util
import os
import sys
import types
import unittest
from unittest import mock


def _load_ribbon_metadata_module(fake_gui=None):
    repo_root = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
    )
    module_path = os.path.join(repo_root, "src", "Gui", "RibbonMetadata.py")
    spec = importlib.util.spec_from_file_location("test_ribbon_metadata_module", module_path)
    module = importlib.util.module_from_spec(spec)
    patched_modules = {"FreeCADGui": fake_gui} if fake_gui is not None else {}
    with mock.patch.dict(sys.modules, patched_modules, clear=False):
        spec.loader.exec_module(module)
    return module


class TestRibbonMetadata(unittest.TestCase):
    def test_registry_adapter_delegates_to_gui_module(self):
        fake_gui = types.SimpleNamespace(
            registerRibbonPanel=mock.Mock(),
            unregisterRibbonPanel=mock.Mock(),
            registerContextualRibbonPanel=mock.Mock(),
            unregisterContextualRibbonPanel=mock.Mock(),
        )

        module = _load_ribbon_metadata_module(fake_gui)
        adapter = module.FreeCADRibbonRegistryAdapter()

        adapter.register_ribbon_panel("Ribbon::Inspect", ("CmdA", "CmdB"))
        adapter.unregister_ribbon_panel("Ribbon::Inspect")
        adapter.register_contextual_ribbon_panel("RibbonContext::Setup", ("CmdC",))
        adapter.unregister_contextual_ribbon_panel("RibbonContext::Setup")

        fake_gui.registerRibbonPanel.assert_called_once_with("Ribbon::Inspect", ["CmdA", "CmdB"])
        fake_gui.unregisterRibbonPanel.assert_called_once_with("Ribbon::Inspect")
        fake_gui.registerContextualRibbonPanel.assert_called_once_with(
            "RibbonContext::Setup", ["CmdC"]
        )
        fake_gui.unregisterContextualRibbonPanel.assert_called_once_with("RibbonContext::Setup")

    def test_helper_functions_delegate_through_registry_port(self):
        module = _load_ribbon_metadata_module()
        registry = mock.Mock()

        module.register_ribbon_panel("Ribbon::Results", ("CmdA",), registry=registry)
        module.unregister_ribbon_panel("Ribbon::Results", registry=registry)
        module.register_contextual_ribbon_panel("RibbonContext::Results", ("CmdB",), registry=registry)
        module.unregister_contextual_ribbon_panel("RibbonContext::Results", registry=registry)

        registry.register_ribbon_panel.assert_called_once_with("Ribbon::Results", ("CmdA",))
        registry.unregister_ribbon_panel.assert_called_once_with("Ribbon::Results")
        registry.register_contextual_ribbon_panel.assert_called_once_with(
            "RibbonContext::Results", ("CmdB",)
        )
        registry.unregister_contextual_ribbon_panel.assert_called_once_with("RibbonContext::Results")

    def test_registry_adapter_raises_without_gui_runtime(self):
        module = _load_ribbon_metadata_module()
        adapter = module.FreeCADRibbonRegistryAdapter()

        with self.assertRaisesRegex(RuntimeError, "FreeCADGui is required"):
            adapter.register_ribbon_panel("Ribbon::Inspect", ())


if __name__ == "__main__":
    unittest.main()