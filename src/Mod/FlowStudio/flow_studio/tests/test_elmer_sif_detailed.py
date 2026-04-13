# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Comprehensive tests for Elmer SIF generation library.

Tests every section type, formatting rule, builder method, and edge case
in flow_studio.solvers.elmer_sif – all pure Python, no FreeCAD needed.
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from flow_studio.solvers.elmer_sif import (
    SifSection, SifProcedure, SifBuilder, _format_kv, _format_float,
)


# ======================================================================
# SifSection tests
# ======================================================================

class TestSifSectionBasics(unittest.TestCase):
    """Basic SifSection creation and data access."""

    def test_create_with_type_only(self):
        s = SifSection("Header")
        self.assertEqual(s.block_type, "Header")
        self.assertIsNone(s.index)
        self.assertIsNone(s.name)
        self.assertEqual(len(s.data), 0)

    def test_create_with_index(self):
        s = SifSection("Body", 1)
        self.assertEqual(s.index, 1)
        self.assertEqual(s.header_line(), "Body 1")

    def test_create_with_name(self):
        s = SifSection("Material", 2, "Copper")
        self.assertEqual(s.name, "Copper")
        self.assertEqual(s.header_line(), "Material 2")

    def test_setitem_getitem(self):
        s = SifSection("Simulation")
        s["Coordinate System"] = "Cartesian 3D"
        self.assertEqual(s["Coordinate System"], "Cartesian 3D")

    def test_contains(self):
        s = SifSection("Simulation")
        s["Foo"] = "Bar"
        self.assertIn("Foo", s)
        self.assertNotIn("Baz", s)

    def test_get_with_default(self):
        s = SifSection("Simulation")
        self.assertIsNone(s.get("Missing"))
        self.assertEqual(s.get("Missing", 42), 42)
        s["Present"] = "yes"
        self.assertEqual(s.get("Present"), "yes")

    def test_insertion_order_preserved(self):
        s = SifSection("Solver", 1)
        s["Alpha"] = 1
        s["Beta"] = 2
        s["Gamma"] = 3
        keys = list(s.data.keys())
        self.assertEqual(keys, ["Alpha", "Beta", "Gamma"])


class TestSifSectionToSif(unittest.TestCase):
    """Test SIF text output for various data types."""

    def test_header_without_index(self):
        s = SifSection("Header")
        s["Mesh DB"] = '"." "mesh"'
        text = s.to_sif()
        self.assertTrue(text.startswith("Header\n"))
        self.assertTrue(text.strip().endswith("End"))

    def test_body_with_index(self):
        s = SifSection("Body", 3)
        s["Name"] = '"Solid"'
        text = s.to_sif()
        self.assertTrue(text.startswith("Body 3\n"))

    def test_string_value(self):
        s = SifSection("Simulation")
        s["Coordinate System"] = "Cartesian 3D"
        text = s.to_sif()
        self.assertIn("Coordinate System = Cartesian 3D", text)

    def test_integer_value(self):
        s = SifSection("Solver", 1)
        s["Max Iterations"] = 500
        text = s.to_sif()
        self.assertIn("Max Iterations = 500", text)

    def test_float_value_normal(self):
        s = SifSection("Material", 1)
        s["Density"] = 7850.0
        text = s.to_sif()
        self.assertIn("Density = 7850", text)

    def test_float_value_scientific(self):
        s = SifSection("Constants")
        s["Permittivity Of Vacuum"] = 8.8542e-12
        text = s.to_sif()
        self.assertIn("Permittivity Of Vacuum = 8.854200e-12", text)

    def test_float_value_large(self):
        s = SifSection("Material", 1)
        s["Youngs Modulus"] = 2.1e11
        text = s.to_sif()
        self.assertIn("2.100000e+11", text)

    def test_bool_true(self):
        s = SifSection("Solver", 1)
        s["Stabilize"] = True
        text = s.to_sif()
        self.assertIn("Stabilize = True", text)

    def test_bool_false(self):
        s = SifSection("Solver", 1)
        s["Nonlinear System Newton After Divergence"] = False
        text = s.to_sif()
        self.assertIn("= False", text)

    def test_procedure_value(self):
        s = SifSection("Solver", 1)
        s["Procedure"] = SifProcedure("HeatSolve", "HeatSolver")
        text = s.to_sif()
        self.assertIn('"HeatSolve" "HeatSolver"', text)

    def test_list_value(self):
        s = SifSection("Solver", 1)
        s["Active Solvers(2)"] = [1, 2]
        text = s.to_sif()
        self.assertIn("Active Solvers(2) = 1 2", text)

    def test_tuple_value(self):
        s = SifSection("Body Force", 1)
        s["Flow Bodyforce"] = (0.0, -9.81, 0.0)
        text = s.to_sif()
        self.assertIn("-9.81", text)

    def test_mixed_list(self):
        s = SifSection("Test")
        s["Mixed"] = [1, 2.5, 3]
        text = s.to_sif()
        self.assertIn("Mixed = 1 2.5 3", text)

    def test_end_block(self):
        s = SifSection("Header")
        text = s.to_sif()
        self.assertTrue(text.strip().endswith("End"))

    def test_multiple_entries(self):
        s = SifSection("Simulation")
        s["Coordinate System"] = "Cartesian 3D"
        s["Simulation Type"] = "Steady State"
        s["Max Output Level"] = 5
        text = s.to_sif()
        lines = text.strip().split("\n")
        # Header + 3 data lines + End
        self.assertEqual(len(lines), 5)


