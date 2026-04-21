# SPDX-License-Identifier: LGPL-2.1-or-later

SET(FlowStudioBase_SRCS
    Init.py
    InitGui.py
)

SET(FlowStudioPackage_SRCS
    flow_studio/__init__.py
    flow_studio/commands.py
    flow_studio/engineering_database.py
    flow_studio/engineering_database_editor.py
    flow_studio/enterprise_commands.py
    flow_studio/geometry_tools.py
    flow_studio/ObjectsFlowStudio.py
    flow_studio/physics_domains.py
    flow_studio/solver_deps.py
    flow_studio/solver_installer.py
    flow_studio/workflow_guide.py
)

SET(FlowStudioEnterprise_SRCS
    flow_studio/enterprise/__init__.py
    flow_studio/enterprise/bootstrap.py
)

SET(FlowStudioEnterpriseAdapters_SRCS
    flow_studio/enterprise/adapters/__init__.py
    flow_studio/enterprise/adapters/base.py
    flow_studio/enterprise/adapters/elmer.py
    flow_studio/enterprise/adapters/fluidx3d.py
    flow_studio/enterprise/adapters/openfoam.py
)

SET(FlowStudioEnterpriseCore_SRCS
    flow_studio/enterprise/core/__init__.py
    flow_studio/enterprise/core/adapter_policy.py
    flow_studio/enterprise/core/contracts.py
    flow_studio/enterprise/core/domain.py
    flow_studio/enterprise/core/sidecar.py
    flow_studio/enterprise/core/serialization.py
)

SET(FlowStudioEnterpriseIntegration_SRCS
    flow_studio/enterprise/integration/__init__.py
    flow_studio/enterprise/integration/freecad_bridge.py
)

SET(FlowStudioEnterpriseApp_SRCS
    flow_studio/enterprise/app/__init__.py
    flow_studio/enterprise/app/legacy_actions.py
)

SET(FlowStudioEnterpriseUi_SRCS
    flow_studio/enterprise/ui/__init__.py
    flow_studio/enterprise/ui/adapter_matrix.py
    flow_studio/enterprise/ui/jobs_panel.py
)

SET(FlowStudioEnterpriseObservability_SRCS
    flow_studio/enterprise/observability/__init__.py
    flow_studio/enterprise/observability/logging.py
)

SET(FlowStudioEnterpriseServices_SRCS
    flow_studio/enterprise/services/__init__.py
    flow_studio/enterprise/services/execution_facade.py
    flow_studio/enterprise/services/jobs.py
    flow_studio/enterprise/services/process_executor.py
    flow_studio/enterprise/services/remote_api.py
    flow_studio/enterprise/services/run_store.py
)

SET(FlowStudioEnterpriseTesting_SRCS
    flow_studio/enterprise/testing/__init__.py
    flow_studio/enterprise/testing/harness.py
)

SET(FlowStudioDocs_SRCS
    docs/ARCHITECTURE.md
    docs/OPTICAL_SOLVER_DEEPSEARCH.md
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
    flow_studio/objects/bc_optical.py
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
    flow_studio/objects/flowefd_features.py
    flow_studio/objects/initial_conditions.py
    flow_studio/objects/measurement_point.py
    flow_studio/objects/measurement_surface.py
    flow_studio/objects/measurement_volume.py
    flow_studio/objects/mesh_gmsh.py
    flow_studio/objects/mesh_region.py
    flow_studio/objects/optical_material.py
    flow_studio/objects/optical_physics_model.py
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
    flow_studio/solvers/optical_runner.py
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
    flow_studio/taskpanels/task_flowefd_features.py
    flow_studio/taskpanels/task_geometry_tools.py
    flow_studio/taskpanels/task_generic_bc.py
    flow_studio/taskpanels/task_initial_conditions.py
    flow_studio/taskpanels/task_materials.py
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
    flow_studio/viewproviders/vp_flowefd_feature.py
    flow_studio/viewproviders/vp_generic_bc.py
    flow_studio/viewproviders/vp_initial_conditions.py
    flow_studio/viewproviders/vp_material.py
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
    flow_studio/tests/test_enterprise_actions.py
    flow_studio/tests/test_enterprise_bridge.py
    flow_studio/tests/test_e2e_cfd_workflow.py
    flow_studio/tests/test_e2e_real_solver.py
    flow_studio/tests/test_e2e_step_import.py
    flow_studio/tests/test_enterprise_contracts.py
    flow_studio/tests/test_enterprise_execution_facade.py
    flow_studio/tests/test_enterprise_policy.py
    flow_studio/tests/test_enterprise_remote.py
    flow_studio/tests/test_enterprise_bootstrap.py
    flow_studio/tests/test_enterprise_adapter_matrix.py
    flow_studio/tests/test_elmer_sif_detailed.py
    flow_studio/tests/test_mesh_and_materials.py
    flow_studio/tests/test_multiphysics.py
    flow_studio/tests/test_objects.py
    flow_studio/tests/test_openfoam.py
    flow_studio/tests/test_physics_domains_detailed.py
    flow_studio/tests/test_registry_detailed.py
)

