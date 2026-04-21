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
import types
import unittest
from unittest import mock


sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

try:
    from flow_studio.taskpanels import task_solver as _task_solver_mod
    from flow_studio.taskpanels import task_fluid_material as _task_fluid_material_mod
    from flow_studio.taskpanels import task_measurement_point as _task_measurement_point_mod
    from flow_studio.taskpanels import task_flowefd_features as _task_flowefd_features_mod
    from flow_studio.taskpanels import task_geometry_tools as _task_geometry_tools_mod
    from flow_studio.taskpanels import task_materials as _task_materials_mod
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
        cls.TaskMeasurementPoint = _task_measurement_point_mod.TaskMeasurementPoint
        cls.TaskFan = _task_flowefd_features_mod.TaskFan
        cls.TaskCheckGeometry = _task_geometry_tools_mod.TaskCheckGeometry
        cls.TaskLeakTracking = _task_geometry_tools_mod.TaskLeakTracking
        cls.TaskMaterial = _task_materials_mod.TaskMaterial
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
        self.assertFalse(panel.grp_line.isEnabled())

        panel.chk_line.setChecked(True)
        self.assertTrue(panel.grp_line.isEnabled())

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

            panel._check()
            self.assertIn("Status: SUCCESSFUL", panel.results.toPlainText())
            self.assertIn("All checked bodies look closed enough for setup.", panel.results.toPlainText())

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

            panel._find_connection()
            self.assertIn("Status: FOUND", panel.results.toPlainText())
            self.assertIn("Connected via Body001", panel.results.toPlainText())

    def test_enterprise_jobs_panel_refresh_filter_and_details_runtime(self):
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
            persisted_run_result=lambda run_id: {"result_ref": f"result-{run_id}"},
            persisted_run_events=lambda run_id: [{"event": "submitted"}, {"event": "finished"}],
            persisted_execution_log=lambda run_id: f"log for {run_id}",
            run_directory=lambda run_id: "C:/tmp/run-1",
            create_support_bundle=lambda run_id, path: path,
        )
        runtime = types.SimpleNamespace(job_service=job_service)

        panel = self.EnterpriseJobsPanel(runtime)
        self.assertEqual(panel.table.rowCount(), 1)
        self.assertEqual(panel.adapter_table.rowCount(), 2)

        panel.table.selectRow(0)
        panel._update_details()
        self.assertIn("RUN-001", panel.details.toPlainText())

        panel.adapter_search.setText("openfoam")
        self.assertEqual(panel.adapter_table.rowCount(), 1)
        self.assertIn("OpenFOAM Remote", panel.adapter_table.item(0, 0).text())

        panel._copy_selected_path()
        self.assertEqual(QtGui.QApplication.clipboard().text(), "C:/tmp/run-1")

        panel._copy_adapter_matrix_json()
        self.assertIn("openfoam-remote", QtGui.QApplication.clipboard().text().lower())

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