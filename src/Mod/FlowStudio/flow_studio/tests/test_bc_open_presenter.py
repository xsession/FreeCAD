# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Unit tests for the frontend-neutral open-boundary task-panel presenter."""

import os
import sys
import types
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


class TestOpenBoundaryPresenter(unittest.TestCase):
    def test_validation_covers_missing_faces_and_temperature(self):
        from flow_studio.ui.bc_open_presenter import OpenBoundaryPresenter, OpenBoundarySettings

        presenter = OpenBoundaryPresenter(service=object())

        level, title, detail = presenter.build_validation(
            OpenBoundarySettings((), 101325.0, 293.15, 0.0, 0.0, 0.0)
        )
        self.assertEqual(level, "incomplete")
        self.assertEqual(title, "Assign open-boundary faces")

        refs = ((types.SimpleNamespace(Label="Enclosure"), ("Face3",)),)
        level, title, detail = presenter.build_validation(
            OpenBoundarySettings(refs, 101325.0, 0.0, 0.0, 0.0, 0.0)
        )
        self.assertEqual(level, "incomplete")
        self.assertEqual(title, "Far-field temperature required")

    def test_persist_settings_round_trips_service_payload(self):
        from flow_studio.ui.bc_open_presenter import OpenBoundaryPresenter, OpenBoundarySettings

        persisted = []
        obj = types.SimpleNamespace()

        class FakeService:
            def persist_settings(self, current_obj, settings):
                persisted.append((current_obj, settings))

        presenter = OpenBoundaryPresenter(service=FakeService())
        settings = OpenBoundarySettings((), 101325.0, 305.0, 14.0, 1.0, -2.0)

        presenter.persist_settings(obj, settings)

        self.assertEqual(len(persisted), 1)
        self.assertIs(persisted[0][0], obj)
        self.assertAlmostEqual(persisted[0][1]["FarFieldTemperature"], 305.0, places=6)
        self.assertAlmostEqual(persisted[0][1]["FarFieldVelocityX"], 14.0, places=6)

    def test_default_service_constructor_reads_object_state(self):
        from flow_studio.ui.bc_open_presenter import OpenBoundaryPresenter

        obj = types.SimpleNamespace(
            References=[],
            FarFieldPressure=101325.0,
            FarFieldTemperature=293.15,
            FarFieldVelocityX=0.0,
            FarFieldVelocityY=0.0,
            FarFieldVelocityZ=0.0,
        )

        settings = OpenBoundaryPresenter().read_settings(obj)

        self.assertAlmostEqual(settings.far_field_pressure, 101325.0, places=6)
        self.assertAlmostEqual(settings.far_field_temperature, 293.15, places=6)


if __name__ == "__main__":
    unittest.main()