# ======================================================================
# SifProcedure tests
# ======================================================================

class TestSifProcedure(unittest.TestCase):
    """Test SifProcedure formatting."""

    def test_repr(self):
        p = SifProcedure("HeatSolve", "HeatSolver")
        self.assertEqual(repr(p), '"HeatSolve" "HeatSolver"')

    def test_attrs(self):
        p = SifProcedure("StatElecSolve", "StatElecSolver")
        self.assertEqual(p.library, "StatElecSolve")
        self.assertEqual(p.routine, "StatElecSolver")

    def test_in_section(self):
        s = SifSection("Solver", 1)
        s["Procedure"] = SifProcedure("FlowSolve", "FlowSolver")
        text = s.to_sif()
        self.assertIn('Procedure = "FlowSolve" "FlowSolver"', text)


# ======================================================================
# SifBuilder tests
# ======================================================================

class TestSifBuilderHeader(unittest.TestCase):
    """Test SifBuilder.set_header."""

    def test_default_header(self):
        b = SifBuilder()
        b.set_header()
        self.assertIn("Mesh DB", b.header.data)
        self.assertIn("Include Path", b.header.data)
        self.assertIn("Results Directory", b.header.data)

    def test_custom_header(self):
        b = SifBuilder()
        b.set_header(mesh_db="/data", mesh_dir="meshes", results_dir="output")
        text = b.header.to_sif()
        self.assertIn('"/data" "meshes"', text)
        self.assertIn('"output"', text)

    def test_header_fluent_api(self):
        b = SifBuilder()
        result = b.set_header()
        self.assertIs(result, b)  # returns self for chaining


