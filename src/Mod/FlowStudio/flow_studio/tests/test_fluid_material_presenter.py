# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Unit tests for the frontend-neutral fluid material task-panel presenter."""

import os
import sys
import types
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


class TestFluidMaterialPresenter(unittest.TestCase):
    def test_validation_covers_missing_regions_density_and_specific_heat(self):
        from flow_studio.ui.fluid_material_presenter import FluidMaterialPresenter, FluidMaterialSettings

        presenter = FluidMaterialPresenter(service=object())

        level, title, detail = presenter.build_validation(
            FluidMaterialSettings((), "Custom", 1.0, 1.0e-3, 1.0e-6, 1000.0, 0.1, 1.0)
        )
        self.assertEqual(level, "incomplete")
        self.assertEqual(title, "Assign fluid regions")

        refs = ((types.SimpleNamespace(Label="Domain"), ("Solid1",)),)
        level, title, detail = presenter.build_validation(
            FluidMaterialSettings(refs, "Custom", 0.0, 1.0e-3, 1.0e-6, 1000.0, 0.1, 1.0)
        )
        self.assertEqual(level, "incomplete")
        self.assertEqual(title, "Fluid density required")

        level, title, detail = presenter.build_validation(
            FluidMaterialSettings(refs, "Custom", 998.2, 1.0e-3, 1.0e-6, 0.0, 0.1, 1.0)
        )
        self.assertEqual(level, "warning")
        self.assertEqual(title, "Specific heat should be positive")

    def test_apply_preset_updates_transport_properties(self):
        from flow_studio.ui.fluid_material_presenter import FluidMaterialPresenter, FluidMaterialSettings

        presenter = FluidMaterialPresenter()
        settings = FluidMaterialSettings(
            (),
            "Custom",
            1.0,
            1.0e-3,
            1.0e-6,
            1000.0,
            0.1,
            1.0,
        )

        applied = presenter.apply_preset(settings, "Water (20°C)")

        self.assertAlmostEqual(applied.density, 998.2, places=3)
        self.assertAlmostEqual(applied.dynamic_viscosity, 1.002e-3, places=7)
        self.assertAlmostEqual(applied.specific_heat, 4182.0, places=3)

    def test_persist_settings_round_trips_service_payload(self):
        from flow_studio.ui.fluid_material_presenter import FluidMaterialPresenter, FluidMaterialSettings

        persisted = []
        obj = types.SimpleNamespace()

        class FakeService:
            def persist_settings(self, current_obj, settings):
                persisted.append((current_obj, settings))

        presenter = FluidMaterialPresenter(service=FakeService())
        settings = FluidMaterialSettings(
            (),
            "Water (20°C)",
            998.2,
            1.002e-3,
            1.004e-6,
            4200.0,
            0.6,
            7.01,
        )

        presenter.persist_settings(obj, settings)

        self.assertEqual(len(persisted), 1)
        self.assertIs(persisted[0][0], obj)
        self.assertEqual(persisted[0][1]["Preset"], "Water (20°C)")
        self.assertAlmostEqual(persisted[0][1]["SpecificHeat"], 4200.0, places=3)


if __name__ == "__main__":
    unittest.main()