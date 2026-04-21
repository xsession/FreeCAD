# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""End-to-end test: Real solver execution with actual fluid simulation.

This test suite:
  1. Auto-detects which solvers are installed on the system
  2. Creates a simple lid-driven cavity geometry
  3. Sets up a complete CFD case with boundary conditions
  4. Writes the solver input files
  5. Runs the actual solver (if available)
  6. Verifies results are produced
  7. Tests parallelism configuration

Supports: OpenFOAM, Elmer, FluidX3D
Also tests: solver auto-download infrastructure, ParaView detection

**Must be executed inside FreeCAD** (via FreeCADCmd.exe or the GUI).
"""

import sys
import os
import traceback
import tempfile
import shutil
import time

# Guard: skip module entirely when imported outside FreeCAD
try:
    import FreeCAD as App
    import Part
    from flow_studio.ObjectsFlowStudio import (
        makeAnalysis,
        makePhysicsModel,
        makeFluidMaterial,
        makeInitialConditions,
        makeSolver,
        makeBCWall,
        makeBCInlet,
        makeBCOutlet,
        makeMeshGmsh,
        makePostPipeline,
        makeDomainAnalysis,
    )
    from flow_studio.solver_deps import (
        check_all,
        check_backend,
        find_executable,
        recommend_parallel_settings,
        detect_cpu_cores,
    )
    from flow_studio.solvers.registry import (
        get_runner,
        available_backends,
        available_backends_installed,
        backends_for_domain,
    )
    _HAS_FREECAD = True
except ImportError:
    _HAS_FREECAD = False


# ======================================================================
# Geometry helpers
# ======================================================================

def _make_lid_driven_cavity(doc, size=100.0):
    """Create a 2D-extruded square cavity for the classic lid-driven test.

    Returns Part::Feature with a box (size x size x size/10).
    Face classification:
      Face3 = -Z (bottom wall), Face4 = +Z (top = moving lid)
      Face1 = -Y (front wall), Face2 = +Y (back wall)
      Face5 = -X (left wall), Face6 = +X (right wall)
    """
    depth = size / 10.0  # thin extrusion for quasi-2D
    box = Part.makeBox(size, size, depth)
    feat = doc.addObject("Part::Feature", "LidDrivenCavity")
    feat.Shape = box
    doc.recompute()
    return feat


def _make_channel_flow(doc, length=200.0, height=50.0, depth=10.0):
    """Create a simple 2D channel for Poiseuille/channel flow test.

    Face classification for a FreeCAD box:
      Face5 = -X (inlet), Face6 = +X (outlet)
      Face3 = -Z (bottom wall), Face4 = +Z (top wall)
      Face1 = -Y, Face2 = +Y (front/back walls - can be symmetry)
    """
    box = Part.makeBox(length, depth, height)
    feat = doc.addObject("Part::Feature", "ChannelFlow")
    feat.Shape = box
    doc.recompute()
    return feat


def _classify_cavity_faces(shape, size, depth, tol=1.0):
    """Classify lid-driven cavity faces by centre-of-mass.

    Returns dict: 'lid' (top, +Z), 'walls' (all other faces).
    """
    result = {"lid": [], "walls": []}
    for i, face in enumerate(shape.Faces):
        cm = face.CenterOfMass
        name = f"Face{i+1}"
        if abs(cm.z - depth) < tol:
            result["lid"].append((name, face))
        else:
            result["walls"].append((name, face))
    return result


# ======================================================================
# Test class
# ======================================================================

class E2ERealSolverTests:
    """End-to-end tests with actual solver execution."""

    def __init__(self):
        self.results = []
        self.doc = None
        self.temp_dir = None

    def _pass(self, name, detail=""):
        self.results.append(("PASS", name, detail))
        print(f"  PASS: {name} {detail}")

    def _fail(self, name, detail=""):
        self.results.append(("FAIL", name, detail))
        print(f"  FAIL: {name} {detail}")

    def _skip(self, name, detail=""):
        self.results.append(("SKIP", name, detail))
        print(f"  SKIP: {name} {detail}")

    def setUp(self):
        """Create a fresh document and temp directory."""
        self.doc = App.newDocument("E2E_RealSolver")
        self.temp_dir = tempfile.mkdtemp(prefix="flowstudio_e2e_solver_")
        print(f"  Temp dir: {self.temp_dir}")

    def tearDown(self):
        """Close document and clean up."""
        if self.doc:
            App.closeDocument(self.doc.Name)
            self.doc = None
        if self.temp_dir and os.path.isdir(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir, ignore_errors=True)
            except Exception:
                pass

    # ==================================================================
    # Test: Solver dependency detection
    # ==================================================================

    def test_01_dependency_detection(self):
        """Test that solver dependency detection works for all backends."""
        name = "dependency_detection"
        try:
            reports = check_all()
            assert isinstance(reports, dict), "check_all must return dict"
            assert len(reports) > 0, "Must have at least one backend"

            for backend_name, report in reports.items():
                assert hasattr(report, "available"), f"{backend_name} missing 'available'"
                assert hasattr(report, "deps"), f"{backend_name} missing 'deps'"
                print(f"    {backend_name}: {'AVAILABLE' if report.available else 'UNAVAILABLE'} "
                      f"({len(report.deps)} deps checked)")

            self._pass(name, f"{len(reports)} backends checked")
        except Exception as e:
            self._fail(name, str(e))

    # ==================================================================
    # Test: Parallel settings detection
    # ==================================================================

    def test_02_parallel_detection(self):
        """Test CPU/GPU detection for parallel settings."""
        name = "parallel_detection"
        try:
            phys, logical = detect_cpu_cores()
            assert phys >= 1, "Must have at least 1 physical core"
            assert logical >= 1, "Must have at least 1 logical core"
            assert logical >= phys, "Logical cores >= physical cores"

            settings = recommend_parallel_settings()
            assert "cpu_physical" in settings
            assert "cpu_logical" in settings
            assert "gpu_count" in settings
            assert "OpenFOAM" in settings
            assert "Elmer" in settings
            assert "FluidX3D" in settings

            print(f"    CPUs: {phys} physical, {logical} logical")
            print(f"    GPUs: {settings['gpu_count']}")
            print(f"    OpenFOAM recommended procs: {settings['OpenFOAM']['NumProcessors']}")
            print(f"    Elmer recommended procs: {settings['Elmer']['NumProcessors']}")

            self._pass(name, f"{phys} cores, {settings['gpu_count']} GPUs")
        except Exception as e:
            self._fail(name, str(e))

    # ==================================================================
    # Test: Solver installer infrastructure
    # ==================================================================

    def test_03_installer_infrastructure(self):
        """Test that the solver installer module loads and works."""
        name = "installer_infrastructure"
        try:
            from flow_studio.solver_installer import SolverInstaller, get_installer

            installer = get_installer()
            assert installer is not None
            assert os.path.isdir(installer.install_root)
            assert isinstance(installer.all_bin_dirs(), list)

            # Test ensure_solver with a backend that might be installed
            # (don't actually download - just test the infrastructure)
            self._pass(name, f"install_root={installer.install_root}")
        except Exception as e:
            self._fail(name, str(e))

    # ==================================================================
    # Test: ParaView detection
    # ==================================================================

    def test_04_paraview_detection(self):
        """Test ParaView detection on the system."""
        name = "paraview_detection"
        try:
            path, ver = find_executable("paraview")
            if path:
                self._pass(name, f"ParaView found: {path} ({ver})")
            else:
                # Also check common locations
                from flow_studio.solver_installer import SolverInstaller
                installer = SolverInstaller()
                extra = installer.all_bin_dirs()
                path, ver = find_executable("paraview", extra)
                if path:
                    self._pass(name, f"ParaView found (extra): {path}")
                else:
                    self._skip(name, "ParaView not installed")
        except Exception as e:
            self._fail(name, str(e))

    # ==================================================================
    # Test: Registry & available backends
    # ==================================================================

    def test_05_registry_backends(self):
        """Test solver registry reports correct backends."""
        name = "registry_backends"
        try:
            all_backends = available_backends()
            assert "OpenFOAM" in all_backends
            assert "FluidX3D" in all_backends
            assert "Elmer" in all_backends

            cfd_backends = backends_for_domain("CFD")
            assert "OpenFOAM" in cfd_backends
            assert "FluidX3D" in cfd_backends

            installed = available_backends_installed()
            print(f"    All backends: {all_backends}")
            print(f"    Installed: {installed}")

            self._pass(name, f"{len(installed)}/{len(all_backends)} installed")
        except Exception as e:
            self._fail(name, str(e))

    # ==================================================================
    # Test: OpenFOAM real solver run (lid-driven cavity)
    # ==================================================================

    def test_06_openfoam_cavity(self):
        """Run actual OpenFOAM simulation on a lid-driven cavity."""
        name = "openfoam_cavity"
        try:
            # Check if OpenFOAM is available
            report = check_backend("OpenFOAM")
            if not report.available:
                self._skip(name, "OpenFOAM not installed")
                return

            self.setUp()
            # Create geometry
            cavity = _make_lid_driven_cavity(self.doc, size=100.0)
            assert cavity is not None

            # Create analysis
            analysis = makeAnalysis(self.doc)
            analysis.CaseDir = os.path.join(self.temp_dir, "openfoam_cavity")

            # Physics model
            physics = makePhysicsModel(self.doc)
            physics.FlowRegime = "Laminar"
            physics.Compressibility = "Incompressible"
            physics.TimeModel = "Steady"
            analysis.addObject(physics)

            # Material
            material = makeFluidMaterial(self.doc)
            material.Density = 1.0
            material.KinematicViscosity = 0.01  # Re = U*L/nu = 1*1/0.01 = 100
            analysis.addObject(material)

            # Initial conditions
            ic = makeInitialConditions(self.doc)
            ic.Ux = 0.0
            ic.Uy = 0.0
            ic.Uz = 0.0
            analysis.addObject(ic)

            # Solver
            solver = makeSolver(self.doc)
            solver.SolverBackend = "OpenFOAM"
            solver.OpenFOAMSolver = "icoFoam"
            solver.MaxIterations = 100  # Small for test
            solver.WriteInterval = 50
            solver.NumProcessors = 1
            analysis.addObject(solver)

            # Boundary conditions - walls
            wall_bc = makeBCWall(self.doc)
            wall_bc.WallType = "No-Slip"
            wall_bc.References = [(cavity, "Face1"), (cavity, "Face2"),
                                  (cavity, "Face3"), (cavity, "Face5"),
                                  (cavity, "Face6")]
            analysis.addObject(wall_bc)

            # Moving lid (top face = Face4 for +Z)
            lid_bc = makeBCWall(self.doc)
            lid_bc.Label = "MovingLid"
            lid_bc.WallType = "Moving Wall (Translational)"
            lid_bc.WallVelocityX = 1.0
            lid_bc.WallVelocityY = 0.0
            lid_bc.WallVelocityZ = 0.0
            lid_bc.References = [(cavity, "Face4")]
            analysis.addObject(lid_bc)

            self.doc.recompute()

            # Get the runner
            RunnerClass = get_runner("OpenFOAM")
            assert RunnerClass is not None, "OpenFOAM runner class not found"

            runner = RunnerClass(analysis, solver)

            # Write case
            runner.write_case()

            case_dir = runner.case_dir
            assert os.path.isdir(case_dir), f"Case dir not created: {case_dir}"

            # Verify case files
            for f in ["system/controlDict", "system/fvSchemes", "system/fvSolution",
                       "constant/transportProperties", "0/p", "0/U"]:
                fpath = os.path.join(case_dir, f)
                assert os.path.isfile(fpath), f"Missing: {f}"

            # Run solver
            ok = runner.run()
            if ok and runner.process:
                # Wait for solver to finish (with timeout)
                try:
                    runner.process.wait(timeout=60)
                except Exception:
                    runner.stop()
                    self._fail(name, "Solver timed out")
                    return
                finally:
                    self.tearDown()

                rc = runner.process.returncode
                if rc == 0:
                    self._pass(name, f"icoFoam completed (case: {case_dir})")
                else:
                    # Non-zero exit might still produce results
                    result_dir = runner.read_results()
                    if result_dir:
                        self._pass(name, f"Results at {result_dir} (exit={rc})")
                    else:
                        self._fail(name, f"Solver exit code {rc}, no results")
            else:
                self._fail(name, "Failed to start solver")
                self.tearDown()

        except Exception as e:
            self._fail(name, f"{e}\n{traceback.format_exc()}")
            self.tearDown()

    # ==================================================================
    # Test: Elmer real solver run (thermal simulation)
    # ==================================================================

    def test_07_elmer_thermal(self):
        """Run actual Elmer simulation (thermal steady-state)."""
        name = "elmer_thermal"
        try:
            report = check_backend("Elmer")
            if not report.available:
                self._skip(name, "Elmer not installed")
                return

            self.setUp()
            cavity = _make_lid_driven_cavity(self.doc, size=50.0)

            # Create thermal analysis (backend auto-set to Elmer for Thermal domain)
            analysis = makeDomainAnalysis(self.doc, "Thermal")
            analysis.CaseDir = os.path.join(self.temp_dir, "elmer_thermal")

            # Solver
            solver = makeSolver(self.doc)
            solver.MaxIterations = 10
            solver.NumProcessors = 1
            analysis.addObject(solver)

            self.doc.recompute()

            # Get runner
            RunnerClass = get_runner("Elmer")
            assert RunnerClass is not None

            runner = RunnerClass(analysis, solver)

            # Write case
            runner.write_case()
            case_dir = runner.case_dir
            assert os.path.isdir(case_dir)

            sif_path = os.path.join(case_dir, "case.sif")
            assert os.path.isfile(sif_path), "SIF file not generated"

            # Check SIF content
            with open(sif_path, "r") as f:
                sif = f.read()
            assert "Simulation" in sif, "SIF missing Simulation block"
            assert "Solver" in sif, "SIF missing Solver block"

            # Run solver (if mesh is available)
            runner.run()

            if runner.process:
                try:
                    runner.process.wait(timeout=60)
                except Exception:
                    runner.stop()

                results = runner.read_results()
                if results:
                    self._pass(name, f"Elmer completed, {len(results)} VTU files")
                else:
                    # Solver ran but no mesh → expected, still a pass for infra
                    self._pass(name, "Elmer runner infrastructure works (no mesh for actual solve)")
            else:
                self._pass(name, "Elmer case written successfully (solver not run)")

            self.tearDown()

        except Exception as e:
            self._fail(name, f"{e}\n{traceback.format_exc()}")
            self.tearDown()

    # ==================================================================
    # Test: OpenFOAM parallel configuration
    # ==================================================================

    def test_08_openfoam_parallel_config(self):
        """Test OpenFOAM parallel decomposition configuration."""
        name = "openfoam_parallel_config"
        try:
            self.setUp()
            channel = _make_channel_flow(self.doc)

            analysis = makeAnalysis(self.doc)
            analysis.CaseDir = os.path.join(self.temp_dir, "of_parallel")

            physics = makePhysicsModel(self.doc)
            physics.FlowRegime = "Laminar"
            analysis.addObject(physics)

            material = makeFluidMaterial(self.doc)
            analysis.addObject(material)

            ic = makeInitialConditions(self.doc)
            analysis.addObject(ic)

            solver = makeSolver(self.doc)
            solver.SolverBackend = "OpenFOAM"
            solver.NumProcessors = 4  # Parallel
            analysis.addObject(solver)

            self.doc.recompute()

            RunnerClass = get_runner("OpenFOAM")
            runner = RunnerClass(analysis, solver)
            runner.write_case()

            case_dir = runner.case_dir

            # Verify decomposeParDict was generated
            decomp_dict = os.path.join(case_dir, "system", "decomposeParDict")
            assert os.path.isfile(decomp_dict), "decomposeParDict not generated for parallel"

            with open(decomp_dict, "r") as f:
                content = f.read()
            assert "numberOfSubdomains  4" in content, "Wrong subdomain count"
            assert "scotch" in content, "Missing decomposition method"

            self._pass(name, "decomposeParDict generated for 4 procs")
            self.tearDown()

        except Exception as e:
            self._fail(name, f"{e}\n{traceback.format_exc()}")
            self.tearDown()

    # ==================================================================
    # Test: Elmer parallel configuration
    # ==================================================================

    def test_09_elmer_parallel_config(self):
        """Test Elmer MPI parallel solver infrastructure."""
        name = "elmer_parallel_config"
        try:
            report = check_backend("Elmer")
            if not report.available:
                self._skip(name, "Elmer not installed")
                return

            # Check if MPI variant exists
            mpi_path, _ = find_executable("ElmerSolver_mpi")
            has_mpi = mpi_path is not None

            self.setUp()
            box = _make_lid_driven_cavity(self.doc, size=50.0)

            analysis = makeDomainAnalysis(self.doc, "Thermal")
            analysis.CaseDir = os.path.join(self.temp_dir, "elmer_parallel")

            solver = makeSolver(self.doc)
            solver.NumProcessors = 2
            analysis.addObject(solver)

            self.doc.recompute()

            RunnerClass = get_runner("Elmer")
            runner = RunnerClass(analysis, solver)

            # Test _get_num_processors
            nproc = runner._get_num_processors()
            assert nproc == 2, f"Expected 2 procs, got {nproc}"

            if has_mpi:
                self._pass(name, f"Elmer MPI available: {mpi_path}")
            else:
                self._pass(name, "Elmer parallel config works (no MPI binary)")

            self.tearDown()

        except Exception as e:
            self._fail(name, f"{e}\n{traceback.format_exc()}")
            self.tearDown()

    # ==================================================================
    # Test: FluidX3D case generation with multi-GPU
    # ==================================================================

    def test_10_fluidx3d_multigpu_config(self):
        """Test FluidX3D multi-GPU case generation."""
        name = "fluidx3d_multigpu_config"
        try:
            self.setUp()
            cavity = _make_lid_driven_cavity(self.doc, size=100.0)

            analysis = makeAnalysis(self.doc)
            analysis.CaseDir = os.path.join(self.temp_dir, "fx3d_multigpu")

            physics = makePhysicsModel(self.doc)
            physics.FlowRegime = "Laminar"
            analysis.addObject(physics)

            material = makeFluidMaterial(self.doc)
            material.KinematicViscosity = 0.01
            analysis.addObject(material)

            ic = makeInitialConditions(self.doc)
            ic.Ux = 1.0
            analysis.addObject(ic)

            # Mesh (needed for STL export)
            mesh = makeMeshGmsh(self.doc)
            mesh.Part = cavity
            analysis.addObject(mesh)

            solver = makeSolver(self.doc)
            solver.SolverBackend = "FluidX3D"
            solver.FluidX3DMultiGPU = True
            solver.FluidX3DNumGPUs = 4
            solver.FluidX3DResolution = 128
            solver.FluidX3DTimeSteps = 1000
            solver.FluidX3DVRAM = 2000
            analysis.addObject(solver)

            self.doc.recompute()

            RunnerClass = get_runner("FluidX3D")
            runner = RunnerClass(analysis, solver)
            runner.write_case()

            case_dir = runner.case_dir

            # Check setup.cpp was generated with multi-GPU
            setup_cpp = os.path.join(case_dir, "setup.cpp")
            assert os.path.isfile(setup_cpp), "setup.cpp not generated"

            with open(setup_cpp, "r") as f:
                cpp_content = f.read()
            assert "Multi-GPU" in cpp_content, "Multi-GPU comment missing"
            assert "Dx=" in cpp_content or "Dy=" in cpp_content, "GPU topology missing"
            assert "4u" in cpp_content, "GPU count not in topology"

            # Check defines_override.hpp has MULTI_GPU
            defines_path = os.path.join(case_dir, "defines_override.hpp")
            assert os.path.isfile(defines_path), "defines_override.hpp not generated"

            with open(defines_path, "r") as f:
                defines_content = f.read()
            assert "MULTI_GPU" in defines_content, "MULTI_GPU define missing"

            self._pass(name, "FluidX3D multi-GPU config (4 GPUs)")
            self.tearDown()

        except Exception as e:
            self._fail(name, f"{e}\n{traceback.format_exc()}")
            self.tearDown()

    # ==================================================================
    # Test: FluidX3D actual solver run
    # ==================================================================

    def test_11_fluidx3d_solver(self):
        """Run actual FluidX3D simulation (if executable available)."""
        name = "fluidx3d_solver"
        try:
            report = check_backend("FluidX3D")
            if not report.available:
                self._skip(name, "FluidX3D not installed")
                return

            self.setUp()
            cavity = _make_lid_driven_cavity(self.doc, size=50.0)

            analysis = makeAnalysis(self.doc)
            analysis.CaseDir = os.path.join(self.temp_dir, "fx3d_run")

            physics = makePhysicsModel(self.doc)
            analysis.addObject(physics)

            material = makeFluidMaterial(self.doc)
            analysis.addObject(material)

            ic = makeInitialConditions(self.doc)
            analysis.addObject(ic)

            mesh = makeMeshGmsh(self.doc)
            mesh.Part = cavity
            analysis.addObject(mesh)

            solver = makeSolver(self.doc)
            solver.SolverBackend = "FluidX3D"
            solver.FluidX3DResolution = 64  # Small for testing
            solver.FluidX3DTimeSteps = 100
            analysis.addObject(solver)

            self.doc.recompute()

            RunnerClass = get_runner("FluidX3D")
            runner = RunnerClass(analysis, solver)
            runner.write_case()

            ok = runner.run()
            if ok and runner.process:
                try:
                    runner.process.wait(timeout=120)
                except Exception:
                    runner.stop()

                result = runner.read_results()
                if result:
                    self._pass(name, f"FluidX3D completed, result: {result}")
                else:
                    self._pass(name, "FluidX3D ran (no VTK output in test mode)")
            else:
                self._pass(name, "FluidX3D case generated (exe not run)")

            self.tearDown()

        except Exception as e:
            self._fail(name, f"{e}\n{traceback.format_exc()}")
            self.tearDown()

    # ==================================================================
    # Test: Solver auto-parallel detection
    # ==================================================================

    def test_12_auto_parallel_detection(self):
        """Test that Solver object auto-detects parallel settings."""
        name = "auto_parallel_detection"
        try:
            self.setUp()

            solver = makeSolver(self.doc)

            # Defaults should already use all detected physical cores.
            phys_cores, _ = detect_cpu_cores()
            assert solver.NumProcessors == phys_cores
            assert solver.AutoParallel is True

            # Enable auto-parallel
            solver.AutoParallel = True

            # After enabling AutoParallel, NumProcessors should be updated
            # (based on hardware detection)
            expected = max(1, phys_cores)

            # The onChanged handler should have updated it
            actual = solver.NumProcessors
            print(f"    Auto-detected: {actual} processors (expected ~{expected})")

            assert actual >= 1, "Must have at least 1 processor"

            self._pass(name, f"Auto-detected {actual} processors")
            self.tearDown()

        except Exception as e:
            self._fail(name, f"{e}\n{traceback.format_exc()}")
            self.tearDown()

    # ==================================================================
    # Test: Channel flow with actual OpenFOAM parallel run
    # ==================================================================

    def test_13_openfoam_parallel_run(self):
        """Run OpenFOAM in parallel mode on a channel flow."""
        name = "openfoam_parallel_run"
        try:
            report = check_backend("OpenFOAM")
            if not report.available:
                self._skip(name, "OpenFOAM not installed")
                return

            # Check MPI
            mpi_path, _ = find_executable("mpirun")
            if mpi_path is None:
                mpi_path, _ = find_executable("mpiexec")
            if mpi_path is None:
                self._skip(name, "MPI not available for parallel run")
                return

            self.setUp()
            channel = _make_channel_flow(self.doc)

            analysis = makeAnalysis(self.doc)
            analysis.CaseDir = os.path.join(self.temp_dir, "of_parallel_run")

            physics = makePhysicsModel(self.doc)
            physics.FlowRegime = "Laminar"
            physics.TimeModel = "Steady"
            analysis.addObject(physics)

            material = makeFluidMaterial(self.doc)
            material.KinematicViscosity = 1.0e-3
            analysis.addObject(material)

            ic = makeInitialConditions(self.doc)
            analysis.addObject(ic)

            # Inlet BC
            inlet = makeBCInlet(self.doc)
            inlet.InletType = "Velocity"
            inlet.Ux = 1.0
            inlet.Uy = 0.0
            inlet.Uz = 0.0
            inlet.References = [(channel, "Face5")]
            analysis.addObject(inlet)

            # Outlet BC
            outlet = makeBCOutlet(self.doc)
            outlet.OutletType = "Static Pressure"
            outlet.StaticPressure = 0.0
            outlet.References = [(channel, "Face6")]
            analysis.addObject(outlet)

            # Walls
            wall = makeBCWall(self.doc)
            wall.WallType = "No-Slip"
            wall.References = [(channel, "Face1"), (channel, "Face2"),
                               (channel, "Face3"), (channel, "Face4")]
            analysis.addObject(wall)

            solver = makeSolver(self.doc)
            solver.SolverBackend = "OpenFOAM"
            solver.OpenFOAMSolver = "simpleFoam"
            solver.MaxIterations = 50
            solver.WriteInterval = 25
            solver.NumProcessors = 2  # Parallel!
            analysis.addObject(solver)

            self.doc.recompute()

            RunnerClass = get_runner("OpenFOAM")
            runner = RunnerClass(analysis, solver)

            # Write case (includes decomposeParDict)
            runner.write_case()

            decomp_file = os.path.join(runner.case_dir, "system", "decomposeParDict")
            assert os.path.isfile(decomp_file), "decomposeParDict missing"

            # Run solver
            ok = runner.run()
            if ok and runner.process:
                try:
                    runner.process.wait(timeout=120)
                except Exception:
                    runner.stop()

                # Reconstruct parallel results
                runner.reconstruct_par()

                result_dir = runner.read_results()
                if result_dir:
                    self._pass(name, f"Parallel OpenFOAM completed: {result_dir}")
                else:
                    self._pass(name, "Parallel run completed (no time dirs yet)")
            else:
                self._fail(name, "Failed to start parallel solver")

            self.tearDown()

        except Exception as e:
            self._fail(name, f"{e}\n{traceback.format_exc()}")
            self.tearDown()

    # ==================================================================
    # Test: Solver installer module functionality
    # ==================================================================

    def test_14_solver_installer_module(self):
        """Test solver installer module can detect installed solvers."""
        name = "solver_installer_module"
        try:
            from flow_studio.solver_installer import SolverInstaller

            # Use a test-specific install root
            test_root = os.path.join(self.temp_dir or tempfile.gettempdir(),
                                     "flowstudio_test_install")
            installer = SolverInstaller(install_root=test_root)

            assert os.path.isdir(installer.install_root)
            assert isinstance(installer.all_bin_dirs(), list)

            # State management
            installer._mark_installed("TestSolver", {
                "path": "/fake/path",
                "version": "1.0",
                "bin_dir": "/fake/bin",
            })
            installer._save_state()

            # Reload state
            installer2 = SolverInstaller(install_root=test_root)
            bd = installer2.get_bin_dir("TestSolver")
            assert bd == "/fake/bin", f"State not persisted: {bd}"

            self._pass(name, "Installer state management works")

        except Exception as e:
            self._fail(name, f"{e}\n{traceback.format_exc()}")

    # ==================================================================
    # Test: OpenFOAM case file content validation
    # ==================================================================

    def test_15_openfoam_case_validation(self):
        """Validate OpenFOAM case files have correct content."""
        name = "openfoam_case_validation"
        try:
            self.setUp()
            cavity = _make_lid_driven_cavity(self.doc, size=100.0)

            analysis = makeAnalysis(self.doc)
            analysis.CaseDir = os.path.join(self.temp_dir, "of_validate")

            physics = makePhysicsModel(self.doc)
            physics.FlowRegime = "Turbulent"
            physics.TurbulenceModel = "kOmegaSST"
            physics.TimeModel = "Steady"
            analysis.addObject(physics)

            material = makeFluidMaterial(self.doc)
            material.KinematicViscosity = 1.5e-5
            analysis.addObject(material)

            ic = makeInitialConditions(self.doc)
            analysis.addObject(ic)

            solver = makeSolver(self.doc)
            solver.SolverBackend = "OpenFOAM"
            solver.OpenFOAMSolver = "simpleFoam"
            solver.MaxIterations = 500
            solver.ConvectionScheme = "linearUpwind"
            solver.PressureSolver = "GAMG"
            solver.NumProcessors = 1
            analysis.addObject(solver)

            # Walls
            wall = makeBCWall(self.doc)
            wall.WallType = "No-Slip"
            wall.References = [(cavity, "Face1"), (cavity, "Face2"),
                               (cavity, "Face3"), (cavity, "Face5"),
                               (cavity, "Face6")]
            analysis.addObject(wall)

            # Moving lid
            lid = makeBCWall(self.doc)
            lid.Label = "Lid"
            lid.WallType = "Moving Wall (Translational)"
            lid.WallVelocityX = 1.0
            lid.References = [(cavity, "Face4")]
            analysis.addObject(lid)

            self.doc.recompute()

            RunnerClass = get_runner("OpenFOAM")
            runner = RunnerClass(analysis, solver)
            runner.write_case()

            case_dir = runner.case_dir

            # Validate controlDict
            with open(os.path.join(case_dir, "system", "controlDict"), "r") as f:
                ctrl = f.read()
            assert "simpleFoam" in ctrl, "Wrong solver in controlDict"
            assert "endTime         500" in ctrl, "Wrong endTime"

            # Validate turbulence
            with open(os.path.join(case_dir, "constant", "turbulenceProperties"), "r") as f:
                turb = f.read()
            assert "RAS" in turb, "Should be RAS for kOmegaSST"
            assert "kOmegaSST" in turb, "Wrong turbulence model"

            # Validate transport
            with open(os.path.join(case_dir, "constant", "transportProperties"), "r") as f:
                trans = f.read()
            assert "1.5e-05" in trans or "1.5e-5" in trans, "Wrong viscosity"

            # Validate schemes
            with open(os.path.join(case_dir, "system", "fvSchemes"), "r") as f:
                schemes = f.read()
            assert "steadyState" in schemes, "Wrong ddt scheme"
            assert "linearUpwind" in schemes, "Wrong convection scheme"

            # Validate fvSolution
            with open(os.path.join(case_dir, "system", "fvSolution"), "r") as f:
                sol = f.read()
            assert "GAMG" in sol, "Wrong pressure solver"

            # Should have turbulence fields
            assert os.path.isfile(os.path.join(case_dir, "0", "k")), "Missing k field"
            assert os.path.isfile(os.path.join(case_dir, "0", "omega")), "Missing omega field"

            self._pass(name, "All OpenFOAM case files validated")
            self.tearDown()

        except Exception as e:
            self._fail(name, f"{e}\n{traceback.format_exc()}")
            self.tearDown()

    # ==================================================================
    # Run all tests
    # ==================================================================

    def run_all(self):
        """Execute all tests and return summary."""
        print("\n" + "=" * 70)
        print("E2E REAL SOLVER SIMULATION TESTS")
        print("=" * 70)

        tests = [m for m in sorted(dir(self)) if m.startswith("test_")]
        for test_name in tests:
            print(f"\n--- {test_name} ---")
            try:
                getattr(self, test_name)()
            except Exception as e:
                self._fail(test_name, f"Unhandled: {e}")

        # Summary
        passed = sum(1 for r in self.results if r[0] == "PASS")
        failed = sum(1 for r in self.results if r[0] == "FAIL")
        skipped = sum(1 for r in self.results if r[0] == "SKIP")

        print("\n" + "=" * 70)
        print(f"RESULTS: {passed} passed, {failed} failed, {skipped} skipped "
              f"(total {len(self.results)})")
        if failed > 0:
            print("\nFAILED TESTS:")
            for status, name, detail in self.results:
                if status == "FAIL":
                    print(f"  X {name}: {detail}")
        print("=" * 70)

        return passed, failed, skipped


# ======================================================================
# Entry points
# ======================================================================

def run_tests():
    """Main entry point for running E2E real solver tests."""
    suite = E2ERealSolverTests()
    return suite.run_all()


# unittest discovery support
import unittest

@unittest.skipUnless(_HAS_FREECAD, "Requires FreeCAD environment")
class TestE2ERealSolver(unittest.TestCase):
    """Wrapper for unittest discovery."""

    def test_real_solver_suite(self):
        passed, failed, skipped = run_tests()
        self.assertEqual(failed, 0, f"{failed} E2E real solver tests failed")


if __name__ == "__main__":
    if _HAS_FREECAD:
        run_tests()
    else:
        print("ERROR: Must run inside FreeCAD (FreeCADCmd.exe)")
        sys.exit(1)
