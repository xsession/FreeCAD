# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Unit tests for the frontend-neutral Gmsh mesh presenter."""

import os
import sys
import types
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


class TestMeshGmshPresenter(unittest.TestCase):
    def test_validation_flags_non_positive_base_size_and_invalid_ranges(self):
        from flow_studio.ui.mesh_gmsh_presenter import MeshGmshPresenter, MeshGmshSettings

        presenter = MeshGmshPresenter(service=object())

        level, title, detail = presenter.build_validation(
            MeshGmshSettings(0.0, 1.0, 2.0, "Delaunay", "1st Order", "Tetrahedral", 1.2, 3, "GMSH (.msh)")
        )
        self.assertEqual(level, "error")
        self.assertIn("positive", title)

        level, title, detail = presenter.build_validation(
            MeshGmshSettings(5.0, 10.0, 2.0, "Delaunay", "1st Order", "Tetrahedral", 1.2, 3, "GMSH (.msh)")
        )
        self.assertEqual(level, "warning")
        self.assertIn("Minimum size exceeds maximum size", title)
        self.assertIn("increase the maximum element size", detail)

    def test_run_mesh_persists_settings_and_returns_success_state(self):
        from flow_studio.ui.mesh_gmsh_presenter import MeshGmshPresenter, MeshGmshSettings

        persisted = []
        obj = types.SimpleNamespace()
        result = types.SimpleNamespace(status="SUCCESSFUL", mesh_file="C:/tmp/case.msh", num_cells=120, num_points=42)

        class FakeService:
            def read_settings(self, _obj):
                return {}

            def persist_settings(self, current_obj, settings):
                persisted.append((current_obj, settings))

            def generate_mesh(self, current_obj):
                return result

        presenter = MeshGmshPresenter(service=FakeService())
        settings = MeshGmshSettings(5.0, 1.0, 10.0, "Delaunay", "1st Order", "Tetrahedral", 1.2, 3, "GMSH (.msh)")

        state = presenter.run_mesh(obj, settings)

        self.assertEqual(len(persisted), 1)
        self.assertIs(persisted[0][0], obj)
        self.assertEqual(persisted[0][1]["CharacteristicLength"], 5.0)
        self.assertEqual(state.status, "SUCCESSFUL")
        self.assertEqual(state.stats_text, "Cells: 120 | Points: 42")
        self.assertIn("Mesh generated successfully", state.console_message)
        self.assertFalse(state.show_warning)

    def test_run_mesh_returns_warning_state_when_generation_is_blocked(self):
        from flow_studio.ui.mesh_gmsh_presenter import MeshGmshPresenter, MeshGmshSettings

        result = types.SimpleNamespace(status="ERROR", issues=["Gap is not watertight"])

        class FakeService:
            def read_settings(self, _obj):
                return {}

            def persist_settings(self, _obj, _settings):
                return None

            def generate_mesh(self, _obj):
                return result

        presenter = MeshGmshPresenter(service=FakeService())
        settings = MeshGmshSettings(5.0, 1.0, 10.0, "Delaunay", "1st Order", "Tetrahedral", 1.2, 3, "GMSH (.msh)")

        state = presenter.run_mesh(types.SimpleNamespace(), settings)

        self.assertEqual(state.status, "ERROR")
        self.assertTrue(state.show_warning)
        self.assertEqual(state.stats_text, "Mesh blocked by geometry issues")
        self.assertIn("Gap is not watertight", state.dialog_message)


if __name__ == "__main__":
    unittest.main()