# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Unit tests for multi-physics domain system.

Tests the domain registry, Elmer SIF generation, and domain-aware
solver registry — all pure Python with no FreeCAD dependency.
"""

import unittest
import sys
import os
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


class TestPhysicsDomains(unittest.TestCase):
    """Test the physics domain registry."""

    def test_all_domains_registered(self):
        from flow_studio.physics_domains import available_domains
        ids = available_domains()
        for domain in ("CFD", "Structural", "Electrostatic",
                       "Electromagnetic", "Thermal", "Optical"):
            self.assertIn(domain, ids)

    def test_domain_has_solver_backends(self):
        from flow_studio.physics_domains import get_domain
        cfd = get_domain("CFD")
        self.assertIn("OpenFOAM", cfd.solver_backends)
        self.assertIn("FluidX3D", cfd.solver_backends)
        self.assertIn("Elmer", cfd.solver_backends)

    def test_optical_domain_includes_geant4(self):
        from flow_studio.physics_domains import get_domain
        optical = get_domain("Optical")
        self.assertIn("Geant4", optical.solver_backends)
        self.assertIn("FlowStudio::BCGeant4Source", optical.bc_types)

    def test_structural_uses_elmer(self):
        from flow_studio.physics_domains import get_domain
        s = get_domain("Structural")
        self.assertIn("Elmer", s.solver_backends)

    def test_domain_labels(self):
        from flow_studio.physics_domains import get_domain
        em = get_domain("Electromagnetic")
        self.assertTrue(len(em.label) > 0)
        self.assertTrue(len(em.description) > 0)

    def test_unknown_domain_returns_none(self):
        from flow_studio.physics_domains import get_domain
        self.assertIsNone(get_domain("UnknownDomain"))

    def test_domain_all(self):
        from flow_studio.physics_domains import all_domains
        domains = all_domains()
        self.assertEqual(len(domains), 6)


class TestDomainSolverRegistry(unittest.TestCase):
    """Test the domain-aware solver registry."""

    def test_available_backends_for_cfd(self):
        from flow_studio.solvers.registry import backends_for_domain
        backends = backends_for_domain("CFD")
        self.assertIn("OpenFOAM", backends)
        self.assertIn("FluidX3D", backends)
        self.assertIn("Elmer", backends)

    def test_available_backends_for_structural(self):
        from flow_studio.solvers.registry import backends_for_domain
        backends = backends_for_domain("Structural")
        self.assertIn("Elmer", backends)

    def test_available_backends_for_optical(self):
        from flow_studio.solvers.registry import backends_for_domain
        backends = backends_for_domain("Optical")
        self.assertIn("Geant4", backends)

    def test_domain_solver_entries(self):
        from flow_studio.solvers.registry import _DOMAIN_SOLVERS
        self.assertIn("Electrostatic", _DOMAIN_SOLVERS)
        self.assertIn("Electromagnetic", _DOMAIN_SOLVERS)
        self.assertIn("Thermal", _DOMAIN_SOLVERS)

    def test_backward_compat_get_runner(self):
        from flow_studio.solvers.registry import _REGISTRY_PATHS
        # Just verify OpenFOAM is registered; actual import needs FreeCAD
        self.assertIn("OpenFOAM", _REGISTRY_PATHS)
        self.assertIn("Elmer", _REGISTRY_PATHS)


class TestElmerSif(unittest.TestCase):
    """Test Elmer SIF generation library."""

    def test_sif_section_set_get(self):
        from flow_studio.solvers.elmer_sif import SifSection
        s = SifSection("Header")
        s["Mesh DB"] = '"." "."'
        s["Coordinate System"] = "Cartesian"
        self.assertEqual(s["Coordinate System"], "Cartesian")

    def test_sif_section_to_sif(self):
        from flow_studio.solvers.elmer_sif import SifSection
        s = SifSection("Header")
        s["Mesh DB"] = '"." "."'
        s["Include Path"] = '""'
        text = s.to_sif()
        self.assertIn('Mesh DB = "." "."', text)
        self.assertIn('Include Path = ""', text)

    def test_sif_builder_header(self):
        from flow_studio.solvers.elmer_sif import SifBuilder
        b = SifBuilder()
        b.set_header()
        self.assertIn("Mesh DB", b.header.data)

    def test_sif_builder_add_body(self):
        from flow_studio.solvers.elmer_sif import SifBuilder
        b = SifBuilder()
        body = b.add_body("Body 1", equation=1)
        self.assertEqual(len(b.bodies), 1)
        self.assertIn("Equation", body.data)

    def test_sif_builder_add_solver(self):
        from flow_studio.solvers.elmer_sif import SifBuilder, SifProcedure
        b = SifBuilder()
        proc = SifProcedure("HeatSolve", "HeatSolver")
        s = b.add_solver("Heat Equation", proc, variable="Temperature")
        self.assertEqual(len(b.solvers), 1)
        self.assertIn("Equation", s.data)

    def test_sif_builder_add_material(self):
        from flow_studio.solvers.elmer_sif import SifBuilder
        b = SifBuilder()
        m = b.add_material("Steel")
        m["Density"] = 7850.0
        self.assertEqual(len(b.materials), 1)

    def test_sif_builder_add_bc(self):
        from flow_studio.solvers.elmer_sif import SifBuilder
        b = SifBuilder()
        bc = b.add_boundary_condition("Wall")
        bc["Temperature"] = 300.0
        self.assertEqual(len(b.boundary_conditions), 1)

    def test_sif_generate_output(self):
        from flow_studio.solvers.elmer_sif import SifBuilder, SifProcedure
        b = SifBuilder()
        b.set_header()
        b.set_simulation()
        b.set_constant("Permittivity Of Vacuum", 8.8542e-12)
        body = b.add_body("Body 1", equation=1, material=1)
        mat = b.add_material("Air")
        mat["Density"] = 1.225

        content = b.generate()
        self.assertIn("Header", content)
        self.assertIn("Simulation", content)
        self.assertIn("Body 1", content)
        self.assertIn("Density = 1.225", content)

    def test_sif_procedure(self):
        from flow_studio.solvers.elmer_sif import SifProcedure, SifSection
        s = SifSection("Solver", 1)
        s["Procedure"] = SifProcedure("HeatSolve", "HeatSolver")
        text = s.to_sif()
        self.assertIn('"HeatSolve" "HeatSolver"', text)

    def test_sif_bool_formatting(self):
        from flow_studio.solvers.elmer_sif import SifSection
        s = SifSection("Solver", 1)
        s["Stabilize"] = True
        s["Nonlinear"] = False
        text = s.to_sif()
        self.assertIn("Stabilize = True", text)
        self.assertIn("Nonlinear = False", text)

    def test_sif_int_formatting(self):
        from flow_studio.solvers.elmer_sif import SifSection
        s = SifSection("Solver", 1)
        s["Max Iterations"] = 500
        text = s.to_sif()
        self.assertIn("Max Iterations = 500", text)

    def test_sif_builder_add_equation(self):
        from flow_studio.solvers.elmer_sif import SifBuilder
        b = SifBuilder()
        eq = b.add_equation("Heat", [1])
        self.assertEqual(len(b.equations), 1)
        self.assertIn("Active Solvers(1)", eq.data)


_FREECAD_AVAILABLE = False
try:
    import FreeCAD
    _FREECAD_AVAILABLE = True
except ImportError:
    pass


class TestModuleImports(unittest.TestCase):
    """Test that pure-Python modules can be imported (no FreeCAD needed)."""

    def test_import_physics_domains(self):
        from flow_studio.physics_domains import get_domain, PhysicsDomain, available_domains
        self.assertTrue(callable(get_domain))
        self.assertTrue(hasattr(PhysicsDomain, "key"))

    def test_import_elmer_sif(self):
        from flow_studio.solvers.elmer_sif import SifBuilder, SifSection
        self.assertTrue(callable(SifBuilder))

    def test_import_registry(self):
        from flow_studio.solvers.registry import get_runner, backends_for_domain
        self.assertTrue(callable(get_runner))
        self.assertTrue(callable(backends_for_domain))


@unittest.skipUnless(_FREECAD_AVAILABLE, "FreeCAD not available")
class TestFreeCADModuleImports(unittest.TestCase):
    """Test imports that require FreeCAD runtime."""

    def test_import_elmer_runner(self):
        from flow_studio.solvers.elmer_runner import ElmerRunner
        self.assertTrue(callable(ElmerRunner))

    def test_import_solid_material(self):
        from flow_studio.objects.solid_material import SolidMaterial
        self.assertTrue(callable(SolidMaterial))

    def test_import_electrostatic_material(self):
        from flow_studio.objects.electrostatic_material import ElectrostaticMaterial
        self.assertTrue(callable(ElectrostaticMaterial))

    def test_import_electromagnetic_material(self):
        from flow_studio.objects.electromagnetic_material import ElectromagneticMaterial
        self.assertTrue(callable(ElectromagneticMaterial))

    def test_import_thermal_material(self):
        from flow_studio.objects.thermal_material import ThermalMaterial
        self.assertTrue(callable(ThermalMaterial))

    def test_import_electrostatic_physics(self):
        from flow_studio.objects.electrostatic_physics_model import ElectrostaticPhysicsModel
        self.assertTrue(callable(ElectrostaticPhysicsModel))

    def test_import_electromagnetic_physics(self):
        from flow_studio.objects.electromagnetic_physics_model import ElectromagneticPhysicsModel
        self.assertTrue(callable(ElectromagneticPhysicsModel))

    def test_import_thermal_physics(self):
        from flow_studio.objects.thermal_physics_model import ThermalPhysicsModel
        self.assertTrue(callable(ThermalPhysicsModel))

    def test_import_structural_physics(self):
        from flow_studio.objects.structural_physics_model import StructuralPhysicsModel
        self.assertTrue(callable(StructuralPhysicsModel))

    def test_import_bc_structural(self):
        from flow_studio.objects.bc_structural import (
            BCFixedDisplacement, BCForce, BCPressureLoad
        )
        self.assertTrue(callable(BCFixedDisplacement))

    def test_import_bc_electrostatic(self):
        from flow_studio.objects.bc_electrostatic import (
            BCElectricPotential, BCSurfaceCharge, BCElectricFlux
        )
        self.assertTrue(callable(BCElectricPotential))

    def test_import_bc_electromagnetic(self):
        from flow_studio.objects.bc_electromagnetic import (
            BCMagneticPotential, BCCurrentDensity, BCMagneticFluxDensity,
            BCFarFieldEM
        )
        self.assertTrue(callable(BCMagneticPotential))

    def test_import_bc_thermal(self):
        from flow_studio.objects.bc_thermal import (
            BCTemperature, BCHeatFlux, BCConvection, BCRadiation
        )
        self.assertTrue(callable(BCTemperature))


if __name__ == "__main__":
    unittest.main()
