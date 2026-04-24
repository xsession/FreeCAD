# SPDX-License-Identifier: LGPL-2.1-or-later

import unittest
from pathlib import Path


class TestTaskPanelMetadata(unittest.TestCase):
    def _read(self, relative_path):
        root = Path(__file__).resolve().parents[1]
        path = root / relative_path
        return path, path.read_text(encoding="utf-8")

    def test_joint_task_publishes_live_taskview_metadata(self):
        path, source = self._read("JointObject.py")

        self.assertIn("def _refresh_taskview_metadata(self):", source, path.as_posix())
        self.assertIn('self._publish_taskview_property("taskview_context_mode", context_mode)', source, path.as_posix())
        self.assertIn('translate("Assembly", "Joint Definition")', source, path.as_posix())
        self.assertIn('translate("Assembly", "Select two references")', source, path.as_posix())
        self.assertIn("self.updateJoint()", source, path.as_posix())
        self.assertIn("self._refresh_taskview_metadata()", source, path.as_posix())

    def test_bom_task_publishes_live_taskview_metadata(self):
        path, source = self._read("CommandCreateBom.py")

        self.assertIn("def _refresh_taskview_metadata(self):", source, path.as_posix())
        self.assertIn('self._publish_taskview_property("taskview_context_mode", context_mode)', source, path.as_posix())
        self.assertIn('translate("Assembly", "Bill Of Materials Columns")', source, path.as_posix())
        self.assertIn('translate("Assembly", "Add at least one column")', source, path.as_posix())
        self.assertIn("self.updateColumnList()", source, path.as_posix())
        self.assertIn("self._refresh_taskview_metadata()", source, path.as_posix())


if __name__ == "__main__":
    unittest.main()