SET(FlowStudioIcons_SRCS
    Resources/icons/FlowStudioAnalysis.svg
    Resources/icons/FlowStudioBoundaryLayer.svg
    Resources/icons/FlowStudioConvection.svg
    Resources/icons/FlowStudioCurrentDensity.svg
    Resources/icons/FlowStudioDielectricMaterial.svg
    Resources/icons/FlowStudioElectricFlux.svg
    Resources/icons/FlowStudioElectricPotential.svg
    Resources/icons/FlowStudioElectromagnetic.svg
    Resources/icons/FlowStudioElectromagneticPhysics.svg
    Resources/icons/FlowStudioElectrostatic.svg
    Resources/icons/FlowStudioElectrostaticPhysics.svg
    Resources/icons/FlowStudioEMMaterial.svg
    Resources/icons/FlowStudioFarFieldEM.svg
    Resources/icons/FlowStudioFixedDisplacement.svg
    Resources/icons/FlowStudioForce.svg
    Resources/icons/FlowStudioGeneric.svg
    Resources/icons/FlowStudioHeatFlux.svg
    Resources/icons/FlowStudioInitial.svg
    Resources/icons/FlowStudioInlet.svg
    Resources/icons/FlowStudioMagneticFluxDensity.svg
    Resources/icons/FlowStudioMagneticPotential.svg
    Resources/icons/FlowStudioMaterial.svg
    Resources/icons/FlowStudioMesh.svg
    Resources/icons/FlowStudioMeshRegion.svg
    Resources/icons/FlowStudioOpen.svg
    Resources/icons/FlowStudioOutlet.svg
    Resources/icons/FlowStudioPhysics.svg
    Resources/icons/FlowStudioPost.svg
    Resources/icons/FlowStudioPostContour.svg
    Resources/icons/FlowStudioPostForce.svg
    Resources/icons/FlowStudioPostProbe.svg
    Resources/icons/FlowStudioPostStreamlines.svg
    Resources/icons/FlowStudioPressureLoad.svg
    Resources/icons/FlowStudioRadiation.svg
    Resources/icons/FlowStudioRunSolver.svg
    Resources/icons/FlowStudioSolidMaterial.svg
    Resources/icons/FlowStudioSolver.svg
    Resources/icons/FlowStudioSolverSettings.svg
    Resources/icons/FlowStudioStructural.svg
    Resources/icons/FlowStudioStructuralPhysics.svg
    Resources/icons/FlowStudioSurfaceCharge.svg
    Resources/icons/FlowStudioSymmetry.svg
    Resources/icons/FlowStudioTemperature.svg
    Resources/icons/FlowStudioThermal.svg
    Resources/icons/FlowStudioThermalMaterial.svg
    Resources/icons/FlowStudioThermalPhysics.svg
    Resources/icons/FlowStudioWall.svg
    Resources/icons/FlowStudioWorkbench.svg
)