class TestSifBuilderSimulation(unittest.TestCase):
    """Test SifBuilder.set_simulation."""

    def test_default_simulation(self):
        b = SifBuilder()
        b.set_simulation()
        self.assertEqual(b.simulation["Coordinate System"], "Cartesian 3D")
        self.assertEqual(b.simulation["Simulation Type"], "Steady State")
        self.assertEqual(b.simulation["Steady State Max Iterations"], 1)
        self.assertEqual(b.simulation["Max Output Level"], 5)

    def test_custom_simulation(self):
        b = SifBuilder()
        b.set_simulation(
            coord_system="Axi Symmetric",
            sim_type="Transient",
            steady_max_iter=20,
            output_level=3,
        )
        self.assertEqual(b.simulation["Coordinate System"], "Axi Symmetric")
        self.assertEqual(b.simulation["Simulation Type"], "Transient")
        self.assertEqual(b.simulation["Steady State Max Iterations"], 20)
        self.assertEqual(b.simulation["Max Output Level"], 3)

    def test_extra_kwargs(self):
        b = SifBuilder()
        b.set_simulation(Timestepping_Method="BDF",
                         BDF_Order=2)
        self.assertEqual(b.simulation["Timestepping Method"], "BDF")
        self.assertEqual(b.simulation["BDF Order"], 2)

    def test_simulation_fluent_api(self):
        b = SifBuilder()
        result = b.set_simulation()
        self.assertIs(result, b)


class TestSifBuilderConstants(unittest.TestCase):
    """Test SifBuilder.set_constant."""

    def test_set_single_constant(self):
        b = SifBuilder()
        b.set_constant("Permittivity Of Vacuum", 8.8542e-12)
        self.assertIn("Permittivity Of Vacuum", b.constants.data)
        self.assertAlmostEqual(b.constants["Permittivity Of Vacuum"],
                               8.8542e-12, places=18)

    def test_set_multiple_constants(self):
        b = SifBuilder()
        b.set_constant("Boltzmann Constant", 1.3807e-23)
        b.set_constant("Stefan Boltzmann", 5.6704e-8)
        self.assertEqual(len(b.constants.data), 2)

    def test_constant_fluent_api(self):
        b = SifBuilder()
        result = b.set_constant("A", 1)
        self.assertIs(result, b)


class TestSifBuilderBodies(unittest.TestCase):
    """Test SifBuilder.add_body."""

    def test_add_single_body(self):
        b = SifBuilder()
        body = b.add_body("Fluid", equation=1, material=1)
        self.assertEqual(len(b.bodies), 1)
        self.assertEqual(body.index, 1)
        self.assertEqual(body["Equation"], 1)
        self.assertEqual(body["Material"], 1)

    def test_add_multiple_bodies(self):
        b = SifBuilder()
        b1 = b.add_body("Body1", equation=1, material=1)
        b2 = b.add_body("Body2", equation=1, material=2)
        self.assertEqual(len(b.bodies), 2)
        self.assertEqual(b1.index, 1)
        self.assertEqual(b2.index, 2)

    def test_body_optional_params(self):
        b = SifBuilder()
        body = b.add_body("Full",
                          equation=1, material=1,
                          body_force=1, initial_condition=1)
        self.assertEqual(body["Body Force"], 1)
        self.assertEqual(body["Initial Condition"], 1)

    def test_body_minimal(self):
        b = SifBuilder()
        body = b.add_body("Empty")
        self.assertNotIn("Equation", body.data)
        self.assertNotIn("Material", body.data)

    def test_body_name_in_output(self):
        b = SifBuilder()
        body = b.add_body("Test Body")
        self.assertEqual(body["Name"], '"Test Body"')


class TestSifBuilderMaterials(unittest.TestCase):
    """Test SifBuilder.add_material."""

    def test_add_material(self):
        b = SifBuilder()
        m = b.add_material("Air")
        m["Density"] = 1.225
        m["Viscosity"] = 1.81e-5
        self.assertEqual(len(b.materials), 1)
        self.assertEqual(m.index, 1)
        self.assertAlmostEqual(m["Density"], 1.225)

    def test_material_indexing(self):
        b = SifBuilder()
        m1 = b.add_material("Air")
        m2 = b.add_material("Water")
        m3 = b.add_material("Steel")
        self.assertEqual(m1.index, 1)
        self.assertEqual(m2.index, 2)
        self.assertEqual(m3.index, 3)

    def test_material_name(self):
        b = SifBuilder()
        m = b.add_material("Copper")
        self.assertEqual(m["Name"], '"Copper"')


