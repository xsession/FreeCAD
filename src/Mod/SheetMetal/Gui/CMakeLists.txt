# SPDX-License-Identifier: LGPL-2.1-or-later

set(SheetMetalGui_LIBS
    SheetMetal
    FreeCADGui
)

set(SheetMetalGui_SRCS
    PreCompiled.h
    AppSheetMetalGui.cpp
    CommandSheetMetal.cpp
    CommandSheetMetal.h
)

add_library(SheetMetalGui SHARED ${SheetMetalGui_SRCS})

if(FREECAD_USE_PCH)
    target_precompile_headers(SheetMetalGui PRIVATE
            $<$<COMPILE_LANGUAGE:CXX>:"${CMAKE_CURRENT_LIST_DIR}/PreCompiled.h">
    )
endif(FREECAD_USE_PCH)

target_include_directories(SheetMetalGui
    PRIVATE
    ${CMAKE_BINARY_DIR}
    ${CMAKE_BINARY_DIR}/src
    ${CMAKE_SOURCE_DIR}/src
)

target_link_libraries(SheetMetalGui ${SheetMetalGui_LIBS})

if(MSVC)
    target_compile_options(SheetMetalGui PRIVATE /wd4251)
endif()

if(FREECAD_WARN_ERROR)
    target_compile_warn_error(SheetMetalGui)
endif()

SET_BIN_DIR(SheetMetalGui SheetMetalGui /Mod/SheetMetal)
SET_PYTHON_PREFIX_SUFFIX(SheetMetalGui)

install(TARGETS SheetMetalGui DESTINATION ${CMAKE_INSTALL_LIBDIR})
