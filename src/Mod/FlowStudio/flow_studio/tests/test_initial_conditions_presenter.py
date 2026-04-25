# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Unit tests for the frontend-neutral initial conditions task-panel presenter."""

import os
import sys
import types
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


class TestInitialConditionsPresenter(unittest.TestCase):
    def test_validation_covers_missing_regions_temperature_and_turbulence_rules(self):
        from flow_studio.ui.initial_conditions_presenter import InitialConditionsPresenter, InitialConditionsSettings

        presenter = InitialConditionsPresenter(service=object())

        level, title, detail = presenter.build_validation(
            InitialConditionsSettings((), 0.0, 0.0, 0.0, 0.0, 293.15, 0.001, 1.0, False)
        )
        self.assertEqual(level, "incomplete")
        self.assertEqual(title, "Assign target regions")

        refs = ((types.SimpleNamespace(Label="Fluid Domain"), ("Solid1",)),)
        level, title, detail = presenter.build_validation(
            InitialConditionsSettings(refs, 0.0, 0.0, 0.0, 0.0, -5.0, 0.001, 1.0, False)
        )
        self.assertEqual(level, "incomplete")
        self.assertEqual(title, "Initial temperature required")

        level, title, detail = presenter.build_validation(
            InitialConditionsSettings(refs, 0.0, 0.0, 0.0, 0.0, 293.15, -0.001, 1.0, False)
        )
        self.assertEqual(level, "warning")
        self.assertEqual(title, "Turbulent kinetic energy cannot be negative")

    def test_persist_settings_round_trips_service_payload(self):
        from flow_studio.ui.initial_conditions_presenter import InitialConditionsPresenter, InitialConditionsSettings

        persisted = []
        obj = types.SimpleNamespace()

        class FakeService:
            def persist_settings(self, current_obj, settings):
                persisted.append((current_obj, settings))

        presenter = InitialConditionsPresenter(service=FakeService())
        settings = InitialConditionsSettings(
            (),
            4.0,
            1.5,
            -0.5,
            101325.0,
            310.0,
            0.002,
            2.0,
            True,
        )

        presenter.persist_settings(obj, settings)

        self.assertEqual(len(persisted), 1)
        self.assertIs(persisted[0][0], obj)
        self.assertAlmostEqual(persisted[0][1]["Ux"], 4.0, places=6)
        self.assertAlmostEqual(persisted[0][1]["Temperature"], 310.0, places=6)
        self.assertTrue(persisted[0][1]["UsePotentialFlow"])

    def test_default_service_constructor_reads_object_state(self):
        from flow_studio.ui.initial_conditions_presenter import InitialConditionsPresenter

        obj = types.SimpleNamespace(
            References=[],
            Ux=0.0,
            Uy=0.0,
            Uz=0.0,
            Pressure=0.0,
            Temperature=293.15,
            TurbulentKineticEnergy=0.001,
            SpecificDissipationRate=1.0,
            UsePotentialFlow=False,
        )

        settings = InitialConditionsPresenter().read_settings(obj)

        self.assertAlmostEqual(settings.temperature, 293.15, places=6)
        self.assertAlmostEqual(settings.turbulent_kinetic_energy, 0.001, places=6)
        self.assertFalse(settings.use_potential_flow)


if __name__ == "__main__":
    unittest.main()