class TestSifBuilderSolvers(unittest.TestCase):
    """Test SifBuilder.add_solver."""

    def test_add_heat_solver(self):
        b = SifBuilder()
        proc = SifProcedure("HeatSolve", "HeatSolver")
        s = b.add_solver("Heat Equation", proc,
                         variable="Temperature", variable_dofs=1)
        self.assertEqual(len(b.solvers), 1)
        self.assertEqual(s["Equation"], '"Heat Equation"')
        self.assertEqual(s["Variable"], '"Temperature"')
        self.assertEqual(s["Variable DOFs"], 1)

    def test_add_solver_with_settings(self):
        b = SifBuilder()
        proc = SifProcedure("FlowSolve", "FlowSolver")
        s = b.add_solver("Navier-Stokes", proc,
                         variable="Flow Solution",
                         variable_dofs=4,
                         Stabilize=True,
                         Nonlinear_System_Convergence_Tolerance=1e-5)
        # kwargs get stored as-is (keys not transformed)
        self.assertTrue(s["Stabilize"])

    def test_solver_without_variable(self):
        b = SifBuilder()
        proc = SifProcedure("ResultOutputSolve", "ResultOutputSolver")
        s = b.add_solver("Result Output", proc)
        self.assertNotIn("Variable", s.data)

    def test_solver_indexing(self):
        b = SifBuilder()
        p = SifProcedure("A", "B")
        s1 = b.add_solver("S1", p)
        s2 = b.add_solver("S2", p)
        self.assertEqual(s1.index, 1)
        self.assertEqual(s2.index, 2)


class TestSifBuilderEquations(unittest.TestCase):
    """Test SifBuilder.add_equation."""

    def test_single_solver_equation(self):
        b = SifBuilder()
        eq = b.add_equation("Heat", [1])
        self.assertEqual(len(b.equations), 1)
        self.assertIn("Active Solvers(1)", eq.data)
        self.assertEqual(eq.data["Active Solvers(1)"], "1")

    def test_multi_solver_equation(self):
        b = SifBuilder()
        eq = b.add_equation("Coupled", [1, 2, 3])
        self.assertIn("Active Solvers(3)", eq.data)
        self.assertEqual(eq.data["Active Solvers(3)"], "1 2 3")

    def test_equation_name(self):
        b = SifBuilder()
        eq = b.add_equation("My Equation", [1])
        self.assertEqual(eq["Name"], '"My Equation"')


class TestSifBuilderBoundaryConditions(unittest.TestCase):
    """Test SifBuilder.add_boundary_condition."""

    def test_add_bc(self):
        b = SifBuilder()
        bc = b.add_boundary_condition("Hot Wall")
        bc["Temperature"] = 373.15
        bc["Target Boundaries(1)"] = 1
        self.assertEqual(len(b.boundary_conditions), 1)
        self.assertAlmostEqual(bc["Temperature"], 373.15)

    def test_bc_indexing(self):
        b = SifBuilder()
        bc1 = b.add_boundary_condition("Wall")
        bc2 = b.add_boundary_condition("Inlet")
        bc3 = b.add_boundary_condition("Outlet")
        self.assertEqual(bc1.index, 1)
        self.assertEqual(bc2.index, 2)
        self.assertEqual(bc3.index, 3)


class TestSifBuilderInitialConditions(unittest.TestCase):
    """Test SifBuilder.add_initial_condition."""

    def test_add_ic(self):
        b = SifBuilder()
        ic = b.add_initial_condition("Initial Temperature")
        ic["Temperature"] = 293.15
        self.assertEqual(len(b.initial_conditions), 1)

    def test_ic_indexing(self):
        b = SifBuilder()
        ic1 = b.add_initial_condition("IC1")
        ic2 = b.add_initial_condition("IC2")
        self.assertEqual(ic1.index, 1)
        self.assertEqual(ic2.index, 2)


