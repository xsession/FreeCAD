# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Unit tests for the frontend-neutral generic boundary task-panel presenter."""

import os
import sys
import types
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


class TestGenericBoundaryPresenter(unittest.TestCase):
    def test_validation_covers_missing_targets_and_thermal_rules(self):
        from flow_studio.ui.generic_bc_presenter import GenericBoundaryPresenter, GenericBoundarySettings

        presenter = GenericBoundaryPresenter(service=object())

        level, title, detail = presenter.build_validation(
            GenericBoundarySettings("Boundary", "FlowStudio::BCTemperature", (), {"Temperature": 300.0})
        )
        self.assertEqual(level, "incomplete")
        self.assertEqual(title, "Assign boundary targets")

        refs = ((types.SimpleNamespace(Label="Body"), ("Face1",)),)
        level, title, detail = presenter.build_validation(
            GenericBoundarySettings("Thermal BC", "FlowStudio::BCTemperature", refs, {"Temperature": 0.0})
        )
        self.assertEqual(level, "warning")
        self.assertEqual(title, "Thermal BC temperature required")

        level, title, detail = presenter.build_validation(
            GenericBoundarySettings("Convection BC", "FlowStudio::BCConvection", refs, {"AmbientTemperature": 0.0})
        )
        self.assertEqual(level, "warning")
        self.assertEqual(title, "Convection BC ambient temperature required")

        level, title, detail = presenter.build_validation(
            GenericBoundarySettings("Convection BC", "FlowStudio::BCConvection", refs, {"AmbientTemperature": 300.0, "HeatTransferCoefficient": 0.0})
        )
        self.assertEqual(level, "warning")
        self.assertEqual(title, "Convection BC coefficient required")

        level, title, detail = presenter.build_validation(
            GenericBoundarySettings("Radiation BC", "FlowStudio::BCRadiation", refs, {"Emissivity": 1.2})
        )
        self.assertEqual(level, "warning")
        self.assertEqual(title, "Radiation BC emissivity out of range")

    def test_persist_settings_round_trips_service_payload(self):
        from flow_studio.ui.generic_bc_presenter import GenericBoundaryPresenter, GenericBoundarySettings

        persisted = []
        obj = types.SimpleNamespace()

        class FakeService:
            def persist_settings(self, current_obj, values):
                persisted.append((current_obj, values))

        presenter = GenericBoundaryPresenter(service=FakeService())
        settings = GenericBoundarySettings(
            "Convection BC",
            "FlowStudio::BCConvection",
            (),
            {"HeatTransferCoefficient": 25.0, "AmbientTemperature": 295.0},
        )

        presenter.persist_settings(obj, settings)

        self.assertEqual(len(persisted), 1)
        self.assertIs(persisted[0][0], obj)
        self.assertAlmostEqual(persisted[0][1]["HeatTransferCoefficient"], 25.0, places=6)
        self.assertAlmostEqual(persisted[0][1]["AmbientTemperature"], 295.0, places=6)

    def test_default_service_constructor_reads_object_state(self):
        from flow_studio.ui.generic_bc_presenter import GenericBoundaryPresenter

        obj = types.SimpleNamespace(
            BCLabel="Radiation BC",
            FlowType="FlowStudio::BCRadiation",
            References=[],
            Emissivity=0.85,
            AmbientTemperature=298.15,
        )

        settings = GenericBoundaryPresenter().read_settings(obj, ["Emissivity", "AmbientTemperature"])

        self.assertEqual(settings.title, "Radiation BC")
        self.assertEqual(settings.flow_type, "FlowStudio::BCRadiation")
        self.assertAlmostEqual(settings.values["Emissivity"], 0.85, places=6)
        self.assertAlmostEqual(settings.values["AmbientTemperature"], 298.15, places=6)


if __name__ == "__main__":
    unittest.main()