# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Static regression tests for FlowStudio task-panel wiring.

These tests intentionally inspect source/AST instead of importing task panels,
so they remain stable in headless CI and still catch UI regressions such as:

- button or signal hookups being removed,
- editable widgets no longer being persisted in ``_store()``,
- signal callbacks referencing methods that do not exist,
- display-only widgets accidentally looking editable when no persistence exists.
"""

from __future__ import annotations

import ast
import os
import unittest


TASKPANEL_FILES = {
    "task_solver.py": [
        "self.cb_backend.currentTextChanged.connect(self._on_backend_changed)",
    ],
    "task_post_pipeline.py": [
        "btn_load.clicked.connect(self._load_results)",
    ],
    "task_mesh_gmsh.py": [
        "btn_run.clicked.connect(self._run_mesh)",
    ],
    "task_measurement_point.py": [
        "self.chk_line.toggled.connect(grp_line.setEnabled)",
    ],
    "task_materials.py": [
        "self.cb_preset.currentTextChanged.connect(self._on_preset_changed)",
        "btn_db.clicked.connect(show_engineering_database_editor)",
    ],
    "task_fluid_material.py": [
        "self.cb_preset.currentTextChanged.connect(self._on_preset_changed)",
        "btn_db.clicked.connect(self._open_database)",
    ],
    "task_geometry_tools.py": [
        "apply_btn.clicked.connect(self._reload_objects)",
        "self.btn_check.clicked.connect(self._check)",
        "self.btn_volume.clicked.connect(self._toggle_volume)",
        "self.btn_leak.clicked.connect(self._open_leak_tracking)",
        "self.btn_find.clicked.connect(self._find_connection)",
        "self.btn_use_a.clicked.connect(self._use_selection_a)",
        "self.btn_use_b.clicked.connect(self._use_selection_b)",
    ],
    "task_project_cockpit.py": [
        'button.clicked.connect(lambda _checked=False, c=command_name: self._run_command(c))',
        "self.btn_stop.clicked.connect(self._stop_run)",
        "self.btn_results.clicked.connect(self._open_results)",
        "self._timer.timeout.connect(self._refresh)",
    ],
    "task_flowefd_features.py": [
        "self.btn_use_selection.clicked.connect(self._use_current_selection)",
        "self.btn_clear_selection.clicked.connect(self._clear_selection)",
        "self.cb_curve.currentTextChanged.connect(self._on_curve_changed)",
        "btn_db.clicked.connect(show_engineering_database_editor)",
        "self.curve_table.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)",
    ],
}

ENTERPRISE_FILE = "enterprise/ui/jobs_panel.py"
ENTERPRISE_SNIPPETS = [
    "self.table.itemSelectionChanged.connect(self._update_details)",
    "self.table.itemDoubleClicked.connect(self._open_selected_result)",
    "self.adapter_search.textChanged.connect(self._apply_adapter_filters)",
    "self.adapter_family_filter.currentIndexChanged.connect(self._apply_adapter_filters)",
    "self.adapter_capability_filter.currentIndexChanged.connect(self._apply_adapter_filters)",
    "self.copy_adapter_json_button.clicked.connect(self._copy_adapter_matrix_json)",
    "self.export_adapter_csv_button.clicked.connect(self._export_adapter_matrix_csv)",
    "self.refresh_button.clicked.connect(self.refresh)",
    "self.copy_path_button.clicked.connect(self._copy_selected_path)",
    "self.bundle_button.clicked.connect(self._export_selected_bundle)",
    "self.import_geant4_button.clicked.connect(self._import_selected_geant4_result)",
    "self.print_button.clicked.connect(self._print_selected_summary)",
    "self.adapter_table.itemSelectionChanged.connect(self._update_adapter_details)",
]

PERSISTENCE_EXPECTATIONS = {
    "task_bc_inlet.py": {
        "TaskBCInlet": [
            "cb_type", "sp_ux", "sp_uy", "sp_uz", "chk_normal",
            "sp_mfr", "sp_vfr", "cb_turb", "sp_ti", "sp_T",
        ],
    },
    "task_bc_open.py": {
        "TaskBCOpen": ["sp_p", "sp_T", "sp_vx", "sp_vy", "sp_vz"],
    },
    "task_bc_outlet.py": {
        "TaskBCOutlet": ["cb_type", "sp_p", "sp_mfr", "chk_backflow"],
    },
    "task_bc_wall.py": {
        "TaskBCWall": ["cb_type", "cb_thermal", "sp_temp", "sp_flux", "sp_htc", "sp_rough"],
    },
    "task_fluid_material.py": {
        "TaskFluidMaterial": ["cb_preset", "sp_rho", "sp_mu", "sp_nu", "sp_cp", "sp_k", "sp_pr"],
    },
    "task_initial_conditions.py": {
        "TaskInitialConditions": ["sp_ux", "sp_uy", "sp_uz", "sp_p", "sp_T", "sp_k", "sp_omega", "chk_pot"],
    },
    "task_materials.py": {
        "TaskMaterial": ["cb_preset", "le_name"],
    },
    "task_measurement_point.py": {
        "TaskMeasurementPoint": [
            "le_desc", "sp_px", "sp_py", "sp_pz", "chk_line",
            "sp_sx", "sp_sy", "sp_sz", "sp_ex", "sp_ey", "sp_ez",
            "sp_res", "le_fields", "chk_csv", "chk_ts",
        ],
    },
    "task_measurement_surface.py": {
        "TaskMeasurementSurface": [
            "le_desc", "cb_type", "sp_ox", "sp_oy", "sp_oz", "cb_normal",
            "sp_nx", "sp_ny", "sp_nz", "le_isofield", "sp_isoval",
            "le_fields", "chk_avg", "chk_integ", "chk_mflow", "chk_force",
            "sp_rpx", "sp_rpy", "sp_rpz", "chk_csv", "chk_vtk", "chk_ts",
        ],
    },
    "task_measurement_volume.py": {
        "TaskMeasurementVolume": [
            "le_desc", "cb_type", "sp_bx0", "sp_by0", "sp_bz0", "sp_bx1",
            "sp_by1", "sp_bz1", "sp_scx", "sp_scy", "sp_scz", "sp_sr",
            "sp_ccx", "sp_ccy", "sp_ccz", "sp_cax", "sp_cay", "sp_caz",
            "sp_cr", "sp_ch", "le_thrfield", "sp_thrmin", "sp_thrmax",
            "le_fields", "chk_avg", "chk_minmax", "chk_integ", "chk_csv", "chk_ts",
        ],
    },
    "task_mesh_gmsh.py": {
        "TaskMeshGmsh": ["sp_char", "sp_min", "sp_max", "cb_algo", "cb_order", "cb_type", "sp_growth", "sp_gap", "cb_format"],
    },
    "task_physics_model.py": {
        "TaskPhysicsModel": ["cb_flow", "cb_turb", "cb_comp", "cb_time", "chk_gravity", "chk_heat", "chk_buoy", "chk_vof", "chk_scalar"],
    },
    "task_post_pipeline.py": {
        "TaskPostPipeline": ["cb_vis", "cb_field", "chk_auto", "sp_min", "sp_max"],
    },
    "task_solver.py": {
        "TaskSolver": [
            "cb_backend", "cb_of_solver", "sp_iter", "sp_tol", "sp_nproc",
            "cb_conv", "cb_elmer_solver", "sp_elmer_nproc", "cb_fx_prec",
            "sp_fx_res", "sp_fx_steps", "sp_fx_vram", "chk_multigpu", "sp_ngpu",
            "chk_multi_solver", "chk_multi_openfoam", "chk_multi_elmer",
            "chk_multi_fluidx3d", "chk_multi_geant4", "sp_runtime_soft",
            "sp_runtime_max", "sp_runtime_stall", "sp_runtime_progress",
            "chk_abort_threshold",
        ],
    },
    "task_flowefd_features.py": {
        "TaskVolumeSource": ["cb_type", "sp_q", "sp_m", "chk_goals"],
        "TaskFan": ["cb_type", "cb_curve", "sp_p", "chk_goals"],
        "TaskResultPlot": [
            "cb_kind", "cb_field", "sp_contours", "chk_contours", "chk_isolines",
            "chk_vectors", "chk_streamlines", "cb_plane", "sp_offset", "chk_cad",
            "chk_interp", "chk_excel",
        ],
        "TaskParticleStudy": [
            "chk_acc", "chk_ero", "chk_grav", "sp_gx", "sp_gy", "sp_gz",
            "cb_shape", "sp_d", "cb_color", "sp_len", "sp_time", "sp_max",
        ],
    },
}


class TestTaskPanelWiring(unittest.TestCase):
    """Headless regression tests for signal hookups and widget persistence."""

    @classmethod
    def setUpClass(cls):
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        cls.pkg_dir = os.path.join(root_dir, "flow_studio")

    def _read_source(self, rel_path):
        abs_path = os.path.join(self.pkg_dir, rel_path)
        with open(abs_path, "r", encoding="utf-8") as handle:
            return abs_path, handle.read()

    def _class_method_source(self, source, class_name, method_name):
        tree = ast.parse(source)
        for node in tree.body:
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                for stmt in node.body:
                    if isinstance(stmt, ast.FunctionDef) and stmt.name == method_name:
                        return ast.get_source_segment(source, stmt) or ""
        self.fail(f"Could not find {class_name}.{method_name}")

    def test_expected_signal_connections_exist(self):
        for rel_path, snippets in TASKPANEL_FILES.items():
            abs_path, source = self._read_source(os.path.join("taskpanels", rel_path))
            for snippet in snippets:
                self.assertIn(snippet, source, f"Missing signal hookup in {abs_path}: {snippet}")

        abs_path, source = self._read_source(ENTERPRISE_FILE)
        for snippet in ENTERPRISE_SNIPPETS:
            self.assertIn(snippet, source, f"Missing signal hookup in {abs_path}: {snippet}")

    def test_geant4_result_command_is_exposed_in_post_processing_surface(self):
        initgui_path, initgui_source = self._read_source("../InitGui.py")
        commands_path, commands_source = self._read_source("commands.py")

        self.assertIn(
            '"FlowStudio_Geant4Result"',
            initgui_source,
            f"Missing Geant4 result command in post-processing surfaces: {initgui_path}",
        )
        self.assertIn(
            'FreeCADGui.addCommand("FlowStudio_Geant4Result", _CmdGeant4Result())',
            commands_source,
            f"Missing Geant4 result command registration: {commands_path}",
        )
        self.assertIn(
            '"FlowStudio_ImportGeant4Result"',
            initgui_source,
            f"Missing Geant4 import command in post-processing surfaces: {initgui_path}",
        )
        self.assertIn(
            'FreeCADGui.addCommand("FlowStudio_ImportGeant4Result", _CmdImportGeant4Result())',
            commands_source,
            f"Missing Geant4 import command registration: {commands_path}",
        )

    def test_step_import_command_is_exposed_in_geometry_surface(self):
        initgui_path, initgui_source = self._read_source("../InitGui.py")
        commands_path, commands_source = self._read_source("commands.py")

        self.assertIn(
            '"FlowStudio_ImportStep"',
            initgui_source,
            f"Missing STEP import command in geometry surfaces: {initgui_path}",
        )
        self.assertIn(
            'FreeCADGui.addCommand("FlowStudio_ImportStep", _CmdImportStep())',
            commands_source,
            f"Missing STEP import command registration: {commands_path}",
        )

    def test_project_cockpit_command_is_exposed_in_workbench_surface(self):
        initgui_path, initgui_source = self._read_source("../InitGui.py")
        commands_path, commands_source = self._read_source("commands.py")

        self.assertIn(
            '"FlowStudio_ProjectCockpit"',
            initgui_source,
            f"Missing project cockpit command in workbench surfaces: {initgui_path}",
        )
        self.assertIn(
            'FreeCADGui.addCommand("FlowStudio_ProjectCockpit", _CmdWorkflowGuide())',
            commands_source,
            f"Missing project cockpit command registration: {commands_path}",
        )
        self.assertIn('self.appendMenu("FlowStudio", self.ANALYSIS_COMMANDS)', initgui_source, initgui_path)

    def test_electronics_cooling_study_command_is_exposed_in_workbench_surface(self):
        initgui_path, initgui_source = self._read_source("../InitGui.py")
        commands_path, commands_source = self._read_source("commands.py")

        self.assertIn(
            'FreeCADGui.addCommand("FlowStudio_ElectronicsCoolingStudy", _CmdElectronicsCoolingStudy())',
            commands_source,
            f"Missing electronics cooling study command registration: {commands_path}",
        )

        self.assertIn(
            'EXAMPLE_COMMANDS = all_example_commands()',
            initgui_source,
            f"Workbench should source example starters from domain metadata: {initgui_path}",
        )
        self.assertIn(
            'for _group_key, group_label, commands in self.EXAMPLE_COMMAND_GROUPS:',
            initgui_source,
            f"Workbench should expose example starters through grouped domain menus: {initgui_path}",
        )

    def test_cooling_channel_study_command_is_exposed_in_workbench_surface(self):
        initgui_path, initgui_source = self._read_source("../InitGui.py")
        commands_path, commands_source = self._read_source("commands.py")

        self.assertIn('EXAMPLE_COMMANDS = all_example_commands()', initgui_source, initgui_path)
        self.assertIn('from flow_studio.workflows.studies import apply_cooling_channel_defaults', commands_source, commands_path)
        self.assertIn('result_plot = makeResultPlot(name="CoolingChannelTemperaturePlot", plot_kind="Cut Plot")', commands_source, commands_path)
        self.assertIn('apply_cooling_channel_defaults(', commands_source, commands_path)
        self.assertIn(
            'FreeCADGui.addCommand("FlowStudio_CoolingChannelStudy", _CmdCoolingChannelStudy())',
            commands_source,
            f"Missing cooling channel study command registration: {commands_path}",
        )

    def test_examples_toolbar_is_separate_from_analysis_toolbar(self):
        initgui_path, initgui_source = self._read_source("../InitGui.py")

        self.assertIn(
            'for index, (group_key, _group_label, commands) in enumerate(self.EXAMPLE_COMMAND_GROUPS):',
            initgui_source,
            f"Ribbon workbench should expose grouped Examples toolbars: {initgui_path}",
        )
        self.assertIn(
            'self.appendToolbar(f"FlowStudio {group_key} Examples", list(commands))',
            initgui_source,
            f"Classic workbench should expose grouped Examples toolbars: {initgui_path}",
        )

    def test_external_aero_study_command_is_exposed_in_workbench_surface(self):
        initgui_path, initgui_source = self._read_source("../InitGui.py")
        commands_path, commands_source = self._read_source("commands.py")

        self.assertIn('EXAMPLE_COMMANDS = all_example_commands()', initgui_source, initgui_path)
        self.assertIn(
            'FreeCADGui.addCommand("FlowStudio_ExternalAeroStudy", _CmdExternalAeroStudy())',
            commands_source,
            f"Missing external aero study command registration: {commands_path}",
        )

    def test_buildings_study_command_is_exposed_in_workbench_surface(self):
        initgui_path, initgui_source = self._read_source("../InitGui.py")
        commands_path, commands_source = self._read_source("commands.py")

        self.assertIn('EXAMPLE_COMMANDS = all_example_commands()', initgui_source, initgui_path)
        self.assertIn('from flow_studio.workflows.studies import apply_buildings_defaults', commands_source, commands_path)
        self.assertIn('result_plot = makeResultPlot(name="BuildingsWindPlot", plot_kind="Cut Plot")', commands_source, commands_path)
        self.assertIn('apply_buildings_defaults(', commands_source, commands_path)
        self.assertIn(
            'FreeCADGui.addCommand("FlowStudio_BuildingsStudy", _CmdBuildingsStudy())',
            commands_source,
            f"Missing buildings study command registration: {commands_path}",
        )

    def test_airfoil_study_command_is_exposed_in_workbench_surface(self):
        initgui_path, initgui_source = self._read_source("../InitGui.py")
        commands_path, commands_source = self._read_source("commands.py")

        self.assertIn('EXAMPLE_COMMANDS = all_example_commands()', initgui_source, initgui_path)
        self.assertIn('from flow_studio.workflows.studies import apply_airfoil_defaults', commands_source, commands_path)
        self.assertIn('result_plot = makeResultPlot(name="AirfoilCpPlot", plot_kind="Surface Plot")', commands_source, commands_path)
        self.assertIn('apply_airfoil_defaults(', commands_source, commands_path)
        self.assertIn(
            'FreeCADGui.addCommand("FlowStudio_AirfoilStudy", _CmdAirfoilStudy())',
            commands_source,
            f"Missing airfoil study command registration: {commands_path}",
        )

    def test_tesla_valve_study_command_is_exposed_in_workbench_surface(self):
        initgui_path, initgui_source = self._read_source("../InitGui.py")
        commands_path, commands_source = self._read_source("commands.py")

        self.assertIn('EXAMPLE_COMMANDS = all_example_commands()', initgui_source, initgui_path)
        self.assertIn('from flow_studio.workflows.studies import apply_tesla_valve_defaults', commands_source, commands_path)
        self.assertIn('result_plot = makeResultPlot(name="TeslaValvePressurePlot", plot_kind="Cut Plot")', commands_source, commands_path)
        self.assertIn('apply_tesla_valve_defaults(', commands_source, commands_path)
        self.assertIn(
            'FreeCADGui.addCommand("FlowStudio_TeslaValveStudy", _CmdTeslaValveStudy())',
            commands_source,
            f"Missing Tesla valve study command registration: {commands_path}",
        )

    def test_von_karman_study_command_is_exposed_in_workbench_surface(self):
        initgui_path, initgui_source = self._read_source("../InitGui.py")
        commands_path, commands_source = self._read_source("commands.py")

        self.assertIn('EXAMPLE_COMMANDS = all_example_commands()', initgui_source, initgui_path)
        self.assertIn('from flow_studio.workflows.studies import apply_von_karman_defaults', commands_source, commands_path)
        self.assertIn('result_plot = makeResultPlot(name="VonKarmanVorticityPlot", plot_kind="Cut Plot")', commands_source, commands_path)
        self.assertIn('apply_von_karman_defaults(', commands_source, commands_path)
        self.assertIn(
            'FreeCADGui.addCommand("FlowStudio_VonKarmanStudy", _CmdVonKarmanStudy())',
            commands_source,
            f"Missing Von Karman study command registration: {commands_path}",
        )

    def test_pipe_flow_study_command_is_exposed_in_workbench_surface(self):
        initgui_path, initgui_source = self._read_source("../InitGui.py")
        commands_path, commands_source = self._read_source("commands.py")

        self.assertIn('EXAMPLE_COMMANDS = all_example_commands()', initgui_source, initgui_path)
        self.assertIn(
            'FreeCADGui.addCommand("FlowStudio_PipeFlowStudy", _CmdPipeFlowStudy())',
            commands_source,
            f"Missing pipe flow study command registration: {commands_path}",
        )

    def test_static_mixer_study_command_is_exposed_in_workbench_surface(self):
        initgui_path, initgui_source = self._read_source("../InitGui.py")
        commands_path, commands_source = self._read_source("commands.py")

        self.assertIn('EXAMPLE_COMMANDS = all_example_commands()', initgui_source, initgui_path)
        self.assertIn(
            'FreeCADGui.addCommand("FlowStudio_StaticMixerStudy", _CmdStaticMixerStudy())',
            commands_source,
            f"Missing static mixer study command registration: {commands_path}",
        )

    def test_structural_example_command_is_exposed_in_workbench_surface(self):
        initgui_path, initgui_source = self._read_source("../InitGui.py")
        commands_path, commands_source = self._read_source("commands.py")

        self.assertIn('EXAMPLE_COMMANDS = all_example_commands()', initgui_source, initgui_path)
        self.assertIn('from flow_studio.workflows.studies import apply_structural_bracket_defaults', commands_source, commands_path)
        self.assertIn('post = makePostPipeline(name="StructuralBracketPost")', commands_source, commands_path)
        self.assertIn('result_plot = makeResultPlot(name="BracketStressPlot", plot_kind="Surface Plot")', commands_source, commands_path)
        self.assertIn('apply_structural_bracket_defaults(', commands_source, commands_path)
        self.assertIn(
            'FreeCADGui.addCommand("FlowStudio_StructuralBracketExample", _CmdStructuralBracketExample())',
            commands_source,
            f"Missing structural example command registration: {commands_path}",
        )

    def test_electrostatic_example_command_is_exposed_in_workbench_surface(self):
        initgui_path, initgui_source = self._read_source("../InitGui.py")
        commands_path, commands_source = self._read_source("commands.py")

        self.assertIn('EXAMPLE_COMMANDS = all_example_commands()', initgui_source, initgui_path)
        self.assertIn('from flow_studio.workflows.studies import apply_electrostatic_capacitor_defaults', commands_source, commands_path)
        self.assertIn('post = makePostPipeline(name="ElectrostaticCapacitorPost")', commands_source, commands_path)
        self.assertIn('result_plot = makeResultPlot(name="PotentialCutPlot", plot_kind="Cut Plot")', commands_source, commands_path)
        self.assertIn('apply_electrostatic_capacitor_defaults(', commands_source, commands_path)
        self.assertIn(
            'FreeCADGui.addCommand("FlowStudio_ElectrostaticCapacitorExample", _CmdElectrostaticCapacitorExample())',
            commands_source,
            f"Missing electrostatic example command registration: {commands_path}",
        )

    def test_electromagnetic_example_command_is_exposed_in_workbench_surface(self):
        initgui_path, initgui_source = self._read_source("../InitGui.py")
        commands_path, commands_source = self._read_source("commands.py")

        self.assertIn('EXAMPLE_COMMANDS = all_example_commands()', initgui_source, initgui_path)
        self.assertIn('from flow_studio.workflows.studies import apply_electromagnetic_coil_defaults', commands_source, commands_path)
        self.assertIn('post = makePostPipeline(name="ElectromagneticCoilPost")', commands_source, commands_path)
        self.assertIn('result_plot = makeResultPlot(name="MagneticFluxPlot", plot_kind="Surface Plot")', commands_source, commands_path)
        self.assertIn('apply_electromagnetic_coil_defaults(', commands_source, commands_path)
        self.assertIn(
            'FreeCADGui.addCommand("FlowStudio_ElectromagneticCoilExample", _CmdElectromagneticCoilExample())',
            commands_source,
            f"Missing electromagnetic example command registration: {commands_path}",
        )

    def test_thermal_example_command_is_exposed_in_workbench_surface(self):
        initgui_path, initgui_source = self._read_source("../InitGui.py")
        commands_path, commands_source = self._read_source("commands.py")

        self.assertIn('EXAMPLE_COMMANDS = all_example_commands()', initgui_source, initgui_path)
        self.assertIn('from flow_studio.workflows.studies import apply_thermal_plate_defaults', commands_source, commands_path)
        self.assertIn('post = makePostPipeline(name="ThermalPlatePost")', commands_source, commands_path)
        self.assertIn('result_plot = makeResultPlot(name="TemperatureCutPlot", plot_kind="Cut Plot")', commands_source, commands_path)
        self.assertIn('apply_thermal_plate_defaults(', commands_source, commands_path)
        self.assertIn(
            'FreeCADGui.addCommand("FlowStudio_ThermalPlateExample", _CmdThermalPlateExample())',
            commands_source,
            f"Missing thermal example command registration: {commands_path}",
        )

    def test_optical_example_command_is_exposed_in_workbench_surface(self):
        initgui_path, initgui_source = self._read_source("../InitGui.py")
        commands_path, commands_source = self._read_source("commands.py")

        self.assertIn('EXAMPLE_COMMANDS = all_example_commands()', initgui_source, initgui_path)
        self.assertIn('from flow_studio.workflows.studies import apply_optical_lens_defaults', commands_source, commands_path)
        self.assertIn('post = makePostPipeline(name="OpticalLensPost")', commands_source, commands_path)
        self.assertIn('result_plot = makeResultPlot(name="IrradianceSurfacePlot", plot_kind="Surface Plot")', commands_source, commands_path)
        self.assertIn('apply_optical_lens_defaults(', commands_source, commands_path)
        self.assertIn(
            'FreeCADGui.addCommand("FlowStudio_OpticalLensExample", _CmdOpticalLensExample())',
            commands_source,
            f"Missing optical example command registration: {commands_path}",
        )

    def test_project_cockpit_sources_starters_from_domain_metadata(self):
        cockpit_path, cockpit_source = self._read_source(os.path.join("taskpanels", "task_project_cockpit.py"))

        self.assertIn(
            'STARTER_COMMAND_GROUPS = tuple(',
            cockpit_source,
            f"Cockpit should derive starter groups dynamically: {cockpit_path}",
        )
        self.assertIn(
            'for _group_key, group_label, commands in example_command_groups()',
            cockpit_source,
            f"Cockpit should iterate over grouped domain example commands: {cockpit_path}",
        )
        self.assertIn(
            'starter_group = QtGui.QGroupBox("Starter Examples")',
            cockpit_source,
            f"Cockpit should render a dedicated starter examples area: {cockpit_path}",
        )

    def test_project_cockpit_prioritizes_primary_result_objects(self):
        cockpit_path, cockpit_source = self._read_source(os.path.join("taskpanels", "task_project_cockpit.py"))

        self.assertIn(
            'if command_name == "FlowStudio_PostPipeline":',
            cockpit_source,
            f"Post actions should route through the cockpit result resolver: {cockpit_path}",
        )
        self.assertIn(
            "def _preferred_result_object(self, analysis):",
            cockpit_source,
            f"Cockpit should resolve a preferred result object before opening results: {cockpit_path}",
        )
        self.assertIn(
            'flow_type == "FlowStudio::ResultPlot"',
            cockpit_source,
            f"Cockpit should prefer starter result plots when available: {cockpit_path}",
        )
        self.assertIn(
            "FreeCADGui.ActiveDocument.setEdit(target.Name)",
            cockpit_source,
            f"Cockpit should open the preferred result object directly: {cockpit_path}",
        )
        self.assertIn(
            'self.btn_results.setEnabled(preferred_result is not None or bool(result_path))',
            cockpit_source,
            f"Open Results should stay enabled when a starter result object already exists: {cockpit_path}",
        )

    def test_connected_self_methods_exist(self):
        files = [os.path.join("taskpanels", name) for name in TASKPANEL_FILES] + [ENTERPRISE_FILE]
        for rel_path in files:
            abs_path, source = self._read_source(rel_path)
            tree = ast.parse(source)
            for class_node in [node for node in tree.body if isinstance(node, ast.ClassDef)]:
                methods = {
                    stmt.name
                    for stmt in class_node.body
                    if isinstance(stmt, ast.FunctionDef)
                }
                for stmt in ast.walk(class_node):
                    if not isinstance(stmt, ast.Call):
                        continue
                    func = stmt.func
                    if not isinstance(func, ast.Attribute) or func.attr != "connect":
                        continue
                    if not stmt.args:
                        continue
                    target = stmt.args[0]
                    if not isinstance(target, ast.Attribute):
                        continue
                    if not isinstance(target.value, ast.Name) or target.value.id != "self":
                        continue
                    self.assertIn(
                        target.attr,
                        methods,
                        f"{abs_path}: {class_node.name} connects to missing method self.{target.attr}()",
                    )

    def test_editable_widgets_are_persisted(self):
        for rel_path, class_map in PERSISTENCE_EXPECTATIONS.items():
            abs_path, source = self._read_source(os.path.join("taskpanels", rel_path))
            for class_name, attrs in class_map.items():
                store_source = self._class_method_source(source, class_name, "_store")
                for attr in attrs:
                    self.assertIn(
                        f"self.{attr}",
                        store_source,
                        f"{abs_path}: {class_name} does not persist widget {attr} in _store()",
                    )

    def test_enterprise_jobs_panel_publishes_taskview_metadata(self):
        abs_path, source = self._read_source("enterprise/ui/jobs_panel.py")

        self.assertIn('self._publish_taskview_property("taskview_summary_title", summary_title)', source, abs_path)
        self.assertIn('self._publish_taskview_property("taskview_validation_level", validation_level)', source, abs_path)
        self.assertIn('self._set_taskview_metadata(', source, abs_path)
        self.assertIn('"Enterprise Jobs"', source, abs_path)
        self.assertIn('"No persisted enterprise runs"', source, abs_path)
        self.assertIn('"Native Geant4 result available"', source, abs_path)

    def test_dynamic_widget_maps_are_persisted(self):
        abs_path, source = self._read_source(os.path.join("taskpanels", "task_materials.py"))
        store_source = self._class_method_source(source, "TaskMaterial", "_store")
        self.assertIn("for prop, widget in self._widgets.items()", store_source)
        self.assertIn("setattr(self.obj, prop, widget.value())", store_source)

    def test_base_task_panel_publishes_context_metadata(self):
        abs_path, source = self._read_source(os.path.join("taskpanels", "base_taskpanel.py"))

        self.assertIn('self._publish_taskview_property("taskview_context_mode", mode)', source, abs_path)
        self.assertIn('self._publish_taskview_property("taskview_context_title", title)', source, abs_path)
        self.assertIn('self._publish_taskview_property("taskview_context_detail", detail)', source, abs_path)
        self.assertIn("def _build_task_context", source, abs_path)
        self.assertIn("CONTEXT_MODE = \"Edit\"", source, abs_path)

        abs_path, source = self._read_source(os.path.join("taskpanels", "task_generic_bc.py"))
        store_source = self._class_method_source(source, "TaskGenericBC", "_store")
        self.assertIn("for prop, widget in self._widgets.items()", store_source)
        self.assertIn("widget.isChecked()", store_source)
        self.assertIn("widget.currentText()", store_source)
        self.assertIn("widget.value()", store_source)

    def test_taskfan_curve_table_is_display_only(self):
        abs_path, source = self._read_source(os.path.join("taskpanels", "task_flowefd_features.py"))
        self.assertIn(
            "self.curve_table.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)",
            source,
            f"{abs_path}: TaskFan curve table should be read-only because it displays preset data only",
        )


if __name__ == "__main__":
    unittest.main()