class TestSifBuilderBodyForces(unittest.TestCase):
    """Test SifBuilder.add_body_force."""

    def test_add_body_force(self):
        b = SifBuilder()
        bf = b.add_body_force("Gravity")
        bf["Flow Bodyforce 2"] = -9.81
        self.assertEqual(len(b.body_forces), 1)

    def test_body_force_indexing(self):
        b = SifBuilder()
        bf1 = b.add_body_force("BF1")
        bf2 = b.add_body_force("BF2")
        self.assertEqual(bf1.index, 1)
        self.assertEqual(bf2.index, 2)


class TestSifBuilderGenerate(unittest.TestCase):
    """Test complete SIF file generation."""

    def _build_heat_sif(self):
        """Build a complete heat transfer SIF for testing."""
        b = SifBuilder()
        b.set_header(mesh_db=".", mesh_dir="mesh")
        b.set_simulation(
            coord_system="Cartesian 3D",
            sim_type="Steady State",
            steady_max_iter=1,
        )
        b.set_constant("Stefan Boltzmann", 5.67e-8)

        b.add_body("Solid", equation=1, material=1, initial_condition=1)
        m = b.add_material("Copper")
        m["Density"] = 8960.0
        m["Heat Conductivity"] = 401.0
        m["Heat Capacity"] = 385.0

        proc = SifProcedure("HeatSolve", "HeatSolver")
        b.add_solver("Heat Equation", proc,
                     variable="Temperature", variable_dofs=1)
        b.add_equation("Heat", [1])

        bc_hot = b.add_boundary_condition("Hot Wall")
        bc_hot["Temperature"] = 373.15
        bc_hot["Target Boundaries(1)"] = 1

        bc_cold = b.add_boundary_condition("Cold Wall")
        bc_cold["Temperature"] = 293.15
        bc_cold["Target Boundaries(1)"] = 2

        ic = b.add_initial_condition("Room Temp")
        ic["Temperature"] = 293.15

        return b

    def test_generate_contains_check_keywords(self):
        b = self._build_heat_sif()
        sif = b.generate()
        self.assertIn('Check Keywords "Warn"', sif)

    def test_generate_has_header(self):
        sif = self._build_heat_sif().generate()
        self.assertIn("Header\n", sif)
        self.assertIn("Mesh DB", sif)

    def test_generate_has_simulation(self):
        sif = self._build_heat_sif().generate()
        self.assertIn("Simulation\n", sif)
        self.assertIn("Steady State", sif)
        self.assertIn("Cartesian 3D", sif)

    def test_generate_has_constants(self):
        sif = self._build_heat_sif().generate()
        self.assertIn("Constants\n", sif)
        self.assertIn("Stefan Boltzmann", sif)

    def test_generate_has_body(self):
        sif = self._build_heat_sif().generate()
        self.assertIn("Body 1\n", sif)
        self.assertIn('"Solid"', sif)

    def test_generate_has_material(self):
        sif = self._build_heat_sif().generate()
        self.assertIn("Material 1\n", sif)
        self.assertIn("Density = 8960", sif)
        self.assertIn("Heat Conductivity = 401", sif)

    def test_generate_has_solver(self):
        sif = self._build_heat_sif().generate()
        self.assertIn("Solver 1\n", sif)
        self.assertIn('"HeatSolve" "HeatSolver"', sif)

    def test_generate_has_equation(self):
        sif = self._build_heat_sif().generate()
        self.assertIn("Equation 1\n", sif)
        self.assertIn("Active Solvers(1) = 1", sif)

    def test_generate_has_boundary_conditions(self):
        sif = self._build_heat_sif().generate()
        self.assertIn("Boundary Condition 1\n", sif)
        self.assertIn("Boundary Condition 2\n", sif)
        self.assertIn("Temperature = 373.15", sif)
        self.assertIn("Temperature = 293.15", sif)

    def test_generate_has_initial_condition(self):
        sif = self._build_heat_sif().generate()
        self.assertIn("Initial Condition 1\n", sif)
        self.assertIn("Temperature = 293.15", sif)

    def test_generate_all_end_blocks(self):
        sif = self._build_heat_sif().generate()
        # Count "End" blocks
        end_count = sif.count("\nEnd\n") + sif.count("\nEnd")
        # Header + Simulation + Constants + Body + Material + Solver +
        # Equation + 2 BCs + IC = 10
        self.assertGreaterEqual(end_count, 10)

    def test_generate_empty_builder(self):
        b = SifBuilder()
        sif = b.generate()
        self.assertIn('Check Keywords "Warn"', sif)
        self.assertIn("Header", sif)
        self.assertIn("Simulation", sif)

    def test_no_constants_if_empty(self):
        b = SifBuilder()
        b.set_header()
        b.set_simulation()
        sif = b.generate()
        self.assertNotIn("Constants\n", sif)


