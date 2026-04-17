# SPDX-License-Identifier: LGPL-2.1-or-later

SET(ElectricalHarnessBase_SRCS
    Init.py
    InitGui.py
)

SET(ElectricalHarnessPackage_SRCS
    electrical_harness/__init__.py
)

SET(ElectricalHarnessApp_SRCS
    App/__init__.py
    App/document_objects.py
    App/entities.py
    App/flattening.py
    App/ids.py
    App/import_export.py
    App/library.py
    App/integration_route_core.py
    App/integration_dolibarr.py
    App/model.py
    App/project_store.py
    App/reports.py
    App/routing.py
    App/serialization.py
    App/services.py
    App/validation.py
)

SET(ElectricalHarnessGui_SRCS
    Gui/__init__.py
    Gui/editor2d.py
    Gui/panels.py
    Gui/routing3d_tools.py
    Gui/selection_bridge.py
    Gui/workbench.py
)

SET(ElectricalHarnessCommands_SRCS
    Commands/__init__.py
    Commands/command_registry.py
    Commands/object_factory.py
)

SET(ElectricalHarnessTests_SRCS
    Tests/__init__.py
    Tests/test_model.py
    Tests/test_project_store.py
    Tests/test_reports.py
    Tests/test_reports_extended.py
    Tests/test_serialization.py
    Tests/test_validation.py
    Tests/test_validation_extended.py
    Tests/test_flattening.py
    Tests/test_phase2.py
    Tests/test_library.py
    Tests/test_integration_route_core.py
    Tests/test_integration_dolibarr.py
    Tests/TestElectricalHarness.py
)

SET(ElectricalHarnessDocs_SRCS
    docs/ARCHITECTURE.md
    docs/BACKLOG.md
    docs/COMPETITIVE_SPECIFICATION.md
)

SET(ElectricalHarnessExamples_SRCS
    examples/sample_project.ehproj.json
)

SET(ElectricalHarnessIcons_SRCS
    Resources/icons/ElectricalHarnessWorkbench.svg
    Resources/icons/ElectricalHarnessGeneric.svg
)

SET(all_files
    ${ElectricalHarnessBase_SRCS}
    ${ElectricalHarnessPackage_SRCS}
    ${ElectricalHarnessApp_SRCS}
    ${ElectricalHarnessGui_SRCS}
    ${ElectricalHarnessCommands_SRCS}
    ${ElectricalHarnessTests_SRCS}
    ${ElectricalHarnessDocs_SRCS}
    ${ElectricalHarnessExamples_SRCS}
    ${ElectricalHarnessIcons_SRCS}
)

ADD_CUSTOM_TARGET(ElectricalHarness ALL
    SOURCES ${all_files}
)

fc_copy_sources(ElectricalHarness "${CMAKE_BINARY_DIR}/Mod/ElectricalHarness" ${all_files})

INSTALL(FILES ${ElectricalHarnessBase_SRCS} DESTINATION Mod/ElectricalHarness)
INSTALL(FILES ${ElectricalHarnessPackage_SRCS} DESTINATION Mod/ElectricalHarness/electrical_harness)
INSTALL(FILES ${ElectricalHarnessApp_SRCS} DESTINATION Mod/ElectricalHarness/App)
INSTALL(FILES ${ElectricalHarnessGui_SRCS} DESTINATION Mod/ElectricalHarness/Gui)
INSTALL(FILES ${ElectricalHarnessCommands_SRCS} DESTINATION Mod/ElectricalHarness/Commands)
INSTALL(FILES ${ElectricalHarnessTests_SRCS} DESTINATION Mod/ElectricalHarness/Tests)
INSTALL(FILES ${ElectricalHarnessDocs_SRCS} DESTINATION Mod/ElectricalHarness/docs)
INSTALL(FILES ${ElectricalHarnessExamples_SRCS} DESTINATION Mod/ElectricalHarness/examples)
INSTALL(FILES ${ElectricalHarnessIcons_SRCS} DESTINATION Mod/ElectricalHarness/Resources/icons)
