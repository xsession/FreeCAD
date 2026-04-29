# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Unit tests for the frontend-neutral inlet-boundary task-panel presenter."""

import os
import sys
import types
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


class TestInletBoundaryPresenter(unittest.TestCase):
    def test_validation_covers_missing_faces_and_flow_requirements(self):
        from flow_studio.ui.bc_inlet_presenter import InletBoundaryPresenter, InletBoundarySettings

        presenter = InletBoundaryPresenter(service=object())

        level, title, detail = presenter.build_validation(
            InletBoundarySettings((), "Velocity", 1.0, 0.0, 0.0, False, 0.0, 0.0, "", 0.0, 293.15)
        )
        self.assertEqual(level, "incomplete")
        self.assertEqual(title, "Assign inlet faces")

        refs = ((types.SimpleNamespace(Label="InletFace"), ("Face1",)),)
        level, title, detail = presenter.build_validation(
            InletBoundarySettings(refs, "Mass Flow Rate", 0.0, 0.0, 0.0, False, 0.0, 0.0, "", 0.0, 293.15)
        )
        self.assertEqual(level, "incomplete")
        self.assertEqual(title, "Mass flow rate required")

        level, title, detail = presenter.build_validation(
            InletBoundarySettings(refs, "Volumetric Flow Rate", 0.0, 0.0, 0.0, False, 0.0, 0.0, "", 0.0, 293.15)
        )
        self.assertEqual(level, "incomplete")
        self.assertEqual(title, "Volumetric flow rate required")

    def test_persist_settings_round_trips_service_payload(self):
        from flow_studio.ui.bc_inlet_presenter import InletBoundaryPresenter, InletBoundarySettings

        persisted = []
        obj = types.SimpleNamespace()

        class FakeService:
            def persist_settings(self, current_obj, settings):
                persisted.append((current_obj, settings))

        presenter = InletBoundaryPresenter(service=FakeService())
        settings = InletBoundarySettings((), "Velocity", 12.0, 1.5, -0.5, True, 0.2, 0.1, "k & Omega", 4.5, 310.0)

        presenter.persist_settings(obj, settings)

        self.assertEqual(len(persisted), 1)
        self.assertIs(persisted[0][0], obj)
        self.assertEqual(persisted[0][1]["InletType"], "Velocity")
        self.assertAlmostEqual(persisted[0][1]["Ux"], 12.0, places=6)
        self.assertTrue(persisted[0][1]["NormalToFace"])

    def test_default_service_constructor_reads_object_state(self):
        from flow_studio.ui.bc_inlet_presenter import InletBoundaryPresenter

        obj = types.SimpleNamespace(
            References=[],
            InletType="Velocity",
            Ux=10.0,
            Uy=1.0,
            Uz=2.0,
            NormalToFace=True,
            MassFlowRate=0.0,
            VolFlowRate=0.0,
            TurbulenceSpec="Intensity & Length Scale",
            TurbulenceIntensity=5.0,
            InletTemperature=295.0,
        )

        settings = InletBoundaryPresenter().read_settings(obj)

        self.assertEqual(settings.inlet_type, "Velocity")
        self.assertAlmostEqual(settings.velocity_x, 10.0, places=6)
        self.assertTrue(settings.normal_to_face)


if __name__ == "__main__":
    unittest.main()