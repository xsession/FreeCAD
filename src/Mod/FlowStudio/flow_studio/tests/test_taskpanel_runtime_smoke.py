# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""FreeCAD-backed runtime smoke tests for FlowStudio task panels.

These tests instantiate real Qt widgets for a representative set of task
panels and verify that key interactive behavior still works end to end:

- stacked pages react to backend selection,
- preset-driven fields update widget values,
- toggles enable/disable dependent UI groups,
- ``_store()`` writes edited values back to the underlying object.

They are intentionally small and focused so they can run in a headless
FreeCAD/PySide environment without requiring a full GUI session.
"""

from __future__ import annotations

import os
import sys
import tempfile
import types
import unittest
from unittest import mock


sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

try:
    from flow_studio.taskpanels import task_solver as _task_solver_mod
    from flow_studio.taskpanels import task_fluid_material as _task_fluid_material_mod
    from flow_studio.taskpanels import task_bc_inlet as _task_bc_inlet_mod
    from flow_studio.taskpanels import task_bc_open as _task_bc_open_mod
    from flow_studio.taskpanels import task_bc_outlet as _task_bc_outlet_mod
    from flow_studio.taskpanels import task_bc_wall as _task_bc_wall_mod
    from flow_studio.taskpanels import task_initial_conditions as _task_initial_conditions_mod
    from flow_studio.taskpanels import task_generic_bc as _task_generic_bc_mod
    from flow_studio.taskpanels import task_mesh_gmsh as _task_mesh_gmsh_mod
    from flow_studio.taskpanels import task_measurement_point as _task_measurement_point_mod
    from flow_studio.taskpanels import task_measurement_surface as _task_measurement_surface_mod
    from flow_studio.taskpanels import task_measurement_volume as _task_measurement_volume_mod
    from flow_studio.taskpanels import task_flowefd_features as _task_flowefd_features_mod
    from flow_studio.taskpanels import task_geometry_tools as _task_geometry_tools_mod
    from flow_studio.taskpanels import task_geant4_result as _task_geant4_result_mod
    from flow_studio.taskpanels import task_geant4_result_component as _task_geant4_result_component_mod
    from flow_studio.taskpanels import task_materials as _task_materials_mod
    from flow_studio.taskpanels import task_post_pipeline as _task_post_pipeline_mod
    from flow_studio.taskpanels import task_physics_model as _task_physics_model_mod
    from flow_studio.enterprise.ui import jobs_panel as _jobs_panel_mod
    from flow_studio import engineering_database_editor as _engineering_database_editor_mod
    from PySide import QtGui
    _HAS_TASKPANEL_RUNTIME = True
except Exception:
    _HAS_TASKPANEL_RUNTIME = False
    QtGui = None


@unittest.skipUnless(_HAS_TASKPANEL_RUNTIME, "Requires FlowStudio task panels with FreeCAD/PySide runtime")
class TestTaskPanelRuntimeSmoke(unittest.TestCase):
    """Runtime smoke coverage for representative task-panel interactions."""

    @classmethod
    def setUpClass(cls):
        cls._app = QtGui.QApplication.instance()
        if cls._app is None:
            cls._app = QtGui.QApplication([])

        cls.TaskSolver = _task_solver_mod.TaskSolver
        cls.TaskFluidMaterial = _task_fluid_material_mod.TaskFluidMaterial
        cls.TaskBCInlet = _task_bc_inlet_mod.TaskBCInlet
        cls.TaskBCOpen = _task_bc_open_mod.TaskBCOpen
        cls.TaskBCOutlet = _task_bc_outlet_mod.TaskBCOutlet
        cls.TaskBCWall = _task_bc_wall_mod.TaskBCWall
        cls.TaskInitialConditions = _task_initial_conditions_mod.TaskInitialConditions
        cls.TaskGenericBC = _task_generic_bc_mod.TaskGenericBC
        cls.TaskMeshGmsh = _task_mesh_gmsh_mod.TaskMeshGmsh
        cls.TaskMeasurementPoint = _task_measurement_point_mod.TaskMeasurementPoint
        cls.TaskMeasurementSurface = _task_measurement_surface_mod.TaskMeasurementSurface
        cls.TaskMeasurementVolume = _task_measurement_volume_mod.TaskMeasurementVolume
        cls.TaskFan = _task_flowefd_features_mod.TaskFan
        cls.TaskResultPlot = _task_flowefd_features_mod.TaskResultPlot
        cls.TaskCheckGeometry = _task_geometry_tools_mod.TaskCheckGeometry
        cls.TaskLeakTracking = _task_geometry_tools_mod.TaskLeakTracking
        cls.TaskGeant4Result = _task_geant4_result_mod.TaskGeant4Result
        cls.TaskGeant4ResultComponent = _task_geant4_result_component_mod.TaskGeant4ResultComponent
        cls.TaskMaterial = _task_materials_mod.TaskMaterial
        cls.TaskPostPipeline = _task_post_pipeline_mod.TaskPostPipeline
        cls.TaskPhysicsModel = _task_physics_model_mod.TaskPhysicsModel
        cls.EnterpriseJobsPanel = _jobs_panel_mod.EnterpriseJobsPanel
        cls.EngineeringDatabaseEditorModule = _engineering_database_editor_mod
        cls.MATERIALS_DB = _task_fluid_material_mod.MATERIALS_DB
        cls.FreeCAD = _task_measurement_point_mod.FreeCAD

    def test_solver_backend_switch_updates_stack_and_store(self):
        obj = types.SimpleNamespace(
            SolverBackend="OpenFOAM",
            OpenFOAMSolver="simpleFoam",
            MaxIterations=100,
            ConvergenceTolerance=1e-5,
            NumProcessors=6,
            ConvectionScheme="upwind",
            ElmerSolverBinary="ElmerSolver",
            FluidX3DPrecision="FP32/FP32",
            FluidX3DResolution=128,
            FluidX3DTimeSteps=500,
            FluidX3DVRAM=4096,
            FluidX3DMultiGPU=False,
            FluidX3DNumGPUs=1,
            MultiSolverEnabled=False,
            MultiSolverBackends=["OpenFOAM", "Elmer"],
            SoftRuntimeWarningSeconds=0,
            MaxRuntimeSeconds=0,
            StallTimeoutSeconds=0,
            MinProgressPercent=0.0,
            AbortOnThreshold=True,
        )

        panel = self.TaskSolver(obj)
        self.assertEqual(panel.stack.currentIndex(), 0)

        panel.cb_backend.setCurrentIndex(panel.cb_backend.findText("Elmer"))
        self.assertEqual(panel.stack.currentIndex(), 1)

        panel.cb_elmer_solver.setCurrentIndex(panel.cb_elmer_solver.findText("ElmerSolver_mpi"))
        panel.sp_elmer_nproc.setValue(8)
        panel._store()

        self.assertEqual(obj.SolverBackend, "Elmer")
        self.assertEqual(obj.ElmerSolverBinary, "ElmerSolver_mpi")
        self.assertEqual(obj.NumProcessors, 8)

    def test_task_panels_publish_summary_metadata(self):
        inlet_obj = types.SimpleNamespace(
            References=[],
            PropertiesList=["References"],
            InletType="Velocity",
            Ux=1.0,
            Uy=0.0,
            Uz=0.0,
            NormalToFace=True,
            MassFlowRate=0.1,
            VolFlowRate=0.01,
            TurbulenceSpec="Intensity & Length Scale",
            TurbulenceIntensity=5.0,
            InletTemperature=300.0,
            Label="Main Inlet",
        )
        inlet_panel = self.TaskBCInlet(inlet_obj)
        self.assertEqual(inlet_panel.taskview_summary_title, "Inlet Boundary Condition")
        self.assertIn("Main Inlet", inlet_panel.taskview_summary_detail)

        solver_obj = types.SimpleNamespace(
            SolverBackend="OpenFOAM",
            OpenFOAMSolver="simpleFoam",
            MaxIterations=100,
            ConvergenceTolerance=1e-5,
            NumProcessors=4,
            ConvectionScheme="upwind",
            ElmerSolverBinary="ElmerSolver",
            FluidX3DPrecision="FP32/FP32",
            FluidX3DResolution=128,
            FluidX3DTimeSteps=500,
            FluidX3DVRAM=4096,
            FluidX3DMultiGPU=False,
            FluidX3DNumGPUs=1,
            MultiSolverEnabled=False,
            MultiSolverBackends=["OpenFOAM", "Elmer"],
            SoftRuntimeWarningSeconds=0,
            MaxRuntimeSeconds=0,
            StallTimeoutSeconds=0,
            MinProgressPercent=0.0,
            AbortOnThreshold=True,
            Label="Case Solver",
        )
        solver_panel = self.TaskSolver(solver_obj)
        self.assertEqual(solver_panel.taskview_summary_title, "Solver Configuration")
        self.assertIn("Case Solver", solver_panel.taskview_summary_detail)

    def test_solver_panel_publishes_geant4_validation_metadata_when_executable_missing(self):
        solver_obj = types.SimpleNamespace(
            SolverBackend="Geant4",
            OpenFOAMSolver="simpleFoam",
            MaxIterations=100,
            ConvergenceTolerance=1e-5,
            NumProcessors=4,
            ConvectionScheme="upwind",
            ElmerSolverBinary="ElmerSolver",
            FluidX3DPrecision="FP32/FP32",
            FluidX3DResolution=128,
            FluidX3DTimeSteps=500,
            FluidX3DVRAM=4096,
            FluidX3DMultiGPU=False,
            FluidX3DNumGPUs=1,
            MultiSolverEnabled=False,
            MultiSolverBackends=["Geant4", "OpenFOAM"],
            Geant4Executable="",
            Geant4PhysicsList="FTFP_BERT",
            Geant4EventCount=1000,
            Geant4Threads=1,
            Geant4MacroName="run.mac",
            Geant4EnableVisualization=False,
            SoftRuntimeWarningSeconds=0,
            MaxRuntimeSeconds=0,
            StallTimeoutSeconds=0,
            MinProgressPercent=0.0,
            AbortOnThreshold=True,
            Label="Geant4 Solver",
        )

        solver_panel = self.TaskSolver(solver_obj)
        self.assertEqual(solver_panel.taskview_validation_level, "incomplete")
        self.assertEqual(solver_panel.taskview_validation_title, "Geant4 executable required")
        self.assertIn("compiled Geant4 application path", solver_panel.taskview_validation_detail)

    def test_solver_panel_multi_solver_and_runtime_thresholds_store_roundtrip(self):
        solver_obj = types.SimpleNamespace(
            SolverBackend="OpenFOAM",
            OpenFOAMSolver="simpleFoam",
            MaxIterations=100,
            ConvergenceTolerance=1e-5,
            NumProcessors=4,
            ConvectionScheme="upwind",
            ElmerSolverBinary="ElmerSolver",
            FluidX3DPrecision="FP32/FP32",
            FluidX3DResolution=128,
            FluidX3DTimeSteps=500,
            FluidX3DVRAM=4096,
            FluidX3DMultiGPU=False,
            FluidX3DNumGPUs=1,
            Geant4Executable="C:/geant4/demo.exe",
            Geant4PhysicsList="FTFP_BERT",
            Geant4EventCount=1000,
            Geant4Threads=1,
            Geant4MacroName="run.mac",
            Geant4EnableVisualization=False,
            MultiSolverEnabled=False,
            MultiSolverBackends=["OpenFOAM", "Elmer"],
            SoftRuntimeWarningSeconds=0,
            MaxRuntimeSeconds=0,
            StallTimeoutSeconds=0,
            MinProgressPercent=0.0,
            AbortOnThreshold=True,
        )

        solver_panel = self.TaskSolver(solver_obj)
        solver_panel.chk_multi_solver.setChecked(True)
        solver_panel.chk_multi_openfoam.setChecked(True)
        solver_panel.chk_multi_elmer.setChecked(True)
        solver_panel.chk_multi_geant4.setChecked(True)
        solver_panel.sp_runtime_soft.setValue(120)
        solver_panel.sp_runtime_max.setValue(300)
        solver_panel.sp_runtime_stall.setValue(90)
        solver_panel.sp_runtime_progress.setValue(12.5)
        solver_panel.chk_abort_threshold.setChecked(False)
        solver_panel._store()

        self.assertTrue(solver_obj.MultiSolverEnabled)
        self.assertEqual(solver_obj.MultiSolverBackends, ["OpenFOAM", "Elmer", "Geant4"])
        self.assertEqual(solver_obj.SoftRuntimeWarningSeconds, 120)
        self.assertEqual(solver_obj.MaxRuntimeSeconds, 300)
        self.assertEqual(solver_obj.StallTimeoutSeconds, 90)
        self.assertAlmostEqual(solver_obj.MinProgressPercent, 12.5, places=3)
        self.assertFalse(solver_obj.AbortOnThreshold)

    def test_inlet_panel_publishes_validation_metadata_for_missing_setup(self):
        inlet_obj = types.SimpleNamespace(
            References=[],
            PropertiesList=["References"],
            InletType="Mass Flow Rate",
            Ux=0.0,
            Uy=0.0,
            Uz=0.0,
            NormalToFace=True,
            MassFlowRate=0.0,
            VolFlowRate=0.0,
            TurbulenceSpec="Intensity & Length Scale",
            TurbulenceIntensity=5.0,
            InletTemperature=300.0,
            Label="Mass Inlet",
        )

        inlet_panel = self.TaskBCInlet(inlet_obj)
        self.assertEqual(inlet_panel.taskview_validation_level, "incomplete")
        self.assertEqual(inlet_panel.taskview_validation_title, "Assign inlet faces")
        self.assertIn("boundary faces", inlet_panel.taskview_validation_detail)

        referenced_obj = types.SimpleNamespace(Label="Body")
        inlet_obj.References = [(referenced_obj, ["Face1"])]
        inlet_panel = self.TaskBCInlet(inlet_obj)
        self.assertEqual(inlet_panel.taskview_validation_level, "incomplete")
        self.assertEqual(inlet_panel.taskview_validation_title, "Mass flow rate required")
        self.assertIn("positive mass flow rate", inlet_panel.taskview_validation_detail)

    def test_open_boundary_panel_publishes_selection_validation_and_store_roundtrip(self):
        open_obj = types.SimpleNamespace(
            References=[],
            PropertiesList=["References"],
            FarFieldPressure=101325.0,
            FarFieldTemperature=293.15,
            FarFieldVelocityX=0.0,
            FarFieldVelocityY=0.0,
            FarFieldVelocityZ=0.0,
            Label="Exterior",
        )

        open_panel = self.TaskBCOpen(open_obj)
        self.assertEqual(open_panel.taskview_validation_level, "incomplete")
        self.assertEqual(open_panel.taskview_validation_title, "Assign open-boundary faces")
        self.assertIn("exterior faces", open_panel.taskview_validation_detail)

        referenced_obj = types.SimpleNamespace(Label="Enclosure")
        open_obj.References = [(referenced_obj, ["Face3"])]
        open_panel = self.TaskBCOpen(open_obj)
        self.assertEqual(open_panel.taskview_summary_title, "Open Boundary")
        self.assertEqual(open_panel.taskview_validation_level, "")

        open_panel.sp_vx.setValue(14.0)
        open_panel.sp_T.setValue(305.0)
        open_panel._store()

        self.assertAlmostEqual(open_obj.FarFieldVelocityX, 14.0, places=6)
        self.assertAlmostEqual(open_obj.FarFieldTemperature, 305.0, places=6)

    def test_outlet_panel_publishes_validation_metadata_and_stores_mass_flow_rate(self):
        outlet_obj = types.SimpleNamespace(
            References=[],
            PropertiesList=["References"],
            OutletType="Mass Flow Rate",
            StaticPressure=0.0,
            OutletMassFlowRate=0.0,
            PreventBackflow=True,
            Label="Outlet",
        )

        outlet_panel = self.TaskBCOutlet(outlet_obj)
        self.assertEqual(outlet_panel.taskview_validation_level, "incomplete")
        self.assertEqual(outlet_panel.taskview_validation_title, "Assign outlet faces")

        referenced_obj = types.SimpleNamespace(Label="Body")
        outlet_obj.References = [(referenced_obj, ["Face6"])]
        outlet_panel = self.TaskBCOutlet(outlet_obj)
        self.assertEqual(outlet_panel.taskview_validation_title, "Outlet mass flow rate required")
        self.assertIn("positive outlet mass flow rate", outlet_panel.taskview_validation_detail)

        outlet_panel.sp_mfr.setValue(0.25)
        outlet_panel.chk_backflow.setChecked(False)
        outlet_panel._store()

        self.assertAlmostEqual(outlet_obj.OutletMassFlowRate, 0.25, places=6)
        self.assertFalse(outlet_obj.PreventBackflow)

    def test_wall_panel_publishes_validation_metadata_for_missing_thermal_inputs(self):
        wall_obj = types.SimpleNamespace(
            References=[],
            PropertiesList=["References"],
            WallType="Rough Wall",
            ThermalType="Heat Transfer Coefficient",
            WallTemperature=293.15,
            HeatFlux=0.0,
            HeatTransferCoeff=0.0,
            RoughnessHeight=0.0,
            Label="Wall",
        )

        wall_panel = self.TaskBCWall(wall_obj)
        self.assertEqual(wall_panel.taskview_validation_level, "incomplete")
        self.assertEqual(wall_panel.taskview_validation_title, "Assign wall faces")

        referenced_obj = types.SimpleNamespace(Label="Body")
        wall_obj.References = [(referenced_obj, ["Face1"])]
        wall_panel = self.TaskBCWall(wall_obj)
        self.assertEqual(wall_panel.taskview_validation_title, "Heat-transfer coefficient required")

        wall_panel.sp_htc.setValue(42.0)
        wall_panel._store()
        self.assertAlmostEqual(wall_obj.HeatTransferCoeff, 42.0, places=6)

        wall_obj.HeatTransferCoeff = 42.0
        wall_panel = self.TaskBCWall(wall_obj)
        self.assertEqual(wall_panel.taskview_validation_title, "Wall roughness required")

    def test_initial_conditions_panel_publishes_validation_metadata_and_store_roundtrip(self):
        initial_obj = types.SimpleNamespace(
            References=[],
            PropertiesList=["References"],
            Ux=0.0,
            Uy=0.0,
            Uz=0.0,
            Pressure=0.0,
            Temperature=293.15,
            TurbulentKineticEnergy=0.001,
            SpecificDissipationRate=1.0,
            UsePotentialFlow=False,
            Label="Initial State",
        )

        initial_panel = self.TaskInitialConditions(initial_obj)
        self.assertEqual(initial_panel.taskview_validation_level, "incomplete")
        self.assertEqual(initial_panel.taskview_validation_title, "Assign target regions")

        referenced_obj = types.SimpleNamespace(Label="Fluid Domain")
        initial_obj.References = [(referenced_obj, ["Solid1"])]
        initial_obj.Temperature = -5.0
        initial_panel = self.TaskInitialConditions(initial_obj)
        self.assertEqual(initial_panel.taskview_validation_title, "Initial temperature required")

        initial_panel.sp_T.setValue(310.0)
        initial_panel.sp_ux.setValue(4.0)
        initial_panel.chk_pot.setChecked(True)
        initial_panel._store()

        self.assertAlmostEqual(initial_obj.Temperature, 310.0, places=6)
        self.assertAlmostEqual(initial_obj.Ux, 4.0, places=6)
        self.assertTrue(initial_obj.UsePotentialFlow)

    def test_physics_model_validation_and_store_roundtrip(self):
        obj = types.SimpleNamespace(
            FlowRegime="Turbulent",
            TurbulenceModel="kOmegaSST",
            Compressibility="Incompressible",
            TimeModel="Steady",
            Gravity=False,
            HeatTransfer=False,
            Buoyancy=False,
            FreeSurface=False,
            PassiveScalar=False,
            Label="Physics",
        )

        panel = self.TaskPhysicsModel(obj)
        panel.chk_buoy.setChecked(True)
        self.assertEqual(panel.taskview_validation_title, "Buoyancy needs gravity")

        panel.chk_gravity.setChecked(True)
        self.assertEqual(panel.taskview_validation_title, "Buoyancy usually needs heat transfer")

        panel.chk_heat.setChecked(True)
        panel.cb_flow.setCurrentIndex(panel.cb_flow.findText("Laminar"))
        panel.cb_turb.setCurrentIndex(panel.cb_turb.findText("kEpsilon"))
        self.assertEqual(panel.taskview_validation_title, "Laminar flow selected")

        panel.chk_scalar.setChecked(True)
        panel._store()
        self.assertEqual(obj.FlowRegime, "Laminar")
        self.assertTrue(obj.Gravity)
        self.assertTrue(obj.HeatTransfer)
        self.assertTrue(obj.PassiveScalar)

    def test_fluid_material_panel_publishes_validation_metadata_for_missing_setup(self):
        fluid_obj = types.SimpleNamespace(
            References=[],
            PropertiesList=["References"],
            Preset="Custom",
            Density=0.0,
            DynamicViscosity=1.0e-3,
            KinematicViscosity=1.0e-6,
            SpecificHeat=1000.0,
            ThermalConductivity=0.1,
            PrandtlNumber=1.0,
            Label="Fluid",
        )

        fluid_panel = self.TaskFluidMaterial(fluid_obj)
        self.assertEqual(fluid_panel.taskview_validation_level, "incomplete")
        self.assertEqual(fluid_panel.taskview_validation_title, "Assign fluid regions")

        referenced_obj = types.SimpleNamespace(Label="Domain")
        fluid_obj.References = [(referenced_obj, ["Solid1"])]
        fluid_panel = self.TaskFluidMaterial(fluid_obj)
        self.assertEqual(fluid_panel.taskview_validation_title, "Fluid density required")

    def test_generic_bc_validation_for_missing_targets_and_invalid_thermal_values(self):
        bc_obj = types.SimpleNamespace(
            References=[],
            PropertiesList=["References", "Temperature"],
            FlowType="FlowStudio::BCTemperature",
            BCLabel="Temperature",
            Temperature=-1.0,
            Label="Temperature BC",
        )

        panel = self.TaskGenericBC(bc_obj)
        self.assertEqual(panel.taskview_validation_title, "Assign boundary targets")

        target = types.SimpleNamespace(Label="Wall")
        bc_obj.References = [(target, ["Face1"])]
        panel = self.TaskGenericBC(bc_obj)
        self.assertEqual(panel.taskview_validation_title, "Temperature temperature required")

        panel._widgets["Temperature"].setValue(320.0)
        panel._store()
        self.assertAlmostEqual(bc_obj.Temperature, 320.0, places=6)

    def test_material_panel_publishes_validation_metadata_for_missing_targets(self):
        material_obj = types.SimpleNamespace(
            References=[],
            PropertiesList=["References", "MaterialPreset", "MaterialName", "Density", "ThermalConductivity", "SpecificHeat", "Emissivity"],
            FlowType="FlowStudio::ThermalMaterial",
            MaterialPreset="Custom",
            MaterialName="",
            Density=7850.0,
            ThermalConductivity=50.0,
            SpecificHeat=500.0,
            Emissivity=0.3,
            Label="Thermal Material",
        )

        material_panel = self.TaskMaterial(material_obj)
        self.assertEqual(material_panel.taskview_validation_level, "incomplete")
        self.assertEqual(material_panel.taskview_validation_title, "Assign material targets")

        referenced_obj = types.SimpleNamespace(Label="Housing")
        material_obj.References = [(referenced_obj, ["Solid1"])]
        material_panel = self.TaskMaterial(material_obj)
        self.assertEqual(material_panel.taskview_validation_title, "Material name required")

    def test_post_pipeline_panel_publishes_validation_metadata_for_missing_or_invalid_ranges(self):
        post_obj = types.SimpleNamespace(
            VisualizationType="Contour (Surface)",
            AvailableFields=[],
            ActiveField="U",
            AutoRange=True,
            MinRange=0.0,
            MaxRange=1.0,
            ResultFile="",
            Label="Results",
        )

        post_panel = self.TaskPostPipeline(post_obj)
        self.assertEqual(post_panel.taskview_validation_level, "info")
        self.assertEqual(post_panel.taskview_validation_title, "Load results to begin post-processing")

        post_obj.ResultFile = "C:/tmp/case.vtk"
        post_obj.AvailableFields = ["U", "p"]
        post_obj.ActiveField = "T"
        post_panel = self.TaskPostPipeline(post_obj)
        self.assertEqual(post_panel.taskview_validation_title, "Active field is not available")

        post_obj.ActiveField = "U"
        post_obj.AutoRange = False
        post_obj.MinRange = 5.0
        post_obj.MaxRange = 1.0
        post_panel = self.TaskPostPipeline(post_obj)
        self.assertEqual(post_panel.taskview_validation_title, "Manual range is invalid")

    def test_mesh_panel_publishes_validation_metadata_for_invalid_ranges(self):
        mesh_obj = types.SimpleNamespace(
            CharacteristicLength=5.0,
            MinElementSize=10.0,
            MaxElementSize=2.0,
            Algorithm3D="Delaunay",
            ElementOrder="1st Order",
            ElementType="Tetrahedral",
            GrowthRate=1.2,
            CellsInGap=3,
            MeshFormat="GMSH (.msh)",
            NumCells=0,
            Label="Demo Mesh",
        )

        mesh_panel = self.TaskMeshGmsh(mesh_obj)
        self.assertEqual(mesh_panel.taskview_validation_level, "warning")
        self.assertEqual(mesh_panel.taskview_validation_title, "Minimum size exceeds maximum size")
        self.assertIn("increase the maximum element size", mesh_panel.taskview_validation_detail)

    def test_fluid_material_preset_populates_widgets_and_store(self):
        obj = types.SimpleNamespace(
            References=[],
            PropertiesList=["References"],
            Preset="Custom",
            Density=1.0,
            DynamicViscosity=1.0e-3,
            KinematicViscosity=1.0e-6,
            SpecificHeat=1000.0,
            ThermalConductivity=0.1,
            PrandtlNumber=1.0,
        )

        panel = self.TaskFluidMaterial(obj)
        panel._on_preset_changed("Water (20°C)")

        expected = self.MATERIALS_DB["Water (20°C)"]
        self.assertAlmostEqual(panel.sp_rho.value(), expected["Density"], places=3)
        self.assertAlmostEqual(panel.sp_mu.value(), expected["DynamicViscosity"], places=7)

        panel.cb_preset.setCurrentIndex(panel.cb_preset.findText("Water (20°C)"))
        panel.sp_cp.setValue(4200.0)
        panel._store()

        self.assertEqual(obj.Preset, "Water (20°C)")
        self.assertAlmostEqual(obj.Density, expected["Density"], places=3)
        self.assertAlmostEqual(obj.SpecificHeat, 4200.0, places=1)

    def test_measurement_point_toggle_and_store_roundtrip(self):
        obj = types.SimpleNamespace(
            Label2="Probe",
            ProbeLocation=self.FreeCAD.Vector(1, 2, 3),
            UseLine=False,
            LineStart=self.FreeCAD.Vector(0, 0, 0),
            LineEnd=self.FreeCAD.Vector(10, 0, 0),
            LineResolution=10,
            SampleFields=["U", "p"],
            ExportCSV=False,
            TimeSeries=False,
        )

        panel = self.TaskMeasurementPoint(obj)
        self.assertEqual(panel.taskview_validation_title, "")
        self.assertFalse(panel.grp_line.isEnabled())

        panel.chk_line.setChecked(True)
        self.assertTrue(panel.grp_line.isEnabled())

        panel.le_fields.setText("")
        self.assertEqual(panel.taskview_validation_title, "Select sampled fields")

        panel.le_fields.setText("U")
        panel.sp_sx.setValue(1.0)
        panel.sp_sy.setValue(2.0)
        panel.sp_sz.setValue(3.0)
        panel.sp_ex.setValue(1.0)
        panel.sp_ey.setValue(2.0)
        panel.sp_ez.setValue(3.0)
        self.assertEqual(panel.taskview_validation_title, "Line probe needs distinct endpoints")

        panel.sp_ex.setValue(25.0)
        self.assertEqual(panel.taskview_validation_title, "")

        panel.le_desc.setText("Centerline Probe")
        panel.sp_px.setValue(4.5)
        panel.sp_py.setValue(5.5)
        panel.sp_pz.setValue(6.5)
        panel.sp_ex.setValue(25.0)
        panel.sp_res.setValue(64)
        panel.le_fields.setText("U, p, T")
        panel.chk_csv.setChecked(True)
        panel.chk_ts.setChecked(True)
        panel._store()

        self.assertEqual(obj.Label2, "Centerline Probe")
        self.assertTrue(obj.UseLine)
        self.assertEqual(obj.SampleFields, ["U", "p", "T"])
        self.assertTrue(obj.ExportCSV)
        self.assertTrue(obj.TimeSeries)
        self.assertAlmostEqual(obj.ProbeLocation.x, 4.5, places=6)
        self.assertAlmostEqual(obj.ProbeLocation.y, 5.5, places=6)
        self.assertAlmostEqual(obj.ProbeLocation.z, 6.5, places=6)
        self.assertAlmostEqual(obj.LineEnd.x, 25.0, places=6)
        self.assertEqual(obj.LineResolution, 64)

    def test_measurement_surface_validation_and_store_roundtrip(self):
        obj = types.SimpleNamespace(
            Label2="Surface",
            SurfaceType="Iso-Surface",
            PlaneOrigin=self.FreeCAD.Vector(0, 0, 0),
            PlaneNormal="Custom",
            CustomNormal=self.FreeCAD.Vector(1, 0, 0),
            IsoField="p",
            IsoValue=0.0,
            FaceRefs=[],
            SampleFields=["U", "p"],
            ComputeAverage=True,
            ComputeIntegral=False,
            ComputeMassFlow=False,
            ComputeForce=False,
            ForceRefPoint=self.FreeCAD.Vector(0, 0, 0),
            ExportCSV=True,
            ExportVTK=False,
            TimeSeries=False,
        )

        panel = self.TaskMeasurementSurface(obj)
        panel.le_fields.setText("")
        self.assertEqual(panel.taskview_validation_title, "Select sampled fields")

        panel.le_fields.setText("U")
        panel.le_isofield.setText("")
        self.assertEqual(panel.taskview_validation_title, "Iso field required")

        panel.le_isofield.setText("p")
        panel.chk_avg.setChecked(False)
        panel.chk_integ.setChecked(False)
        panel.chk_mflow.setChecked(False)
        panel.chk_force.setChecked(False)
        self.assertEqual(panel.taskview_validation_title, "Select an evaluation output")

        panel.chk_force.setChecked(True)
        panel._store()
        self.assertEqual(obj.SampleFields, ["U"])
        self.assertTrue(obj.ComputeForce)

    def test_measurement_volume_validation_and_store_roundtrip(self):
        obj = types.SimpleNamespace(
            Label2="Volume",
            VolumeType="Threshold (field-based)",
            BoxMin=self.FreeCAD.Vector(-1, -1, -1),
            BoxMax=self.FreeCAD.Vector(1, 1, 1),
            SphereCenter=self.FreeCAD.Vector(0, 0, 0),
            SphereRadius=10.0,
            CylinderCenter=self.FreeCAD.Vector(0, 0, 0),
            CylinderAxis=self.FreeCAD.Vector(0, 0, 1),
            CylinderRadius=5.0,
            CylinderHeight=10.0,
            ThresholdField="p",
            ThresholdMin=0.0,
            ThresholdMax=1.0,
            SampleFields=["U", "p"],
            ComputeAverage=True,
            ComputeMinMax=True,
            ComputeIntegral=False,
            ExportCSV=True,
            TimeSeries=False,
        )

        panel = self.TaskMeasurementVolume(obj)
        panel.le_fields.setText("")
        self.assertEqual(panel.taskview_validation_title, "Select sampled fields")

        panel.le_fields.setText("U")
        panel.le_thrfield.setText("")
        self.assertEqual(panel.taskview_validation_title, "Threshold field required")

        panel.le_thrfield.setText("T")
        panel.sp_thrmin.setValue(5.0)
        panel.sp_thrmax.setValue(1.0)
        self.assertEqual(panel.taskview_validation_title, "Threshold range is invalid")

        panel.sp_thrmax.setValue(9.0)
        panel._store()
        self.assertEqual(obj.SampleFields, ["U"])
        self.assertEqual(obj.ThresholdField, "T")
        self.assertAlmostEqual(obj.ThresholdMax, 9.0, places=6)

    def test_fan_preset_populates_display_only_curve_table_and_store(self):
        obj = types.SimpleNamespace(
            References=[],
            PropertiesList=["References"],
            FanType="Internal Fan",
            FanCurvePreset="User Defined",
            ReferencePressure=101325.0,
            CreateAssociatedGoals=False,
        )

        panel = self.TaskFan(obj)
        self.assertEqual(panel.curve_table.editTriggers(), QtGui.QAbstractItemView.NoEditTriggers)

        preset_name = next(name for name in sorted(panel.fan_database) if panel.fan_database[name].get("curve"))
        preset = panel.fan_database[preset_name]
        panel.cb_curve.setCurrentIndex(panel.cb_curve.findText(preset_name))

        self.assertGreater(panel.curve_table.rowCount(), 0)
        if "ReferencePressure" in preset:
            self.assertAlmostEqual(panel.sp_p.value(), float(preset["ReferencePressure"]), places=3)
        if "FanType" in preset:
            self.assertEqual(panel.cb_type.currentText(), str(preset["FanType"]))

        panel.chk_goals.setChecked(True)
        panel._store()

        self.assertEqual(obj.FanCurvePreset, preset_name)
        self.assertTrue(obj.CreateAssociatedGoals)

    def test_result_plot_validation_and_store_roundtrip(self):
        selected = types.SimpleNamespace(Label="Wall")
        obj = types.SimpleNamespace(
            References=[],
            PropertiesList=["References"],
            PlotKind="Surface Plot",
            Field="Pressure",
            ContourCount=10,
            Contours=True,
            Isolines=False,
            Vectors=False,
            Streamlines=False,
            CutPlane="XY Plane",
            PlaneOffset=0.0,
            UseCADGeometry=True,
            Interpolate=True,
            ExportExcel=False,
            Label="Pressure Plot",
        )

        panel = self.TaskResultPlot(obj)
        self.assertEqual(panel.taskview_validation_title, "Assign plot targets")

        obj.References = [(selected, ["Face1"])]
        panel = self.TaskResultPlot(obj)
        panel.chk_contours.setChecked(False)
        panel.chk_isolines.setChecked(False)
        panel.chk_vectors.setChecked(False)
        panel.chk_streamlines.setChecked(False)
        self.assertEqual(panel.taskview_validation_title, "Enable a display mode")

        panel.chk_vectors.setChecked(True)
        panel.cb_field.setCurrentIndex(panel.cb_field.findText("Velocity"))
        panel._store()
        self.assertEqual(obj.Field, "Velocity")
        self.assertTrue(obj.Vectors)

    def test_particle_study_validation_and_store_roundtrip(self):
        injection = types.SimpleNamespace(Label="Inlet")
        obj = types.SimpleNamespace(
            Injections=[],
            PropertiesList=["Injections"],
            Accretion=False,
            Erosion=False,
            Gravity=True,
            GravityVector=self.FreeCAD.Vector(0, 0, 0),
            ParticleShape="Spheres",
            ParticleDiameter=0.004,
            ColorByField="Pressure",
            TrackLength=10.0,
            TrackTime=3600.0,
            MaxParticles=50000,
            Label="Particles",
        )

        panel = self.TaskParticleStudy(obj)
        self.assertEqual(panel.taskview_validation_title, "Assign particle injections")

        obj.Injections = [(injection, ["Face1"])]
        panel = self.TaskParticleStudy(obj)
        self.assertEqual(panel.taskview_validation_title, "Gravity vector is zero")

        panel.sp_gy.setValue(-9.81)
        panel.sp_d.setValue(0.0)
        self.assertEqual(panel.taskview_validation_title, "Particle diameter required")

        panel.sp_d.setValue(0.002)
        panel.sp_len.setValue(5.0)
        panel.sp_time.setValue(60.0)
        panel.chk_acc.setChecked(True)
        panel._store()

        self.assertTrue(obj.Accretion)
        self.assertAlmostEqual(obj.ParticleDiameter, 0.002, places=6)
        self.assertAlmostEqual(obj.TrackTime, 60.0, places=6)

    def test_material_preset_updates_name_and_persists_dynamic_values(self):
        obj = types.SimpleNamespace(
            References=[],
            PropertiesList=["References", "MaterialPreset", "MaterialName", "Density", "ThermalConductivity", "SpecificHeat", "Emissivity"],
            FlowType="FlowStudio::ThermalMaterial",
            MaterialPreset="Custom",
            MaterialName="Material",
            Density=5000.0,
            ThermalConductivity=10.0,
            SpecificHeat=100.0,
            Emissivity=0.5,
        )

        panel = self.TaskMaterial(obj)
        panel._on_preset_changed("Copper")
        self.assertIn("Copper", panel.le_name.text())
        self.assertGreater(panel._widgets["ThermalConductivity"].value(), 100.0)

        panel.cb_preset.setCurrentIndex(panel.cb_preset.findText("Copper"))
        panel._widgets["Emissivity"].setValue(0.12)
        panel._store()

        self.assertEqual(obj.MaterialPreset, "Copper")
        self.assertAlmostEqual(obj.Emissivity, 0.12, places=3)
        self.assertIn("Copper", obj.MaterialName)

    def test_geant4_result_panel_validation_and_store_roundtrip(self):
        obj = types.SimpleNamespace(
            ResultFile="",
            SummaryFile="",
            PrimaryQuantity="dose",
            ScoringResults=[],
            DetectorResults=[],
            AvailableFields=[],
            ActiveField="dose",
            MonitorNames=[],
            ArtifactFiles=[],
            ImportNotes="",
            Label="Geant4 Result",
        )

        panel = self.TaskGeant4Result(obj)
        self.assertEqual(panel.taskview_validation_title, "Import a Geant4 result")

        obj.ResultFile = "C:/tmp/result.json"
        obj.AvailableFields = ["dose", "energy"]
        obj.ActiveField = "fluence"
        panel = self.TaskGeant4Result(obj)
        self.assertEqual(panel.taskview_validation_title, "Selected field is unavailable")

        panel.cb_field.setCurrentIndex(panel.cb_field.findText("energy"))
        panel._store()
        self.assertEqual(obj.ActiveField, "energy")

    def test_geant4_result_component_validation_for_missing_parent_and_fields(self):
        scoring_parent = types.SimpleNamespace(Label="Parent Result")
        scoring_obj = types.SimpleNamespace(
            FlowType="FlowStudio::Geant4ScoringResult",
            ParentResult=None,
            ScoreQuantity="dose",
            ScoringType="mesh",
            BinShape="xyz",
            AvailableFields=[],
            ActiveField="dose",
            ReferenceTargets=[],
            ArtifactFiles=[],
            ImportNotes="",
            Label="Dose Mesh",
        )

        panel = self.TaskGeant4ResultComponent(scoring_obj)
        self.assertEqual(panel.taskview_validation_title, "Parent Geant4 result missing")

        scoring_obj.ParentResult = scoring_parent
        panel = self.TaskGeant4ResultComponent(scoring_obj)
        self.assertEqual(panel.taskview_validation_title, "No scoring fields available")

        scoring_obj.AvailableFields = ["dose", "energy"]
        scoring_obj.ActiveField = "fluence"
        panel = self.TaskGeant4ResultComponent(scoring_obj)
        self.assertEqual(panel.taskview_validation_title, "Selected field is unavailable")

        scoring_obj.ActiveField = "dose"
        scoring_obj.ArtifactFiles = ["dose.csv"]
        panel = self.TaskGeant4ResultComponent(scoring_obj)
        self.assertEqual(panel.taskview_validation_title, "Geant4 component ready")

    def test_geometry_tools_check_and_toggle_volume_runtime(self):
        fake_obj = types.SimpleNamespace(
            Name="Box001",
            Label="Box",
            Shape=types.SimpleNamespace(Solids=[object()]),
        )
        fake_doc = types.SimpleNamespace(getObject=lambda name: fake_obj if name == "Box001" else None)
        fake_result = types.SimpleNamespace(
            status="SUCCESSFUL",
            analysis_type="Internal",
            fluid_volume=0.125,
            solid_volume=1.0,
            objects=[types.SimpleNamespace(label="Box", solids=1, shells=0, faces=6, volume=1.0)],
            issues=[],
        )
        visible = {"state": False}

        def _create_volume(_result):
            visible["state"] = True

        def _hide_volume():
            visible["state"] = False

        with mock.patch.object(self.FreeCAD, "ActiveDocument", fake_doc), \
             mock.patch.object(_task_geometry_tools_mod, "iter_geometry_objects", return_value=[fake_obj]), \
             mock.patch.object(_task_geometry_tools_mod, "check_geometry", return_value=fake_result), \
             mock.patch.object(_task_geometry_tools_mod, "fluid_volume_is_visible", side_effect=lambda: visible["state"]), \
             mock.patch.object(_task_geometry_tools_mod, "create_or_update_fluid_volume", side_effect=_create_volume), \
             mock.patch.object(_task_geometry_tools_mod, "hide_fluid_volume", side_effect=_hide_volume):
            panel = self.TaskCheckGeometry()
            self.assertEqual(panel.state_tree.topLevelItemCount(), 1)
            self.assertEqual(panel.btn_volume.text(), "Show Fluid Volume")
            self.assertEqual(panel.state_tree.topLevelItem(0).checkState(0), _task_geometry_tools_mod.QtCore.Qt.Checked)
            self.assertEqual(panel.taskview_validation_title, "Run geometry check")

            panel.state_tree.topLevelItem(0).setCheckState(0, _task_geometry_tools_mod.QtCore.Qt.Unchecked)
            self.assertEqual(panel.taskview_validation_title, "Select geometry to analyze")

            panel.state_tree.topLevelItem(0).setCheckState(0, _task_geometry_tools_mod.QtCore.Qt.Checked)
            self.assertEqual(panel.taskview_validation_title, "Run geometry check")

            panel._check()
            self.assertIn("Status: SUCCESSFUL", panel.results.toPlainText())
            self.assertIn("All checked bodies look closed enough for setup.", panel.results.toPlainText())
            self.assertEqual(panel.taskview_validation_title, "Geometry looks ready")

            panel._toggle_volume()
            self.assertEqual(panel.btn_volume.text(), "Hide Fluid Volume")

            panel._toggle_volume()
            self.assertEqual(panel.btn_volume.text(), "Show Fluid Volume")

    def test_leak_tracking_selection_and_find_runtime(self):
        refs = [("internal", "Face1"), ("external", "Face9")]

        with mock.patch.object(_task_geometry_tools_mod, "selected_face_refs", return_value=refs), \
             mock.patch.object(_task_geometry_tools_mod, "describe_face_ref", side_effect=lambda ref: f"DESC:{ref[0]}:{ref[1]}"), \
             mock.patch.object(_task_geometry_tools_mod, "run_leak_tracking", return_value={"status": "FOUND", "messages": ["Connected via Body001"]}):
            panel = self.TaskLeakTracking()
            self.assertEqual(panel.face_a_list.item(0).text(), "DESC:internal:Face1")
            self.assertEqual(panel.face_b_list.item(0).text(), "DESC:external:Face9")
            self.assertEqual(panel.taskview_validation_title, "Ready to find connection")

            panel._find_connection()
            self.assertIn("Status: FOUND", panel.results.toPlainText())
            self.assertIn("Connected via Body001", panel.results.toPlainText())

    def test_leak_tracking_panel_flags_missing_or_duplicate_faces(self):
        with mock.patch.object(_task_geometry_tools_mod, "selected_face_refs", return_value=[]), \
             mock.patch.object(_task_geometry_tools_mod, "describe_face_ref", side_effect=lambda ref: f"DESC:{ref[0]}:{ref[1]}"):
            panel = self.TaskLeakTracking()
            self.assertEqual(panel.taskview_validation_title, "Select internal and external faces")

            panel.face_a = ("internal", "Face1")
            panel.face_b = ("internal", "Face1")
            panel._refresh()
            self.assertEqual(panel.taskview_validation_title, "Faces must be different")

    def test_enterprise_jobs_panel_refresh_filter_and_details_runtime(self):
        summary_dir = tempfile.mkdtemp(prefix="flowstudio-geant4-summary-")
        summary_path = os.path.join(summary_dir, "flowstudio_geant4_result_summary.json")
        with open(summary_path, "w", encoding="utf-8") as handle:
            handle.write("{}")

        summaries = [
            {
                "run_id": "RUN-001",
                "state": "completed",
                "target_ref": "Study::Demo",
                "adapter_id": "elmer-local",
                "study_id": "study-1",
                "run_directory": "C:/tmp/run-1",
            }
        ]
        adapter_rows = [
            {
                "adapter_id": "elmer-local",
                "display_name": "Elmer Local",
                "family": "Elmer",
                "version": "9.0",
                "commercial_core_safe": True,
                "supports_gpu": False,
                "supports_remote": False,
                "supports_parallel": True,
                "supports_transient": True,
                "experimental": False,
                "supported_solver_versions": ("9.0",),
                "supported_physics": ("thermal",),
                "feature_flags": {"mpi": True},
                "notes": "validated",
            },
            {
                "adapter_id": "openfoam-remote",
                "display_name": "OpenFOAM Remote",
                "family": "OpenFOAM",
                "version": "11",
                "commercial_core_safe": True,
                "supports_gpu": False,
                "supports_remote": True,
                "supports_parallel": True,
                "supports_transient": True,
                "experimental": False,
                "supported_solver_versions": ("11",),
                "supported_physics": ("cfd",),
                "feature_flags": {"cluster": True},
                "notes": "remote",
            },
        ]

        job_service = types.SimpleNamespace(
            persisted_run_summaries=lambda: summaries,
            adapter_capability_matrix=lambda: adapter_rows,
            persisted_run_record=lambda run_id: {"run_id": run_id, "state": "completed", "target_ref": "Study::Demo", "adapter_id": "elmer-local"},
            persisted_run_result=lambda run_id: {"result_ref": f"result-{run_id}", "artifact_manifest": {"result_summary": summary_path}},
            persisted_run_events=lambda run_id: [{"event": "submitted"}, {"event": "finished"}],
            persisted_execution_log=lambda run_id: f"log for {run_id}",
            run_directory=lambda run_id: "C:/tmp/run-1",
            create_support_bundle=lambda run_id, path: path,
        )
        runtime = types.SimpleNamespace(job_service=job_service)

        panel = self.EnterpriseJobsPanel(runtime)
        self.assertEqual(panel.table.rowCount(), 1)
        self.assertEqual(panel.adapter_table.rowCount(), 2)
        self.assertTrue(panel.import_geant4_button.isEnabled())
        self.assertIn("reopened as a native Geant4 result", panel.result_status_banner.text())
        self.assertEqual(panel.taskview_summary_title, "Enterprise Jobs")
        self.assertIn("Selected run: RUN-001", panel.taskview_summary_detail)
        self.assertEqual(panel.taskview_validation_level, "info")
        self.assertEqual(panel.taskview_validation_title, "Native Geant4 result available")

        panel.table.selectRow(0)
        panel._update_details()
        self.assertIn("RUN-001", panel.details.toPlainText())
        self.assertIn('"kind": "geant4-native-import"', panel.details.toPlainText())
        self.assertIn('"available": true', panel.details.toPlainText().lower())
        self.assertIn(summary_path, panel.result_status_banner.text())

        panel.adapter_search.setText("openfoam")
        self.assertEqual(panel.adapter_table.rowCount(), 1)
        self.assertIn("OpenFOAM Remote", panel.adapter_table.item(0, 0).text())
        self.assertIn("1 adapter row(s) visible", panel.taskview_summary_detail)

        panel._copy_selected_path()
        self.assertEqual(QtGui.QApplication.clipboard().text(), "C:/tmp/run-1")

        panel._copy_adapter_matrix_json()
        self.assertIn("openfoam-remote", QtGui.QApplication.clipboard().text().lower())

        imported = []
        with mock.patch.object(_jobs_panel_mod, "get_active_analysis", return_value=types.SimpleNamespace(Name="ActiveAnalysis")), \
             mock.patch.object(_jobs_panel_mod.FreeCAD, "ActiveDocument", types.SimpleNamespace(Name="ActiveDoc"), create=True), \
             mock.patch.object(_jobs_panel_mod.FreeCADGui, "ActiveDocument", types.SimpleNamespace(setEdit=lambda *_args, **_kwargs: None), create=True), \
             mock.patch("flow_studio.feminout.importFlowStudio.open_geant4_summary", side_effect=lambda path, doc=None, analysis=None: imported.append((path, doc, analysis)) or types.SimpleNamespace(Name="ImportedGeant4Result")):
            panel._open_selected_result()

        self.assertEqual(imported[0][0], summary_path)
        self.assertEqual(imported[0][1].Name, "ActiveDoc")
        self.assertEqual(imported[0][2].Name, "ActiveAnalysis")

    def test_enterprise_jobs_panel_publishes_empty_state_taskview_metadata(self):
        job_service = types.SimpleNamespace(
            persisted_run_summaries=lambda: [],
            adapter_capability_matrix=lambda: [],
            persisted_run_record=lambda _run_id: {},
            persisted_run_result=lambda _run_id: {},
            persisted_run_events=lambda _run_id: [],
            persisted_execution_log=lambda _run_id: "",
            run_directory=lambda _run_id: "",
            create_support_bundle=lambda _run_id, path: path,
        )
        runtime = types.SimpleNamespace(job_service=job_service)

        panel = self.EnterpriseJobsPanel(runtime)
        self.assertEqual(panel.taskview_summary_title, "Enterprise Jobs")
        self.assertIn("0 run(s) loaded", panel.taskview_summary_detail)
        self.assertEqual(panel.taskview_validation_level, "info")
        self.assertEqual(panel.taskview_validation_title, "No persisted enterprise runs")
        self.assertIn("populate this history view", panel.taskview_validation_detail)

    def test_engineering_database_editor_shows_and_reuses_dialog(self):
        editor = self.EngineeringDatabaseEditorModule

        dialog = editor.show_engineering_database_editor()
        self.assertTrue(dialog.isVisible())
        self.assertEqual(dialog.windowTitle(), "FlowStudio Engineering Database")

        same_dialog = editor.show_engineering_database_editor()
        self.assertIs(dialog, same_dialog)

        dialog.close()
        QtGui.QApplication.processEvents()


if __name__ == "__main__":
    unittest.main()