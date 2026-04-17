# SPDX-License-Identifier: LGPL-2.1-or-later

set(SheetMetal_LIBS
    FreeCADApp
)

set(SheetMetal_SRCS
    PreCompiled.h
    AppSheetMetal.cpp
    SheetMetalBend.cpp
    SheetMetalBend.h
)

add_library(SheetMetal SHARED ${SheetMetal_SRCS})
target_compile_definitions(SheetMetal PRIVATE SheetMetal_EXPORTS)

if(FREECAD_USE_PCH)
    target_precompile_headers(SheetMetal PRIVATE
            $<$<COMPILE_LANGUAGE:CXX>:"${CMAKE_CURRENT_LIST_DIR}/PreCompiled.h">
    )
endif(FREECAD_USE_PCH)

target_include_directories(SheetMetal
    PRIVATE
    ${CMAKE_BINARY_DIR}
    ${CMAKE_BINARY_DIR}/src
    ${CMAKE_SOURCE_DIR}/src
)

target_link_libraries(SheetMetal ${SheetMetal_LIBS})

if(FREECAD_WARN_ERROR)
    target_compile_warn_error(SheetMetal)
endif()

SET_BIN_DIR(SheetMetal SheetMetal /Mod/SheetMetal)
SET_PYTHON_PREFIX_SUFFIX(SheetMetal)

install(TARGETS SheetMetal DESTINATION ${CMAKE_INSTALL_LIBDIR})
