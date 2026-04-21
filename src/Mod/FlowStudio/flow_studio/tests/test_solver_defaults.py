# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Pure tests for FlowStudio solver default parallel settings."""

import importlib
import os
import sys
import types
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


class _FakeFeatureObject:
    def __init__(self):
        self.PropertiesList = []
        self.Proxy = None

    def addProperty(self, _prop_type, name, _group, _description):
        if name not in self.PropertiesList:
            self.PropertiesList.append(name)
        setattr(self, name, None)
        return self

    def setPropertyStatus(self, _name, _status):
        return None


def _load_solver_module():
    sys.modules.pop("flow_studio.objects.base_object", None)
    sys.modules.pop("flow_studio.objects.solver", None)
    with patch.dict(sys.modules, {"FreeCAD": types.SimpleNamespace()}):
        return importlib.import_module("flow_studio.objects.solver")


class TestSolverDefaultParallelSettings(unittest.TestCase):
    def test_parallel_recommendations_use_all_physical_cores(self):
        solver_module = _load_solver_module()
        with patch(
            "flow_studio.runtime.dependencies.recommend_parallel_settings",
            return_value={
                "cpu_physical": 8,
                "cpu_logical": 16,
                "gpu_count": 1,
                "OpenFOAM": {"NumProcessors": 8, "mpi_available": True},
                "Elmer": {"NumProcessors": 8, "mpi_available": True},
                "FluidX3D": {"NumGPUs": 1, "MultiGPU": False},
            },
        ):
            defaults = solver_module.recommended_parallel_defaults("OpenFOAM")

        self.assertTrue(defaults["AutoParallel"])
        self.assertEqual(defaults["NumProcessors"], 8)

    def test_elmer_defaults_to_mpi_binary_when_available(self):
        solver_module = _load_solver_module()
        with patch(
            "flow_studio.runtime.dependencies.recommend_parallel_settings",
            return_value={
                "cpu_physical": 6,
                "cpu_logical": 12,
                "gpu_count": 0,
                "OpenFOAM": {"NumProcessors": 6, "mpi_available": True},
                "Elmer": {"NumProcessors": 6, "mpi_available": True},
                "FluidX3D": {"NumGPUs": 1, "MultiGPU": False},
            },
        ):
            fake = _FakeFeatureObject()
            solver_module.Solver(fake)

        self.assertTrue(fake.AutoParallel)
        self.assertEqual(fake.NumProcessors, 6)
        self.assertEqual(fake.ElmerSolverBinary, "ElmerSolver_mpi")


if __name__ == "__main__":
    unittest.main()