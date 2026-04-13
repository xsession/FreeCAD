# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Unit tests for FlowStudio document objects."""

import unittest
import sys
import os

# Add parent directory to path for standalone testing
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


class TestMeshUtilsYPlus(unittest.TestCase):
    """Test y+ estimation (pure math, no FreeCAD dependency)."""

    def test_yplus_air_flow(self):
        from flow_studio.utils.mesh_utils import estimate_y_plus_height
        # Air at 10 m/s, 1m length, nu=1.48e-5
        h = estimate_y_plus_height(10.0, 1.0, 1.48e-5, y_plus_target=1.0)
        self.assertGreater(h, 0)
        self.assertLess(h, 0.001)  # Should be sub-mm

    def test_yplus_water_flow(self):
        from flow_studio.utils.mesh_utils import estimate_y_plus_height
        h = estimate_y_plus_height(1.0, 0.1, 1.004e-6, y_plus_target=1.0)
        self.assertGreater(h, 0)
        self.assertLess(h, 0.001)

    def test_yplus_zero_velocity(self):
        from flow_studio.utils.mesh_utils import estimate_y_plus_height
        h = estimate_y_plus_height(0.0, 1.0, 1.48e-5, y_plus_target=1.0)
        # Should return fallback value
        self.assertEqual(h, 1e-3)

    def test_yplus_30_target(self):
        from flow_studio.utils.mesh_utils import estimate_y_plus_height
        h1 = estimate_y_plus_height(10.0, 1.0, 1.48e-5, y_plus_target=1.0)
        h30 = estimate_y_plus_height(10.0, 1.0, 1.48e-5, y_plus_target=30.0)
        self.assertAlmostEqual(h30 / h1, 30.0, places=3)


class TestMaterialsDB(unittest.TestCase):
    """Test the predefined material database."""

    def test_air_properties(self):
        from flow_studio.taskpanels.task_fluid_material import MATERIALS_DB
        air = MATERIALS_DB["Air (20°C, 1atm)"]
        self.assertAlmostEqual(air["Density"], 1.225, places=2)
        self.assertAlmostEqual(air["PrandtlNumber"], 0.707, places=2)

    def test_water_properties(self):
        from flow_studio.taskpanels.task_fluid_material import MATERIALS_DB
        water = MATERIALS_DB["Water (20°C)"]
        self.assertAlmostEqual(water["Density"], 998.2, places=0)
        self.assertGreater(water["PrandtlNumber"], 6.0)

    def test_all_presets_have_required_keys(self):
        from flow_studio.taskpanels.task_fluid_material import MATERIALS_DB
        required = {"Density", "DynamicViscosity", "KinematicViscosity",
                     "SpecificHeat", "ThermalConductivity", "PrandtlNumber"}
        for name, props in MATERIALS_DB.items():
            self.assertTrue(required.issubset(props.keys()),
                            f"Material '{name}' missing keys: "
                            f"{required - props.keys()}")


class TestSolverRegistry(unittest.TestCase):
    """Test solver backend registry (no FreeCAD dependency)."""

    def test_available_backends(self):
        from flow_studio.solvers.registry import available_backends
        backends = available_backends()
        self.assertIn("OpenFOAM", backends)
        self.assertIn("FluidX3D", backends)

    def test_get_runner_openfoam(self):
        from flow_studio.solvers.registry import _REGISTRY_PATHS
        self.assertIn("OpenFOAM", _REGISTRY_PATHS)
        mod_path, cls_name = _REGISTRY_PATHS["OpenFOAM"]
        self.assertEqual(cls_name, "OpenFOAMRunner")

    def test_get_runner_fluidx3d(self):
        from flow_studio.solvers.registry import _REGISTRY_PATHS
        self.assertIn("FluidX3D", _REGISTRY_PATHS)
        mod_path, cls_name = _REGISTRY_PATHS["FluidX3D"]
        self.assertEqual(cls_name, "FluidX3DRunner")

    def test_unknown_backend(self):
        from flow_studio.solvers.registry import get_runner
        cls = get_runner("NonExistent")
        self.assertIsNone(cls)


class TestPackageImports(unittest.TestCase):
    """Test that pure-Python package modules can be imported."""

    def test_import_package(self):
        import flow_studio
        self.assertEqual(flow_studio.__version__, "0.2.0")

    def test_import_registry(self):
        from flow_studio.solvers import registry
        self.assertTrue(hasattr(registry, "get_runner"))


if __name__ == "__main__":
    unittest.main()
