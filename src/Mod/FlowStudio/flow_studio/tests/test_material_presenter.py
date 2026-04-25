# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Unit tests for the frontend-neutral material task-panel presenter."""

import os
import sys
import types
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


class TestMaterialPresenter(unittest.TestCase):
    def test_validation_covers_missing_targets_name_and_positive_properties(self):
        from flow_studio.ui.material_presenter import MaterialPresenter, MaterialSettings

        presenter = MaterialPresenter(service=object())

        level, title, detail = presenter.build_validation(
            MaterialSettings(
                flow_type="FlowStudio::ThermalMaterial",
                properties=("References", "MaterialPreset", "MaterialName", "Density", "ThermalConductivity"),
                references=(),
                material_preset="Custom",
                material_name="",
                values={"Density": 1000.0, "ThermalConductivity": 1.0},
            )
        )
        self.assertEqual(level, "incomplete")
        self.assertEqual(title, "Assign material targets")

        level, title, detail = presenter.build_validation(
            MaterialSettings(
                flow_type="FlowStudio::ThermalMaterial",
                properties=("References", "MaterialPreset", "MaterialName", "Density", "ThermalConductivity"),
                references=((types.SimpleNamespace(Label="Housing"), ("Solid1",)),),
                material_preset="Custom",
                material_name="",
                values={"Density": 1000.0, "ThermalConductivity": 1.0},
            )
        )
        self.assertEqual(level, "incomplete")
        self.assertEqual(title, "Material name required")

        level, title, detail = presenter.build_validation(
            MaterialSettings(
                flow_type="FlowStudio::ThermalMaterial",
                properties=("References", "MaterialPreset", "MaterialName", "Density", "ThermalConductivity"),
                references=((types.SimpleNamespace(Label="Housing"), ("Solid1",)),),
                material_preset="Custom",
                material_name="Copper",
                values={"Density": 8960.0, "ThermalConductivity": 0.0},
            )
        )
        self.assertEqual(level, "warning")
        self.assertEqual(title, "Thermal conductivity must be positive")

    def test_apply_preset_updates_name_and_known_numeric_values(self):
        from flow_studio.ui.material_presenter import MaterialPresenter, MaterialSettings

        presenter = MaterialPresenter()
        settings = MaterialSettings(
            flow_type="FlowStudio::ThermalMaterial",
            properties=("References", "MaterialPreset", "MaterialName", "Density", "ThermalConductivity", "SpecificHeat", "Emissivity"),
            references=((types.SimpleNamespace(Label="Housing"), ("Solid1",)),),
            material_preset="Custom",
            material_name="Material",
            values={
                "Density": 5000.0,
                "ThermalConductivity": 10.0,
                "SpecificHeat": 100.0,
                "Emissivity": 0.5,
            },
        )

        applied = presenter.apply_preset(settings, "Copper")

        self.assertEqual(applied.material_name, "Copper")
        self.assertAlmostEqual(applied.values["ThermalConductivity"], 385.0, places=3)
        self.assertAlmostEqual(applied.values["Emissivity"], 0.03, places=3)

    def test_persist_settings_round_trips_service_payload(self):
        from flow_studio.ui.material_presenter import MaterialPresenter, MaterialSettings

        persisted = []
        obj = types.SimpleNamespace()

        class FakeService:
            def persist_state(self, current_obj, state):
                persisted.append((current_obj, state))

        presenter = MaterialPresenter(service=FakeService())
        settings = MaterialSettings(
            flow_type="FlowStudio::ThermalMaterial",
            properties=("References", "MaterialPreset", "MaterialName", "Density", "ThermalConductivity", "SpecificHeat", "Emissivity"),
            references=((types.SimpleNamespace(Label="Housing"), ("Solid1",)),),
            material_preset="Copper",
            material_name="Copper",
            values={
                "Density": 8960.0,
                "ThermalConductivity": 385.0,
                "SpecificHeat": 385.0,
                "Emissivity": 0.12,
            },
        )

        presenter.persist_settings(obj, settings)

        self.assertEqual(len(persisted), 1)
        self.assertIs(persisted[0][0], obj)
        self.assertEqual(persisted[0][1]["MaterialPreset"], "Copper")
        self.assertEqual(persisted[0][1]["MaterialName"], "Copper")
        self.assertAlmostEqual(persisted[0][1]["Values"]["Emissivity"], 0.12, places=3)


if __name__ == "__main__":
    unittest.main()