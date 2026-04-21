# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Elmer FEM solver runner – multi-physics SIF generation and execution.

Supports all FlowStudio physics domains:
  - CFD (FlowSolve)
  - Structural Mechanics (ElasticSolve / StressSolve)
  - Electrostatics (StatElecSolve)
  - Magnetostatics / Magnetodynamics (WhitneyAV / MagnetoDynamics)
  - Thermal (HeatSolve)

The runner:
  1. Converts GMSH mesh to Elmer format via ElmerGrid
  2. Generates the SIF (Solver Input File) from the analysis tree
  3. Writes the ELMERSOLVER_STARTINFO file
  4. Launches ElmerSolver
  5. Reads VTU results back into FreeCAD
"""

import os
import shutil
import subprocess

import FreeCAD

from flow_studio.solvers.base_solver import BaseSolverRunner
from flow_studio.solvers.elmer_sif import SifBuilder, SifProcedure


class ElmerRunner(BaseSolverRunner):
    """Elmer FEM multi-physics solver backend."""

    name = "Elmer"

    # ------------------------------------------------------------------
    # Helpers to find analysis children by FlowType
    # ------------------------------------------------------------------

    def _children_of_type(self, prefix):
        """Return all children whose FlowType starts with *prefix*."""
        result = []
        for obj in self.analysis.Group:
            ft = getattr(obj, "FlowType", "")
            if ft.startswith(prefix):
                result.append(obj)
        return result

    def _child_of_type(self, flow_type):
        """Return the first child with exact FlowType, or None."""
        for obj in self.analysis.Group:
            if getattr(obj, "FlowType", "") == flow_type:
                return obj
        return None

    def _get_domain(self):
        """Return the PhysicsDomain key from the analysis."""
        return getattr(self.analysis, "PhysicsDomain", "CFD")

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def check(self):
        """Verify that ElmerSolver and ElmerGrid are available."""
        errors = []
        for exe in ("ElmerSolver", "ElmerGrid"):
            if shutil.which(exe) is None:
                errors.append(
                    f"{exe} not found in PATH. "
                    f"Install Elmer FEM (https://www.elmerfem.org)."
                )
        return errors

    def write_case(self):
        """Generate the complete Elmer case (mesh + SIF)."""
        FreeCAD.Console.PrintMessage(
            "FlowStudio [Elmer]: Writing case files...\n"
        )
        self._convert_mesh()
        sif_content = self._generate_sif()
        sif_path = os.path.join(self.case_dir, "case.sif")
        with open(sif_path, "w", encoding="utf-8") as f:
            f.write(sif_content)
        FreeCAD.Console.PrintMessage(
            f"FlowStudio [Elmer]: SIF written to {sif_path}\n"
        )
        # Write ELMERSOLVER_STARTINFO
        start_info = os.path.join(self.case_dir, "ELMERSOLVER_STARTINFO")
        with open(start_info, "w", encoding="utf-8") as f:
            f.write("case.sif\n1\n")

    def _get_num_processors(self):
        """Return the number of MPI processes to use."""
        solver = self._child_of_type("FlowStudio::Solver")
        if solver:
            return max(1, getattr(solver, "NumProcessors", 1))
        return 1

    def _get_solver_binary(self):
        """Return the preferred Elmer solver executable name."""
        solver = self._child_of_type("FlowStudio::Solver")
        if solver is not None:
            preferred = getattr(solver, "ElmerSolverBinary", "ElmerSolver")
            if preferred in ("ElmerSolver", "ElmerSolver_mpi"):
                return preferred
        return "ElmerSolver"

    def _partition_mesh(self, num_procs):
        """Partition mesh for parallel run using ElmerGrid."""
        mesh_dir = os.path.join(self.case_dir, "mesh")
        if not os.path.isdir(mesh_dir):
            FreeCAD.Console.PrintWarning(
                "FlowStudio [Elmer]: No mesh directory for partitioning.\n"
            )
            return False

        elmer_grid = shutil.which("ElmerGrid")
        if elmer_grid is None:
            FreeCAD.Console.PrintError(
                "FlowStudio [Elmer]: ElmerGrid not found for partitioning.\n"
            )
            return False

        # ElmerGrid: partition Elmer mesh (format 2) to N parts
        # 2 2 = Elmer → Elmer, with -metis N for partitioning
        cmd = [
            elmer_grid, "2", "2", mesh_dir,
            "-metis", str(num_procs),
            "-out", os.path.join(self.case_dir, "partitioning." + str(num_procs)),
        ]
        FreeCAD.Console.PrintMessage(
            f"FlowStudio [Elmer]: Partitioning mesh for {num_procs} processes: "
            f"{' '.join(cmd)}\n"
        )
        result = subprocess.run(
            cmd, cwd=self.case_dir,
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            FreeCAD.Console.PrintError(
                f"FlowStudio [Elmer]: Mesh partitioning failed:\n{result.stderr}\n"
            )
            return False

        FreeCAD.Console.PrintMessage(
            f"FlowStudio [Elmer]: Mesh partitioned into {num_procs} parts.\n"
        )
        return True

    def run(self):
        """Launch ElmerSolver (serial or parallel via MPI)."""
        num_procs = self._get_num_processors()
        preferred_solver = self._get_solver_binary()
        is_parallel = num_procs > 1 and preferred_solver == "ElmerSolver_mpi"

        if is_parallel:
            FreeCAD.Console.PrintMessage(
                f"FlowStudio [Elmer]: Launching parallel ElmerSolver "
                f"with {num_procs} MPI processes...\n"
            )
            # Partition mesh for parallel execution
            self._partition_mesh(num_procs)
        else:
            if preferred_solver == "ElmerSolver_mpi" and num_procs <= 1:
                FreeCAD.Console.PrintWarning(
                    "FlowStudio [Elmer]: ElmerSolver_mpi requested with one processor; "
                    "using ElmerSolver instead.\n"
                )
            FreeCAD.Console.PrintMessage(
                "FlowStudio [Elmer]: Launching ElmerSolver...\n"
            )

        if is_parallel:
            exe = shutil.which(preferred_solver)
            if exe is None:
                FreeCAD.Console.PrintWarning(
                    "FlowStudio [Elmer]: ElmerSolver_mpi not found, "
                    "falling back to serial ElmerSolver.\n"
                )
                exe = shutil.which("ElmerSolver")
                is_parallel = False
        else:
            exe = shutil.which("ElmerSolver")

        if exe is None:
            FreeCAD.Console.PrintError(
                "FlowStudio [Elmer]: ElmerSolver not found.\n"
            )
            return

        if is_parallel:
            # Find mpirun/mpiexec
            mpi_exe = shutil.which("mpirun") or shutil.which("mpiexec")
            if mpi_exe is None:
                FreeCAD.Console.PrintWarning(
                    "FlowStudio [Elmer]: mpirun/mpiexec not found, "
                    "falling back to serial.\n"
                )
                cmd = [exe]
            else:
                cmd = [mpi_exe, "-np", str(num_procs), exe]
        else:
            cmd = [exe]

        FreeCAD.Console.PrintMessage(
            f"FlowStudio [Elmer]: Command: {' '.join(cmd)}\n"
        )

        self.process = subprocess.Popen(
            cmd,
            cwd=self.case_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        # Stream output
        for line in self.process.stdout:
            decoded = line.decode("utf-8", errors="replace").rstrip()
            FreeCAD.Console.PrintMessage(f"  [Elmer] {decoded}\n")
        self.process.wait()
        rc = self.process.returncode
        if rc == 0:
            FreeCAD.Console.PrintMessage(
                "FlowStudio [Elmer]: Solver finished successfully.\n"
            )
        else:
            FreeCAD.Console.PrintError(
                f"FlowStudio [Elmer]: Solver exited with code {rc}.\n"
            )

    def read_results(self):
        """Read Elmer VTU results."""
        vtu_files = [
            f for f in os.listdir(self.case_dir) if f.endswith(".vtu")
        ]
        if vtu_files:
            FreeCAD.Console.PrintMessage(
                f"FlowStudio [Elmer]: Found {len(vtu_files)} VTU result file(s).\n"
            )
        else:
            FreeCAD.Console.PrintWarning(
                "FlowStudio [Elmer]: No VTU result files found.\n"
            )
        return vtu_files

    # ------------------------------------------------------------------
    # Mesh conversion
    # ------------------------------------------------------------------

    def _convert_mesh(self):
        """Convert GMSH mesh to Elmer format using ElmerGrid."""
        mesh_obj = self._child_of_type("FlowStudio::MeshGmsh")
        if mesh_obj is None:
            FreeCAD.Console.PrintWarning(
                "FlowStudio [Elmer]: No mesh object found, skipping mesh conversion.\n"
            )
            return

        mesh_path = getattr(mesh_obj, "MeshPath", "")
        if not mesh_path or not os.path.exists(mesh_path):
            FreeCAD.Console.PrintWarning(
                f"FlowStudio [Elmer]: Mesh file not found: {mesh_path}\n"
            )
            return

        elmer_grid = shutil.which("ElmerGrid")
        if elmer_grid is None:
            FreeCAD.Console.PrintError(
                "FlowStudio [Elmer]: ElmerGrid not found.\n"
            )
            return

        mesh_dir = os.path.join(self.case_dir, "mesh")
        # ElmerGrid: convert GMSH (format 14) to Elmer (format 2)
        cmd = [elmer_grid, "14", "2", mesh_path, "-out", mesh_dir]
        FreeCAD.Console.PrintMessage(
            f"FlowStudio [Elmer]: Converting mesh: {' '.join(cmd)}\n"
        )
        result = subprocess.run(
            cmd, cwd=self.case_dir,
            capture_output=True, text=True
        )
        if result.returncode != 0:
            FreeCAD.Console.PrintError(
                f"FlowStudio [Elmer]: ElmerGrid failed:\n{result.stderr}\n"
            )
        else:
            FreeCAD.Console.PrintMessage(
                "FlowStudio [Elmer]: Mesh conversion complete.\n"
            )

    # ------------------------------------------------------------------
    # SIF generation
    # ------------------------------------------------------------------

    def _generate_sif(self):
        """Generate the Elmer SIF file from the analysis object tree."""
        domain = self._get_domain()
        builder = SifBuilder()

        # Header
        builder.set_header(mesh_db=".", mesh_dir="mesh")

        # Simulation
        sim_type = self._get_simulation_type()
        coord_system = "Cartesian 3D"
        builder.set_simulation(
            coord_system=coord_system,
            sim_type=sim_type,
            steady_max_iter=self._get_max_iterations(),
            output_level=5,
        )
        # Add coordinate scaling (mm → m for FreeCAD)
        builder.simulation["Coordinate Scaling"] = 0.001

        # Transient settings
        if sim_type == "Transient":
            self._add_transient_settings(builder)

        # Constants
        self._add_constants(builder, domain)

        # Dispatch to domain-specific SIF generation
        handler = _DOMAIN_HANDLERS.get(domain, _generate_sif_cfd)
        handler(self, builder)

        # Add result output solver
        self._add_result_output_solver(builder)

        return builder.generate()

    def _get_simulation_type(self):
        """Determine simulation type from physics model or solver object."""
        physics = self._child_of_type("FlowStudio::PhysicsModel")
        if physics:
            time_model = getattr(physics, "TimeModel", "Steady")
            if time_model == "Transient":
                return "Transient"
        # Check other physics models
        for suffix in ("Structural", "Electrostatic", "Electromagnetic", "Thermal"):
            pm = self._child_of_type(f"FlowStudio::{suffix}PhysicsModel")
            if pm:
                time_model = getattr(pm, "TimeModel", "Steady")
                if time_model == "Transient":
                    return "Transient"
        return "Steady State"

    def _get_max_iterations(self):
        """Get max iterations from solver object."""
        solver = self._child_of_type("FlowStudio::Solver")
        if solver:
            return getattr(solver, "MaxIterations", 1)
        return 1

    def _add_transient_settings(self, builder):
        """Add transient time stepping to simulation block."""
        solver = self._child_of_type("FlowStudio::Solver")
        if solver:
            dt = getattr(solver, "TimeStep", 0.001)
            end_time = getattr(solver, "EndTime", 1.0)
            if dt > 0:
                n_steps = max(1, int(end_time / dt))
                builder.simulation["Timestep Intervals"] = n_steps
                builder.simulation["Timestep Sizes"] = dt
                builder.simulation["Output Intervals"] = max(
                    1, getattr(solver, "WriteInterval", 1)
                )

    def _add_constants(self, builder, domain):
        """Add physics constants based on domain."""
        builder.set_constant("Stefan Boltzmann", 5.67e-8)
        if domain in ("Electrostatic", "Electromagnetic"):
            builder.set_constant("Permittivity Of Vacuum", 8.8542e-12)
        if domain == "Electromagnetic":
            builder.set_constant("Permeability Of Vacuum", 1.2566e-6)
        builder.set_constant("Gravity(4)", "0 -1 0 9.82")

    def _add_result_output_solver(self, builder):
        """Add VTU result output solver."""
        solver = builder.add_solver(
            "Result Output",
            SifProcedure("ResultOutputSolve", "ResultOutputSolver"),
        )
        solver["Exec Solver"] = '"after all"'
        solver["Output File Name"] = '"case"'
        solver["Vtu Format"] = True
        # Don't count in Variable DOFs
        if "Variable DOFs" in solver.data:
            del solver.data["Variable DOFs"]
        if "Variable" in solver.data:
            del solver.data["Variable"]

    # ------------------------------------------------------------------
    # Linear system defaults
    # ------------------------------------------------------------------

    @staticmethod
    def _add_linear_system_defaults(solver_sec, method="Iterative",
                                     iter_method="BiCGStab",
                                     preconditioning="ILU1",
                                     max_iter=500, tol=1e-8):
        """Add common linear system settings to a solver section."""
        solver_sec["Linear System Solver"] = f'"{method}"'
        if method == "Iterative":
            solver_sec["Linear System Iterative Method"] = f'"{iter_method}"'
            solver_sec["Linear System Max Iterations"] = max_iter
            solver_sec["Linear System Convergence Tolerance"] = tol
            solver_sec["Linear System Preconditioning"] = f'"{preconditioning}"'
            solver_sec["Linear System Residual Output"] = 10
        elif method == "Direct":
            solver_sec["Linear System Direct Method"] = '"umfpack"'

    @staticmethod
    def _add_nonlinear_defaults(solver_sec, max_iter=1, tol=1e-5):
        """Add nonlinear iteration settings."""
        solver_sec["Nonlinear System Max Iterations"] = max_iter
        solver_sec["Nonlinear System Convergence Tolerance"] = tol

    @staticmethod
    def _add_steady_state_defaults(solver_sec, tol=1e-5):
        solver_sec["Steady State Convergence Tolerance"] = tol


# ======================================================================
# Domain-specific SIF handlers
# ======================================================================

def _generate_sif_cfd(runner, builder):
    """Generate SIF sections for CFD (Navier-Stokes) domain."""
    # Material
    mat_obj = runner._child_of_type("FlowStudio::FluidMaterial")
    mat = builder.add_material("Fluid")
    if mat_obj:
        mat["Density"] = getattr(mat_obj, "Density", 1.225)
        mat["Viscosity"] = getattr(mat_obj, "DynamicViscosity", 1.81e-5)
        if getattr(mat_obj, "ThermalConductivity", 0) > 0:
            mat["Heat Conductivity"] = mat_obj.ThermalConductivity
            mat["Heat Capacity"] = getattr(mat_obj, "SpecificHeat", 1005.0)
    else:
        mat["Density"] = 1.225
        mat["Viscosity"] = 1.81e-5

    # Flow solver
    flow_solver = builder.add_solver(
        "Navier-Stokes",
        SifProcedure("FlowSolve", "FlowSolver"),
        variable="Flow Solution",
        variable_dofs=1,  # Elmer auto-determines DOFs for Navier-Stokes
    )
    flow_solver["Exec Solver"] = '"Always"'
    flow_solver["Stabilize"] = True
    flow_solver["Optimize Bandwidth"] = True
    ElmerRunner._add_linear_system_defaults(flow_solver)
    ElmerRunner._add_nonlinear_defaults(flow_solver, max_iter=20, tol=1e-5)
    ElmerRunner._add_steady_state_defaults(flow_solver)

    # Equation
    solver_ids = [1]  # Flow solver

    # Check for heat transfer
    physics = runner._child_of_type("FlowStudio::PhysicsModel")
    has_heat = physics and getattr(physics, "HeatTransfer", False)
    if has_heat:
        heat_solver = builder.add_solver(
            "Heat Equation",
            SifProcedure("HeatSolve", "HeatSolver"),
            variable="Temperature",
            variable_dofs=1,
        )
        heat_solver["Exec Solver"] = '"Always"'
        heat_solver["Stabilize"] = True
        ElmerRunner._add_linear_system_defaults(heat_solver)
        ElmerRunner._add_nonlinear_defaults(heat_solver, max_iter=1, tol=1e-5)
        ElmerRunner._add_steady_state_defaults(heat_solver)
        solver_ids.append(2)

    eq = builder.add_equation("CFD", solver_ids)
    if has_heat:
        eq["Convection"] = '"Computed"'

    # Body
    builder.add_body("Fluid Domain", equation=1, material=1,
                     initial_condition=1)

    # Initial conditions
    ic_obj = runner._child_of_type("FlowStudio::InitialConditions")
    ic = builder.add_initial_condition("Initial Fields")
    if ic_obj:
        vx = getattr(ic_obj, "VelocityX", 0.0)
        vy = getattr(ic_obj, "VelocityY", 0.0)
        vz = getattr(ic_obj, "VelocityZ", 0.0)
        ic["Velocity 1"] = vx
        ic["Velocity 2"] = vy
        ic["Velocity 3"] = vz
        ic["Pressure"] = getattr(ic_obj, "Pressure", 0.0)
        if has_heat:
            ic["Temperature"] = getattr(ic_obj, "Temperature", 293.15)
    else:
        ic["Velocity 1"] = 0.0
        ic["Velocity 2"] = 0.0
        ic["Velocity 3"] = 0.0
        ic["Pressure"] = 0.0

    # Boundary conditions
    _add_cfd_boundary_conditions(runner, builder, has_heat)


def _add_cfd_boundary_conditions(runner, builder, has_heat):
    """Add CFD boundary conditions from analysis objects."""
    bc_idx = 0

    for obj in runner._children_of_type("FlowStudio::BC"):
        ft = getattr(obj, "FlowType", "")
        bc_idx += 1

        if ft == "FlowStudio::BCWall":
            bc = builder.add_boundary_condition(obj.Label)
            bc[f"Target Boundaries(1)"] = bc_idx
            wall_type = getattr(obj, "WallType", "No-Slip")
            if wall_type == "No-Slip":
                bc["Velocity 1"] = 0.0
                bc["Velocity 2"] = 0.0
                bc["Velocity 3"] = 0.0
            elif wall_type == "Slip":
                bc["Normal-Tangential Velocity"] = True
                bc["Velocity 1"] = 0.0  # normal component = 0
            if has_heat:
                thermal = getattr(obj, "ThermalBC", "Adiabatic")
                if thermal == "Fixed Temperature":
                    bc["Temperature"] = getattr(obj, "WallTemperature", 293.15)
                elif thermal == "Heat Flux":
                    bc["Heat Flux BC"] = True
                    bc["Heat Flux"] = getattr(obj, "HeatFlux", 0.0)

        elif ft == "FlowStudio::BCInlet":
            bc = builder.add_boundary_condition(obj.Label)
            bc[f"Target Boundaries(1)"] = bc_idx
            inlet_type = getattr(obj, "InletType", "Velocity")
            if inlet_type == "Velocity":
                bc["Velocity 1"] = getattr(obj, "VelocityX", 0.0)
                bc["Velocity 2"] = getattr(obj, "VelocityY", 0.0)
                bc["Velocity 3"] = getattr(obj, "VelocityZ", 1.0)
            if has_heat:
                bc["Temperature"] = getattr(obj, "InletTemperature", 293.15)

        elif ft == "FlowStudio::BCOutlet":
            bc = builder.add_boundary_condition(obj.Label)
            bc[f"Target Boundaries(1)"] = bc_idx
            bc["Pressure"] = getattr(obj, "Pressure", 0.0)

        elif ft == "FlowStudio::BCSymmetry":
            bc = builder.add_boundary_condition(obj.Label)
            bc[f"Target Boundaries(1)"] = bc_idx
            bc["Normal-Tangential Velocity"] = True
            bc["Velocity 1"] = 0.0

        elif ft == "FlowStudio::BCOpenBoundary":
            bc = builder.add_boundary_condition(obj.Label)
            bc[f"Target Boundaries(1)"] = bc_idx
            bc["External Pressure"] = getattr(obj, "Pressure", 101325.0)


def _generate_sif_structural(runner, builder):
    """Generate SIF sections for Structural Mechanics domain."""
    # Material
    mat_obj = runner._child_of_type("FlowStudio::SolidMaterial")
    mat = builder.add_material("Solid")
    if mat_obj:
        mat["Density"] = getattr(mat_obj, "Density", 7850.0)
        mat["Youngs Modulus"] = getattr(mat_obj, "YoungsModulus", 2.1e11)
        mat["Poisson Ratio"] = getattr(mat_obj, "PoissonRatio", 0.3)
    else:
        mat["Density"] = 7850.0
        mat["Youngs Modulus"] = 2.1e11
        mat["Poisson Ratio"] = 0.3

    # Elasticity solver
    solver = builder.add_solver(
        "Linear Elasticity",
        SifProcedure("StressSolve", "StressSolver"),
        variable="Displacement",
        variable_dofs=3,
    )
    solver["Exec Solver"] = '"Always"'
    solver["Calculate Stresses"] = True
    solver["Calculate Strains"] = True
    ElmerRunner._add_linear_system_defaults(solver, method="Direct")
    ElmerRunner._add_nonlinear_defaults(solver, max_iter=1, tol=1e-6)
    ElmerRunner._add_steady_state_defaults(solver)

    # Equation
    builder.add_equation("Structural", [1])

    # Body
    builder.add_body("Solid Body", equation=1, material=1, initial_condition=1)

    # Initial condition
    ic = builder.add_initial_condition("Zero Displacement")
    ic["Displacement 1"] = 0.0
    ic["Displacement 2"] = 0.0
    ic["Displacement 3"] = 0.0

    # Boundary conditions from analysis
    bc_idx = 0
    for obj in runner._children_of_type("FlowStudio::BC"):
        ft = getattr(obj, "FlowType", "")
        bc_idx += 1

        if ft == "FlowStudio::BCFixedDisplacement":
            bc = builder.add_boundary_condition(obj.Label)
            bc[f"Target Boundaries(1)"] = bc_idx
            bc["Displacement 1"] = 0.0
            bc["Displacement 2"] = 0.0
            bc["Displacement 3"] = 0.0

        elif ft == "FlowStudio::BCForce":
            bc = builder.add_boundary_condition(obj.Label)
            bc[f"Target Boundaries(1)"] = bc_idx
            bc["Force 1"] = getattr(obj, "ForceX", 0.0)
            bc["Force 2"] = getattr(obj, "ForceY", 0.0)
            bc["Force 3"] = getattr(obj, "ForceZ", 0.0)

        elif ft == "FlowStudio::BCPressureLoad":
            bc = builder.add_boundary_condition(obj.Label)
            bc[f"Target Boundaries(1)"] = bc_idx
            bc["Normal Force"] = getattr(obj, "Pressure", 0.0)


def _generate_sif_electrostatic(runner, builder):
    """Generate SIF sections for Electrostatic domain."""
    # Material
    mat_obj = runner._child_of_type("FlowStudio::ElectrostaticMaterial")
    mat = builder.add_material("Dielectric")
    if mat_obj:
        mat["Relative Permittivity"] = getattr(
            mat_obj, "RelativePermittivity", 1.0
        )
    else:
        mat["Relative Permittivity"] = 1.0

    # StatElecSolver
    solver = builder.add_solver(
        "Stat Elec Solver",
        SifProcedure("StatElecSolve", "StatElecSolver"),
        variable="Potential",
        variable_dofs=1,
    )
    solver["Exec Solver"] = '"Always"'
    solver["Calculate Electric Energy"] = True
    solver["Calculate Electric Field"] = True
    solver["Calculate Electric Flux"] = True
    ElmerRunner._add_linear_system_defaults(solver)
    ElmerRunner._add_nonlinear_defaults(solver, max_iter=1, tol=1e-5)
    ElmerRunner._add_steady_state_defaults(solver)

    # Electric force solver
    force_solver = builder.add_solver(
        "Electric Force",
        SifProcedure("ElectricForce", "StatElecForce"),
    )
    force_solver["Exec Solver"] = '"Always"'
    # Clean up defaults not needed
    if "Variable DOFs" in force_solver.data:
        del force_solver.data["Variable DOFs"]
    if "Variable" in force_solver.data:
        del force_solver.data["Variable"]

    # Equation
    eq = builder.add_equation("Electrostatic", [1, 2])
    eq["Calculate Electric Energy"] = True

    # Body
    builder.add_body("Domain", equation=1, material=1)

    # Boundary conditions
    bc_idx = 0
    for obj in runner._children_of_type("FlowStudio::BC"):
        ft = getattr(obj, "FlowType", "")
        bc_idx += 1

        if ft == "FlowStudio::BCElectricPotential":
            bc = builder.add_boundary_condition(obj.Label)
            bc[f"Target Boundaries(1)"] = bc_idx
            bc["Potential"] = getattr(obj, "Potential", 0.0)
            if getattr(obj, "CalculateForce", False):
                bc["Calculate Electric Force"] = True

        elif ft == "FlowStudio::BCSurfaceCharge":
            bc = builder.add_boundary_condition(obj.Label)
            bc[f"Target Boundaries(1)"] = bc_idx
            bc["Surface Charge Density"] = getattr(
                obj, "SurfaceChargeDensity", 0.0
            )


def _generate_sif_electromagnetic(runner, builder):
    """Generate SIF sections for Electromagnetic domain."""
    # Material
    mat_obj = runner._child_of_type("FlowStudio::ElectromagneticMaterial")
    mat = builder.add_material("Conductor")
    if mat_obj:
        mat["Relative Permeability"] = getattr(
            mat_obj, "RelativePermeability", 1.0
        )
        mat["Relative Permittivity"] = getattr(
            mat_obj, "RelativePermittivity", 1.0
        )
        mat["Electric Conductivity"] = getattr(
            mat_obj, "ElectricConductivity", 0.0
        )
    else:
        mat["Relative Permeability"] = 1.0
        mat["Relative Permittivity"] = 1.0
        mat["Electric Conductivity"] = 0.0

    # Check analysis type for harmonic vs transient
    analysis_type = getattr(runner.analysis, "AnalysisType", "Magnetostatic")

    if "Harmonic" in analysis_type:
        # Harmonic magnetodynamic solver (WhitneyAV Harmonic)
        solver = builder.add_solver(
            "MGDynamics",
            SifProcedure("MagnetoDynamics", "WhitneyAVHarmonicSolver"),
            variable='AV[AV re:1 AV im:1]',
            variable_dofs=1,
        )
        solver["Exec Solver"] = '"Always"'
        solver["Linear System Symmetric"] = True
        ElmerRunner._add_linear_system_defaults(
            solver, iter_method="BiCGStabl", max_iter=1000
        )
        # Add angular frequency
        em_physics = runner._child_of_type(
            "FlowStudio::ElectromagneticPhysicsModel"
        )
        if em_physics:
            freq = getattr(em_physics, "Frequency", 50.0)
            import math
            builder.simulation["Angular Frequency"] = 2.0 * math.pi * freq
    else:
        # Static or transient magnetodynamic (WhitneyAV)
        solver = builder.add_solver(
            "MGDynamics",
            SifProcedure("MagnetoDynamics", "WhitneyAVSolver"),
            variable="AV",
            variable_dofs=1,
        )
        solver["Exec Solver"] = '"Always"'
        ElmerRunner._add_linear_system_defaults(solver, max_iter=1000)

    ElmerRunner._add_nonlinear_defaults(solver, max_iter=10, tol=1e-6)
    ElmerRunner._add_steady_state_defaults(solver)

    # Post-processing: MagnetoDynamicsCalcFields
    calc_solver = builder.add_solver(
        "MGDynamicsCalc",
        SifProcedure("MagnetoDynamics", "MagnetoDynamicsCalcFields"),
    )
    calc_solver["Exec Solver"] = '"Always"'
    calc_solver["Potential Variable"] = '"AV"'
    calc_solver["Calculate Current Density"] = True
    calc_solver["Calculate Electric Field"] = True
    calc_solver["Calculate Magnetic Field Strength"] = True
    calc_solver["Calculate Joule Heating"] = True
    ElmerRunner._add_linear_system_defaults(
        calc_solver, iter_method="CG", max_iter=5000
    )
    # Clean unnecessary defaults
    if "Variable DOFs" in calc_solver.data:
        del calc_solver.data["Variable DOFs"]
    if "Variable" in calc_solver.data:
        del calc_solver.data["Variable"]

    # Equation
    builder.add_equation("Electromagnetic", [1, 2])

    # Body
    builder.add_body("Domain", equation=1, material=1)

    # Boundary conditions
    bc_idx = 0
    for obj in runner._children_of_type("FlowStudio::BC"):
        ft = getattr(obj, "FlowType", "")
        bc_idx += 1

        if ft == "FlowStudio::BCMagneticPotential":
            bc = builder.add_boundary_condition(obj.Label)
            bc[f"Target Boundaries(1)"] = bc_idx
            bc["AV {e} 1"] = 0.0
            bc["AV {e} 2"] = 0.0
            potential = getattr(obj, "MagneticVectorPotential", 0.0)
            bc["AV"] = potential

        elif ft == "FlowStudio::BCCurrentDensity":
            bc = builder.add_boundary_condition(obj.Label)
            bc[f"Target Boundaries(1)"] = bc_idx
            bc["Current Density 1"] = getattr(obj, "CurrentDensityX", 0.0)
            bc["Current Density 2"] = getattr(obj, "CurrentDensityY", 0.0)
            bc["Current Density 3"] = getattr(obj, "CurrentDensityZ", 0.0)


def _generate_sif_thermal(runner, builder):
    """Generate SIF sections for Thermal (heat transfer) domain."""
    # Material
    mat_obj = runner._child_of_type("FlowStudio::ThermalMaterial")
    mat = builder.add_material("Solid")
    if mat_obj:
        mat["Density"] = getattr(mat_obj, "Density", 7850.0)
        mat["Heat Conductivity"] = getattr(
            mat_obj, "ThermalConductivity", 50.0
        )
        mat["Heat Capacity"] = getattr(mat_obj, "SpecificHeat", 500.0)
    else:
        mat["Density"] = 7850.0
        mat["Heat Conductivity"] = 50.0
        mat["Heat Capacity"] = 500.0

    # Heat solver
    solver = builder.add_solver(
        "Heat Equation",
        SifProcedure("HeatSolve", "HeatSolver"),
        variable="Temperature",
        variable_dofs=1,
    )
    solver["Exec Solver"] = '"Always"'
    solver["Stabilize"] = True
    ElmerRunner._add_linear_system_defaults(solver)
    ElmerRunner._add_nonlinear_defaults(solver, max_iter=1, tol=1e-5)
    ElmerRunner._add_steady_state_defaults(solver)

    # Equation
    builder.add_equation("Heat Transfer", [1])

    # Body
    builder.add_body("Solid Body", equation=1, material=1,
                     initial_condition=1)

    # Initial condition
    ic = builder.add_initial_condition("Initial Temperature")
    ic["Temperature"] = 293.15

    # Boundary conditions
    bc_idx = 0
    for obj in runner._children_of_type("FlowStudio::BC"):
        ft = getattr(obj, "FlowType", "")
        bc_idx += 1

        if ft == "FlowStudio::BCTemperature":
            bc = builder.add_boundary_condition(obj.Label)
            bc[f"Target Boundaries(1)"] = bc_idx
            bc["Temperature"] = getattr(obj, "Temperature", 293.15)

        elif ft == "FlowStudio::BCHeatFlux":
            bc = builder.add_boundary_condition(obj.Label)
            bc[f"Target Boundaries(1)"] = bc_idx
            bc["Heat Flux BC"] = True
            bc["Heat Flux"] = getattr(obj, "HeatFlux", 0.0)

        elif ft == "FlowStudio::BCConvection":
            bc = builder.add_boundary_condition(obj.Label)
            bc[f"Target Boundaries(1)"] = bc_idx
            bc["Heat Flux BC"] = True
            bc["Heat Transfer Coefficient"] = getattr(
                obj, "HeatTransferCoefficient", 10.0
            )
            bc["External Temperature"] = getattr(
                obj, "AmbientTemperature", 293.15
            )

        elif ft == "FlowStudio::BCRadiation":
            bc = builder.add_boundary_condition(obj.Label)
            bc[f"Target Boundaries(1)"] = bc_idx
            bc["Radiation"] = '"Diffuse Gray"'
            bc["Emissivity"] = getattr(obj, "Emissivity", 0.9)


# Domain → handler function mapping
_DOMAIN_HANDLERS = {
    "CFD": _generate_sif_cfd,
    "Structural": _generate_sif_structural,
    "Electrostatic": _generate_sif_electrostatic,
    "Electromagnetic": _generate_sif_electromagnetic,
    "Thermal": _generate_sif_thermal,
}