# ======================================================================
# Domain-specific SIF templates
# ======================================================================

class TestElectrostaticSif(unittest.TestCase):
    """Test SIF generation for electrostatic analysis."""

    def test_electrostatic_template(self):
        b = SifBuilder()
        b.set_header()
        b.set_simulation()
        b.set_constant("Permittivity Of Vacuum", 8.8542e-12)

        body = b.add_body("Dielectric", equation=1, material=1)
        mat = b.add_material("FR4")
        mat["Relative Permittivity"] = 4.5

        proc = SifProcedure("StatElecSolve", "StatElecSolver")
        b.add_solver("Stat Elec Solver", proc,
                     variable="Potential", variable_dofs=1)
        b.add_equation("Electrostatic", [1])

        bc = b.add_boundary_condition("Electrode")
        bc["Potential"] = 100.0
        bc["Target Boundaries(1)"] = 1

        sif = b.generate()
        self.assertIn("Permittivity Of Vacuum", sif)
        self.assertIn("Relative Permittivity = 4.5", sif)
        self.assertIn("StatElecSolve", sif)
        self.assertIn("Potential = 100", sif)


class TestStructuralSif(unittest.TestCase):
    """Test SIF generation for structural analysis."""

    def test_linear_elasticity_template(self):
        b = SifBuilder()
        b.set_header()
        b.set_simulation()

        body = b.add_body("Beam", equation=1, material=1)
        mat = b.add_material("Steel")
        mat["Youngs Modulus"] = 2.1e11
        mat["Poisson Ratio"] = 0.3
        mat["Density"] = 7850.0

        proc = SifProcedure("ElasticSolve", "ElasticSolver")
        b.add_solver("Elasticity Solver", proc,
                     variable="Displacement", variable_dofs=3)
        b.add_equation("Elasticity", [1])

        bc_fix = b.add_boundary_condition("Fixed")
        bc_fix["Displacement 1"] = 0.0
        bc_fix["Displacement 2"] = 0.0
        bc_fix["Displacement 3"] = 0.0

        bc_load = b.add_boundary_condition("Load")
        bc_load["Force 2"] = -1000.0

        sif = b.generate()
        self.assertIn("2.100000e+11", sif)
        self.assertIn("Poisson Ratio = 0.3", sif)
        self.assertIn("Displacement", sif)
        self.assertIn("Force 2 = -1000", sif)


