# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Unit tests for the frontend-neutral outlet-boundary task-panel presenter."""

import os
import sys
import types
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


class TestOutletBoundaryPresenter(unittest.TestCase):
    def test_validation_covers_missing_faces_and_mass_flow_requirement(self):
        from flow_studio.ui.bc_outlet_presenter import OutletBoundaryPresenter, OutletBoundarySettings

        presenter = OutletBoundaryPresenter(service=object())

        level, title, detail = presenter.build_validation(
            OutletBoundarySettings((), "Static Pressure", 101325.0, 0.0, False)
        )
        self.assertEqual(level, "incomplete")
        self.assertEqual(title, "Assign outlet faces")

        refs = ((types.SimpleNamespace(Label="OutletFace"), ("Face2",)),)
        level, title, detail = presenter.build_validation(
            OutletBoundarySettings(refs, "Mass Flow Rate", 101325.0, 0.0, True)
        )
        self.assertEqual(level, "incomplete")
        self.assertEqual(title, "Outlet mass flow rate required")

    def test_persist_settings_round_trips_service_payload(self):
        from flow_studio.ui.bc_outlet_presenter import OutletBoundaryPresenter, OutletBoundarySettings

        persisted = []
        obj = types.SimpleNamespace()

        class FakeService:
            def persist_settings(self, current_obj, settings):
                persisted.append((current_obj, settings))

        presenter = OutletBoundaryPresenter(service=FakeService())
        settings = OutletBoundarySettings((), "Static Pressure", 100500.0, 0.05, True)

        presenter.persist_settings(obj, settings)

        self.assertEqual(len(persisted), 1)
        self.assertIs(persisted[0][0], obj)
        self.assertEqual(persisted[0][1]["OutletType"], "Static Pressure")
        self.assertAlmostEqual(persisted[0][1]["StaticPressure"], 100500.0, places=6)
        self.assertTrue(persisted[0][1]["PreventBackflow"])

    def test_default_service_constructor_reads_object_state(self):
        from flow_studio.ui.bc_outlet_presenter import OutletBoundaryPresenter

        obj = types.SimpleNamespace(
            References=[],
            OutletType="Static Pressure",
            StaticPressure=101325.0,
            OutletMassFlowRate=0.0,
            PreventBackflow=False,
        )

        settings = OutletBoundaryPresenter().read_settings(obj)

        self.assertEqual(settings.outlet_type, "Static Pressure")
        self.assertAlmostEqual(settings.static_pressure, 101325.0, places=6)
        self.assertFalse(settings.prevent_backflow)


if __name__ == "__main__":
    unittest.main()