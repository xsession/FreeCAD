# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Aggregate architecture checks for FlowStudio canonical namespaces."""

from __future__ import annotations

import os
import unittest


class TestNamespaceArchitectureContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo_root = os.path.dirname(
            os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            )
        )
        cls.canonical_modules = {
            "src/Mod/FlowStudio/flow_studio/runtime/artifacts.py": "flow_studio.solver_artifacts",
            "src/Mod/FlowStudio/flow_studio/runtime/monitor.py": "flow_studio.runtime_monitor",
            "src/Mod/FlowStudio/flow_studio/catalog/database.py": "flow_studio.engineering_database",
            "src/Mod/FlowStudio/flow_studio/catalog/editor.py": "flow_studio.engineering_database_editor",
            "src/Mod/FlowStudio/flow_studio/tools/geometry.py": "flow_studio.geometry_tools",
            "src/Mod/FlowStudio/flow_studio/core/workflow.py": "flow_studio.workflow_guide",
        }
        cls.legacy_wrappers = {
            "src/Mod/FlowStudio/flow_studio/solver_artifacts.py": "from flow_studio.runtime.artifacts import *",
            "src/Mod/FlowStudio/flow_studio/runtime_monitor.py": "from flow_studio.runtime.monitor import *",
            "src/Mod/FlowStudio/flow_studio/engineering_database.py": "from flow_studio.catalog.database import *",
            "src/Mod/FlowStudio/flow_studio/engineering_database_editor.py": "from flow_studio.catalog.editor import",
            "src/Mod/FlowStudio/flow_studio/geometry_tools.py": "from flow_studio.tools.geometry import *",
            "src/Mod/FlowStudio/flow_studio/workflow_guide.py": "from flow_studio.core.workflow import *",
        }

    def _read(self, rel_path):
        abs_path = os.path.join(self.repo_root, rel_path)
        with open(abs_path, "r", encoding="utf-8") as handle:
            return abs_path, handle.read()

    def test_root_package_documents_grouped_namespace_strategy(self):
        path, source = self._read("src/Mod/FlowStudio/flow_studio/__init__.py")

        self.assertIn("canonical architecture surface", source, path)
        self.assertIn("compatibility shims", source, path)
        self.assertIn("flow_studio.catalog", source, path)
        self.assertIn("flow_studio.core", source, path)
        self.assertIn("flow_studio.runtime", source, path)
        self.assertIn("flow_studio.tools", source, path)
        self.assertIn("flow_studio.ui", source, path)
        self.assertIn("flow_studio.workflows", source, path)

    def test_canonical_modules_do_not_import_legacy_flat_shims(self):
        for rel_path, legacy_module in self.canonical_modules.items():
            with self.subTest(module=rel_path):
                path, source = self._read(rel_path)
                self.assertNotIn(legacy_module, source, path)

    def test_legacy_modules_remain_one_way_compatibility_wrappers(self):
        for rel_path, expected_import in self.legacy_wrappers.items():
            with self.subTest(module=rel_path):
                path, source = self._read(rel_path)
                self.assertIn("Compatibility wrapper", source, path)
                self.assertIn(expected_import, source, path)


if __name__ == "__main__":
    unittest.main()