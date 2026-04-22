# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Comprehensive tests for the physics domain registry.

Validates domain definitions, registration, lookup, solver-backend
mapping, BC types, material types, and edge cases – all pure Python.
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from flow_studio.physics_domains import (
    PhysicsDomain, register_domain, get_domain, available_domains,
    all_domains, CFD, STRUCTURAL, ELECTROSTATIC, ELECTROMAGNETIC, THERMAL,
    _DOMAINS,
)


# ======================================================================
# PhysicsDomain class tests
# ======================================================================

class TestPhysicsDomainInit(unittest.TestCase):
    """Test PhysicsDomain construction."""

    def test_minimal_creation(self):
        d = PhysicsDomain(key="TEST", label="Test Domain")
        self.assertEqual(d.key, "TEST")
        self.assertEqual(d.label, "Test Domain")
        self.assertEqual(d.description, "")
        self.assertEqual(d.icon, "")
        self.assertEqual(d.analysis_types, [])
        self.assertEqual(d.bc_types, [])
        self.assertEqual(d.solver_backends, [])
        self.assertIsNone(d.material_type)
        self.assertIsNone(d.physics_model_type)

    def test_full_creation(self):
        d = PhysicsDomain(
            key="FULL",
            label="Full Domain",
            description="A full domain",
            icon="full.svg",
            analysis_types=["Type1", "Type2"],
            bc_types=["BC1"],
            solver_backends=["Solver1"],
            material_type="Material1",
            physics_model_type="PhysicsModel1",
        )
        self.assertEqual(d.key, "FULL")
        self.assertEqual(len(d.analysis_types), 2)
        self.assertEqual(len(d.bc_types), 1)
        self.assertEqual(d.material_type, "Material1")

    def test_slots(self):
        d = PhysicsDomain(key="A", label="B")
        with self.assertRaises(AttributeError):
            d.nonexistent_attr = "fail"


# ======================================================================
# Built-in domain definitions
# ======================================================================

class TestCFDDomain(unittest.TestCase):
    """Test CFD domain definition."""

    def test_key(self):
        self.assertEqual(CFD.key, "CFD")

    def test_label(self):
        self.assertIn("Fluid", CFD.label)

    def test_description(self):
        self.assertIn("Fluid Dynamics", CFD.description)

    def test_icon(self):
        self.assertTrue(CFD.icon.endswith(".svg"))

    def test_analysis_types(self):
        self.assertIn("Internal Flow", CFD.analysis_types)
        self.assertIn("External Flow", CFD.analysis_types)
        self.assertIn("Heat Transfer", CFD.analysis_types)
        self.assertGreaterEqual(len(CFD.analysis_types), 4)

    def test_bc_types(self):
        expected = ["FlowStudio::BCWall", "FlowStudio::BCInlet",
                     "FlowStudio::BCOutlet", "FlowStudio::BCOpenBoundary",
                     "FlowStudio::BCSymmetry"]
        for bc in expected:
            self.assertIn(bc, CFD.bc_types)

    def test_solver_backends(self):
        self.assertIn("OpenFOAM", CFD.solver_backends)
        self.assertIn("FluidX3D", CFD.solver_backends)
        self.assertIn("Elmer", CFD.solver_backends)

    def test_material_type(self):
        self.assertEqual(CFD.material_type, "FlowStudio::FluidMaterial")

    def test_physics_model_type(self):
        self.assertEqual(CFD.physics_model_type, "FlowStudio::PhysicsModel")


class TestStructuralDomain(unittest.TestCase):
    """Test Structural domain definition."""

    def test_key(self):
        self.assertEqual(STRUCTURAL.key, "Structural")

    def test_solver_backends(self):
        self.assertEqual(STRUCTURAL.solver_backends, ["Elmer"])

    def test_bc_types(self):
        self.assertIn("FlowStudio::BCFixedDisplacement", STRUCTURAL.bc_types)
        self.assertIn("FlowStudio::BCForce", STRUCTURAL.bc_types)
        self.assertIn("FlowStudio::BCPressureLoad", STRUCTURAL.bc_types)
        self.assertIn("FlowStudio::BCSymmetry", STRUCTURAL.bc_types)

    def test_material_type(self):
        self.assertEqual(STRUCTURAL.material_type, "FlowStudio::SolidMaterial")

    def test_analysis_types(self):
        self.assertIn("Static Linear Elastic", STRUCTURAL.analysis_types)
        self.assertIn("Modal Analysis", STRUCTURAL.analysis_types)