class TestMagnetostaticSif(unittest.TestCase):
    """Test SIF generation for electromagnetic analysis."""

    def test_magnetostatic_template(self):
        b = SifBuilder()
        b.set_header()
        b.set_simulation()

        body = b.add_body("Coil", equation=1, material=1)
        mat = b.add_material("Air")
        mat["Relative Permeability"] = 1.0

        proc = SifProcedure("MagnetoDynamics", "WhitneyAVSolver")
        b.add_solver("Magnetodynamics", proc,
                     variable="AV", variable_dofs=1)
        b.add_equation("MagnetoDynamics", [1])

        bf = b.add_body_force("Current")
        bf["Current Density 1"] = 0.0
        bf["Current Density 2"] = 0.0
        bf["Current Density 3"] = 1e6

        sif = b.generate()
        self.assertIn("MagnetoDynamics", sif)
        self.assertIn("WhitneyAVSolver", sif)
        self.assertIn("Current Density 3", sif)
        self.assertIn("Body Force 1\n", sif)


class TestThermalSif(unittest.TestCase):
    """Test SIF generation for thermal analysis."""

    def test_heat_conduction_template(self):
        b = SifBuilder()
        b.set_header()
        b.set_simulation()
        b.set_constant("Stefan Boltzmann", 5.6704e-8)

        body = b.add_body("PCB", equation=1, material=1)
        mat = b.add_material("FR4")
        mat["Density"] = 1900.0
        mat["Heat Conductivity"] = 0.3
        mat["Heat Capacity"] = 1369.0

        proc = SifProcedure("HeatSolve", "HeatSolver")
        b.add_solver("Heat Equation", proc,
                     variable="Temperature", variable_dofs=1)
        b.add_equation("Heat Transfer", [1])

        bc_temp = b.add_boundary_condition("Chip Surface")
        bc_temp["Temperature"] = 358.15  # 85°C

        bc_conv = b.add_boundary_condition("Ambient")
        bc_conv["Heat Transfer Coefficient"] = 10.0
        bc_conv["External Temperature"] = 293.15

        sif = b.generate()
        self.assertIn("Stefan Boltzmann", sif)
        self.assertIn("Heat Conductivity = 0.3", sif)
        self.assertIn("Temperature = 358.15", sif)
        self.assertIn("Heat Transfer Coefficient = 10", sif)
        self.assertIn("External Temperature = 293.15", sif)


# ======================================================================
# Formatting helper tests
# ======================================================================

class TestFormatFloat(unittest.TestCase):
    """Test _format_float edge cases."""

    def test_zero(self):
        # abs(0.0) < 1e-3 triggers scientific notation path
        result = _format_float(0.0)
        self.assertIn("0", result)
        self.assertAlmostEqual(float(result), 0.0)

    def test_normal_float(self):
        result = _format_float(1.225)
        self.assertEqual(result, "1.225")

    def test_small_float(self):
        result = _format_float(1e-5)
        self.assertIn("e-", result)

    def test_large_float(self):
        result = _format_float(2.1e11)
        self.assertIn("e+", result)

    def test_one(self):
        result = _format_float(1.0)
        self.assertEqual(result, "1")

    def test_negative(self):
        result = _format_float(-9.81)
        self.assertEqual(result, "-9.81")


class TestFormatKV(unittest.TestCase):
    """Test _format_kv for all value types."""

    def test_string(self):
        result = _format_kv("Key", "Value")
        self.assertEqual(result, "Key = Value")

    def test_integer(self):
        result = _format_kv("N", 42)
        self.assertEqual(result, "N = 42")

    def test_float(self):
        result = _format_kv("D", 1.225)
        self.assertEqual(result, "D = 1.225")

    def test_bool_true(self):
        result = _format_kv("Flag", True)
        self.assertEqual(result, "Flag = True")

    def test_bool_false(self):
        result = _format_kv("Flag", False)
        self.assertEqual(result, "Flag = False")

    def test_procedure(self):
        p = SifProcedure("A", "B")
        result = _format_kv("Procedure", p)
        self.assertEqual(result, 'Procedure = "A" "B"')

    def test_list(self):
        result = _format_kv("Items(3)", [1, 2, 3])
        self.assertEqual(result, "Items(3) = 1 2 3")


if __name__ == "__main__":
    unittest.main()
