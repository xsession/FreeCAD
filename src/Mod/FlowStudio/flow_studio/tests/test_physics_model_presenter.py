# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Unit tests for the frontend-neutral physics model task-panel presenter."""

import os
import sys
import types
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


class TestPhysicsModelPresenter(unittest.TestCase):
    def test_validation_covers_buoyancy_and_laminar_rules(self):
        from flow_studio.ui.physics_model_presenter import PhysicsModelPresenter, PhysicsModelSettings

        presenter = PhysicsModelPresenter(service=object())

        level, title, detail = presenter.build_validation(
            PhysicsModelSettings("Turbulent", "kOmegaSST", "Incompressible", "Steady", False, False, True, False, False)
        )
        self.assertEqual(level, "warning")
        self.assertEqual(title, "Buoyancy needs gravity")

        level, title, detail = presenter.build_validation(
            PhysicsModelSettings("Turbulent", "kOmegaSST", "Incompressible", "Steady", True, False, True, False, False)
        )
        self.assertEqual(level, "warning")
        self.assertEqual(title, "Buoyancy usually needs heat transfer")

        level, title, detail = presenter.build_validation(
            PhysicsModelSettings("Laminar", "kEpsilon", "Incompressible", "Steady", True, True, True, False, False)
        )
        self.assertEqual(level, "info")
        self.assertEqual(title, "Laminar flow selected")

    def test_persist_settings_round_trips_service_payload(self):
        from flow_studio.ui.physics_model_presenter import PhysicsModelPresenter, PhysicsModelSettings

        persisted = []
        obj = types.SimpleNamespace()

        class FakeService:
            def persist_settings(self, current_obj, settings):
                persisted.append((current_obj, settings))

        presenter = PhysicsModelPresenter(service=FakeService())
        settings = PhysicsModelSettings(
            "Laminar",
            "kEpsilon",
            "Compressible",
            "Transient",
            True,
            True,
            True,
            False,
            True,
        )

        presenter.persist_settings(obj, settings)

        self.assertEqual(len(persisted), 1)
        self.assertIs(persisted[0][0], obj)
        self.assertEqual(persisted[0][1]["FlowRegime"], "Laminar")
        self.assertEqual(persisted[0][1]["TurbulenceModel"], "kEpsilon")
        self.assertTrue(persisted[0][1]["PassiveScalar"])

    def test_default_service_constructor_reads_object_state(self):
        from flow_studio.ui.physics_model_presenter import PhysicsModelPresenter

        obj = types.SimpleNamespace(
            FlowRegime="Turbulent",
            TurbulenceModel="kOmegaSST",
            Compressibility="Incompressible",
            TimeModel="Steady",
            Gravity=False,
            HeatTransfer=False,
            Buoyancy=False,
            FreeSurface=False,
            PassiveScalar=False,
        )

        settings = PhysicsModelPresenter().read_settings(obj)

        self.assertEqual(settings.flow_regime, "Turbulent")
        self.assertEqual(settings.turbulence_model, "kOmegaSST")
        self.assertFalse(settings.passive_scalar)


if __name__ == "__main__":
    unittest.main()