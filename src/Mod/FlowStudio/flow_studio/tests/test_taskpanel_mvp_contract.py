# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Static contract tests for FlowStudio taskpanel MVP boundaries."""

from __future__ import annotations

import os
import unittest


TASKPANEL_MVP_SNIPPETS = {
    "task_bc_inlet.py": ["InletBoundaryPresenter", "self._presenter = InletBoundaryPresenter()"],
    "task_bc_open.py": ["OpenBoundaryPresenter", "self._presenter = OpenBoundaryPresenter()"],
    "task_bc_outlet.py": ["OutletBoundaryPresenter", "self._presenter = OutletBoundaryPresenter()"],
    "task_bc_wall.py": ["WallBoundaryPresenter", "self._presenter = WallBoundaryPresenter()"],
    "task_flowefd_features.py": [
        "SelectionPresenter",
        "FreeCADSelectionDesktopAdapter",
        "VolumeSourcePresenter",
        "FanPresenter",
        "ResultPlotPresenter",
        "ParticleStudyPresenter",
    ],
    "task_fluid_material.py": ["FluidMaterialPresenter", "self._presenter = FluidMaterialPresenter()"],
    "task_geant4_result.py": ["Geant4ResultPresenter", "self._presenter = Geant4ResultPresenter()"],
    "task_geant4_result_component.py": [
        "Geant4ResultComponentPresenter",
        "self._presenter = Geant4ResultComponentPresenter()",
    ],
    "task_generic_bc.py": ["GenericBoundaryPresenter", "self._presenter = GenericBoundaryPresenter()"],
    "task_geometry_tools.py": [
        "GeometryCheckPresenter",
        "LeakTrackingPresenter",
        "FlowStudioGeometryCheckService",
        "FlowStudioLeakTrackingService",
    ],
    "task_initial_conditions.py": ["InitialConditionsPresenter", "self._presenter = InitialConditionsPresenter()"],
    "task_materials.py": ["MaterialPresenter", "self._presenter = MaterialPresenter()"],
    "task_measurement_point.py": ["MeasurementPointPresenter", "self._presenter = MeasurementPointPresenter()"],
    "task_measurement_surface.py": ["MeasurementSurfacePresenter", "self._presenter = MeasurementSurfacePresenter()"],
    "task_measurement_volume.py": ["MeasurementVolumePresenter", "self._presenter = MeasurementVolumePresenter()"],
    "task_mesh_gmsh.py": ["MeshGmshPresenter", "self._presenter = MeshGmshPresenter()"],
    "task_physics_model.py": ["PhysicsModelPresenter", "self._presenter = PhysicsModelPresenter()"],
    "task_post_pipeline.py": ["PostPipelinePresenter", "self._presenter = PostPipelinePresenter()"],
    "task_project_cockpit.py": [
        "ProjectCockpitPresenter",
        "FreeCADProjectCockpitActions",
        "FreeCADTaskPanelDesktopLifecycle",
    ],
    "task_solver.py": ["SolverPresenter", "self._presenter = SolverPresenter()"],
    "base_taskpanel.py": ["FreeCADTaskPanelDesktopLifecycle", "self._lifecycle = lifecycle or FreeCADTaskPanelDesktopLifecycle()"],
}


class TestTaskPanelMvpContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        cls.taskpanel_dir = os.path.join(root_dir, "flow_studio", "taskpanels")

    def test_taskpanels_delegate_through_presenters_or_desktop_adapters(self):
        for file_name, snippets in TASKPANEL_MVP_SNIPPETS.items():
            abs_path = os.path.join(self.taskpanel_dir, file_name)
            with open(abs_path, "r", encoding="utf-8") as handle:
                source = handle.read()
            for snippet in snippets:
                self.assertIn(
                    snippet,
                    source,
                    f"Missing MVP delegation snippet in {abs_path}: {snippet}",
                )


if __name__ == "__main__":
    unittest.main()