SET(all_files
    ${FlowStudioBase_SRCS}
    ${FlowStudioPackage_SRCS}
    ${FlowStudioEnterprise_SRCS}
    ${FlowStudioEnterpriseAdapters_SRCS}
    ${FlowStudioEnterpriseCore_SRCS}
    ${FlowStudioEnterpriseIntegration_SRCS}
    ${FlowStudioEnterpriseApp_SRCS}
    ${FlowStudioEnterpriseUi_SRCS}
    ${FlowStudioEnterpriseObservability_SRCS}
    ${FlowStudioEnterpriseServices_SRCS}
    ${FlowStudioEnterpriseTesting_SRCS}
    ${FlowStudioFeminout_SRCS}
    ${FlowStudioObjects_SRCS}
    ${FlowStudioSolvers_SRCS}
    ${FlowStudioTaskpanels_SRCS}
    ${FlowStudioUtils_SRCS}
    ${FlowStudioViewproviders_SRCS}
    ${FlowStudioTests_SRCS}
    ${FlowStudioDocs_SRCS}
    ${FlowStudioIcons_SRCS}
)

ADD_CUSTOM_TARGET(FlowStudio ALL
    SOURCES ${all_files}
)

fc_copy_sources(FlowStudio "${CMAKE_BINARY_DIR}/Mod/FlowStudio" ${all_files})

INSTALL(FILES ${FlowStudioBase_SRCS} DESTINATION Mod/FlowStudio)
INSTALL(FILES ${FlowStudioPackage_SRCS} DESTINATION Mod/FlowStudio/flow_studio)
INSTALL(FILES ${FlowStudioEnterprise_SRCS} DESTINATION Mod/FlowStudio/flow_studio/enterprise)
INSTALL(FILES ${FlowStudioEnterpriseAdapters_SRCS} DESTINATION Mod/FlowStudio/flow_studio/enterprise/adapters)
INSTALL(FILES ${FlowStudioEnterpriseCore_SRCS} DESTINATION Mod/FlowStudio/flow_studio/enterprise/core)
INSTALL(FILES ${FlowStudioEnterpriseIntegration_SRCS} DESTINATION Mod/FlowStudio/flow_studio/enterprise/integration)
INSTALL(FILES ${FlowStudioEnterpriseApp_SRCS} DESTINATION Mod/FlowStudio/flow_studio/enterprise/app)
INSTALL(FILES ${FlowStudioEnterpriseUi_SRCS} DESTINATION Mod/FlowStudio/flow_studio/enterprise/ui)
INSTALL(FILES ${FlowStudioEnterpriseObservability_SRCS} DESTINATION Mod/FlowStudio/flow_studio/enterprise/observability)
INSTALL(FILES ${FlowStudioEnterpriseServices_SRCS} DESTINATION Mod/FlowStudio/flow_studio/enterprise/services)
INSTALL(FILES ${FlowStudioEnterpriseTesting_SRCS} DESTINATION Mod/FlowStudio/flow_studio/enterprise/testing)
INSTALL(FILES ${FlowStudioFeminout_SRCS} DESTINATION Mod/FlowStudio/flow_studio/feminout)
INSTALL(FILES ${FlowStudioObjects_SRCS} DESTINATION Mod/FlowStudio/flow_studio/objects)
INSTALL(FILES ${FlowStudioSolvers_SRCS} DESTINATION Mod/FlowStudio/flow_studio/solvers)
INSTALL(FILES ${FlowStudioTaskpanels_SRCS} DESTINATION Mod/FlowStudio/flow_studio/taskpanels)
INSTALL(FILES ${FlowStudioUtils_SRCS} DESTINATION Mod/FlowStudio/flow_studio/utils)
INSTALL(FILES ${FlowStudioViewproviders_SRCS} DESTINATION Mod/FlowStudio/flow_studio/viewproviders)
INSTALL(FILES ${FlowStudioTests_SRCS} DESTINATION Mod/FlowStudio/flow_studio/tests)
INSTALL(FILES ${FlowStudioDocs_SRCS} DESTINATION Mod/FlowStudio/docs)
INSTALL(FILES ${FlowStudioIcons_SRCS} DESTINATION Mod/FlowStudio/Resources/icons)
