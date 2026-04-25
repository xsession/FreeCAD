# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Static contract checks for the canonical FlowStudio runtime namespace."""

from __future__ import annotations

import os
import unittest


class TestRuntimeNamespaceContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo_root = os.path.dirname(
            os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            )
        )

    def _read(self, rel_path):
        abs_path = os.path.join(self.repo_root, rel_path)
        with open(abs_path, "r", encoding="utf-8") as handle:
            return abs_path, handle.read()

    def test_runtime_package_is_canonical_and_headless_safe(self):
        path, source = self._read("src/Mod/FlowStudio/flow_studio/runtime/__init__.py")

        self.assertIn("from flow_studio.runtime.artifacts import *", source, path)
        self.assertIn("from flow_studio.runtime.dependencies import *", source, path)
        self.assertIn("from flow_studio.runtime.installer import *", source, path)
        self.assertIn("try:", source, path)
        self.assertIn("from flow_studio.runtime.monitor import *", source, path)
        self.assertIn('if exc.name != "FreeCAD"', source, path)

    def test_flat_runtime_modules_are_compatibility_wrappers(self):
        monitor_path, monitor_source = self._read("src/Mod/FlowStudio/flow_studio/runtime_monitor.py")
        artifacts_path, artifacts_source = self._read("src/Mod/FlowStudio/flow_studio/solver_artifacts.py")

        self.assertIn("Compatibility wrapper", monitor_source, monitor_path)
        self.assertIn("from flow_studio.runtime.monitor import *", monitor_source, monitor_path)
        self.assertIn("Compatibility wrapper", artifacts_source, artifacts_path)
        self.assertIn("from flow_studio.runtime.artifacts import *", artifacts_source, artifacts_path)

    def test_runtime_clients_use_canonical_namespace(self):
        commands_path, commands_source = self._read("src/Mod/FlowStudio/flow_studio/commands.py")
        cockpit_path, cockpit_source = self._read("src/Mod/FlowStudio/flow_studio/taskpanels/task_project_cockpit.py")
        executor_path, executor_source = self._read(
            "src/Mod/FlowStudio/flow_studio/enterprise/services/process_executor.py"
        )
        deps_path, deps_source = self._read("src/Mod/FlowStudio/flow_studio/solver_deps.py")

        self.assertIn("from flow_studio.runtime.monitor import register_run", commands_source, commands_path)
        self.assertIn("from flow_studio.runtime.monitor import terminate_run", commands_source, commands_path)
        self.assertIn(
            "from flow_studio.runtime.monitor import get_run_snapshot, sync_post_pipeline, terminate_run",
            cockpit_source,
            cockpit_path,
        )
        self.assertIn("from flow_studio.runtime.artifacts import resolve_solver_artifact", executor_source, executor_path)
        self.assertIn(
            "from flow_studio.runtime.artifacts import artifact_search_dirs, resolve_solver_artifact",
            deps_source,
            deps_path,
        )


if __name__ == "__main__":
    unittest.main()