class TestElectrostaticDomain(unittest.TestCase):
    """Test Electrostatic domain definition."""

    def test_key(self):
        self.assertEqual(ELECTROSTATIC.key, "Electrostatic")

    def test_solver_backends(self):
        self.assertEqual(ELECTROSTATIC.solver_backends, ["Elmer"])

    def test_bc_types(self):
        self.assertIn("FlowStudio::BCElectricPotential", ELECTROSTATIC.bc_types)
        self.assertIn("FlowStudio::BCSurfaceCharge", ELECTROSTATIC.bc_types)

    def test_material_type(self):
        self.assertEqual(ELECTROSTATIC.material_type,
                         "FlowStudio::ElectrostaticMaterial")

    def test_analysis_types(self):
        self.assertIn("Electrostatic Potential", ELECTROSTATIC.analysis_types)
        self.assertIn("Capacitance Matrix", ELECTROSTATIC.analysis_types)


class TestElectromagneticDomain(unittest.TestCase):
    """Test Electromagnetic domain definition."""

    def test_key(self):
        self.assertEqual(ELECTROMAGNETIC.key, "Electromagnetic")

    def test_solver_backends(self):
        self.assertEqual(ELECTROMAGNETIC.solver_backends, ["Elmer"])

    def test_bc_types(self):
        self.assertIn("FlowStudio::BCMagneticPotential", ELECTROMAGNETIC.bc_types)
        self.assertIn("FlowStudio::BCCurrentDensity", ELECTROMAGNETIC.bc_types)

    def test_material_type(self):
        self.assertEqual(ELECTROMAGNETIC.material_type,
                         "FlowStudio::ElectromagneticMaterial")

    def test_analysis_types(self):
        self.assertIn("Magnetostatic", ELECTROMAGNETIC.analysis_types)
        self.assertIn("Magnetodynamic Harmonic", ELECTROMAGNETIC.analysis_types)
        self.assertIn("Magnetodynamic Transient", ELECTROMAGNETIC.analysis_types)


class TestThermalDomain(unittest.TestCase):
    """Test Thermal domain definition."""

    def test_key(self):
        self.assertEqual(THERMAL.key, "Thermal")

    def test_solver_backends(self):
        self.assertEqual(THERMAL.solver_backends, ["Elmer"])

    def test_bc_types(self):
        self.assertIn("FlowStudio::BCTemperature", THERMAL.bc_types)
        self.assertIn("FlowStudio::BCHeatFlux", THERMAL.bc_types)
        self.assertIn("FlowStudio::BCConvection", THERMAL.bc_types)
        self.assertIn("FlowStudio::BCRadiation", THERMAL.bc_types)

    def test_material_type(self):
        self.assertEqual(THERMAL.material_type, "FlowStudio::ThermalMaterial")

    def test_analysis_types(self):
        self.assertIn("Steady-State Heat Transfer", THERMAL.analysis_types)
        self.assertIn("Transient Heat Transfer", THERMAL.analysis_types)


class TestOpticalDomain(unittest.TestCase):
    """Test Optical domain definition."""

    def test_key(self):
        from flow_studio.physics_domains import OPTICAL
        self.assertEqual(OPTICAL.key, "Optical")

    def test_solver_backends(self):
        from flow_studio.physics_domains import OPTICAL
        for backend in ("Raysect", "Meep", "openEMS", "Optiland", "Geant4"):
            self.assertIn(backend, OPTICAL.solver_backends)

    def test_description_mentions_radiation_transport(self):
        from flow_studio.physics_domains import OPTICAL
        self.assertIn("radiation transport", OPTICAL.description)

    def test_bc_types_include_geant4_authoring_objects(self):
        from flow_studio.physics_domains import OPTICAL
        self.assertIn("FlowStudio::BCGeant4Source", OPTICAL.bc_types)
        self.assertIn("FlowStudio::BCGeant4Detector", OPTICAL.bc_types)
        self.assertIn("FlowStudio::BCGeant4Scoring", OPTICAL.bc_types)


# ======================================================================
# Registry function tests
# ======================================================================

