# SPDX-License-Identifier: LGPL-2.1-or-later

SET(FlowStudioBase_SRCS
    Init.py
    InitGui.py
)

SET(FlowStudioPackage_SRCS
    flow_studio/__init__.py
    flow_studio/commands.py
    flow_studio/ObjectsFlowStudio.py
    flow_studio/physics_domains.py
    flow_studio/solver_deps.py
    flow_studio/solver_installer.py
    flow_studio/workflow_guide.py
)

SET(FlowStudioFeminout_SRCS
    flow_studio/feminout/__init__.py
    flow_studio/feminout/importFlowStudio.py
)

SET(FlowStudioObjects_SRCS
    flow_studio/objects/__init__.py
    flow_studio/objects/analysis.py
    flow_studio/objects/base_bc.py
    flow_studio/objects/base_object.py
    flow_studio/objects/bc_electromagnetic.py
    flow_studio/objects/bc_electrostatic.py
    flow_studio/objects/bc_inlet.py
    flow_studio/objects/bc_open_boundary.py
    flow_studio/objects/bc_outlet.py
    flow_studio/objects/bc_structural.py
    flow_studio/objects/bc_symmetry.py
    flow_studio/objects/bc_thermal.py
    flow_studio/objects/bc_wall.py
    flow_studio/objects/boundary_layer.py
    flow_studio/objects/electromagnetic_material.py
    flow_studio/objects/electromagnetic_physics_model.py
    flow_studio/objects/electrostatic_material.py
    flow_studio/objects/electrostatic_physics_model.py
    flow_studio/objects/fluid_material.py
    flow_studio/objects/initial_conditions.py
    flow_studio/objects/measurement_point.py
    flow_studio/objects/measurement_surface.py
    flow_studio/objects/measurement_volume.py
    flow_studio/objects/mesh_gmsh.py
    flow_studio/objects/mesh_region.py
    flow_studio/objects/physics_model.py
    flow_studio/objects/post_pipeline.py
    flow_studio/objects/solid_material.py
    flow_studio/objects/solver.py
    flow_studio/objects/structural_physics_model.py
    flow_studio/objects/thermal_material.py
    flow_studio/objects/thermal_physics_model.py
)

SET(FlowStudioSolvers_SRCS
    flow_studio/solvers/__init__.py
    flow_studio/solvers/base_solver.py
    flow_studio/solvers/elmer_runner.py
    flow_studio/solvers/elmer_sif.py
    flow_studio/solvers/fluidx3d_runner.py
    flow_studio/solvers/openfoam_runner.py
    flow_studio/solvers/registry.py
)

SET(FlowStudioTaskpanels_SRCS
    flow_studio/taskpanels/__init__.py
    flow_studio/taskpanels/base_taskpanel.py
    flow_studio/taskpanels/task_bc_inlet.py
    flow_studio/taskpanels/task_bc_open.py
    flow_studio/taskpanels/task_bc_outlet.py
    flow_studio/taskpanels/task_bc_wall.py
    flow_studio/taskpanels/task_fluid_material.py
    flow_studio/taskpanels/task_initial_conditions.py
    flow_studio/taskpanels/task_measurement_point.py
    flow_studio/taskpanels/task_measurement_surface.py
    flow_studio/taskpanels/task_measurement_volume.py
    flow_studio/taskpanels/task_mesh_gmsh.py
    flow_studio/taskpanels/task_physics_model.py
    flow_studio/taskpanels/task_post_pipeline.py
    flow_studio/taskpanels/task_solver.py
)

SET(FlowStudioUtils_SRCS
    flow_studio/utils/__init__.py
    flow_studio/utils/mesh_utils.py
    flow_studio/utils/paraview_script.py
    flow_studio/utils/post_utils.py
)

