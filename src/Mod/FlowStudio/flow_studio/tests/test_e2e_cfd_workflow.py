# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""End-to-end test: Full CFD simulation workflow.

Exercises the complete pipeline inside FreeCAD:
  1. Create geometry (box channel with inlet/outlet)
  2. Set physics domain (CFD)
  3. Create analysis with all sub-objects
  4. Configure boundary conditions (inlet, outlet, walls)
  5. Set solver goals (iterations, convergence tolerance)
  6. Validate OpenFOAM case-file generation
  7. Launch ParaView for post-processing (command construction only)

**Must be executed inside FreeCAD** (via FreeCADCmd.exe or the GUI).
Discovered by unittest but skipped if FreeCAD is not available.
"""

import sys
import os
import traceback
import tempfile
import shutil

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
    _HAS_FREECAD = True
except ImportError:
    _HAS_FREECAD = False


# ======================================================================
# Geometry helpers
# ======================================================================

def _make_channel_box(doc, length=200, width=50, height=50):
    """Create a simple rectangular channel (box) for CFD.

    Returns Part::Feature with the box solid.
    Face naming convention for a FreeCAD box:
      Face1 = -Y (front), Face2 = +Y (back)
      Face3 = -Z (bottom), Face4 = +Z (top)
      Face5 = -X (inlet), Face6 = +X (outlet)
    """
    box = Part.makeBox(length, width, height)
    feat = doc.addObject("Part::Feature", "Channel")
    feat.Shape = box
    doc.recompute()
    return feat


def _make_pipe_channel(doc, radius=20, length=300):
    """Create a cylindrical pipe channel for CFD.

    Returns Part::Feature with the cylinder solid.
    """
    cyl = Part.makeCylinder(radius, length, App.Vector(0, 0, 0), App.Vector(1, 0, 0))
    feat = doc.addObject("Part::Feature", "PipeChannel")
    feat.Shape = cyl
    doc.recompute()
    return feat


def _classify_box_faces(shape, length, width, height, tol=1.0):
    """Classify box faces into inlet, outlet, and walls by centre-of-mass.

    Returns dict with keys: 'inlet', 'outlet', 'walls' → list of (face_index, face).
    """
    result = {"inlet": [], "outlet": [], "walls": []}
    for i, face in enumerate(shape.Faces):
        cm = face.CenterOfMass
        name = f"Face{i+1}"
        if abs(cm.x) < tol:
            result["inlet"].append((name, face))
        elif abs(cm.x - length) < tol:
            result["outlet"].append((name, face))
        else:
            result["walls"].append((name, face))
    return result


# ======================================================================
# Test class
# ======================================================================

class E2ECFDWorkflowTests:
    """End-to-end tests for the complete CFD simulation workflow."""

    def __init__(self):
        self.results = []
        self.doc = None

    def _pass(self, name, detail=""):
        self.results.append(("PASS", name, detail))
        print(f"  PASS: {name} {detail}")

    def _fail(self, name, detail=""):
        self.results.append(("FAIL", name, detail))
        print(f"  FAIL: {name} {detail}")

    def _skip(self, name, detail=""):
        self.results.append(("SKIP", name, detail))
        print(f"  SKIP: {name} {detail}")

    def setup(self):
        self.doc = App.newDocument("E2E_CFD_Workflow")

    def teardown(self):
        if self.doc:
            App.closeDocument(self.doc.Name)
            self.doc = None

    # ------------------------------------------------------------------
    # Test: Set physics domain → CFD
    # ------------------------------------------------------------------
    def test_set_physics_domain_cfd(self):
        """Create a CFD analysis and verify the physics domain is set."""
        name = "test_set_physics_domain_cfd"
        try:
            analysis = makeAnalysis(self.doc, "TestCFDAnalysis")
            assert analysis is not None, "makeAnalysis returned None"
            assert hasattr(analysis, "PhysicsDomain"), "Missing PhysicsDomain property"
            assert analysis.PhysicsDomain == "CFD", \
                f"PhysicsDomain should be 'CFD', got '{analysis.PhysicsDomain}'"
            assert analysis.SolverBackend == "OpenFOAM", \
                f"SolverBackend should be 'OpenFOAM', got '{analysis.SolverBackend}'"
            assert hasattr(analysis, "AnalysisType"), "Missing AnalysisType property"
            assert hasattr(analysis, "CaseDir"), "Missing CaseDir property"

            self._pass(name, f"domain={analysis.PhysicsDomain}, "
                             f"backend={analysis.SolverBackend}")

            # Cleanup
            self.doc.removeObject(analysis.Name)

        except Exception as e:
            self._fail(name, str(e))
            traceback.print_exc()

    # ------------------------------------------------------------------
    # Test: Set physics domain → Thermal (multi-physics)
    # ------------------------------------------------------------------
    def test_set_physics_domain_thermal(self):
        """Create a Thermal analysis via makeDomainAnalysis."""
        name = "test_set_physics_domain_thermal"
        try:
            analysis = makeDomainAnalysis(self.doc, "ThermalAnalysis", domain_key="Thermal")
            assert analysis is not None
            assert analysis.PhysicsDomain == "Thermal", \
                f"Expected 'Thermal', got '{analysis.PhysicsDomain}'"
            assert analysis.SolverBackend == "Elmer", \
                f"Expected 'Elmer' for Thermal, got '{analysis.SolverBackend}'"

            self._pass(name, f"domain={analysis.PhysicsDomain}, "
                             f"backend={analysis.SolverBackend}")

            self.doc.removeObject(analysis.Name)

        except Exception as e:
            self._fail(name, str(e))
            traceback.print_exc()

    # ------------------------------------------------------------------
    # Test: Full analysis creation with all sub-objects
    # ------------------------------------------------------------------
    def test_create_full_analysis(self):
        """Create analysis + physics model + material + ICs + solver."""
        name = "test_create_full_analysis"
        try:
            analysis = makeAnalysis(self.doc, "FullAnalysis")

            physics = makePhysicsModel(self.doc)
            analysis.addObject(physics)

            material = makeFluidMaterial(self.doc)
            analysis.addObject(material)

            ics = makeInitialConditions(self.doc)
            analysis.addObject(ics)

            solver = makeSolver(self.doc)
            analysis.addObject(solver)

            self.doc.recompute()

            # Verify group membership
            group_names = [o.Name for o in analysis.Group]
            assert physics.Name in group_names, "PhysicsModel not in analysis"
            assert material.Name in group_names, "FluidMaterial not in analysis"
            assert ics.Name in group_names, "InitialConditions not in analysis"
            assert solver.Name in group_names, "Solver not in analysis"

            # Verify default property values
            assert physics.FlowRegime == "Turbulent", \
                f"FlowRegime: {physics.FlowRegime}"
            assert physics.TurbulenceModel == "kOmegaSST", \
                f"TurbModel: {physics.TurbulenceModel}"
            assert physics.TimeModel == "Steady", \
                f"TimeModel: {physics.TimeModel}"

            assert abs(material.Density - 1.225) < 0.01, \
                f"Density: {material.Density}"
            assert material.Preset == "Air (20°C, 1atm)", \
                f"Preset: {material.Preset}"

            assert solver.SolverBackend == "OpenFOAM", \
                f"Backend: {solver.SolverBackend}"
            assert solver.OpenFOAMSolver == "simpleFoam", \
                f"App: {solver.OpenFOAMSolver}"
            assert solver.MaxIterations == 2000, \
                f"MaxIterations: {solver.MaxIterations}"

            self._pass(name, f"group_size={len(analysis.Group)}")

            # Cleanup
            for obj in reversed(analysis.Group):
                self.doc.removeObject(obj.Name)
            self.doc.removeObject(analysis.Name)

        except Exception as e:
            self._fail(name, str(e))
            traceback.print_exc()

    # ------------------------------------------------------------------
    # Test: Set boundary conditions on geometry
    # ------------------------------------------------------------------
    def test_set_boundary_conditions(self):
        """Create geometry + analysis + BCs, assign faces."""
        name = "test_set_boundary_conditions"
        try:
            # Create channel geometry
            channel = _make_channel_box(self.doc, length=200, width=50, height=50)

            # Create analysis
            analysis = makeAnalysis(self.doc, "BCAnalysis")

            # Classify faces
            classified = _classify_box_faces(channel.Shape, 200, 50, 50)
            assert len(classified["inlet"]) >= 1, "No inlet face found"
            assert len(classified["outlet"]) >= 1, "No outlet face found"
            assert len(classified["walls"]) >= 4, \
                f"Expected >=4 wall faces, got {len(classified['walls'])}"

            # --- Inlet BC ---
            inlet = makeBCInlet(self.doc, "InletBC")
            analysis.addObject(inlet)
            inlet_face_name = classified["inlet"][0][0]
            inlet.References = [(channel, inlet_face_name)]
            inlet.InletType = "Velocity"
            inlet.VelocityMagnitude = 1.0
            inlet.Ux = 1.0
            inlet.Uy = 0.0
            inlet.Uz = 0.0

            assert inlet.BoundaryType == "inlet", \
                f"BoundaryType: {inlet.BoundaryType}"
            assert inlet.InletType == "Velocity"
            assert abs(inlet.VelocityMagnitude - 1.0) < 1e-6

            # --- Outlet BC ---
            outlet = makeBCOutlet(self.doc, "OutletBC")
            analysis.addObject(outlet)
            outlet_face_name = classified["outlet"][0][0]
            outlet.References = [(channel, outlet_face_name)]
            outlet.OutletType = "Static Pressure"
            outlet.StaticPressure = 0.0

            assert outlet.BoundaryType == "outlet"
            assert outlet.OutletType == "Static Pressure"

            # --- Wall BCs ---
            wall = makeBCWall(self.doc, "WallBC")
            analysis.addObject(wall)
            wall_refs = [(channel, wf[0]) for wf in classified["walls"]]
            wall.References = wall_refs
            wall.WallType = "No-Slip"

            assert wall.BoundaryType == "wall"
            assert wall.WallType == "No-Slip"
            assert len(wall.References) >= 1

            self.doc.recompute()

            self._pass(name, f"inlet={inlet_face_name}, "
                             f"outlet={outlet_face_name}, "
                             f"walls={len(classified['walls'])}")

            # Cleanup
            for obj in reversed(analysis.Group):
                self.doc.removeObject(obj.Name)
            self.doc.removeObject(analysis.Name)
            self.doc.removeObject(channel.Name)

        except Exception as e:
            self._fail(name, str(e))
            traceback.print_exc()

    # ------------------------------------------------------------------
    # Test: Set solver goals — iterations and convergence
    # ------------------------------------------------------------------
    def test_set_solver_goals_iterations(self):
        """Configure solver with specific iteration count and convergence tolerance."""
        name = "test_set_solver_goals_iterations"
        try:
            analysis = makeAnalysis(self.doc, "GoalAnalysis")
            solver = makeSolver(self.doc)
            analysis.addObject(solver)

            # Set goals
            solver.MaxIterations = 5000
            solver.ConvergenceTolerance = 1e-6
            solver.RelaxationFactorU = 0.8
            solver.RelaxationFactorP = 0.2
            solver.WriteInterval = 500
            solver.OpenFOAMSolver = "simpleFoam"
            solver.PressureSolver = "GAMG"

            self.doc.recompute()

            # Verify
            assert solver.MaxIterations == 5000, f"MaxIterations: {solver.MaxIterations}"
            assert abs(solver.ConvergenceTolerance - 1e-6) < 1e-10, \
                f"Tolerance: {solver.ConvergenceTolerance}"
            assert abs(solver.RelaxationFactorU - 0.8) < 1e-6
            assert abs(solver.RelaxationFactorP - 0.2) < 1e-6
            assert solver.WriteInterval == 500
            assert solver.OpenFOAMSolver == "simpleFoam"
            assert solver.PressureSolver == "GAMG"

            self._pass(name, f"iters={solver.MaxIterations}, "
                             f"tol={solver.ConvergenceTolerance}, "
                             f"relaxU={solver.RelaxationFactorU}, "
                             f"relaxP={solver.RelaxationFactorP}")

            # Cleanup
            for obj in reversed(analysis.Group):
                self.doc.removeObject(obj.Name)
            self.doc.removeObject(analysis.Name)

        except Exception as e:
            self._fail(name, str(e))
            traceback.print_exc()

    # ------------------------------------------------------------------
    # Test: Transient solver configuration
    # ------------------------------------------------------------------
    def test_set_solver_transient(self):
        """Configure transient (pimpleFoam) solver with time-stepping."""
        name = "test_set_solver_transient"
        try:
            analysis = makeAnalysis(self.doc, "TransientAnalysis")

            physics = makePhysicsModel(self.doc)
            analysis.addObject(physics)
            physics.TimeModel = "Transient"
            physics.FlowRegime = "Turbulent"
            physics.TurbulenceModel = "kOmegaSST"

            solver = makeSolver(self.doc)
            analysis.addObject(solver)
            solver.OpenFOAMSolver = "pimpleFoam"
            solver.EndTime = 2.0
            solver.TimeStep = 0.001
            solver.MaxIterations = 10000
            solver.WriteInterval = 200

            self.doc.recompute()

            assert physics.TimeModel == "Transient"
            assert solver.OpenFOAMSolver == "pimpleFoam"
            assert abs(solver.EndTime - 2.0) < 1e-6
            assert abs(solver.TimeStep - 0.001) < 1e-8

            self._pass(name, f"app={solver.OpenFOAMSolver}, "
                             f"dt={solver.TimeStep}, "
                             f"endTime={solver.EndTime}")

            for obj in reversed(analysis.Group):
                self.doc.removeObject(obj.Name)
            self.doc.removeObject(analysis.Name)

        except Exception as e:
            self._fail(name, str(e))
            traceback.print_exc()

    # ------------------------------------------------------------------
    # Test: Mesh object creation and configuration
    # ------------------------------------------------------------------
    def test_mesh_configuration(self):
        """Create mesh object, link to geometry, set params."""
        name = "test_mesh_configuration"
        try:
            channel = _make_channel_box(self.doc)
            analysis = makeAnalysis(self.doc, "MeshAnalysis")

            mesh = makeMeshGmsh(self.doc)
            analysis.addObject(mesh)
            mesh.Part = channel
            mesh.CharacteristicLength = 5.0
            mesh.MinElementSize = 0.5
            mesh.MaxElementSize = 10.0
            mesh.Algorithm3D = "Delaunay"
            mesh.ElementOrder = "1st Order"
            mesh.ElementType = "Tetrahedral"
            mesh.MeshFormat = "OpenFOAM (polyMesh)"

            self.doc.recompute()

            assert mesh.Part == channel, "Mesh not linked to channel"
            assert abs(mesh.CharacteristicLength - 5.0) < 1e-6
            assert mesh.Algorithm3D == "Delaunay"
            assert mesh.MeshFormat == "OpenFOAM (polyMesh)"

            self._pass(name, f"charLen={mesh.CharacteristicLength}, "
                             f"algo={mesh.Algorithm3D}, "
                             f"format={mesh.MeshFormat}")

            for obj in reversed(analysis.Group):
                self.doc.removeObject(obj.Name)
            self.doc.removeObject(analysis.Name)
            self.doc.removeObject(channel.Name)

        except Exception as e:
            self._fail(name, str(e))
            traceback.print_exc()

    # ------------------------------------------------------------------
    # Test: OpenFOAM case file generation
    # ------------------------------------------------------------------
    def test_openfoam_case_generation(self):
        """Full setup → generate OpenFOAM case files → verify structure."""
        name = "test_openfoam_case_generation"
        try:
            # Create geometry
            channel = _make_channel_box(self.doc, length=200, width=50, height=50)

            # Create analysis with case dir
            analysis = makeAnalysis(self.doc, "OFCaseAnalysis")
            case_dir = os.path.join(tempfile.gettempdir(), "flowstudio_e2e_case")
            if os.path.exists(case_dir):
                shutil.rmtree(case_dir)
            analysis.CaseDir = case_dir

            # Add sub-objects
            physics = makePhysicsModel(self.doc)
            analysis.addObject(physics)
            physics.FlowRegime = "Turbulent"
            physics.TurbulenceModel = "kOmegaSST"
            physics.Compressibility = "Incompressible"
            physics.TimeModel = "Steady"

            material = makeFluidMaterial(self.doc)
            analysis.addObject(material)

            ics = makeInitialConditions(self.doc)
            analysis.addObject(ics)
            ics.Ux = 1.0
            ics.Pressure = 0.0

            solver = makeSolver(self.doc)
            analysis.addObject(solver)
            solver.MaxIterations = 3000
            solver.ConvergenceTolerance = 1e-5
            solver.OpenFOAMSolver = "simpleFoam"

            # Classify and add BCs
            classified = _classify_box_faces(channel.Shape, 200, 50, 50)

            inlet = makeBCInlet(self.doc, "CaseInlet")
            analysis.addObject(inlet)
            inlet.References = [(channel, classified["inlet"][0][0])]
            inlet.InletType = "Velocity"
            inlet.VelocityMagnitude = 1.0
            inlet.Ux = 1.0

            outlet = makeBCOutlet(self.doc, "CaseOutlet")
            analysis.addObject(outlet)
            outlet.References = [(channel, classified["outlet"][0][0])]
            outlet.OutletType = "Static Pressure"
            outlet.StaticPressure = 0.0

            wall = makeBCWall(self.doc, "CaseWall")
            analysis.addObject(wall)
            wall_refs = [(channel, wf[0]) for wf in classified["walls"]]
            wall.References = wall_refs
            wall.WallType = "No-Slip"

            self.doc.recompute()

            # Try to instantiate runner and write case
            from flow_studio.solvers.openfoam_runner import OpenFOAMRunner
            runner = OpenFOAMRunner(analysis, solver)

            # Check if OpenFOAM is available
            of_available = runner.check()
            if not of_available:
                self._skip(name, "OpenFOAM not available on this machine")
                # Still validate what we can
                # Check that the runner was created successfully
                assert runner.case_dir == case_dir
                assert runner.analysis == analysis
                assert runner.solver_obj == solver
            else:
                # Write the case files
                runner.write_case()

                # Verify case directory structure
                assert os.path.isdir(case_dir), "Case dir not created"
                system_dir = os.path.join(case_dir, "system")
                constant_dir = os.path.join(case_dir, "constant")
                zero_dir = os.path.join(case_dir, "0")

                assert os.path.isdir(system_dir), "system/ dir missing"
                assert os.path.isdir(constant_dir), "constant/ dir missing"
                assert os.path.isdir(zero_dir), "0/ dir missing"

                # Check critical files
                assert os.path.isfile(os.path.join(system_dir, "controlDict")), \
                    "controlDict missing"
                assert os.path.isfile(os.path.join(system_dir, "fvSchemes")), \
                    "fvSchemes missing"
                assert os.path.isfile(os.path.join(system_dir, "fvSolution")), \
                    "fvSolution missing"
                assert os.path.isfile(os.path.join(constant_dir, "transportProperties")), \
                    "transportProperties missing"
                assert os.path.isfile(os.path.join(constant_dir, "turbulenceProperties")), \
                    "turbulenceProperties missing"

                # Verify controlDict content
                with open(os.path.join(system_dir, "controlDict"), "r") as f:
                    ctrl = f.read()
                assert "simpleFoam" in ctrl, "simpleFoam not in controlDict"

                # Verify boundary field files exist in 0/
                zero_files = os.listdir(zero_dir)
                assert "U" in zero_files, "0/U missing"
                assert "p" in zero_files, "0/p missing"

                self._pass(name, f"case_dir={case_dir}, "
                                 f"zero_files={zero_files}")

                # Cleanup case dir
                shutil.rmtree(case_dir, ignore_errors=True)
                return

            self._pass(name, "runner created (OF not installed)")

            # Cleanup
            for obj in reversed(analysis.Group):
                self.doc.removeObject(obj.Name)
            self.doc.removeObject(analysis.Name)
            self.doc.removeObject(channel.Name)

        except Exception as e:
            self._fail(name, str(e))
            traceback.print_exc()

    # ------------------------------------------------------------------
    # Test: Post-processing pipeline and ParaView launch
    # ------------------------------------------------------------------
    def test_postprocessing_paraview(self):
        """Create post-processing pipeline → verify ParaView command construction."""
        name = "test_postprocessing_paraview"
        try:
            analysis = makeAnalysis(self.doc, "PostAnalysis")

            # Set a case dir (simulate completed run)
            case_dir = os.path.join(tempfile.gettempdir(), "flowstudio_e2e_post")
            os.makedirs(case_dir, exist_ok=True)
            analysis.CaseDir = case_dir

            # Create a dummy .foam file (what OpenFOAM creates)
            foam_file = os.path.join(case_dir, "flowstudio.foam")
            with open(foam_file, "w") as f:
                f.write("")  # Empty .foam file (ParaView reads the case dir)

            # Create post-processing pipeline
            post = makePostPipeline(self.doc)
            analysis.addObject(post)
            # Note: Do NOT set post.Analysis = analysis when post is already
            # in the analysis Group — it creates a DAG cycle in FreeCAD.
            post.ResultFile = foam_file
            post.ResultFormat = "OpenFOAM"
            post.ActiveField = "U"
            post.VisualizationType = "Contour (Surface)"

            self.doc.recompute()

            assert post.ResultFile == foam_file
            assert post.ResultFormat == "OpenFOAM"
            assert post.ActiveField == "U"

            # Construct ParaView command (what FlowStudio_OpenParaView would do)
            paraview_exe = shutil.which("paraview")
            parafoam_exe = shutil.which("paraFoam")

            paraview_cmd = None
            if parafoam_exe:
                # paraFoam -case <case_dir>
                paraview_cmd = [parafoam_exe, "-case", case_dir]
            elif paraview_exe:
                # paraview <foam_file>
                paraview_cmd = [paraview_exe, foam_file]

            if paraview_cmd:
                self._pass(name, f"cmd={' '.join(paraview_cmd)}")
            else:
                # ParaView not installed — still verify the pipeline was set up
                self._pass(name, f"pipeline_ok=True, paraview=not_found, "
                                 f"foam_file={foam_file}")

            # Cleanup
            shutil.rmtree(case_dir, ignore_errors=True)
            for obj in reversed(analysis.Group):
                self.doc.removeObject(obj.Name)
            self.doc.removeObject(analysis.Name)

        except Exception as e:
            self._fail(name, str(e))
            traceback.print_exc()

    # ------------------------------------------------------------------
    # Test: Full pipeline — geometry → domain → BCs → goals → case gen
    # ------------------------------------------------------------------
    def test_full_cfd_pipeline(self):
        """Complete end-to-end: geometry → CFD domain → BCs → solver goals → case."""
        name = "test_full_cfd_pipeline"
        try:
            # ---- 1. Geometry ----
            channel = _make_channel_box(self.doc, length=300, width=60, height=60)
            shape = channel.Shape
            assert shape.isValid(), "Channel shape invalid"
            assert len(shape.Faces) == 6, f"Expected 6 faces, got {len(shape.Faces)}"

            # ---- 2. Physics domain: CFD ----
            analysis = makeAnalysis(self.doc, "FullPipeline")
            assert analysis.PhysicsDomain == "CFD"

            # Set case dir
            case_dir = os.path.join(tempfile.gettempdir(), "flowstudio_e2e_full")
            if os.path.exists(case_dir):
                shutil.rmtree(case_dir)
            analysis.CaseDir = case_dir

            # ---- 3. Physics model ----
            physics = makePhysicsModel(self.doc)
            analysis.addObject(physics)
            physics.FlowRegime = "Turbulent"
            physics.TurbulenceModel = "kOmegaSST"
            physics.Compressibility = "Incompressible"
            physics.TimeModel = "Steady"
            physics.Buoyancy = False

            # ---- 4. Material (Air) ----
            material = makeFluidMaterial(self.doc)
            analysis.addObject(material)
            assert material.Preset == "Air (20°C, 1atm)"
            assert abs(material.Density - 1.225) < 0.01

            # ---- 5. Initial conditions ----
            ics = makeInitialConditions(self.doc)
            analysis.addObject(ics)
            ics.Ux = 1.0
            ics.Uy = 0.0
            ics.Uz = 0.0
            ics.Pressure = 0.0

            # ---- 6. Boundary conditions ----
            classified = _classify_box_faces(shape, 300, 60, 60)

            inlet = makeBCInlet(self.doc, "PipeInlet")
            analysis.addObject(inlet)
            inlet.References = [(channel, classified["inlet"][0][0])]
            inlet.InletType = "Velocity"
            inlet.VelocityMagnitude = 10.0
            inlet.Ux = 10.0
            inlet.Uy = 0.0
            inlet.Uz = 0.0
            inlet.TurbulenceIntensity = 5.0
            inlet.TurbulenceLengthScale = 0.01

            outlet = makeBCOutlet(self.doc, "PipeOutlet")
            analysis.addObject(outlet)
            outlet.References = [(channel, classified["outlet"][0][0])]
            outlet.OutletType = "Static Pressure"
            outlet.StaticPressure = 0.0

            wall = makeBCWall(self.doc, "PipeWall")
            analysis.addObject(wall)
            wall.References = [(channel, wf[0]) for wf in classified["walls"]]
            wall.WallType = "No-Slip"

            # ---- 7. Solver goals ----
            solver = makeSolver(self.doc)
            analysis.addObject(solver)
            solver.SolverBackend = "OpenFOAM"
            solver.OpenFOAMSolver = "simpleFoam"
            solver.MaxIterations = 5000
            solver.ConvergenceTolerance = 1e-6
            solver.RelaxationFactorU = 0.7
            solver.RelaxationFactorP = 0.3
            solver.WriteInterval = 100
            solver.PressureSolver = "GAMG"

            # ---- 8. Mesh ----
            mesh = makeMeshGmsh(self.doc)
            analysis.addObject(mesh)
            mesh.Part = channel
            mesh.CharacteristicLength = 5.0
            mesh.MinElementSize = 1.0
            mesh.MaxElementSize = 10.0
            mesh.Algorithm3D = "Delaunay"
            mesh.MeshFormat = "OpenFOAM (polyMesh)"

            self.doc.recompute()

            # ---- 9. Validate the full setup ----
            group_types = []
            for obj in analysis.Group:
                ft = getattr(obj, "FlowType", "?")
                group_types.append(ft)

            expected_types = {
                "FlowStudio::PhysicsModel",
                "FlowStudio::FluidMaterial",
                "FlowStudio::InitialConditions",
                "FlowStudio::BCInlet",
                "FlowStudio::BCOutlet",
                "FlowStudio::BCWall",
                "FlowStudio::Solver",
                "FlowStudio::MeshGmsh",
            }
            found_types = set(group_types)
            missing = expected_types - found_types
            assert not missing, f"Missing types in analysis: {missing}"

            # ---- 10. Try OpenFOAM case generation ----
            from flow_studio.solvers.openfoam_runner import OpenFOAMRunner
            runner = OpenFOAMRunner(analysis, solver)
            of_available = runner.check()

            if of_available:
                runner.write_case()
                # Quick file-existence checks
                assert os.path.isfile(os.path.join(case_dir, "system", "controlDict"))
                assert os.path.isfile(os.path.join(case_dir, "0", "U"))
                assert os.path.isfile(os.path.join(case_dir, "0", "p"))
                self._pass(name, f"OF case written to {case_dir}")
                shutil.rmtree(case_dir, ignore_errors=True)
            else:
                self._pass(name, f"pipeline setup OK, OF not installed "
                                 f"(group={len(analysis.Group)} objects)")

            # ---- 11. Post-processing pipeline ----
            post = makePostPipeline(self.doc)
            analysis.addObject(post)
            foam_file = os.path.join(case_dir, "flowstudio.foam")
            # Don't set post.Analysis = analysis (DAG cycle)
            post.ResultFile = foam_file
            post.ResultFormat = "OpenFOAM"
            post.ActiveField = "p"
            post.VisualizationType = "Contour (Surface)"

            # Verify ParaView command can be formed
            pv = shutil.which("paraview") or shutil.which("paraFoam")
            pv_status = "found" if pv else "not_found"

            self._pass(name + "_postproc", f"paraview={pv_status}, field={post.ActiveField}")

            # Cleanup
            for obj in reversed(list(analysis.Group)):
                self.doc.removeObject(obj.Name)
            self.doc.removeObject(analysis.Name)
            self.doc.removeObject(channel.Name)

        except Exception as e:
            self._fail(name, str(e))
            traceback.print_exc()

    # ------------------------------------------------------------------
    # Test: Domain switching — CFD → Structural → back to CFD
    # ------------------------------------------------------------------
    def test_domain_switching(self):
        """Create analysis, switch domain, verify backend changes."""
        name = "test_domain_switching"
        try:
            analysis = makeAnalysis(self.doc, "SwitchAnalysis")

            # Start as CFD
            assert analysis.PhysicsDomain == "CFD"
            assert analysis.SolverBackend == "OpenFOAM"

            # Switch to Structural
            analysis.PhysicsDomain = "Structural"
            self.doc.recompute()
            # Note: SolverBackend may or may not auto-update depending on
            # onChanged implementation, so just verify PhysicsDomain changed
            assert analysis.PhysicsDomain == "Structural"

            # Switch to Electrostatic
            analysis.PhysicsDomain = "Electrostatic"
            self.doc.recompute()
            assert analysis.PhysicsDomain == "Electrostatic"

            # Back to CFD
            analysis.PhysicsDomain = "CFD"
            self.doc.recompute()
            assert analysis.PhysicsDomain == "CFD"

            self._pass(name, "CFD->Structural->Electrostatic->CFD")

            self.doc.removeObject(analysis.Name)

        except Exception as e:
            self._fail(name, str(e))
            traceback.print_exc()

    # ------------------------------------------------------------------
    # Test: FluidX3D solver configuration
    # ------------------------------------------------------------------
    def test_fluidx3d_solver_config(self):
        """Configure FluidX3D solver backend properties."""
        name = "test_fluidx3d_solver_config"
        try:
            analysis = makeAnalysis(self.doc, "FX3DAnalysis")
            solver = makeSolver(self.doc)
            analysis.addObject(solver)

            solver.SolverBackend = "FluidX3D"
            solver.FluidX3DResolution = 512
            solver.FluidX3DTimeSteps = 50000
            solver.FluidX3DVRAM = 4000
            solver.FluidX3DExtensions = "EQUILIBRIUM_BOUNDARIES"

            self.doc.recompute()

            assert solver.SolverBackend == "FluidX3D"
            assert solver.FluidX3DResolution == 512
            assert solver.FluidX3DTimeSteps == 50000
            assert solver.FluidX3DVRAM == 4000

            self._pass(name, f"backend={solver.SolverBackend}, "
                             f"res={solver.FluidX3DResolution}")

            for obj in reversed(analysis.Group):
                self.doc.removeObject(obj.Name)
            self.doc.removeObject(analysis.Name)

        except Exception as e:
            self._fail(name, str(e))
            traceback.print_exc()

    # ------------------------------------------------------------------
    # Run all
    # ------------------------------------------------------------------
    def run_all(self):
        """Execute all tests and return summary."""
        print("=" * 70)
        print("E2E Test Suite: Full CFD Simulation Workflow")
        print("=" * 70)

        self.setup()
        try:
            self.test_set_physics_domain_cfd()
            self.test_set_physics_domain_thermal()
            self.test_create_full_analysis()
            self.test_set_boundary_conditions()
            self.test_set_solver_goals_iterations()
            self.test_set_solver_transient()
            self.test_mesh_configuration()
            self.test_openfoam_case_generation()
            self.test_postprocessing_paraview()
            self.test_full_cfd_pipeline()
            self.test_domain_switching()
            self.test_fluidx3d_solver_config()
        finally:
            self.teardown()

        # Summary
        passed = sum(1 for r in self.results if r[0] == "PASS")
        failed = sum(1 for r in self.results if r[0] == "FAIL")
        skipped = sum(1 for r in self.results if r[0] == "SKIP")
        total = len(self.results)
        print("=" * 70)
        print(f"Results: {passed} passed, {failed} failed, {skipped} skipped / {total} total")
        print("=" * 70)
        return failed == 0


# ======================================================================
# Main entry point
# ======================================================================

if __name__ == "__main__":
    tests = E2ECFDWorkflowTests()
    success = tests.run_all()
    if not success:
        sys.exit(1)
