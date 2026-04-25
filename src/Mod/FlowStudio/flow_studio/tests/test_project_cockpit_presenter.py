# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Unit tests for the UI-neutral FlowStudio cockpit presenter."""

import os
import sys
import types
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


class TestProjectCockpitPresenter(unittest.TestCase):
    @staticmethod
    def _make_service(*, analysis=None, profile_label="CFD", study_recipe=None, steps=(), snapshot=None,
                      sync_post_pipeline_fn=None, terminate_run_fn=None):
        class FakeService:
            def get_active_analysis(self):
                return analysis

            def get_workflow_context(self):
                return {
                    "analysis": analysis,
                    "profile": types.SimpleNamespace(label=profile_label),
                    "study_recipe": study_recipe,
                }

            def get_workflow_status(self):
                return steps

            def get_run_snapshot(self, _analysis=None):
                return snapshot or {
                    "status": "IDLE",
                    "phase": "No active run",
                    "progress_percent": None,
                    "elapsed_seconds": 0.0,
                    "backend": "",
                    "case_dir": "",
                    "pid": None,
                    "result_path": "",
                    "result_format": "",
                    "last_error": "",
                    "log_tail": [],
                }

            def sync_post_pipeline(self, current_analysis, *, snapshot=None):
                if sync_post_pipeline_fn is not None:
                    return sync_post_pipeline_fn(current_analysis, snapshot=snapshot)
                return None

            def terminate_run(self, current_analysis=None):
                if terminate_run_fn is not None:
                    return terminate_run_fn(current_analysis)
                return False

        return FakeService()

    def test_build_view_state_returns_toolkit_neutral_cockpit_state(self):
        from flow_studio.ui.project_cockpit_presenter import ProjectCockpitPresenter

        analysis = types.SimpleNamespace(
            Label="Cooling Study",
            Name="Analysis",
            Group=[
                types.SimpleNamespace(Name="PrimaryPlot", FlowType="FlowStudio::ResultPlot"),
            ],
        )
        recipe = types.SimpleNamespace(
            label="Electronics Cooling",
            summary="Reference CFD recipe",
            reference_url="https://example.invalid/recipe",
            milestones=("Import the enclosure", "Assign fan zone"),
            key_parameters=("MaxIterations=800", "k-epsilon"),
        )
        profile = types.SimpleNamespace(label="CFD")
        steps = (
            types.SimpleNamespace(
                number=1,
                name="Analysis",
                description="Create the analysis",
                complete=True,
                active=True,
                command_name="FlowStudio_Analysis",
                hint="",
            ),
            types.SimpleNamespace(
                number=2,
                name="Import Geometry",
                description="Import the CAD model",
                complete=False,
                active=True,
                command_name="FlowStudio_ImportStep",
                hint="Bring in the main assembly",
            ),
            types.SimpleNamespace(
                number=3,
                name="Mesh",
                description="Generate the mesh",
                complete=False,
                active=False,
                command_name="FlowStudio_MeshGmsh",
                hint="",
            ),
        )
        snapshot = {
            "status": "RUNNING",
            "phase": "Iterating solver",
            "progress_percent": 25.0,
            "elapsed_seconds": 18.4,
            "backend": "OpenFOAM",
            "case_dir": "C:/case",
            "pid": 4242,
            "result_path": "C:/case/postProcessing",
            "result_format": "OpenFOAM",
            "last_error": "",
            "log_tail": ["iter 1", "iter 2"],
        }
        sync_calls = []

        presenter = ProjectCockpitPresenter(
            (
                ("FlowStudio_Analysis", "1. Analysis"),
                ("FlowStudio_ImportStep", "2. Import Model"),
                ("FlowStudio_MeshGmsh", "4. Mesh"),
            ),
            service=self._make_service(
                analysis=analysis,
                profile_label=profile.label,
                study_recipe=recipe,
                steps=steps,
                snapshot=snapshot,
                sync_post_pipeline_fn=lambda _analysis, snapshot=None: sync_calls.append(snapshot),
            ),
        )

        state = presenter.build_view_state()

        self.assertEqual(state.profile_label, "CFD")
        self.assertEqual(state.analysis_label, "Cooling Study")
        self.assertEqual(state.progress_percent, 33)
        self.assertEqual(state.banner.level, "active")
        self.assertIn("2. Import Geometry", state.banner.title)
        self.assertTrue(state.recipe.visible)
        self.assertEqual(state.steps[2].level, "blocked")
        self.assertEqual(state.actions[0].level, "done")
        self.assertTrue(state.actions[1].enabled)
        self.assertFalse(state.actions[2].enabled)
        self.assertEqual(state.runtime.level, "running")
        self.assertTrue(state.runtime.progress_indeterminate is False)
        self.assertTrue(state.runtime.stop_enabled)
        self.assertTrue(state.runtime.results_enabled)
        self.assertEqual(state.runtime.results_label, "Open Primary Plot")
        self.assertEqual(len(sync_calls), 1)
        self.assertEqual(sync_calls[0]["result_path"], "C:/case/postProcessing")

    def test_stop_run_and_result_target_delegate_to_injected_application_hooks(self):
        from flow_studio.ui.project_cockpit_presenter import ProjectCockpitPresenter

        target = types.SimpleNamespace(Name="ResultPlot", FlowType="FlowStudio::ResultPlot")
        analysis = types.SimpleNamespace(Group=[target])
        terminate_calls = []

        presenter = ProjectCockpitPresenter(
            (),
            service=self._make_service(
                analysis=analysis,
                terminate_run_fn=lambda current: terminate_calls.append(current) or True,
            ),
        )

        self.assertIs(presenter.resolve_results_target(), target)
        self.assertTrue(presenter.stop_run())
        self.assertEqual(terminate_calls, [analysis])

    def test_user_intents_delegate_to_action_port(self):
        from flow_studio.ui.project_cockpit_presenter import ProjectCockpitPresenter

        target = types.SimpleNamespace(Name="ResultPlot", FlowType="FlowStudio::ResultPlot")
        analysis = types.SimpleNamespace(Group=[target])
        commands = []
        activations = []

        class FakeActions:
            def execute_command(self, command_name):
                commands.append(command_name)

            def activate_result_target(self, object_name):
                activations.append(object_name)
                return False

        presenter = ProjectCockpitPresenter(
            (("FlowStudio_RunSolver", "6. Run"),),
            service=self._make_service(analysis=analysis),
            actions=FakeActions(),
        )

        self.assertTrue(presenter.handle_command("FlowStudio_RunSolver"))
        self.assertEqual(commands, ["FlowStudio_RunSolver"])

        self.assertTrue(presenter.handle_open_results())
        self.assertEqual(activations, ["ResultPlot"])
        self.assertEqual(commands, ["FlowStudio_RunSolver", "FlowStudio_PostPipeline"])


if __name__ == "__main__":
    unittest.main()