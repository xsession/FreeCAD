# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Static contract checks for the canonical FlowStudio workflow namespace."""

from __future__ import annotations

import os
import unittest


class TestWorkflowNamespaceContract(unittest.TestCase):
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

    def test_core_workflow_module_is_canonical(self):
        path, source = self._read("src/Mod/FlowStudio/flow_studio/core/workflow.py")

        self.assertIn("Canonical workflow status and activation helpers", source, path)
        self.assertIn("def get_workflow_context(analysis=None)", source, path)
        self.assertIn("def get_workflow_status()", source, path)
        self.assertIn("class WorkflowChecker", source, path)
        self.assertIn("from flow_studio.ui.layouts import get_workspace_layout", source, path)

    def test_flat_workflow_module_is_compatibility_wrapper(self):
        path, source = self._read("src/Mod/FlowStudio/flow_studio/workflow_guide.py")

        self.assertIn("Compatibility wrapper", source, path)
        self.assertIn("from flow_studio.core.workflow import *", source, path)

    def test_workflow_clients_use_canonical_namespace(self):
        commands_path, commands_source = self._read("src/Mod/FlowStudio/flow_studio/commands.py")
        cockpit_path, cockpit_source = self._read("src/Mod/FlowStudio/flow_studio/taskpanels/task_project_cockpit.py")

        self.assertIn("from flow_studio.core.workflow import get_workflow_context, get_workflow_status", commands_source, commands_path)
        self.assertIn(
            "from flow_studio.core.workflow import get_active_analysis, get_workflow_context, get_workflow_status",
            cockpit_source,
            cockpit_path,
        )


if __name__ == "__main__":
    unittest.main()