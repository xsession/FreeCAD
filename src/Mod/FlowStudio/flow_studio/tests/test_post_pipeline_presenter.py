# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Unit tests for the frontend-neutral post-pipeline task-panel presenter."""

import os
import sys
import types
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


class TestPostPipelinePresenter(unittest.TestCase):
    def test_validation_covers_missing_results_invalid_field_and_manual_range(self):
        from flow_studio.ui.post_pipeline_presenter import PostPipelinePresenter, PostPipelineSettings

        presenter = PostPipelinePresenter(service=object())

        level, title, detail = presenter.build_validation(
            PostPipelineSettings("Contour (Surface)", "U", True, 0.0, 1.0, (), "")
        )
        self.assertEqual(level, "info")
        self.assertEqual(title, "Load results to begin post-processing")

        level, title, detail = presenter.build_validation(
            PostPipelineSettings("Contour (Surface)", "T", True, 0.0, 1.0, ("U", "p"), "C:/tmp/case.vtk")
        )
        self.assertEqual(level, "warning")
        self.assertEqual(title, "Active field is not available")

        level, title, detail = presenter.build_validation(
            PostPipelineSettings("Contour (Surface)", "U", False, 5.0, 1.0, ("U", "p"), "C:/tmp/case.vtk")
        )
        self.assertEqual(level, "warning")
        self.assertEqual(title, "Manual range is invalid")

    def test_persist_settings_round_trips_service_payload(self):
        from flow_studio.ui.post_pipeline_presenter import PostPipelinePresenter, PostPipelineSettings

        persisted = []
        obj = types.SimpleNamespace()

        class FakeService:
            def persist_settings(self, current_obj, settings):
                persisted.append((current_obj, settings))

        presenter = PostPipelinePresenter(service=FakeService())
        settings = PostPipelineSettings(
            "Vectors",
            "U",
            False,
            -2.0,
            15.0,
            ("U", "p"),
            "C:/tmp/case.vtk",
        )

        presenter.persist_settings(obj, settings)

        self.assertEqual(len(persisted), 1)
        self.assertIs(persisted[0][0], obj)
        self.assertEqual(persisted[0][1]["VisualizationType"], "Vectors")
        self.assertEqual(persisted[0][1]["ActiveField"], "U")
        self.assertFalse(persisted[0][1]["AutoRange"])

    def test_default_service_constructor_reads_object_state(self):
        from flow_studio.ui.post_pipeline_presenter import PostPipelinePresenter

        obj = types.SimpleNamespace(
            VisualizationType="Contour (Surface)",
            ActiveField="U",
            AutoRange=True,
            MinRange=0.0,
            MaxRange=1.0,
            AvailableFields=["U", "p"],
            ResultFile="C:/tmp/case.vtk",
        )

        settings = PostPipelinePresenter().read_settings(obj)

        self.assertEqual(settings.visualization_type, "Contour (Surface)")
        self.assertEqual(settings.available_fields, ("U", "p"))
        self.assertEqual(settings.result_file, "C:/tmp/case.vtk")


if __name__ == "__main__":
    unittest.main()