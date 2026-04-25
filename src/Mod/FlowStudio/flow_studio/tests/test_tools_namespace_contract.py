# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Static contract checks for the canonical FlowStudio tools namespace."""

from __future__ import annotations

import os
import unittest


class TestToolsNamespaceContract(unittest.TestCase):
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

    def test_grouped_geometry_module_is_canonical(self):
        path, source = self._read("src/Mod/FlowStudio/flow_studio/tools/geometry.py")

        self.assertIn("class GeometryCheckOptions", source, path)
        self.assertIn("def analyze_shape_topology(shape, use_cache=True)", source, path)
        self.assertIn("def import_step_optimized(path, document=None, object_name=None, repair=False)", source, path)
        self.assertIn("def generate_mesh_from_geometry(mesh_obj, geometry_objects=None, output_dir=None, options=None)", source, path)
        self.assertIn("def run_leak_tracking(source_ref, target_ref, document=None, tolerance=1e-5)", source, path)

    def test_flat_geometry_module_is_compatibility_wrapper(self):
        path, source = self._read("src/Mod/FlowStudio/flow_studio/geometry_tools.py")

        self.assertIn("Compatibility wrapper", source, path)
        self.assertIn("from flow_studio.tools.geometry import *", source, path)

    def test_geometry_clients_use_canonical_namespace(self):
        commands_path, commands_source = self._read("src/Mod/FlowStudio/flow_studio/commands.py")
        mesh_path, mesh_source = self._read("src/Mod/FlowStudio/flow_studio/taskpanels/task_mesh_gmsh.py")
        task_path, task_source = self._read("src/Mod/FlowStudio/flow_studio/taskpanels/task_geometry_tools.py")

        self.assertIn("from flow_studio.tools.geometry import import_step_optimized", commands_source, commands_path)
        self.assertIn("from flow_studio.tools.geometry import generate_mesh_from_geometry", mesh_source, mesh_path)
        self.assertIn("from flow_studio.tools.geometry import (", task_source, task_path)


if __name__ == "__main__":
    unittest.main()