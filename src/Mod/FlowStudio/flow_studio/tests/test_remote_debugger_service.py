# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Unit tests for FreeCAD remote debugger service helpers."""

import importlib.util
import os
import unittest
from unittest import mock


def _load_remote_debugger_service_module():
    repo_root = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
    )
    module_path = os.path.join(repo_root, "src", "Gui", "RemoteDebuggerService.py")
    spec = importlib.util.spec_from_file_location("test_remote_debugger_service_module", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakePrefs:
    def __init__(self, ints=None, strings=None):
        self.ints = dict(ints or {})
        self.strings = dict(strings or {})

    def GetInt(self, key, default):
        return self.ints.get(key, default)

    def GetString(self, key, default):
        return self.strings.get(key, default)

    def SetInt(self, key, value):
        self.ints[key] = value

    def SetString(self, key, value):
        self.strings[key] = value


class TestRemoteDebuggerService(unittest.TestCase):
    def test_read_preferences_uses_saved_values_with_defaults(self):
        module = _load_remote_debugger_service_module()
        prefs = FakePrefs(ints={"TabIndex": 1, "VSCodePort": 9000}, strings={"VSCodeAddress": "127.0.0.1"})

        self.assertEqual(
            module.read_preferences(prefs),
            {"tab_index": 1, "address": "127.0.0.1", "port": 9000},
        )

    def test_attach_debugger_starts_winpdb_and_persists_selected_tab(self):
        module = _load_remote_debugger_service_module()
        prefs = FakePrefs()
        rpdb2_module = mock.Mock()

        module.attach_debugger(
            {"tab_index": 0, "password": "secret"},
            prefs,
            rpdb2_module=rpdb2_module,
        )

        self.assertEqual(prefs.ints["TabIndex"], 0)
        rpdb2_module.start_embedded_debugger.assert_called_once_with("secret", timeout=30)

    def test_attach_debugger_starts_debugpy_and_persists_vscode_settings(self):
        module = _load_remote_debugger_service_module()
        prefs = FakePrefs()
        debugpy_module = mock.Mock()
        python_exe_getter = mock.Mock(return_value="python.exe")

        module.attach_debugger(
            {"tab_index": 1, "address": "localhost", "port": 5678},
            prefs,
            debugpy_module=debugpy_module,
            python_exe_getter=python_exe_getter,
        )

        self.assertEqual(prefs.ints["TabIndex"], 1)
        self.assertEqual(prefs.ints["VSCodePort"], 5678)
        self.assertEqual(prefs.strings["VSCodeAddress"], "localhost")
        debugpy_module.configure.assert_called_once_with(python="python.exe")
        debugpy_module.listen.assert_called_once_with(("localhost", 5678))
        debugpy_module.wait_for_client.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()