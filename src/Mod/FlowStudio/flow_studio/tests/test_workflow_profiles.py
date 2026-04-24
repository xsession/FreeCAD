# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Static tests for CST-inspired workflow profiles and workspace layouts."""

import os
import sys
import types
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


class TestWorkflowProfiles(unittest.TestCase):
    """Ensure each supported domain exposes profile and workspace metadata."""

    def test_optical_profile_exists(self):
        from flow_studio.workflows.profiles import get_workflow_profile

        profile = get_workflow_profile("Optical")
        self.assertEqual(profile.label, "Optical / Photonics")
        self.assertEqual(len(profile.steps), 9)
        self.assertEqual(profile.steps[4].name, "Define Sources, Detectors, and Boundaries")
        self.assertIn("Radiation transport", profile.workflows)

    def test_cfd_layout_exists(self):
        from flow_studio.ui.layouts import get_workspace_layout

        layout = get_workspace_layout("CFD")
        self.assertIn("Project Tree", layout.left_panes)
        self.assertIn("Results", layout.bottom_panes)

    def test_default_profile_falls_back_to_cfd(self):
        from flow_studio.workflows.profiles import get_workflow_profile

        self.assertEqual(get_workflow_profile(None).domain_key, "CFD")
        self.assertEqual(get_workflow_profile("Unknown").domain_key, "CFD")

    def test_electronics_cooling_recipe_exists_for_cfd_cht(self):
        from flow_studio.workflows.studies import get_study_recipe

        recipe = get_study_recipe("CFD", "Conjugate Heat Transfer")
        self.assertIsNotNone(recipe)
        self.assertEqual(recipe.label, "Electronics Cooling CHT + Radiation")
        self.assertIn("1.25e6 W/m^3", " ".join(recipe.key_parameters))
        self.assertIn("solid", " ".join(recipe.milestones).lower())

    def test_workflow_context_applies_electronics_cooling_step_overrides(self):
        from flow_studio.workflow_guide import get_workflow_context

        analysis = types.SimpleNamespace(PhysicsDomain="CFD", AnalysisType="Conjugate Heat Transfer", StudyRecipeKey="")
        context = get_workflow_context(analysis)

        self.assertIsNotNone(context["study_recipe"])
        self.assertEqual(context["study_recipe"].key, "cfd-electronics-cooling")
        self.assertEqual(context["profile"].steps[1].name, "Import Geometry And Cooling Features")
        self.assertIn("Realizable k-epsilon", context["profile"].steps[6].hint)

    def test_non_recipe_analysis_type_keeps_generic_cfd_profile(self):
        from flow_studio.workflow_guide import get_workflow_context

        analysis = types.SimpleNamespace(PhysicsDomain="CFD", AnalysisType="Internal Flow", StudyRecipeKey="")
        context = get_workflow_context(analysis)

        self.assertIsNone(context["study_recipe"])
        self.assertEqual(context["profile"].steps[1].name, "Import / Create Geometry")

    def test_non_cfd_example_recipes_are_selected_by_study_key(self):
        from flow_studio.workflows.studies import get_study_recipe

        self.assertEqual(
            get_study_recipe("Structural", "Static Linear Elastic", "structural-bracket-example").key,
            "structural-bracket-example",
        )
        self.assertEqual(
            get_study_recipe("Electrostatic", "Capacitance Matrix", "electrostatic-capacitor-example").key,
            "electrostatic-capacitor-example",
        )
        self.assertEqual(
            get_study_recipe("Electromagnetic", "Magnetostatic", "electromagnetic-coil-example").key,
            "electromagnetic-coil-example",
        )
        self.assertEqual(
            get_study_recipe("Thermal", "Steady-State Heat Transfer", "thermal-plate-example").key,
            "thermal-plate-example",
        )
        self.assertEqual(
            get_study_recipe("Optical", "Illumination", "optical-lens-example").key,
            "optical-lens-example",
        )

    def test_non_cfd_example_recipes_apply_workflow_overrides(self):
        from flow_studio.workflow_guide import get_workflow_context

        cases = (
            (
                types.SimpleNamespace(
                    PhysicsDomain="Structural",
                    AnalysisType="Static Linear Elastic",
                    StudyRecipeKey="structural-bracket-example",
                ),
                "structural-bracket-example",
                "Apply Support And Tip Load",
            ),
            (
                types.SimpleNamespace(
                    PhysicsDomain="Electrostatic",
                    AnalysisType="Capacitance Matrix",
                    StudyRecipeKey="electrostatic-capacitor-example",
                ),
                "electrostatic-capacitor-example",
                "Assign Electrode Potentials",
            ),
            (
                types.SimpleNamespace(
                    PhysicsDomain="Electromagnetic",
                    AnalysisType="Magnetostatic",
                    StudyRecipeKey="electromagnetic-coil-example",
                ),
                "electromagnetic-coil-example",
                "Apply Coil Excitation And Far Field",
            ),
            (
                types.SimpleNamespace(
                    PhysicsDomain="Thermal",
                    AnalysisType="Steady-State Heat Transfer",
                    StudyRecipeKey="thermal-plate-example",
                ),
                "thermal-plate-example",
                "Apply Heat Flux And Convection",
            ),
            (
                types.SimpleNamespace(
                    PhysicsDomain="Optical",
                    AnalysisType="Illumination",
                    StudyRecipeKey="optical-lens-example",
                ),
                "optical-lens-example",
                "Place Source, Detector, And Housing Boundary",
            ),
        )

        for analysis, recipe_key, step_name in cases:
            with self.subTest(recipe_key=recipe_key):
                context = get_workflow_context(analysis)
                self.assertIsNotNone(context["study_recipe"])
                self.assertEqual(context["study_recipe"].key, recipe_key)
                self.assertEqual(context["profile"].steps[4].name, step_name)

    def test_generic_non_cfd_profile_remains_when_study_key_is_missing(self):
        from flow_studio.workflow_guide import get_workflow_context

        analysis = types.SimpleNamespace(
            PhysicsDomain="Thermal",
            AnalysisType="Steady-State Heat Transfer",
            StudyRecipeKey="",
        )
        context = get_workflow_context(analysis)

        self.assertIsNone(context["study_recipe"])
        self.assertEqual(context["profile"].steps[4].name, "Define Thermal Loads and Boundaries")

    def test_electronics_cooling_defaults_apply_expected_benchmark_values(self):
        from flow_studio.workflows.studies import apply_electronics_cooling_defaults

        analysis = types.SimpleNamespace(PhysicsDomain="CFD", AnalysisType="Internal Flow", StudyRecipeKey="", Label="")
        physics = types.SimpleNamespace(FlowRegime="Laminar", TurbulenceModel="kOmegaSST", HeatTransfer=False, Compressibility="Compressible", TimeModel="Transient")
        fluid = types.SimpleNamespace(Preset="Custom", MaterialName="", ReferenceTemperature=0.0)
        solid = types.SimpleNamespace(MaterialPreset="Custom", MaterialName="")
        solver = types.SimpleNamespace(SolverBackend="Elmer", OpenFOAMSolver="pimpleFoam", MaxIterations=0, ConvergenceTolerance=1.0, RelaxationFactorP=0.0, RelaxationFactorU=0.0, ConvectionScheme="upwind")
        initial = types.SimpleNamespace(Temperature=0.0, UsePotentialFlow=True)
        fan = types.SimpleNamespace(Label="", FanType="Internal Fan", ReferencePressure=0.0)
        source = types.SimpleNamespace(Label="", SourceType="Mass Source", HeatPowerDensity=0.0)
        mesh = types.SimpleNamespace(CharacteristicLength=0.0, MinElementSize=0.0, MaxElementSize=0.0, GrowthRate=0.0, MeshFormat="SU2 (.su2)")
        post = types.SimpleNamespace(Label="")

        apply_electronics_cooling_defaults(
            analysis,
            physics_model=physics,
            fluid_material=fluid,
            solid_material=solid,
            solver=solver,
            initial_conditions=initial,
            fan=fan,
            volume_source=source,
            mesh=mesh,
            post_pipeline=post,
        )

        self.assertEqual(analysis.AnalysisType, "Conjugate Heat Transfer")
        self.assertEqual(physics.TurbulenceModel, "kEpsilon")
        self.assertTrue(physics.HeatTransfer)
        self.assertEqual(fluid.Preset, "Air (20°C, 1atm)")
        self.assertEqual(solid.MaterialPreset, "Aluminum 6061-T6")
        self.assertEqual(solver.OpenFOAMSolver, "simpleFoam")
        self.assertEqual(solver.MaxIterations, 800)
        self.assertAlmostEqual(solver.ConvergenceTolerance, 1e-8)
        self.assertAlmostEqual(source.HeatPowerDensity, 1250000.0)
        self.assertEqual(mesh.MeshFormat, "OpenFOAM (polyMesh)")

    def test_external_aero_recipe_is_selected_by_study_key(self):
        from flow_studio.workflow_guide import get_workflow_context

        analysis = types.SimpleNamespace(PhysicsDomain="CFD", AnalysisType="External Flow", StudyRecipeKey="cfd-external-aero")
        context = get_workflow_context(analysis)

        self.assertIsNotNone(context["study_recipe"])
        self.assertEqual(context["study_recipe"].key, "cfd-external-aero")
        self.assertEqual(context["profile"].steps[1].name, "Prepare External Domain")

    def test_buildings_recipe_is_selected_by_study_key(self):
        from flow_studio.workflow_guide import get_workflow_context

        analysis = types.SimpleNamespace(PhysicsDomain="CFD", AnalysisType="External Flow", StudyRecipeKey="cfd-buildings")
        context = get_workflow_context(analysis)

        self.assertIsNotNone(context["study_recipe"])
        self.assertEqual(context["study_recipe"].key, "cfd-buildings")
        self.assertEqual(context["study_recipe"].reference_url, "https://help.sim-flow.com/tutorials/buildings")

    def test_cooling_channel_recipe_is_selected_by_study_key(self):
        from flow_studio.workflow_guide import get_workflow_context

        analysis = types.SimpleNamespace(PhysicsDomain="CFD", AnalysisType="Conjugate Heat Transfer", StudyRecipeKey="cfd-cooling-channel")
        context = get_workflow_context(analysis)

        self.assertIsNotNone(context["study_recipe"])
        self.assertEqual(context["study_recipe"].key, "cfd-cooling-channel")
        self.assertEqual(context["study_recipe"].reference_url, "https://help.sim-flow.com/tutorials/cooling-channel")

    def test_airfoil_recipe_is_selected_by_study_key(self):
        from flow_studio.workflow_guide import get_workflow_context

        analysis = types.SimpleNamespace(PhysicsDomain="CFD", AnalysisType="External Flow", StudyRecipeKey="cfd-airfoil-naca-0012")
        context = get_workflow_context(analysis)

        self.assertIsNotNone(context["study_recipe"])
        self.assertEqual(context["study_recipe"].key, "cfd-airfoil-naca-0012")
        self.assertEqual(context["study_recipe"].reference_url, "https://help.sim-flow.com/tutorials/airfoil-naca-0012")

    def test_tesla_valve_recipe_is_selected_by_study_key(self):
        from flow_studio.workflow_guide import get_workflow_context

        analysis = types.SimpleNamespace(PhysicsDomain="CFD", AnalysisType="Internal Flow", StudyRecipeKey="cfd-tesla-valve")
        context = get_workflow_context(analysis)

        self.assertIsNotNone(context["study_recipe"])
        self.assertEqual(context["study_recipe"].key, "cfd-tesla-valve")
        self.assertEqual(context["study_recipe"].reference_url, "https://help.sim-flow.com/tutorials/tesla-valve")

    def test_von_karman_recipe_is_selected_by_study_key(self):
        from flow_studio.workflow_guide import get_workflow_context

        analysis = types.SimpleNamespace(PhysicsDomain="CFD", AnalysisType="External Flow", StudyRecipeKey="cfd-von-karman-vortex-street")
        context = get_workflow_context(analysis)

        self.assertIsNotNone(context["study_recipe"])
        self.assertEqual(context["study_recipe"].key, "cfd-von-karman-vortex-street")
        self.assertEqual(context["study_recipe"].reference_url, "https://help.sim-flow.com/tutorials/von-karman-vortex-street")

    def test_internal_flow_recipe_does_not_auto_select_without_study_key(self):
        from flow_studio.workflows.studies import get_study_recipe

        self.assertIsNone(get_study_recipe("CFD", "Internal Flow", ""))
        self.assertEqual(get_study_recipe("CFD", "Internal Flow", "cfd-pipe-flow").key, "cfd-pipe-flow")
        self.assertEqual(get_study_recipe("CFD", "Internal Flow", "cfd-static-mixer").key, "cfd-static-mixer")

    def test_external_aero_defaults_apply_expected_baseline_values(self):
        from flow_studio.workflows.studies import apply_external_aero_defaults

        analysis = types.SimpleNamespace(PhysicsDomain="CFD", AnalysisType="Internal Flow", StudyRecipeKey="", Label="")
        physics = types.SimpleNamespace(FlowRegime="Laminar", TurbulenceModel="kEpsilon", HeatTransfer=True, Compressibility="Compressible", TimeModel="Transient")
        fluid = types.SimpleNamespace(Preset="Custom", MaterialName="", ReferenceTemperature=0.0)
        solver = types.SimpleNamespace(SolverBackend="Elmer", OpenFOAMSolver="pimpleFoam", MaxIterations=0, ConvergenceTolerance=1.0, ConvectionScheme="upwind")
        initial = types.SimpleNamespace(UsePotentialFlow=False, Ux=0.0, Uy=1.0, Uz=2.0)
        mesh = types.SimpleNamespace(CharacteristicLength=0.0, MinElementSize=0.0, MaxElementSize=0.0, GrowthRate=0.0, MeshFormat="SU2 (.su2)")
        post = types.SimpleNamespace(Label="")

        apply_external_aero_defaults(
            analysis,
            physics_model=physics,
            fluid_material=fluid,
            solver=solver,
            initial_conditions=initial,
            mesh=mesh,
            post_pipeline=post,
        )

        self.assertEqual(analysis.AnalysisType, "External Flow")
        self.assertEqual(analysis.StudyRecipeKey, "cfd-external-aero")
        self.assertEqual(physics.TurbulenceModel, "kOmegaSST")
        self.assertFalse(physics.HeatTransfer)
        self.assertTrue(initial.UsePotentialFlow)
        self.assertEqual(initial.Ux, 20.0)
        self.assertEqual(initial.Uy, 0.0)
        self.assertEqual(initial.Uz, 0.0)
        self.assertEqual(solver.OpenFOAMSolver, "simpleFoam")
        self.assertEqual(mesh.MeshFormat, "OpenFOAM (polyMesh)")

    def test_buildings_defaults_apply_expected_baseline_values(self):
        from flow_studio.workflows.studies import apply_buildings_defaults

        analysis = types.SimpleNamespace(PhysicsDomain="CFD", AnalysisType="Internal Flow", StudyRecipeKey="", Label="")
        physics = types.SimpleNamespace(TurbulenceModel="kOmegaSST")
        fluid = types.SimpleNamespace(Preset="Custom", MaterialName="", ReferenceTemperature=0.0)
        solver = types.SimpleNamespace(MaxIterations=0, OpenFOAMSolver="pimpleFoam")
        initial = types.SimpleNamespace(Ux=0.0, Uy=1.0, Uz=2.0)
        mesh = types.SimpleNamespace(CharacteristicLength=0.0, MinElementSize=0.0, MaxElementSize=0.0)
        post = types.SimpleNamespace(Label="", AvailableFields=[], ActiveField="", VisualizationType="")
        plot = types.SimpleNamespace(Label="", PlotKind="Surface Plot", Field="", CutPlane="XY Plane", Contours=False)

        apply_buildings_defaults(
            analysis,
            physics_model=physics,
            fluid_material=fluid,
            solver=solver,
            initial_conditions=initial,
            mesh=mesh,
            post_pipeline=post,
            result_plot=plot,
        )

        self.assertEqual(analysis.StudyRecipeKey, "cfd-buildings")
        self.assertEqual(analysis.Label, "Wind Around Buildings Study")
        self.assertEqual(physics.TurbulenceModel, "kEpsilon")
        self.assertEqual(initial.Ux, 8.0)
        self.assertEqual(post.ActiveField, "Velocity Magnitude")
        self.assertEqual(plot.Field, "Velocity Magnitude")
        self.assertEqual(plot.CutPlane, "YZ Plane")

    def test_cooling_channel_defaults_apply_expected_baseline_values(self):
        from flow_studio.workflows.studies import apply_cooling_channel_defaults

        analysis = types.SimpleNamespace(PhysicsDomain="CFD", AnalysisType="Internal Flow", StudyRecipeKey="", Label="")
        physics = types.SimpleNamespace(TurbulenceModel="kEpsilon")
        fluid = types.SimpleNamespace(Preset="Custom", MaterialName="", ReferenceTemperature=0.0)
        solid = types.SimpleNamespace(MaterialPreset="", MaterialName="")
        solver = types.SimpleNamespace(OpenFOAMSolver="simpleFoam", MaxIterations=0)
        initial = types.SimpleNamespace(Temperature=0.0, UsePotentialFlow=True)
        mesh = types.SimpleNamespace(CharacteristicLength=0.0, MinElementSize=0.0, MaxElementSize=0.0, GrowthRate=0.0)
        inlet = types.SimpleNamespace(BCLabel="", VelocityMagnitude=0.0, InletTemperature=0.0)
        outlet = types.SimpleNamespace(BCLabel="", StaticPressure=1.0)
        wall = types.SimpleNamespace(BCLabel="", ThermalType="Adiabatic")
        post = types.SimpleNamespace(Label="", AvailableFields=[], ActiveField="", VisualizationType="")
        plot = types.SimpleNamespace(Label="", PlotKind="Surface Plot", Field="", CutPlane="XY Plane", Contours=False)

        apply_cooling_channel_defaults(
            analysis,
            physics_model=physics,
            fluid_material=fluid,
            solid_material=solid,
            solver=solver,
            initial_conditions=initial,
            mesh=mesh,
            inlet_bc=inlet,
            outlet_bc=outlet,
            wall_bc=wall,
            post_pipeline=post,
            result_plot=plot,
        )

        self.assertEqual(analysis.StudyRecipeKey, "cfd-cooling-channel")
        self.assertEqual(analysis.Label, "Cooling Channel Study")
        self.assertEqual(solver.OpenFOAMSolver, "chtMultiRegionSimpleFoam")
        self.assertEqual(initial.Temperature, 300.15)
        self.assertEqual(inlet.BCLabel, "channel_inlet")
        self.assertEqual(post.ActiveField, "Temperature")
        self.assertEqual(plot.Field, "Temperature")

    def test_airfoil_defaults_apply_expected_baseline_values(self):
        from flow_studio.workflows.studies import apply_airfoil_defaults

        analysis = types.SimpleNamespace(PhysicsDomain="CFD", AnalysisType="Internal Flow", StudyRecipeKey="", Label="")
        physics = types.SimpleNamespace(TurbulenceModel="kEpsilon")
        fluid = types.SimpleNamespace(Preset="Custom", MaterialName="", ReferenceTemperature=0.0)
        solver = types.SimpleNamespace(MaxIterations=0, OpenFOAMSolver="pimpleFoam")
        initial = types.SimpleNamespace(Ux=0.0, Uy=1.0, Uz=2.0)
        mesh = types.SimpleNamespace(CharacteristicLength=0.0, MinElementSize=0.0, MaxElementSize=0.0, GrowthRate=0.0)
        post = types.SimpleNamespace(Label="", AvailableFields=[], ActiveField="", VisualizationType="")
        plot = types.SimpleNamespace(Label="", PlotKind="Cut Plot", Field="", Contours=False)

        apply_airfoil_defaults(
            analysis,
            physics_model=physics,
            fluid_material=fluid,
            solver=solver,
            initial_conditions=initial,
            mesh=mesh,
            post_pipeline=post,
            result_plot=plot,
        )

        self.assertEqual(analysis.StudyRecipeKey, "cfd-airfoil-naca-0012")
        self.assertEqual(analysis.Label, "NACA 0012 Airfoil Study")
        self.assertEqual(physics.TurbulenceModel, "kOmegaSST")
        self.assertEqual(initial.Ux, 30.0)
        self.assertEqual(post.ActiveField, "Pressure Coefficient")
        self.assertEqual(plot.Field, "Pressure Coefficient")
        self.assertEqual(plot.PlotKind, "Surface Plot")

    def test_tesla_valve_defaults_apply_expected_baseline_values(self):
        from flow_studio.workflows.studies import apply_tesla_valve_defaults

        analysis = types.SimpleNamespace(PhysicsDomain="CFD", AnalysisType="External Flow", StudyRecipeKey="", Label="")
        physics = types.SimpleNamespace(TurbulenceModel="kEpsilon")
        fluid = types.SimpleNamespace(Preset="Custom", MaterialName="", ReferenceTemperature=0.0)
        solver = types.SimpleNamespace(MaxIterations=0, OpenFOAMSolver="pimpleFoam")
        initial = types.SimpleNamespace(Ux=0.0, Uy=1.0, Uz=2.0, Pressure=99.0)
        mesh = types.SimpleNamespace(CharacteristicLength=0.0, MinElementSize=0.0, MaxElementSize=0.0, GrowthRate=0.0)
        post = types.SimpleNamespace(Label="", AvailableFields=[], ActiveField="", VisualizationType="")
        plot = types.SimpleNamespace(Label="", PlotKind="Surface Plot", Field="", CutPlane="YZ Plane", Contours=False)

        apply_tesla_valve_defaults(
            analysis,
            physics_model=physics,
            fluid_material=fluid,
            solver=solver,
            initial_conditions=initial,
            mesh=mesh,
            post_pipeline=post,
            result_plot=plot,
        )

        self.assertEqual(analysis.StudyRecipeKey, "cfd-tesla-valve")
        self.assertEqual(analysis.Label, "Tesla Valve Study")
        self.assertEqual(initial.Ux, 1.5)
        self.assertEqual(post.ActiveField, "Pressure")
        self.assertEqual(plot.Field, "Pressure")
        self.assertEqual(plot.CutPlane, "XY Plane")

    def test_von_karman_defaults_apply_expected_baseline_values(self):
        from flow_studio.workflows.studies import apply_von_karman_defaults

        analysis = types.SimpleNamespace(PhysicsDomain="CFD", AnalysisType="Internal Flow", StudyRecipeKey="", Label="")
        physics = types.SimpleNamespace(TimeModel="Steady", TurbulenceModel="kEpsilon")
        fluid = types.SimpleNamespace(Preset="Custom", MaterialName="", ReferenceTemperature=0.0)
        solver = types.SimpleNamespace(MaxIterations=0, OpenFOAMSolver="simpleFoam")
        initial = types.SimpleNamespace(Ux=0.0, Uy=1.0, Uz=2.0, UsePotentialFlow=True)
        mesh = types.SimpleNamespace(CharacteristicLength=0.0, MinElementSize=0.0, MaxElementSize=0.0, GrowthRate=0.0)
        post = types.SimpleNamespace(Label="", AvailableFields=[], ActiveField="", VisualizationType="")
        plot = types.SimpleNamespace(Label="", PlotKind="Surface Plot", Field="", CutPlane="XY Plane", Contours=False)

        apply_von_karman_defaults(
            analysis,
            physics_model=physics,
            fluid_material=fluid,
            solver=solver,
            initial_conditions=initial,
            mesh=mesh,
            post_pipeline=post,
            result_plot=plot,
        )

        self.assertEqual(analysis.StudyRecipeKey, "cfd-von-karman-vortex-street")
        self.assertEqual(analysis.Label, "Von Karman Vortex Study")
        self.assertEqual(physics.TimeModel, "Transient")
        self.assertEqual(solver.OpenFOAMSolver, "pimpleFoam")
        self.assertFalse(initial.UsePotentialFlow)
        self.assertEqual(post.ActiveField, "Vorticity")
        self.assertEqual(plot.Field, "Vorticity")
        self.assertEqual(plot.CutPlane, "YZ Plane")

    def test_pipe_flow_defaults_apply_expected_baseline_values(self):
        from flow_studio.workflows.studies import apply_pipe_flow_defaults

        analysis = types.SimpleNamespace(PhysicsDomain="CFD", AnalysisType="External Flow", StudyRecipeKey="", Label="")
        physics = types.SimpleNamespace(FlowRegime="Laminar", TurbulenceModel="kEpsilon", HeatTransfer=True, Compressibility="Compressible", TimeModel="Transient", PassiveScalar=True)
        fluid = types.SimpleNamespace(Preset="Custom", MaterialName="", ReferenceTemperature=0.0)
        solver = types.SimpleNamespace(SolverBackend="Elmer", OpenFOAMSolver="pimpleFoam", MaxIterations=0, ConvergenceTolerance=1.0, ConvectionScheme="upwind")
        initial = types.SimpleNamespace(Ux=0.0, Uy=1.0, Uz=2.0, Pressure=99.0, UsePotentialFlow=True)
        mesh = types.SimpleNamespace(CharacteristicLength=0.0, MinElementSize=0.0, MaxElementSize=0.0, GrowthRate=0.0, MeshFormat="SU2 (.su2)")
        post = types.SimpleNamespace(Label="")

        apply_pipe_flow_defaults(
            analysis,
            physics_model=physics,
            fluid_material=fluid,
            solver=solver,
            initial_conditions=initial,
            mesh=mesh,
            post_pipeline=post,
        )

        self.assertEqual(analysis.AnalysisType, "Internal Flow")
        self.assertEqual(analysis.StudyRecipeKey, "cfd-pipe-flow")
        self.assertEqual(physics.TurbulenceModel, "kOmegaSST")
        self.assertFalse(physics.PassiveScalar)
        self.assertEqual(fluid.Preset, "Water (20°C)")
        self.assertEqual(solver.OpenFOAMSolver, "simpleFoam")
        self.assertEqual(initial.Ux, 1.0)
        self.assertFalse(initial.UsePotentialFlow)
        self.assertEqual(mesh.MeshFormat, "OpenFOAM (polyMesh)")

    def test_static_mixer_defaults_apply_expected_baseline_values(self):
        from flow_studio.workflows.studies import apply_static_mixer_defaults

        analysis = types.SimpleNamespace(PhysicsDomain="CFD", AnalysisType="External Flow", StudyRecipeKey="", Label="")
        physics = types.SimpleNamespace(FlowRegime="Laminar", TurbulenceModel="kEpsilon", HeatTransfer=True, Compressibility="Compressible", TimeModel="Steady", PassiveScalar=False)
        fluid = types.SimpleNamespace(Preset="Custom", MaterialName="", ReferenceTemperature=0.0)
        solver = types.SimpleNamespace(SolverBackend="Elmer", OpenFOAMSolver="simpleFoam", MaxIterations=0, ConvergenceTolerance=1.0, ConvectionScheme="upwind")
        initial = types.SimpleNamespace(Ux=0.0, Uy=1.0, Uz=2.0, Pressure=99.0, UsePotentialFlow=True)
        mesh = types.SimpleNamespace(CharacteristicLength=0.0, MinElementSize=0.0, MaxElementSize=0.0, GrowthRate=0.0, MeshFormat="SU2 (.su2)")
        post = types.SimpleNamespace(Label="")

        apply_static_mixer_defaults(
            analysis,
            physics_model=physics,
            fluid_material=fluid,
            solver=solver,
            initial_conditions=initial,
            mesh=mesh,
            post_pipeline=post,
        )

        self.assertEqual(analysis.AnalysisType, "Internal Flow")
        self.assertEqual(analysis.StudyRecipeKey, "cfd-static-mixer")
        self.assertEqual(physics.TimeModel, "Transient")
        self.assertTrue(physics.PassiveScalar)
        self.assertEqual(fluid.Preset, "Water (20°C)")
        self.assertEqual(solver.OpenFOAMSolver, "pimpleFoam")
        self.assertEqual(initial.Ux, 0.8)
        self.assertFalse(initial.UsePotentialFlow)
        self.assertEqual(mesh.MeshFormat, "OpenFOAM (polyMesh)")

    def test_structural_bracket_defaults_apply_expected_result_baseline(self):
        from flow_studio.workflows.studies import apply_structural_bracket_defaults

        analysis = types.SimpleNamespace(PhysicsDomain="CFD", AnalysisType="", StudyRecipeKey="", Label="")
        physics = types.SimpleNamespace(AnalysisModel="", TimeModel="Transient", Gravity=True)
        material = types.SimpleNamespace(MaterialPreset="", MaterialName="")
        solver = types.SimpleNamespace(SolverBackend="")
        fixed = types.SimpleNamespace(BCLabel="")
        force = types.SimpleNamespace(BCLabel="", ForceZ=0.0)
        post = types.SimpleNamespace(Label="", AvailableFields=[], ActiveField="", VisualizationType="")
        plot = types.SimpleNamespace(Label="", PlotKind="Cut Plot", Field="", Contours=False, Vectors=True)

        apply_structural_bracket_defaults(
            analysis,
            physics_model=physics,
            solid_material=material,
            solver=solver,
            fixed_constraint=fixed,
            force_constraint=force,
            post_pipeline=post,
            result_plot=plot,
        )

        self.assertEqual(analysis.StudyRecipeKey, "structural-bracket-example")
        self.assertEqual(post.ActiveField, "Von Mises Stress")
        self.assertIn("Displacement", post.AvailableFields)
        self.assertEqual(plot.Field, "Von Mises Stress")
        self.assertEqual(plot.PlotKind, "Surface Plot")

    def test_electrostatic_capacitor_defaults_apply_expected_result_baseline(self):
        from flow_studio.workflows.studies import apply_electrostatic_capacitor_defaults

        analysis = types.SimpleNamespace(PhysicsDomain="CFD", AnalysisType="", StudyRecipeKey="", Label="")
        physics = types.SimpleNamespace(CalculateCapacitanceMatrix=False)
        material = types.SimpleNamespace(MaterialPreset="", MaterialName="")
        solver = types.SimpleNamespace(SolverBackend="")
        positive = types.SimpleNamespace(BCLabel="", Potential=0.0)
        ground = types.SimpleNamespace(BCLabel="", Potential=1.0)
        post = types.SimpleNamespace(Label="", AvailableFields=[], ActiveField="", VisualizationType="")
        plot = types.SimpleNamespace(Label="", PlotKind="Surface Plot", Field="", CutPlane="XY Plane", Contours=False)

        apply_electrostatic_capacitor_defaults(
            analysis,
            physics_model=physics,
            material=material,
            solver=solver,
            positive_bc=positive,
            ground_bc=ground,
            post_pipeline=post,
            result_plot=plot,
        )

        self.assertTrue(physics.CalculateCapacitanceMatrix)
        self.assertEqual(post.ActiveField, "Electric Potential")
        self.assertEqual(post.VisualizationType, "Contour (Slice)")
        self.assertEqual(plot.Field, "Electric Potential")
        self.assertEqual(plot.CutPlane, "YZ Plane")

    def test_electromagnetic_coil_defaults_apply_expected_result_baseline(self):
        from flow_studio.workflows.studies import apply_electromagnetic_coil_defaults

        analysis = types.SimpleNamespace(PhysicsDomain="CFD", AnalysisType="", StudyRecipeKey="", Label="")
        physics = types.SimpleNamespace(EMModel="", TimeModel="Transient")
        material = types.SimpleNamespace(MaterialPreset="", MaterialName="")
        solver = types.SimpleNamespace(SolverBackend="")
        current = types.SimpleNamespace(BCLabel="", CurrentDensityZ=0.0)
        boundary = types.SimpleNamespace(BCLabel="", ZeroPotential=False)
        post = types.SimpleNamespace(Label="", AvailableFields=[], ActiveField="", VisualizationType="")
        plot = types.SimpleNamespace(Label="", PlotKind="Cut Plot", Field="", Contours=False)

        apply_electromagnetic_coil_defaults(
            analysis,
            physics_model=physics,
            material=material,
            solver=solver,
            current_bc=current,
            boundary_bc=boundary,
            post_pipeline=post,
            result_plot=plot,
        )

        self.assertEqual(analysis.StudyRecipeKey, "electromagnetic-coil-example")
        self.assertEqual(current.CurrentDensityZ, 2000000.0)
        self.assertEqual(post.ActiveField, "Magnetic Flux Density")
        self.assertEqual(plot.Field, "Magnetic Flux Density")

    def test_thermal_plate_defaults_apply_expected_result_baseline(self):
        from flow_studio.workflows.studies import apply_thermal_plate_defaults

        analysis = types.SimpleNamespace(PhysicsDomain="CFD", AnalysisType="", StudyRecipeKey="", Label="")
        physics = types.SimpleNamespace(TimeModel="Transient", Convection=False, InternalHeatGeneration=True)
        material = types.SimpleNamespace(MaterialPreset="", MaterialName="")
        solver = types.SimpleNamespace(SolverBackend="")
        heat_flux = types.SimpleNamespace(BCLabel="", HeatFlux=0.0)
        convection = types.SimpleNamespace(BCLabel="", HeatTransferCoefficient=0.0, AmbientTemperature=0.0)
        post = types.SimpleNamespace(Label="", AvailableFields=[], ActiveField="", VisualizationType="")
        plot = types.SimpleNamespace(Label="", PlotKind="Surface Plot", Field="", CutPlane="XZ Plane", Contours=False)

        apply_thermal_plate_defaults(
            analysis,
            physics_model=physics,
            material=material,
            solver=solver,
            heat_flux_bc=heat_flux,
            convection_bc=convection,
            post_pipeline=post,
            result_plot=plot,
        )

        self.assertEqual(analysis.StudyRecipeKey, "thermal-plate-example")
        self.assertEqual(heat_flux.HeatFlux, 5000.0)
        self.assertEqual(post.ActiveField, "Temperature")
        self.assertEqual(plot.Field, "Temperature")
        self.assertEqual(plot.CutPlane, "XY Plane")

    def test_optical_lens_defaults_apply_expected_result_baseline(self):
        from flow_studio.workflows.studies import apply_optical_lens_defaults

        analysis = types.SimpleNamespace(PhysicsDomain="CFD", AnalysisType="", StudyRecipeKey="", Label="")
        physics = types.SimpleNamespace(OpticalModel="", Wavelength=0.0, RayCount=0)
        material = types.SimpleNamespace(MaterialPreset="", MaterialName="", OpticalRole="")
        solver = types.SimpleNamespace(SolverBackend="")
        source = types.SimpleNamespace(BCLabel="", SourceType="", Power=0.0, Wavelength=0.0, RayCount=0)
        detector = types.SimpleNamespace(BCLabel="", DetectorType="")
        boundary = types.SimpleNamespace(BCLabel="", BoundaryType="", Reflectivity=0.0)
        post = types.SimpleNamespace(Label="", AvailableFields=[], ActiveField="", VisualizationType="")
        plot = types.SimpleNamespace(Label="", PlotKind="Cut Plot", Field="", Contours=False)

        apply_optical_lens_defaults(
            analysis,
            physics_model=physics,
            material=material,
            solver=solver,
            source_bc=source,
            detector_bc=detector,
            boundary_bc=boundary,
            post_pipeline=post,
            result_plot=plot,
        )

        self.assertEqual(analysis.StudyRecipeKey, "optical-lens-example")
        self.assertEqual(post.ActiveField, "Irradiance")
        self.assertIn("Illuminance", post.AvailableFields)
        self.assertEqual(plot.Field, "Irradiance")
        self.assertEqual(solver.SolverBackend, "Raysect")

    def test_is_electronics_cooling_analysis_matches_cht_only(self):
        from flow_studio.workflows.studies import is_electronics_cooling_analysis

        self.assertTrue(is_electronics_cooling_analysis(types.SimpleNamespace(PhysicsDomain="CFD", AnalysisType="Conjugate Heat Transfer")))
        self.assertFalse(is_electronics_cooling_analysis(types.SimpleNamespace(PhysicsDomain="CFD", AnalysisType="Internal Flow")))
        self.assertFalse(is_electronics_cooling_analysis(types.SimpleNamespace(PhysicsDomain="Thermal", AnalysisType="Conjugate Heat Transfer")))

    def test_simflow_tutorial_coverage_catalog_contains_all_public_examples(self):
        from flow_studio.workflows.tutorial_coverage import all_tutorial_coverage

        coverage = all_tutorial_coverage()
        self.assertEqual(len(coverage), 28)
        self.assertEqual(len({entry.key for entry in coverage}), 28)

    def test_simflow_tutorial_coverage_keeps_electronics_cooling_as_phase_1_pilot(self):
        from flow_studio.workflows.tutorial_coverage import get_tutorial_coverage

        entry = get_tutorial_coverage("electronics-cooling")
        self.assertIsNotNone(entry)
        self.assertEqual(entry.phase, "Phase 1")
        self.assertEqual(entry.current_posture, "pilot-scaffold-implemented")
        self.assertIn("study-recipe", entry.capabilities)

    def test_phase_zero_family_scaffolds_are_tracked_in_coverage_catalog(self):
        from flow_studio.workflows.tutorial_coverage import get_tutorial_coverage

        self.assertEqual(get_tutorial_coverage("pipe-flow").current_posture, "family-scaffold-implemented")
        self.assertEqual(get_tutorial_coverage("wing").current_posture, "family-scaffold-implemented")
        self.assertEqual(get_tutorial_coverage("static-mixer").current_posture, "family-scaffold-implemented")
        self.assertIn("study-recipe", get_tutorial_coverage("pipe-flow").capabilities)

    def test_phase_zero_dedicated_starters_are_tracked_in_coverage_catalog(self):
        from flow_studio.workflows.tutorial_coverage import get_tutorial_coverage

        self.assertEqual(get_tutorial_coverage("buildings").current_posture, "starter-scaffold-implemented")
        self.assertEqual(get_tutorial_coverage("airfoil-naca-0012").current_posture, "starter-scaffold-implemented")
        self.assertEqual(get_tutorial_coverage("tesla-valve").current_posture, "starter-scaffold-implemented")
        self.assertEqual(get_tutorial_coverage("von-karman-vortex-street").current_posture, "starter-scaffold-implemented")
        self.assertIn("study-recipe", get_tutorial_coverage("buildings").capabilities)
        self.assertIn("study-recipe", get_tutorial_coverage("airfoil-naca-0012").capabilities)
        self.assertIn("study-recipe", get_tutorial_coverage("tesla-valve").capabilities)
        self.assertIn("study-recipe", get_tutorial_coverage("von-karman-vortex-street").capabilities)

    def test_phase_one_cooling_channel_starter_is_tracked_in_coverage_catalog(self):
        from flow_studio.workflows.tutorial_coverage import get_tutorial_coverage

        self.assertEqual(get_tutorial_coverage("cooling-channel").current_posture, "starter-scaffold-implemented")
        self.assertIn("study-recipe", get_tutorial_coverage("cooling-channel").capabilities)

    def test_simflow_tutorial_coverage_phase_zero_contains_foundation_cases(self):
        from flow_studio.workflows.tutorial_coverage import tutorial_coverage_by_phase

        phase_zero = tutorial_coverage_by_phase("Phase 0")
        self.assertEqual(len(phase_zero), 8)
        self.assertIn("pipe-flow", {entry.key for entry in phase_zero})
        self.assertIn("wing", {entry.key for entry in phase_zero})


class TestOpticalPresetCatalog(unittest.TestCase):
    """Validate the richer optical preset catalog used by the optics workflow."""

    def test_bk7_has_dispersion_coefficients(self):
        from flow_studio.catalog.optics import get_optical_material_preset

        bk7 = get_optical_material_preset("BK7")
        self.assertGreater(bk7["SellmeierB1"], 1.0)
        self.assertGreater(bk7["WavelengthMax"], bk7["WavelengthMin"])
        self.assertEqual(bk7["DispersionModel"], "Sellmeier")

    def test_custom_entry_not_in_catalog(self):
        from flow_studio.catalog.optics import OPTICAL_MATERIAL_PRESETS, get_optical_material_preset_names

        self.assertNotIn("Custom", OPTICAL_MATERIAL_PRESETS)
        self.assertEqual(get_optical_material_preset_names()[0], "Custom")


if __name__ == "__main__":
    unittest.main()