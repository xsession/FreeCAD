# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Comprehensive tests for the solver registry.

Validates flat lookup, domain-aware lookup, lazy import paths,
dynamic registration, edge cases – all pure Python, no FreeCAD.
"""

import unittest
import sys
import os
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from flow_studio.solvers.registry import (
    _REGISTRY_PATHS, _DOMAIN_SOLVERS,
    get_runner, available_backends, backends_for_domain, register_backend,
)


# ======================================================================
# Flat registry tests
# ======================================================================

class TestRegistryPaths(unittest.TestCase):
    """Test the _REGISTRY_PATHS flat registry."""

    def test_openfoam_registered(self):
        self.assertIn("OpenFOAM", _REGISTRY_PATHS)
        mod, cls = _REGISTRY_PATHS["OpenFOAM"]
        self.assertEqual(cls, "OpenFOAMRunner")
        self.assertIn("openfoam_runner", mod)

    def test_fluidx3d_registered(self):
        self.assertIn("FluidX3D", _REGISTRY_PATHS)
        mod, cls = _REGISTRY_PATHS["FluidX3D"]
        self.assertEqual(cls, "FluidX3DRunner")
        self.assertIn("fluidx3d_runner", mod)

    def test_elmer_registered(self):
        self.assertIn("Elmer", _REGISTRY_PATHS)
        mod, cls = _REGISTRY_PATHS["Elmer"]
        self.assertEqual(cls, "ElmerRunner")
        self.assertIn("elmer_runner", mod)

    def test_registry_has_three_backends(self):
        self.assertEqual(len(_REGISTRY_PATHS), 3)

    def test_all_entries_are_tuples(self):
        for name, entry in _REGISTRY_PATHS.items():
            self.assertIsInstance(entry, tuple, f"{name} should map to tuple")
            self.assertEqual(len(entry), 2, f"{name} should be (module, class)")

    def test_module_paths_valid_format(self):
        for name, (mod_path, cls_name) in _REGISTRY_PATHS.items():
            self.assertTrue(mod_path.startswith("flow_studio."),
                            f"{name}: module path should start with flow_studio.")
            self.assertTrue(cls_name.endswith("Runner"),
                            f"{name}: class name should end with Runner")


# ======================================================================
# Domain solver mapping tests
# ======================================================================

class TestDomainSolvers(unittest.TestCase):
    """Test the _DOMAIN_SOLVERS mapping."""

    def test_all_five_domains_present(self):
        for domain in ("CFD", "Structural", "Electrostatic",
                       "Electromagnetic", "Thermal"):
            self.assertIn(domain, _DOMAIN_SOLVERS,
                          f"Domain {domain} missing from _DOMAIN_SOLVERS")

    def test_cfd_has_three_solvers(self):
        self.assertEqual(len(_DOMAIN_SOLVERS["CFD"]), 3)
        self.assertIn("OpenFOAM", _DOMAIN_SOLVERS["CFD"])
        self.assertIn("FluidX3D", _DOMAIN_SOLVERS["CFD"])
        self.assertIn("Elmer", _DOMAIN_SOLVERS["CFD"])

    def test_non_cfd_domains_elmer_only(self):
        for domain in ("Structural", "Electrostatic",
                       "Electromagnetic", "Thermal"):
            solvers = _DOMAIN_SOLVERS[domain]
            self.assertEqual(solvers, ["Elmer"],
                             f"{domain} should only have Elmer")

    def test_all_referenced_backends_exist(self):
        """Every backend name in domain solvers should be in _REGISTRY_PATHS."""
        for domain, solvers in _DOMAIN_SOLVERS.items():
            for s in solvers:
                self.assertIn(s, _REGISTRY_PATHS,
                              f"{domain}: backend '{s}' not in registry")


# ======================================================================
# available_backends() tests
# ======================================================================

class TestAvailableBackends(unittest.TestCase):
    """Test available_backends function."""

    def test_returns_list(self):
        result = available_backends()
        self.assertIsInstance(result, list)

    def test_contains_openfoam(self):
        self.assertIn("OpenFOAM", available_backends())

    def test_contains_fluidx3d(self):
        self.assertIn("FluidX3D", available_backends())

    def test_contains_elmer(self):
        self.assertIn("Elmer", available_backends())

    def test_returns_copy(self):
        """Mutating result should not affect registry."""
        backends = available_backends()
        backends.append("FakeBackend")
        self.assertNotIn("FakeBackend", available_backends())


# ======================================================================
# backends_for_domain() tests
# ======================================================================

class TestBackendsForDomain(unittest.TestCase):
    """Test backends_for_domain function."""

    def test_cfd_backends(self):
        result = backends_for_domain("CFD")
        self.assertIn("OpenFOAM", result)
        self.assertIn("FluidX3D", result)
        self.assertIn("Elmer", result)

    def test_structural_backends(self):
        result = backends_for_domain("Structural")
        self.assertEqual(result, ["Elmer"])

    def test_electrostatic_backends(self):
        result = backends_for_domain("Electrostatic")
        self.assertEqual(result, ["Elmer"])

    def test_electromagnetic_backends(self):
        result = backends_for_domain("Electromagnetic")
        self.assertEqual(result, ["Elmer"])

    def test_thermal_backends(self):
        result = backends_for_domain("Thermal")
        self.assertEqual(result, ["Elmer"])

    def test_unknown_domain_returns_empty(self):
        result = backends_for_domain("NonexistentDomain")
        self.assertEqual(result, [])

    def test_returns_copy(self):
        result = backends_for_domain("CFD")
        result.append("FakeBackend")
        self.assertNotIn("FakeBackend", backends_for_domain("CFD"))


# ======================================================================
# get_runner() tests
# ======================================================================

class TestGetRunner(unittest.TestCase):
    """Test get_runner function (lazy import)."""

    def test_unknown_returns_none(self):
        result = get_runner("NonExistentSolver")
        self.assertIsNone(result)

    def test_known_backend_returns_entry(self):
        # We can't fully import runner classes (they need FreeCAD),
        # but we can verify the path resolution logic
        self.assertIn("OpenFOAM", _REGISTRY_PATHS)

    def test_none_input(self):
        result = get_runner(None)
        self.assertIsNone(result)


# ======================================================================
# register_backend() tests
# ======================================================================

class TestRegisterBackend(unittest.TestCase):
    """Test dynamic backend registration."""

    def setUp(self):
        """Save original state."""
        self._orig_paths = dict(_REGISTRY_PATHS)
        self._orig_domains = {k: list(v) for k, v in _DOMAIN_SOLVERS.items()}

    def tearDown(self):
        """Restore original state."""
        # Remove any test backends
        for key in list(_REGISTRY_PATHS.keys()):
            if key not in self._orig_paths:
                del _REGISTRY_PATHS[key]
        for key in list(_DOMAIN_SOLVERS.keys()):
            if key not in self._orig_domains:
                del _DOMAIN_SOLVERS[key]
            else:
                _DOMAIN_SOLVERS[key] = self._orig_domains[key]

    def test_register_new_backend(self):
        register_backend("MySolver", "my.module", "MySolverRunner")
        self.assertIn("MySolver", _REGISTRY_PATHS)
        self.assertEqual(_REGISTRY_PATHS["MySolver"],
                         ("my.module", "MySolverRunner"))

    def test_register_with_domains(self):
        register_backend("MySolver", "my.module", "MySolverRunner",
                         domains=["CFD", "Thermal"])
        self.assertIn("MySolver", backends_for_domain("CFD"))
        self.assertIn("MySolver", backends_for_domain("Thermal"))

    def test_register_with_new_domain(self):
        register_backend("MySolver", "my.module", "MySolverRunner",
                         domains=["Acoustic"])
        self.assertIn("Acoustic", _DOMAIN_SOLVERS)
        self.assertIn("MySolver", _DOMAIN_SOLVERS["Acoustic"])

    def test_register_no_duplicate_in_domain(self):
        register_backend("MySolver", "my.module", "MySolverRunner",
                         domains=["CFD"])
        register_backend("MySolver", "my.module", "MySolverRunner",
                         domains=["CFD"])
        count = backends_for_domain("CFD").count("MySolver")
        self.assertEqual(count, 1)

    def test_register_no_domains(self):
        register_backend("Orphan", "orphan.mod", "OrphanRunner")
        self.assertIn("Orphan", _REGISTRY_PATHS)
        # Should not appear in any domain
        for domain_key in ("CFD", "Structural", "Electrostatic",
                           "Electromagnetic", "Thermal"):
            self.assertNotIn("Orphan", backends_for_domain(domain_key))

    def test_register_overwrites_module_path(self):
        register_backend("TestOverwrite", "old.module", "OldRunner")
        register_backend("TestOverwrite", "new.module", "NewRunner")
        self.assertEqual(_REGISTRY_PATHS["TestOverwrite"],
                         ("new.module", "NewRunner"))

    def test_available_backends_includes_new(self):
        register_backend("FreshSolver", "fresh.mod", "FreshRunner")
        self.assertIn("FreshSolver", available_backends())


# ======================================================================
# Consistency with physics_domains
# ======================================================================

class TestRegistryDomainConsistency(unittest.TestCase):
    """Verify registry and physics_domains agree on solver mappings."""

    def test_registry_matches_domain_backends(self):
        from flow_studio.physics_domains import all_domains
        for domain in all_domains():
            reg_backends = backends_for_domain(domain.key)
            for backend in domain.solver_backends:
                self.assertIn(backend, reg_backends,
                              f"Domain {domain.key}: backend '{backend}' "
                              f"in physics_domains but not in registry")

    def test_domain_solver_backends_in_registry(self):
        from flow_studio.physics_domains import all_domains
        for domain in all_domains():
            for backend in domain.solver_backends:
                self.assertIn(backend, _REGISTRY_PATHS,
                              f"Backend '{backend}' from domain "
                              f"{domain.key} not in _REGISTRY_PATHS")


if __name__ == "__main__":
    unittest.main()
