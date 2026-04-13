# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Comprehensive tests for mesh utilities and material presets.

Tests y+ estimation edge cases, Reynolds number regimes, physical
consistency of material presets, and unit relationships.
"""

import unittest
import sys
import os
import math

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from flow_studio.utils.mesh_utils import estimate_y_plus_height


# ======================================================================
# y+ estimation – physics validation
# ======================================================================

class TestYPlusBasicPhysics(unittest.TestCase):
    """Test fundamental physics of y+ estimation."""

    def test_positive_result(self):
        h = estimate_y_plus_height(10.0, 1.0, 1.48e-5)
        self.assertGreater(h, 0)

    def test_proportional_to_yplus_target(self):
        """Height should scale linearly with y+ target."""
        h1 = estimate_y_plus_height(10.0, 1.0, 1.48e-5, y_plus_target=1.0)
        h5 = estimate_y_plus_height(10.0, 1.0, 1.48e-5, y_plus_target=5.0)
        h30 = estimate_y_plus_height(10.0, 1.0, 1.48e-5, y_plus_target=30.0)
        self.assertAlmostEqual(h5 / h1, 5.0, places=5)
        self.assertAlmostEqual(h30 / h1, 30.0, places=5)

    def test_higher_velocity_smaller_height(self):
        """Higher velocity → thinner BL → smaller first cell."""
        h_slow = estimate_y_plus_height(1.0, 1.0, 1.48e-5)
        h_fast = estimate_y_plus_height(100.0, 1.0, 1.48e-5)
        self.assertGreater(h_slow, h_fast)

    def test_higher_viscosity_larger_height(self):
        """Higher viscosity → larger y for same y+."""
        h_air = estimate_y_plus_height(10.0, 1.0, 1.48e-5)
        h_oil = estimate_y_plus_height(10.0, 1.0, 3.25e-4)
        self.assertGreater(h_oil, h_air)

    def test_longer_plate_different_height(self):
        """Different plate length gives different first cell height."""
        h_short = estimate_y_plus_height(10.0, 0.1, 1.48e-5)
        h_long = estimate_y_plus_height(10.0, 10.0, 1.48e-5)
        # Both should be positive and different
        self.assertGreater(h_short, 0)
        self.assertGreater(h_long, 0)
        self.assertNotAlmostEqual(h_short, h_long)


class TestYPlusEdgeCases(unittest.TestCase):
    """Test y+ estimation edge and fallback cases."""

    def test_zero_velocity(self):
        h = estimate_y_plus_height(0.0, 1.0, 1.48e-5)
        self.assertEqual(h, 1e-3)

    def test_very_small_velocity(self):
        h = estimate_y_plus_height(1e-15, 1.0, 1.48e-5)
        self.assertEqual(h, 1e-3)  # Re < 1 → fallback

    def test_very_high_reynolds(self):
        """High Re (airplane cruise) should give very small first cell."""
        # Air at 250 m/s, 5m chord
        h = estimate_y_plus_height(250.0, 5.0, 1.48e-5, y_plus_target=1.0)
        self.assertGreater(h, 0)
        self.assertLess(h, 1e-4)  # Should be very small

    def test_water_pipe_flow(self):
        """Water in pipe: V=2m/s, D=0.05m."""
        h = estimate_y_plus_height(2.0, 0.05, 1.004e-6, y_plus_target=1.0)
        self.assertGreater(h, 0)
        self.assertLess(h, 1e-4)

    def test_glycerin_flow(self):
        """Glycerin: very high viscosity."""
        h = estimate_y_plus_height(0.1, 0.01, 1.12e-3, y_plus_target=1.0)
        self.assertGreater(h, 0)

    def test_mercury_flow(self):
        """Mercury: low viscosity."""
        h = estimate_y_plus_height(1.0, 0.1, 1.128e-7, y_plus_target=1.0)
        self.assertGreater(h, 0)
        self.assertLess(h, 1e-4)


class TestYPlusWallResolution(unittest.TestCase):
    """Test y+ targets used in practice."""

    def test_yplus_1_resolves_viscous_sublayer(self):
        """y+=1 should give height in μm–mm range for typical flows."""
        h = estimate_y_plus_height(10.0, 1.0, 1.48e-5, y_plus_target=1.0)
        self.assertGreater(h, 1e-6)
        self.assertLess(h, 1e-2)

    def test_yplus_30_wall_function(self):
        """y+=30 for wall functions should be 10-30x the y+=1 height."""
        h1 = estimate_y_plus_height(10.0, 1.0, 1.48e-5, y_plus_target=1.0)
        h30 = estimate_y_plus_height(10.0, 1.0, 1.48e-5, y_plus_target=30.0)
        ratio = h30 / h1
        self.assertAlmostEqual(ratio, 30.0, places=3)

    def test_yplus_100_coarse(self):
        h100 = estimate_y_plus_height(10.0, 1.0, 1.48e-5, y_plus_target=100.0)
        h1 = estimate_y_plus_height(10.0, 1.0, 1.48e-5, y_plus_target=1.0)
        self.assertAlmostEqual(h100 / h1, 100.0, places=3)


class TestYPlusFormula(unittest.TestCase):
    """Verify the actual formula used in the implementation."""

    def test_formula_matches_manual(self):
        """Hand-calculate and compare."""
        U = 10.0
        L = 1.0
        nu = 1.48e-5
        yp = 1.0

        Re = U * L / nu  # ~675676
        Cf = 0.058 * Re ** (-0.2)
        tau_w_over_rho = 0.5 * Cf * U ** 2
        u_tau = math.sqrt(abs(tau_w_over_rho))
        expected = yp * nu / u_tau

        actual = estimate_y_plus_height(U, L, nu, yp)
        self.assertAlmostEqual(actual, expected, places=10)


# ======================================================================
# check_gmsh()
# ======================================================================

class TestCheckGmsh(unittest.TestCase):
    """Test check_gmsh utility."""

    def test_returns_bool(self):
        from flow_studio.utils.mesh_utils import check_gmsh
        result = check_gmsh()
        self.assertIsInstance(result, bool)

    def test_matches_has_gmsh(self):
        from flow_studio.utils.mesh_utils import check_gmsh, HAS_GMSH
        self.assertEqual(check_gmsh(), HAS_GMSH)


# ======================================================================
# Material presets
# ======================================================================

class TestFluidMaterialPresets(unittest.TestCase):
    """Test the predefined fluid material database."""

    def _db(self):
        from flow_studio.taskpanels.task_fluid_material import MATERIALS_DB
        return MATERIALS_DB

    def test_has_air(self):
        self.assertIn("Air (20°C, 1atm)", self._db())

    def test_has_water(self):
        self.assertIn("Water (20°C)", self._db())

    def test_has_oil(self):
        self.assertIn("Oil (SAE 30)", self._db())

    def test_has_glycerin(self):
        self.assertIn("Glycerin", self._db())

    def test_has_mercury(self):
        self.assertIn("Mercury", self._db())

    def test_air_density(self):
        air = self._db()["Air (20°C, 1atm)"]
        self.assertAlmostEqual(air["Density"], 1.225, places=2)

    def test_air_viscosity(self):
        air = self._db()["Air (20°C, 1atm)"]
        self.assertAlmostEqual(air["DynamicViscosity"], 1.81e-5, places=7)

    def test_air_prandtl(self):
        air = self._db()["Air (20°C, 1atm)"]
        self.assertAlmostEqual(air["PrandtlNumber"], 0.707, places=2)

    def test_water_density(self):
        w = self._db()["Water (20°C)"]
        self.assertAlmostEqual(w["Density"], 998.2, places=0)

    def test_water_high_prandtl(self):
        w = self._db()["Water (20°C)"]
        self.assertGreater(w["PrandtlNumber"], 6.0)

    def test_oil_high_viscosity(self):
        oil = self._db()["Oil (SAE 30)"]
        self.assertGreater(oil["DynamicViscosity"], 0.1)

    def test_mercury_high_density(self):
        hg = self._db()["Mercury"]
        self.assertGreater(hg["Density"], 13000)

    def test_all_presets_required_keys(self):
        required = {"Density", "DynamicViscosity", "KinematicViscosity",
                     "SpecificHeat", "ThermalConductivity", "PrandtlNumber"}
        for name, props in self._db().items():
            missing = required - set(props.keys())
            self.assertEqual(missing, set(),
                             f"Material '{name}' missing keys: {missing}")

    def test_all_positive_density(self):
        for name, props in self._db().items():
            self.assertGreater(props["Density"], 0,
                               f"{name}: density must be positive")

    def test_all_positive_viscosity(self):
        for name, props in self._db().items():
            self.assertGreater(props["DynamicViscosity"], 0,
                               f"{name}: dynamic viscosity must be positive")
            self.assertGreater(props["KinematicViscosity"], 0,
                               f"{name}: kinematic viscosity must be positive")

    def test_all_positive_prandtl(self):
        for name, props in self._db().items():
            self.assertGreater(props["PrandtlNumber"], 0,
                               f"{name}: Prandtl number must be positive")

    def test_kinematic_viscosity_consistency(self):
        """nu ≈ mu / rho for each material."""
        for name, props in self._db().items():
            nu_expected = props["DynamicViscosity"] / props["Density"]
            nu_actual = props["KinematicViscosity"]
            self.assertAlmostEqual(
                nu_actual, nu_expected, places=6,
                msg=f"{name}: nu={nu_actual} vs mu/rho={nu_expected}")

    def test_prandtl_consistency(self):
        """Pr = mu * Cp / k for each material."""
        for name, props in self._db().items():
            mu = props["DynamicViscosity"]
            cp = props["SpecificHeat"]
            k = props["ThermalConductivity"]
            if k > 0:
                pr_calc = mu * cp / k
                pr_given = props["PrandtlNumber"]
                # Allow 5% relative tolerance for data rounding
                self.assertAlmostEqual(
                    pr_given / pr_calc, 1.0, places=1,
                    msg=f"{name}: Pr={pr_given} vs mu*Cp/k={pr_calc:.3f}")

    def test_at_least_5_presets(self):
        self.assertGreaterEqual(len(self._db()), 5)


# ======================================================================
# Package version
# ======================================================================

class TestPackageVersion(unittest.TestCase):
    """Test package metadata."""

    def test_version_string(self):
        import flow_studio
        self.assertEqual(flow_studio.__version__, "0.2.0")

    def test_version_format(self):
        import flow_studio
        parts = flow_studio.__version__.split(".")
        self.assertEqual(len(parts), 3)
        for p in parts:
            self.assertTrue(p.isdigit())


if __name__ == "__main__":
    unittest.main()
