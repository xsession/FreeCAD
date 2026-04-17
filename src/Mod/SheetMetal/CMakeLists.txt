# SPDX-License-Identifier: LGPL-2.1-or-later

add_subdirectory(App)

set(SheetMetal_Scripts
    Init.py
)

if(BUILD_GUI)
    list(APPEND SheetMetal_Scripts InitGui.py)
    add_subdirectory(Gui)
endif(BUILD_GUI)

add_custom_target(SheetMetalScripts ALL
    SOURCES ${SheetMetal_Scripts}
)

fc_target_copy_resource(SheetMetalScripts
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${CMAKE_BINARY_DIR}/Mod/SheetMetal
    ${SheetMetal_Scripts}
)

install(
    FILES
        ${SheetMetal_Scripts}
    DESTINATION
        Mod/SheetMetal
)
