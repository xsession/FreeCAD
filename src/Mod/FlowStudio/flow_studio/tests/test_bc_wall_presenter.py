# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Unit tests for the frontend-neutral wall-boundary task-panel presenter."""

import os
import sys
import types
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


class TestWallBoundaryPresenter(unittest.TestCase):
    def test_validation_covers_missing_faces_and_required_wall_parameters(self):
        from flow_studio.ui.bc_wall_presenter import WallBoundaryPresenter, WallBoundarySettings

        presenter = WallBoundaryPresenter(service=object())

        level, title, detail = presenter.build_validation(
            WallBoundarySettings((), "No-Slip", "Adiabatic", 0.0, 0.0, 0.0, 0.0)
        )
        self.assertEqual(level, "incomplete")
        self.assertEqual(title, "Assign wall faces")

        refs = ((types.SimpleNamespace(Label="WallFace"), ("Face4",)),)
        level, title, detail = presenter.build_validation(
            WallBoundarySettings(refs, "No-Slip", "Fixed Temperature", 0.0, 0.0, 0.0, 0.0)
        )
        self.assertEqual(level, "incomplete")
        self.assertEqual(title, "Wall temperature required")

        level, title, detail = presenter.build_validation(
            WallBoundarySettings(refs, "No-Slip", "Heat Transfer Coefficient", 300.0, 0.0, 0.0, 0.0)
        )
        self.assertEqual(level, "incomplete")
        self.assertEqual(title, "Heat-transfer coefficient required")

        level, title, detail = presenter.build_validation(
            WallBoundarySettings(refs, "Rough Wall", "Adiabatic", 300.0, 0.0, 10.0, 0.0)
        )
        self.assertEqual(level, "incomplete")
        self.assertEqual(title, "Wall roughness required")

    def test_persist_settings_round_trips_service_payload(self):
        from flow_studio.ui.bc_wall_presenter import WallBoundaryPresenter, WallBoundarySettings

        persisted = []
        obj = types.SimpleNamespace()

        class FakeService:
            def persist_settings(self, current_obj, settings):
                persisted.append((current_obj, settings))

        presenter = WallBoundaryPresenter(service=FakeService())
        settings = WallBoundarySettings((), "Rough Wall", "Fixed Temperature", 325.0, 100.0, 15.0, 0.001)

        presenter.persist_settings(obj, settings)

        self.assertEqual(len(persisted), 1)
        self.assertIs(persisted[0][0], obj)
        self.assertEqual(persisted[0][1]["WallType"], "Rough Wall")
        self.assertAlmostEqual(persisted[0][1]["WallTemperature"], 325.0, places=6)
        self.assertAlmostEqual(persisted[0][1]["RoughnessHeight"], 0.001, places=6)

    def test_default_service_constructor_reads_object_state(self):
        from flow_studio.ui.bc_wall_presenter import WallBoundaryPresenter

        obj = types.SimpleNamespace(
            References=[],
            WallType="No-Slip",
            ThermalType="Adiabatic",
            WallTemperature=293.15,
            HeatFlux=0.0,
            HeatTransferCoeff=0.0,
            RoughnessHeight=0.0,
        )

        settings = WallBoundaryPresenter().read_settings(obj)

        self.assertEqual(settings.wall_type, "No-Slip")
        self.assertEqual(settings.thermal_type, "Adiabatic")
        self.assertAlmostEqual(settings.wall_temperature, 293.15, places=6)


if __name__ == "__main__":
    unittest.main()