class TestDomainRegistration(unittest.TestCase):
    """Test register_domain / get_domain / available_domains / all_domains."""

    def test_all_six_registered(self):
        keys = available_domains()
        self.assertEqual(len(keys), 6)
        for k in ("CFD", "Structural", "Electrostatic",
                   "Electromagnetic", "Thermal", "Optical"):
            self.assertIn(k, keys)

    def test_get_domain_returns_correct(self):
        d = get_domain("CFD")
        self.assertIs(d, CFD)

    def test_get_domain_structural(self):
        d = get_domain("Structural")
        self.assertIs(d, STRUCTURAL)

    def test_get_domain_electrostatic(self):
        d = get_domain("Electrostatic")
        self.assertIs(d, ELECTROSTATIC)

    def test_get_domain_electromagnetic(self):
        d = get_domain("Electromagnetic")
        self.assertIs(d, ELECTROMAGNETIC)

    def test_get_domain_thermal(self):
        d = get_domain("Thermal")
        self.assertIs(d, THERMAL)

    def test_unknown_domain_returns_none(self):
        self.assertIsNone(get_domain("Nonexistent"))

    def test_all_domains_count(self):
        domains = all_domains()
        self.assertEqual(len(domains), 6)
        self.assertIsInstance(domains[0], PhysicsDomain)

    def test_register_custom_domain(self):
        """Register and retrieve a custom domain, then clean up."""
        custom = PhysicsDomain(
            key="CUSTOM_TEST",
            label="Custom Test Domain",
            solver_backends=["CustomSolver"],
        )
        register_domain(custom)
        try:
            self.assertIn("CUSTOM_TEST", available_domains())
            retrieved = get_domain("CUSTOM_TEST")
            self.assertIs(retrieved, custom)
        finally:
            # Clean up to avoid polluting other tests
            _DOMAINS.pop("CUSTOM_TEST", None)

    def test_re_register_overwrites(self):
        """Re-registering the same key overwrites the old domain."""
        d1 = PhysicsDomain(key="OVERWRITE_TEST", label="First")
        d2 = PhysicsDomain(key="OVERWRITE_TEST", label="Second")
        register_domain(d1)
        register_domain(d2)
        try:
            self.assertEqual(get_domain("OVERWRITE_TEST").label, "Second")
        finally:
            _DOMAINS.pop("OVERWRITE_TEST", None)


# ======================================================================
# Cross-domain consistency
# ======================================================================

class TestCrossDomainConsistency(unittest.TestCase):
    """Cross-cutting validation across all domains."""

    def test_every_domain_has_key_and_label(self):
        for d in all_domains():
            self.assertTrue(len(d.key) > 0, f"Domain missing key")
            self.assertTrue(len(d.label) > 0, f"Domain {d.key} missing label")

    def test_every_domain_has_description(self):
        for d in all_domains():
            self.assertTrue(len(d.description) > 0,
                            f"Domain {d.key} missing description")

    def test_every_domain_has_icon(self):
        for d in all_domains():
            self.assertTrue(d.icon.endswith(".svg"),
                            f"Domain {d.key} icon should end with .svg")

    def test_every_domain_has_solver_backends(self):
        for d in all_domains():
            self.assertGreater(len(d.solver_backends), 0,
                               f"Domain {d.key} has no solver backends")

    def test_every_domain_has_bc_types(self):
        for d in all_domains():
            self.assertGreater(len(d.bc_types), 0,
                               f"Domain {d.key} has no BC types")

    def test_every_domain_has_material_type(self):
        for d in all_domains():
            self.assertIsNotNone(d.material_type,
                                 f"Domain {d.key} has no material type")
            self.assertIn("FlowStudio::", d.material_type)

    def test_every_domain_has_physics_model_type(self):
        for d in all_domains():
            self.assertIsNotNone(d.physics_model_type,
                                 f"Domain {d.key} has no physics model type")
            self.assertIn("FlowStudio::", d.physics_model_type)

    def test_every_domain_has_analysis_types(self):
        for d in all_domains():
            self.assertGreater(len(d.analysis_types), 0,
                               f"Domain {d.key} has no analysis types")

    def test_bc_types_namespaced(self):
        for d in all_domains():
            for bc in d.bc_types:
                self.assertTrue(bc.startswith("FlowStudio::"),
                                f"{d.key}: BC '{bc}' not namespaced")

    def test_no_duplicate_keys(self):
        keys = [d.key for d in all_domains()]
        self.assertEqual(len(keys), len(set(keys)), "Duplicate domain keys")

    def test_solver_backends_match_domain_intent(self):
        """Classical FEM domains use Elmer; optical uses optics/radiation backends."""
        for d in all_domains():
            if d.key == "Optical":
                self.assertNotIn("Elmer", d.solver_backends)
                for backend in ("Raysect", "Meep", "openEMS", "Optiland", "Geant4"):
                    self.assertIn(backend, d.solver_backends)
                continue

            self.assertIn("Elmer", d.solver_backends,
                          f"Domain {d.key} missing Elmer backend")


if __name__ == "__main__":
    unittest.main()
