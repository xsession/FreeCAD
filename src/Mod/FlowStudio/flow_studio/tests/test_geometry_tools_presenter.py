# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Unit tests for frontend-neutral geometry-tools presenters."""

import os
import sys
import types
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


class TestGeometryCheckPresenter(unittest.TestCase):
    def test_validation_covers_selection_pending_results_and_failures(self):
        from flow_studio.ui.geometry_tools_presenter import GeometryCheckPresenter

        presenter = GeometryCheckPresenter()

        level, title, detail = presenter.build_validation(0, None)
        self.assertEqual(level, "incomplete")
        self.assertEqual(title, "Select geometry to analyze")

        level, title, detail = presenter.build_validation(1, None)
        self.assertEqual(level, "info")
        self.assertEqual(title, "Run geometry check")

        blocking = types.SimpleNamespace(errors=["open shell"], issues=[], warnings=[])
        level, title, detail = presenter.build_validation(1, blocking)
        self.assertEqual(level, "warning")
        self.assertEqual(title, "Geometry blocks meshing")

        issues_only = types.SimpleNamespace(errors=[], issues=["small gap"], warnings=[])
        level, title, detail = presenter.build_validation(1, issues_only)
        self.assertEqual(title, "Geometry issues detected")

    def test_result_formatting_covers_success_and_issues(self):
        from flow_studio.ui.geometry_tools_presenter import GeometryCheckPresenter

        presenter = GeometryCheckPresenter()
        result = types.SimpleNamespace(
            status="SUCCESSFUL",
            analysis_type="Default",
            fluid_volume=1.25,
            solid_volume=2.5,
            mesh_ready=True,
            objects=[types.SimpleNamespace(label="Body", solids=1, shells=0, faces=6, volume=1.25)],
            errors=[],
            warnings=[],
            issues=[],
        )

        lines = presenter.build_results(result)

        self.assertIn("Status: SUCCESSFUL. Geometry is OK", lines[0])
        self.assertIn("Mesh readiness: ready", lines[4])
        self.assertEqual(lines[-1], "All checked bodies look closed enough for setup.")
        self.assertEqual(presenter.volume_button_text(True), "Hide Fluid Volume")
        self.assertEqual(presenter.volume_button_text(False), "Show Fluid Volume")


class TestLeakTrackingPresenter(unittest.TestCase):
    def test_validation_and_result_formatting(self):
        from flow_studio.ui.geometry_tools_presenter import LeakTrackingPresenter

        presenter = LeakTrackingPresenter()

        level, title, detail = presenter.build_validation(None, None)
        self.assertEqual(level, "incomplete")
        self.assertEqual(title, "Select internal and external faces")

        face_ref = ("Body", "Face1")
        level, title, detail = presenter.build_validation(face_ref, face_ref)
        self.assertEqual(level, "warning")
        self.assertEqual(title, "Faces must be different")

        level, title, detail = presenter.build_validation(("A", "Face1"), ("B", "Face2"))
        self.assertEqual(level, "info")
        self.assertEqual(title, "Ready to find connection")

        self.assertEqual(
            presenter.build_results({"status": "FOUND", "messages": ["Connected via Body001"]}),
            ["Status: FOUND", "Connected via Body001"],
        )


if __name__ == "__main__":
    unittest.main()