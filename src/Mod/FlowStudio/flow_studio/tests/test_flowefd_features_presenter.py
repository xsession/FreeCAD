# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Unit tests for frontend-neutral FloEFD feature presenters."""

import os
import sys
import types
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


class TestFanPresenter(unittest.TestCase):
    def test_curve_state_applies_preset_values(self):
        from flow_studio.ui.flowefd_features_presenter import FanPresenter

        presenter = FanPresenter(service=object())
        state = presenter.build_curve_state(
            "PresetA",
            {"PresetA": {"FanType": "External Inlet Fan", "ReferencePressure": 12.5, "curve": [(1.0, 2.0)]}},
        )

        self.assertEqual(state["FanType"], "External Inlet Fan")
        self.assertAlmostEqual(state["ReferencePressure"], 12.5, places=6)
        self.assertEqual(state["Curve"], [("1.0", "2.0")])

    def test_persist_settings_round_trips_payload(self):
        from flow_studio.ui.flowefd_features_presenter import FanPresenter, FanSettings

        persisted = []

        class FakeService:
            def persist_settings(self, obj, settings):
                persisted.append((obj, settings))

        obj = types.SimpleNamespace()
        presenter = FanPresenter(service=FakeService())
        presenter.persist_settings(obj, FanSettings((), "Internal Fan", "PresetA", 101325.0, True))

        self.assertEqual(persisted[0][1]["FanCurvePreset"], "PresetA")
        self.assertTrue(persisted[0][1]["CreateAssociatedGoals"])


class TestResultPlotPresenter(unittest.TestCase):
    def test_validation_covers_missing_targets_field_and_modes(self):
        from flow_studio.ui.flowefd_features_presenter import ResultPlotPresenter, ResultPlotSettings

        presenter = ResultPlotPresenter(service=object())

        level, title, detail = presenter.build_validation(
            ResultPlotSettings((), "Surface Plot", "Pressure", 10, True, False, False, False, "XY Plane", 0.0, True, True, False)
        )
        self.assertEqual(title, "Assign plot targets")

        refs = ((types.SimpleNamespace(Label="Wall"), ("Face1",)),)
        level, title, detail = presenter.build_validation(
            ResultPlotSettings(refs, "Surface Plot", "", 10, True, False, False, False, "XY Plane", 0.0, True, True, False)
        )
        self.assertEqual(title, "Result field required")

        level, title, detail = presenter.build_validation(
            ResultPlotSettings(refs, "Surface Plot", "Pressure", 10, False, False, False, False, "XY Plane", 0.0, True, True, False)
        )
        self.assertEqual(title, "Enable a display mode")


class TestParticleStudyPresenter(unittest.TestCase):
    def test_validation_covers_injections_gravity_diameter_and_limits(self):
        from flow_studio.ui.flowefd_features_presenter import ParticleStudyPresenter, ParticleStudySettings

        presenter = ParticleStudyPresenter(service=object())

        level, title, detail = presenter.build_validation(
            ParticleStudySettings((), False, False, True, (0.0, 0.0, 0.0), "Spheres", 0.004, "Pressure", 10.0, 3600.0, 100)
        )
        self.assertEqual(title, "Assign particle injections")

        refs = ((types.SimpleNamespace(Label="Inlet"), ("Face1",)),)
        level, title, detail = presenter.build_validation(
            ParticleStudySettings(refs, False, False, True, (0.0, 0.0, 0.0), "Spheres", 0.004, "Pressure", 10.0, 3600.0, 100)
        )
        self.assertEqual(title, "Gravity vector is zero")

        level, title, detail = presenter.build_validation(
            ParticleStudySettings(refs, False, False, False, (0.0, -9.81, 0.0), "Spheres", 0.0, "Pressure", 10.0, 3600.0, 100)
        )
        self.assertEqual(title, "Particle diameter required")

        level, title, detail = presenter.build_validation(
            ParticleStudySettings(refs, False, False, False, (0.0, -9.81, 0.0), "Spheres", 0.002, "Pressure", 0.0, 0.0, 100)
        )
        self.assertEqual(title, "Tracking limits required")


if __name__ == "__main__":
    unittest.main()