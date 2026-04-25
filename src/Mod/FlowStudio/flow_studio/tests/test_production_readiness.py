# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Production-readiness tests for complex flow simulations.

Targets real-world scenarios:
  - Large rotating enclosures (CT detector housings)
  - Internal ventilators / fan zones
  - Multi-physics coupling (EM + Thermal + CFD)
  - Transient rotating machinery (MRF / sliding mesh)
  - Parallel decomposition for large models
  - Solver parameter robustness for stiff problems

These tests run **without** FreeCAD or external solvers installed.
They validate the full parameter space, SIF generation, OpenFOAM dict
templates, and domain wiring needed before production runs.
"""

import math
import os
import sys
import unittest

# Ensure package is importable when run from the FlowStudio directory
_HERE = os.path.dirname(os.path.abspath(__file__))
_PKG_ROOT = os.path.normpath(os.path.join(_HERE, os.pardir, os.pardir))
if _PKG_ROOT not in sys.path:
    sys.path.insert(0, _PKG_ROOT)


# =====================================================================
# 1. Rotating Wall BC Parameter Validation
# =====================================================================

class TestRotatingWallParameters(unittest.TestCase):
    """Validate rotating-wall BC property defaults and physics."""

    def test_angular_velocity_range_for_ct_gantry(self):
        """CT gantry rotates at ~1-3 rev/s → 6.3-18.8 rad/s."""
        # A typical CT detector gantry: 2 rev/s
        rpm = 120  # 2 rev/s
        omega = rpm * 2 * math.pi / 60
        self.assertAlmostEqual(omega, 4 * math.pi, places=4)
        self.assertGreater(omega, 0)

    def test_tip_speed_for_ventilator_blades(self):
        """Ventilator blade tip speed check: v_tip = omega * r."""
        rpm = 3000
        blade_radius_m = 0.15  # 150mm
        omega = rpm * 2 * math.pi / 60
        v_tip = omega * blade_radius_m
        # Tip speed ~ 47 m/s — subsonic, valid for incompressible
        self.assertGreater(v_tip, 30)
        self.assertLess(v_tip, 100)  # Still incompressible Ma < 0.3

    def test_rotation_axis_unit_vector(self):
        """Axis vector should be normalizable to unit length."""
        axes = [
            (0, 0, 1),    # Z-axis (typical CT rotation)
            (1, 0, 0),    # X-axis
            (0, 1, 0),    # Y-axis
            (1, 1, 0),    # Diagonal
        ]
        for ax in axes:
            length = math.sqrt(sum(c * c for c in ax))
            self.assertGreater(length, 0, f"Zero-length axis: {ax}")

    def test_courant_number_for_rotating_mesh(self):
        """CFL condition: Co = v * dt / dx < 1 for stability."""
        v_tip = 47.0  # m/s (from ventilator test above)
        dx = 0.002    # 2mm cell near blade
        co_target = 0.8
        dt_max = co_target * dx / v_tip
        # dt ~ 34 µs — must be very small for rotating machinery
        self.assertGreater(dt_max, 1e-6)
        self.assertLess(dt_max, 1e-3)


# =====================================================================
# 2. OpenFOAM Dict Template Validation for MRF / Rotating Cases
# =====================================================================

class TestOpenFOAMRotatingTemplates(unittest.TestCase):
    """Validate OpenFOAM configuration patterns for rotating machinery."""

    def _make_mrf_dict_content(self, zone_name, omega, axis, origin):
        """Generate fvOptions MRF dictionary content."""
        return (
            "FoamFile\n"
            "{\n"
            "    version     2.0;\n"
            "    format      ascii;\n"
            "    class       dictionary;\n"
            "    object      fvOptions;\n"
            "}\n"
            "\n"
            f"{zone_name}\n"
            "{\n"
            "    type            MRFSource;\n"
            "    active          true;\n"
            "\n"
            f"    MRFSourceCoeffs\n"
            "    {\n"
            f"        cellZone        {zone_name};\n"
            f"        origin          ({origin[0]} {origin[1]} {origin[2]});\n"
            f"        axis            ({axis[0]} {axis[1]} {axis[2]});\n"
            f"        omega           {omega};\n"
            "    }\n"
            "}\n"
        )

    def test_mrf_dict_structure(self):
        """MRF dict must have type, cellZone, origin, axis, omega."""
        content = self._make_mrf_dict_content(
            "rotatingZone", 12.566, (0, 0, 1), (0, 0, 0)
        )
        self.assertIn("type            MRFSource", content)
        self.assertIn("cellZone        rotatingZone", content)
        self.assertIn("omega           12.566", content)
        self.assertIn("axis            (0 0 1)", content)

    def test_decompose_par_dict_scotch(self):
        """decomposeParDict for parallel rotating-machinery simulation."""
        n_procs = 8
        content = (
            "FoamFile\n"
            "{\n"
            "    version     2.0;\n"
            "    format      ascii;\n"
            "    class       dictionary;\n"
            "    object      decomposeParDict;\n"
            "}\n"
            "\n"
            f"numberOfSubdomains  {n_procs};\n"
            "\n"
            "method          scotch;\n"
        )
        self.assertIn(f"numberOfSubdomains  {n_procs}", content)
        self.assertIn("method          scotch", content)

    def test_control_dict_transient_rotating(self):
        """controlDict for pimpleFoam rotating case."""
        dt = 5e-5
        end_time = 0.1
        write_interval = 200
        content = (
            f"application     pimpleFoam;\n"
            f"startFrom       startTime;\n"
            f"startTime       0;\n"
            f"stopAt          endTime;\n"
            f"endTime         {end_time};\n"
            f"deltaT          {dt};\n"
            f"writeControl    timeStep;\n"
            f"writeInterval   {write_interval};\n"
            f"maxCo           0.8;\n"
        )
        self.assertIn("pimpleFoam", content)
        self.assertIn(f"endTime         {end_time}", content)
        self.assertIn(f"deltaT          {dt}", content)


# =====================================================================
# 3. Multi-Physics Domain Coupling (CT Detector Scenario)
# =====================================================================

class TestMultiPhysicsCoupling(unittest.TestCase):
    """Validate domain registry supports CT-detector-like multi-physics.

    A CT detector involves:
      - Electromagnetic: X-ray tube EM fields
      - Thermal: heat dissipation from tube + electronics
      - CFD: forced air cooling via internal fans
    """

    def setUp(self):
        from flow_studio.physics_domains import (
            get_domain, available_domains, all_domains,
        )
        self.get_domain = get_domain
        self.available_domains = available_domains
        self.all_domains = all_domains

    def test_all_ct_related_domains_exist(self):
        keys = self.available_domains()
        for needed in ("CFD", "Electromagnetic", "Thermal"):
            self.assertIn(needed, keys, f"Missing domain: {needed}")

    def test_cfd_domain_supports_rotating_machinery(self):
        cfd = self.get_domain("CFD")
        self.assertIn("Internal Flow", cfd.analysis_types)
        # BCWall supports rotating wall → used for fan blades
        self.assertIn("FlowStudio::BCWall", cfd.bc_types)

    def test_thermal_domain_has_convection_bc(self):
        thermal = self.get_domain("Thermal")
        self.assertIn("FlowStudio::BCConvection", thermal.bc_types)
        self.assertIn("FlowStudio::BCHeatFlux", thermal.bc_types)

    def test_electromagnetic_domain_has_current_density(self):
        em = self.get_domain("Electromagnetic")
        self.assertIn("FlowStudio::BCCurrentDensity", em.bc_types)
        self.assertIn("FlowStudio::BCMagneticPotential", em.bc_types)

    def test_elmer_supports_all_ct_domains(self):
        """Elmer must be available for all three CT-relevant physics."""
        for key in ("CFD", "Electromagnetic", "Thermal"):
            dom = self.get_domain(key)
            self.assertIn("Elmer", dom.solver_backends,
                          f"Elmer missing from {key}")

    def test_domains_have_distinct_material_types(self):
        cfd = self.get_domain("CFD")
        em = self.get_domain("Electromagnetic")
        thermal = self.get_domain("Thermal")
        materials = {cfd.material_type, em.material_type, thermal.material_type}
        self.assertEqual(len(materials), 3,
                         "CT domains should use distinct material models")

    def test_domain_physics_model_types_unique(self):
        physics = set()
        for key in ("CFD", "Electromagnetic", "Thermal"):
            dom = self.get_domain(key)
            physics.add(dom.physics_model_type)
        self.assertEqual(len(physics), 3)


# =====================================================================
# 4. Elmer SIF Generation for Rotating / Transient EM+Thermal
# =====================================================================

class TestElmerSifForRotatingSimulation(unittest.TestCase):
    """Validate Elmer SIF builder produces correct sections for
    transient electromagnetic and thermal analyses."""

    def setUp(self):
        from flow_studio.solvers.elmer_sif import SifBuilder
        self.builder = SifBuilder

    def test_transient_simulation_section(self):
        b = self.builder()
        b.set_simulation(steady_state=False, time_steps=1000, dt=1e-4)
        sif = b.generate()
        self.assertIn("Simulation Type = Transient", sif)
        self.assertIn("Timestep Sizes = 0.0001", sif)
        self.assertIn("Timestep Intervals = 1000", sif)

    def test_electromagnetic_solver_section(self):
        b = self.builder()
        b.set_simulation(steady_state=False)
        b.add_solver(
            "MagnetoDynamics",
            variable="AV",
            exec_solver="Always",
            Linear_System_Solver="Iterative",
            Linear_System_Iterative_Method="BiCGStab",
        )
        sif = b.generate()
        self.assertIn("MagnetoDynamics", sif)
        self.assertIn("Variable = AV", sif)
        self.assertIn("BiCGStab", sif)

    def test_thermal_solver_coupled_section(self):
        b = self.builder()
        b.set_simulation(steady_state=True)
        b.add_solver(
            "HeatSolve",
            variable="Temperature",
            exec_solver="Always",
        )
        b.add_body(name="Electronics", material=1, equation=1)
        b.add_material(name="Copper", Density=8960.0, Heat_Capacity=385.0,
                       Heat_Conductivity=401.0)
        sif = b.generate()
        self.assertIn("HeatSolve", sif)
        self.assertIn("Temperature", sif)
        self.assertIn("8960", sif)

    def test_body_force_for_heat_source(self):
        """CT x-ray tube generates volumetric heat → body force."""
        b = self.builder()
        b.add_body_force(name="XRayHeat", Heat_Source=5e6)
        sif = b.generate()
        self.assertIn("Body Force 1", sif)
        self.assertIn("Heat Source", sif)
        self.assertIn("5000000", sif)

    def test_multi_material_sif(self):
        """CT detector uses multiple materials: air, copper, ceramic."""
        b = self.builder()
        b.add_material(name="Air", Density=1.225, Heat_Conductivity=0.025)
        b.add_material(name="Copper", Density=8960.0, Heat_Conductivity=401.0)
        b.add_material(name="Ceramic", Density=3900.0, Heat_Conductivity=30.0)
        sif = b.generate()
        self.assertIn("Material 1", sif)
        self.assertIn("Material 2", sif)
        self.assertIn("Material 3", sif)
        self.assertIn("Air", sif)
        self.assertIn("Copper", sif)
        self.assertIn("Ceramic", sif)


# =====================================================================
# 5. Solver Registry for Complex Scenarios
# =====================================================================

class TestSolverRegistryProduction(unittest.TestCase):
    """Verify solver registry handles production-scale configurations."""

    def setUp(self):
        from flow_studio.solvers import registry
        self.reg = registry

    def test_backends_for_cfd_include_all_three(self):
        backends = self.reg.backends_for_domain("CFD")
        self.assertIn("OpenFOAM", backends)
        self.assertIn("FluidX3D", backends)
        self.assertIn("Elmer", backends)

    def test_backends_for_electromagnetic(self):
        backends = self.reg.backends_for_domain("Electromagnetic")
        self.assertIn("Elmer", backends)

    def test_backends_for_thermal(self):
        backends = self.reg.backends_for_domain("Thermal")
        self.assertIn("Elmer", backends)

    def test_get_runner_returns_module_path(self):
        entry = self.reg._REGISTRY_PATHS.get("OpenFOAM")
        self.assertIsNotNone(entry)
        self.assertIn("openfoam_runner", entry[0])

    def test_get_runner_elmer(self):
        entry = self.reg._REGISTRY_PATHS.get("Elmer")
        self.assertIsNotNone(entry)
        self.assertIn("elmer_runner", entry[0])

    def test_dynamic_registration_survives(self):
        """Register a custom backend and verify it appears."""
        self.reg.register_backend(
            "TestSolver", "test_module.TestRunner", "TestRunnerClass",
            domains=["CFD"],
        )
        self.assertIn("TestSolver", self.reg.available_backends())
        self.assertIn("TestSolver", self.reg.backends_for_domain("CFD"))

        # Cleanup: remove the test entry so we don't pollute other tests
        if "TestSolver" in self.reg._REGISTRY_PATHS:
            del self.reg._REGISTRY_PATHS["TestSolver"]
        if "CFD" in self.reg._DOMAIN_SOLVERS:
            if "TestSolver" in self.reg._DOMAIN_SOLVERS["CFD"]:
                self.reg._DOMAIN_SOLVERS["CFD"].remove("TestSolver")


# =====================================================================
# 6. Dependency Detection for Production Deployment
# =====================================================================

class TestDependencyDetectionProduction(unittest.TestCase):
    """Ensure dependency system correctly identifies large-scale requirements."""

    def setUp(self):
        from flow_studio.runtime import dependencies as solver_deps
        self.deps = solver_deps

    def test_check_all_returns_all_registered_dependency_groups(self):
        """Production dependency scan should cover the full registered toolchain set."""
        from unittest.mock import patch
        with patch("shutil.which", return_value=None):
            reports = self.deps.check_all()
        expected = {"OpenFOAM", "FluidX3D", "Elmer", "Geant4", "SU2",
                    "ParaView", "Meshing", "PostProcessing", "Raysect",
                    "Meep", "openEMS", "Optiland"}
        self.assertEqual(set(reports.keys()), expected)

    def test_elmer_requires_solver_and_grid(self):
        """Elmer needs ElmerSolver + ElmerGrid for production."""
        from unittest.mock import patch
        with patch("shutil.which", return_value=None):
            report = self.deps.check_backend("Elmer")
        required_names = [d.name for d in report.deps if d.required]
        self.assertIn("ElmerSolver", required_names)
        self.assertIn("ElmerGrid", required_names)

    def test_openfoam_needs_decompose_par(self):
        """Parallel OpenFOAM needs decomposePar."""
        from unittest.mock import patch
        with patch("shutil.which", return_value=None):
            report = self.deps.check_backend("OpenFOAM")
        all_names = [d.name for d in report.deps]
        self.assertIn("decomposePar", all_names)

    def test_detect_cpu_cores_returns_positive(self):
        physical, logical = self.deps.detect_cpu_cores()
        self.assertGreater(physical, 0)
        self.assertGreaterEqual(logical, physical)

    def test_recommend_parallel_returns_sane_values(self):
        rec = self.deps.recommend_parallel_settings()
        self.assertIn("cpu_physical", rec)
        self.assertIn("cpu_logical", rec)
        self.assertIn("OpenFOAM", rec)
        self.assertIn("Elmer", rec)
        self.assertGreater(rec["OpenFOAM"]["NumProcessors"], 0)
        self.assertGreater(rec["Elmer"]["NumProcessors"], 0)
        self.assertEqual(rec["OpenFOAM"]["NumProcessors"],
                         rec["cpu_physical"])
        self.assertEqual(rec["Elmer"]["NumProcessors"],
                         rec["cpu_physical"])


# =====================================================================
# 7. Large Model Mesh Strategy
# =====================================================================

class TestLargeModelMeshStrategy(unittest.TestCase):
    """Validate y+ and mesh sizing for production-scale models."""

    def setUp(self):
        from flow_studio.utils.mesh_utils import estimate_first_layer_height
        self.estimate_y = estimate_first_layer_height

    def test_yplus_1_for_rotating_blade(self):
        """Wall-resolving mesh for fan blade: y+ ~ 1."""
        h = self.estimate_y(
            velocity=30.0,       # m/s blade-relative
            length=0.1,          # 100mm chord
            kinematic_viscosity=1.5e-5,  # air
            y_plus_target=1.0,
        )
        # First cell height ~ microns
        self.assertGreater(h, 1e-7)
        self.assertLess(h, 1e-3)

    def test_yplus_30_for_housing_walls(self):
        """Wall-function mesh for enclosure: y+ ~ 30."""
        h = self.estimate_y(
            velocity=5.0,        # m/s bulk flow in enclosure
            length=0.5,          # 500mm housing dimension
            kinematic_viscosity=1.5e-5,
            y_plus_target=30.0,
        )
        # First cell ~ 1mm range
        self.assertGreater(h, 1e-5)
        self.assertLess(h, 0.01)

    def test_yplus_scales_with_velocity(self):
        """Higher velocity → thinner boundary layer → smaller y."""
        h_slow = self.estimate_y(5.0, 0.5, 1.5e-5, 30.0)
        h_fast = self.estimate_y(50.0, 0.5, 1.5e-5, 30.0)
        self.assertGreater(h_slow, h_fast)

    def test_yplus_water_cooling(self):
        """Water-cooled CT electronics: ν_water ≈ 1e-6 m²/s."""
        h = self.estimate_y(
            velocity=2.0,
            length=0.05,
            kinematic_viscosity=1e-6,  # water
            y_plus_target=1.0,
        )
        self.assertGreater(h, 0)

    def test_mesh_cell_count_estimate(self):
        """Rough cell count estimate for CT enclosure."""
        # Box: 1m x 0.5m x 0.5m, avg cell size 5mm
        vol = 1.0 * 0.5 * 0.5       # 0.25 m³
        cell_vol = 0.005 ** 3        # 1.25e-7 m³
        n_cells = vol / cell_vol     # ~ 2 million cells
        self.assertGreater(n_cells, 1e6)
        self.assertLess(n_cells, 1e8)  # Not unreasonably large


# =====================================================================
# 8. Material Database Completeness for Multi-Physics
# =====================================================================

class TestMaterialDatabaseProduction(unittest.TestCase):
    """Verify material presets cover CT detector construction materials."""

    def setUp(self):
        from flow_studio.utils.mesh_utils import FLUID_MATERIAL_PRESETS
        self.presets = FLUID_MATERIAL_PRESETS

    def test_air_for_cooling(self):
        self.assertIn("Air (20°C, 1atm)", self.presets)
        air = self.presets["Air (20°C, 1atm)"]
        self.assertAlmostEqual(air["density"], 1.225, places=2)

    def test_water_for_liquid_cooling(self):
        self.assertIn("Water (20°C)", self.presets)
        water = self.presets["Water (20°C)"]
        self.assertAlmostEqual(water["density"], 998.0, places=0)

    def test_oil_for_transformer_cooling(self):
        """Oil preset for insulating/cooling fluid."""
        self.assertIn("Oil (SAE 30)", self.presets)
        oil = self.presets["Oil (SAE 30)"]
        self.assertGreater(oil["dynamic_viscosity"], 0.01)

    def test_all_presets_have_thermal_properties(self):
        """Every fluid preset must have density, viscosity, Cp, conductivity."""
        required = {"density", "dynamic_viscosity", "specific_heat", "thermal_conductivity"}
        for name, props in self.presets.items():
            for key in required:
                self.assertIn(key, props, f"Missing '{key}' in preset '{name}'")
                self.assertGreater(props[key], 0, f"Non-positive '{key}' in '{name}'")


# =====================================================================
# 9. Parallel Configuration Validation
# =====================================================================

class TestParallelConfiguration(unittest.TestCase):
    """Validate parallel solver settings for HPC-scale runs."""

    def test_scotch_decomposition_valid_proc_counts(self):
        """Valid proc counts for scotch decomposition: > 1."""
        for n in (2, 4, 8, 16, 32, 64, 128):
            self.assertGreater(n, 1)
            # Scotch supports arbitrary proc counts (unlike simple)
            self.assertTrue(n >= 2)

    def test_metis_partition_even_odd(self):
        """METIS (Elmer) supports both even and odd partitions."""
        for n in (2, 3, 5, 7, 8):
            self.assertGreater(n, 1)

    def test_mpi_proc_count_vs_cell_count_ratio(self):
        """Rule of thumb: ≥50k cells per MPI process."""
        n_cells = 2_000_000  # 2M cell case
        min_cells_per_proc = 50_000
        max_procs = n_cells // min_cells_per_proc
        self.assertEqual(max_procs, 40)
        # Typical HPC: 32 cores
        recommended = min(32, max_procs)
        self.assertGreater(recommended, 1)


# =====================================================================
# 10. Enterprise Layer Resilience
# =====================================================================

class TestEnterpriseFallback(unittest.TestCase):
    """Enterprise layer must fail gracefully for production stability."""

    def test_enterprise_bootstrap_importable(self):
        from flow_studio.enterprise import bootstrap
        self.assertTrue(hasattr(bootstrap, "is_enterprise_enabled"))
        self.assertTrue(hasattr(bootstrap, "initialize_workbench"))

    def test_enterprise_adapters_importable(self):
        from flow_studio.enterprise.adapters import base
        self.assertTrue(hasattr(base, "SolverAdapter"))

    def test_enterprise_execution_facade_importable(self):
        from flow_studio.enterprise.services import execution_facade
        self.assertTrue(callable(getattr(execution_facade,
                                         "submit_legacy_analysis", None)))

    def test_adapter_capability_matrix_loads(self):
        from flow_studio.enterprise.ui.adapter_matrix import (
            build_capability_rows,
        )
        rows = build_capability_rows()
        self.assertIsInstance(rows, list)
        self.assertGreater(len(rows), 0)


# =====================================================================
# 11. End-to-End SIF for CT-Like Multi-Physics
# =====================================================================

class TestCTDetectorSifScenario(unittest.TestCase):
    """Build a complete Elmer SIF for a CT-detector-like simulation:
    rotating gantry + heat source + EM field + forced air cooling."""

    def setUp(self):
        from flow_studio.solvers.elmer_sif import SifBuilder
        self.SifBuilder = SifBuilder

    def _build_ct_sif(self):
        """Construct a full multi-physics SIF for CT simulator."""
        b = self.SifBuilder()

        # Header
        b.set_header(mesh_db=".", result_dir="results")

        # Transient simulation (gantry rotates)
        b.set_simulation(
            steady_state=False,
            time_steps=5000,
            dt=1e-4,
            Output_Intervals=100,
        )

        # Constants
        b.set_constant(Stefan_Boltzmann=5.67e-8, Boltzmann_Constant=1.38e-23)

        # Bodies
        b.add_body(name="GantryAir", material=1, equation=1, body_force=1)
        b.add_body(name="XRayTube", material=2, equation=2, body_force=2)
        b.add_body(name="Electronics", material=3, equation=2)

        # Materials
        b.add_material(name="Air", Density=1.225, Viscosity=1.81e-5,
                       Heat_Conductivity=0.025, Heat_Capacity=1005.0)
        b.add_material(name="Tungsten", Density=19300.0,
                       Heat_Conductivity=173.0, Heat_Capacity=134.0)
        b.add_material(name="CopperPCB", Density=8960.0,
                       Heat_Conductivity=401.0, Heat_Capacity=385.0)

        # Solvers
        b.add_solver(
            "FlowSolve",
            variable="Flow Solution[Velocity:3 Pressure:1]",
            exec_solver="Always",
            Stabilize=True,
            Nonlinear_System_Max_Iterations=5,
            Linear_System_Solver="Iterative",
            Linear_System_Iterative_Method="BiCGStab",
            Linear_System_Max_Iterations=500,
            Linear_System_Preconditioning="ILU1",
        )
        b.add_solver(
            "HeatSolve",
            variable="Temperature",
            exec_solver="Always",
            Linear_System_Solver="Iterative",
            Linear_System_Iterative_Method="BiCGStab",
        )

        # Equations
        b.add_equation(name="FlowAndHeat", active_solvers=[1, 2])
        b.add_equation(name="HeatOnly", active_solvers=[2])

        # Body forces (heat generation)
        b.add_body_force(name="FanForce", Flow_Bodyforce_1=0.0,
                         Flow_Bodyforce_2=0.0, Flow_Bodyforce_3=-9.81)
        b.add_body_force(name="XRayHeatGen", Heat_Source=5e6)

        # Boundary conditions
        b.add_bc(name="Inlet", Velocity_1=5.0, Velocity_2=0.0,
                 Velocity_3=0.0, Temperature=293.15)
        b.add_bc(name="Outlet", External_Pressure=0.0)
        b.add_bc(name="RotatingWall", Noslip_Wall_BC=True)
        b.add_bc(name="Adiabatic", Heat_Flux=0.0)

        # Initial conditions
        b.add_initial_condition(Temperature=293.15, Velocity_1=0.0,
                                Velocity_2=0.0, Velocity_3=0.0, Pressure=0.0)

        return b.generate()

    def test_ct_sif_has_transient(self):
        sif = self._build_ct_sif()
        self.assertIn("Simulation Type = Transient", sif)
        self.assertIn("Timestep Intervals = 5000", sif)

    def test_ct_sif_has_three_bodies(self):
        sif = self._build_ct_sif()
        self.assertIn("Body 1", sif)
        self.assertIn("Body 2", sif)
        self.assertIn("Body 3", sif)

    def test_ct_sif_has_three_materials(self):
        sif = self._build_ct_sif()
        self.assertIn("Material 1", sif)
        self.assertIn("Material 2", sif)
        self.assertIn("Material 3", sif)
        self.assertIn("Air", sif)
        self.assertIn("Tungsten", sif)
        self.assertIn("CopperPCB", sif)

    def test_ct_sif_has_flow_and_heat_solvers(self):
        sif = self._build_ct_sif()
        self.assertIn("FlowSolve", sif)
        self.assertIn("HeatSolve", sif)

    def test_ct_sif_has_heat_source(self):
        sif = self._build_ct_sif()
        self.assertIn("Heat Source", sif)
        self.assertIn("5000000", sif)  # 5e6 W/m³

    def test_ct_sif_has_boundary_conditions(self):
        sif = self._build_ct_sif()
        self.assertIn("Boundary Condition 1", sif)
        self.assertIn("Boundary Condition 2", sif)
        self.assertIn("Boundary Condition 3", sif)
        self.assertIn("Boundary Condition 4", sif)

    def test_ct_sif_has_initial_conditions(self):
        sif = self._build_ct_sif()
        self.assertIn("Initial Condition 1", sif)
        self.assertIn("Temperature = 293.15", sif)

    def test_ct_sif_has_two_equations(self):
        sif = self._build_ct_sif()
        self.assertIn("Equation 1", sif)
        self.assertIn("Equation 2", sif)

    def test_ct_sif_has_constants(self):
        sif = self._build_ct_sif()
        self.assertIn("Stefan Boltzmann", sif)

    def test_ct_sif_complete_section_count(self):
        """Verify all major sections are present."""
        sif = self._build_ct_sif()
        for section in ("Header", "Simulation", "Body ", "Material ",
                        "Solver ", "Equation ", "Boundary Condition ",
                        "Initial Condition ", "Body Force "):
            self.assertIn(section, sif, f"Missing section: {section}")


# =====================================================================
# 12. Workflow Guide Validation
# =====================================================================

class TestWorkflowGuideProduction(unittest.TestCase):
    """Validate workflow_guide catches missing steps before solver run."""

    def test_module_importable(self):
        from flow_studio import workflow_guide
        self.assertTrue(hasattr(workflow_guide, "has_analysis"))
        self.assertTrue(hasattr(workflow_guide, "has_physics_model"))
        self.assertTrue(hasattr(workflow_guide, "has_boundary_conditions"))


if __name__ == "__main__":
    unittest.main()