SET(FlowStudioViewproviders_SRCS
    flow_studio/viewproviders/__init__.py
    flow_studio/viewproviders/base_vp.py
    flow_studio/viewproviders/vp_analysis.py
    flow_studio/viewproviders/vp_bc_inlet.py
    flow_studio/viewproviders/vp_bc_open_boundary.py
    flow_studio/viewproviders/vp_bc_outlet.py
    flow_studio/viewproviders/vp_bc_symmetry.py
    flow_studio/viewproviders/vp_bc_wall.py
    flow_studio/viewproviders/vp_boundary_layer.py
    flow_studio/viewproviders/vp_fluid_material.py
    flow_studio/viewproviders/vp_initial_conditions.py
    flow_studio/viewproviders/vp_measurement_point.py
    flow_studio/viewproviders/vp_measurement_surface.py
    flow_studio/viewproviders/vp_measurement_volume.py
    flow_studio/viewproviders/vp_mesh_gmsh.py
    flow_studio/viewproviders/vp_mesh_region.py
    flow_studio/viewproviders/vp_physics_model.py
    flow_studio/viewproviders/vp_post_pipeline.py
    flow_studio/viewproviders/vp_solver.py
)

SET(FlowStudioTests_SRCS
    flow_studio/tests/__init__.py
    flow_studio/tests/run_e2e_tests.py
    flow_studio/tests/test_cascading_delete.py
    flow_studio/tests/test_dependencies.py
    flow_studio/tests/test_e2e_cfd_workflow.py
    flow_studio/tests/test_e2e_real_solver.py
    flow_studio/tests/test_e2e_step_import.py
    flow_studio/tests/test_elmer_sif_detailed.py
    flow_studio/tests/test_mesh_and_materials.py
    flow_studio/tests/test_multiphysics.py
    flow_studio/tests/test_objects.py
    flow_studio/tests/test_openfoam.py
    flow_studio/tests/test_physics_domains_detailed.py
    flow_studio/tests/test_registry_detailed.py
)

SET(all_files
    ${FlowStudioBase_SRCS}
    ${FlowStudioPackage_SRCS}
    ${FlowStudioFeminout_SRCS}
    ${FlowStudioObjects_SRCS}
    ${FlowStudioSolvers_SRCS}
    ${FlowStudioTaskpanels_SRCS}
    ${FlowStudioUtils_SRCS}
    ${FlowStudioViewproviders_SRCS}
    ${FlowStudioTests_SRCS}
)

ADD_CUSTOM_TARGET(FlowStudio ALL
    SOURCES ${all_files}
)

fc_copy_sources(FlowStudio "${CMAKE_BINARY_DIR}/Mod/FlowStudio" ${all_files})

INSTALL(FILES ${FlowStudioBase_SRCS} DESTINATION Mod/FlowStudio)
INSTALL(FILES ${FlowStudioPackage_SRCS} DESTINATION Mod/FlowStudio/flow_studio)
INSTALL(FILES ${FlowStudioFeminout_SRCS} DESTINATION Mod/FlowStudio/flow_studio/feminout)
INSTALL(FILES ${FlowStudioObjects_SRCS} DESTINATION Mod/FlowStudio/flow_studio/objects)
INSTALL(FILES ${FlowStudioSolvers_SRCS} DESTINATION Mod/FlowStudio/flow_studio/solvers)
INSTALL(FILES ${FlowStudioTaskpanels_SRCS} DESTINATION Mod/FlowStudio/flow_studio/taskpanels)
INSTALL(FILES ${FlowStudioUtils_SRCS} DESTINATION Mod/FlowStudio/flow_studio/utils)
INSTALL(FILES ${FlowStudioViewproviders_SRCS} DESTINATION Mod/FlowStudio/flow_studio/viewproviders)
INSTALL(FILES ${FlowStudioTests_SRCS} DESTINATION Mod/FlowStudio/flow_studio/tests)

# Icons
FILE(GLOB FlowStudioIcons_SRCS CONFIGURE_DEPENDS "Resources/icons/*.svg")
INSTALL(FILES ${FlowStudioIcons_SRCS} DESTINATION Mod/FlowStudio/Resources/icons)
