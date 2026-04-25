# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Unit tests for the frontend-neutral solver task-panel presenter."""

import os
import sys
import types
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


class TestSolverPresenter(unittest.TestCase):
    def test_validation_covers_multi_solver_geant4_and_runtime_threshold_rules(self):
        from flow_studio.ui.solver_presenter import SolverPresenter, SolverSettings

        presenter = SolverPresenter(service=object())

        level, title, detail = presenter.build_validation(
            SolverSettings(
                "OpenFOAM", "simpleFoam", 100, 1e-5, 4, "upwind", "ElmerSolver",
                "FP32/FP32", 128, 500, 4096, False, 1,
                "", "FTFP_BERT", 1000, 1, "run.mac", False,
                True, ("OpenFOAM",), 0, 0, 0, 0.0, True,
            )
        )
        self.assertEqual(level, "incomplete")
        self.assertIn("multiple solver backends", title)

        level, title, detail = presenter.build_validation(
            SolverSettings(
                "Geant4", "simpleFoam", 100, 1e-5, 4, "upwind", "ElmerSolver",
                "FP32/FP32", 128, 500, 4096, False, 1,
                "", "FTFP_BERT", 1000, 1, "run.mac", False,
                False, (), 0, 0, 0, 0.0, True,
            )
        )
        self.assertEqual(level, "incomplete")
        self.assertEqual(title, "Geant4 executable required")

        level, title, detail = presenter.build_validation(
            SolverSettings(
                "OpenFOAM", "simpleFoam", 100, 1e-5, 4, "upwind", "ElmerSolver",
                "FP32/FP32", 128, 500, 4096, False, 1,
                "C:/geant4/demo.exe", "FTFP_BERT", 1000, 1, "run.mac", False,
                False, (), 300, 120, 0, 0.0, True,
            )
        )
        self.assertEqual(level, "warning")
        self.assertIn("Runtime thresholds out of order", title)

    def test_persist_settings_round_trips_service_payload(self):
        from flow_studio.ui.solver_presenter import SolverPresenter, SolverSettings

        persisted = []
        obj = types.SimpleNamespace()

        class FakeService:
            def read_settings(self, _obj):
                return {}

            def persist_settings(self, current_obj, settings):
                persisted.append((current_obj, settings))

        presenter = SolverPresenter(service=FakeService())
        settings = SolverSettings(
            "Elmer", "simpleFoam", 150, 1e-6, 8, "linearUpwind", "ElmerSolver_mpi",
            "FP32/FP32", 256, 1000, 8192, True, 2,
            "C:/geant4/demo.exe", "QGSP_BERT", 2000, 4, "batch.mac", True,
            True, ("OpenFOAM", "Elmer", "Geant4"), 120, 300, 90, 12.5, False,
        )

        presenter.persist_settings(obj, settings)

        self.assertEqual(len(persisted), 1)
        self.assertIs(persisted[0][0], obj)
        self.assertEqual(persisted[0][1]["SolverBackend"], "Elmer")
        self.assertEqual(persisted[0][1]["ElmerSolverBinary"], "ElmerSolver_mpi")
        self.assertEqual(persisted[0][1]["MultiSolverBackends"], ["OpenFOAM", "Elmer", "Geant4"])
        self.assertAlmostEqual(persisted[0][1]["MinProgressPercent"], 12.5, places=3)

    def test_backend_page_index_matches_supported_stack_pages(self):
        from flow_studio.ui.solver_presenter import SolverPresenter

        presenter = SolverPresenter(service=object())

        self.assertEqual(presenter.backend_page_index("OpenFOAM"), 0)
        self.assertEqual(presenter.backend_page_index("Elmer"), 1)
        self.assertEqual(presenter.backend_page_index("FluidX3D"), 2)
        self.assertEqual(presenter.backend_page_index("SU2"), 3)
        self.assertEqual(presenter.backend_page_index("Geant4"), 4)
        self.assertEqual(presenter.backend_page_index("Unknown"), 0)


if __name__ == "__main__":
    unittest.main()