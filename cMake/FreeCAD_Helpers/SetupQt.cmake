# -------------------------------- Qt --------------------------------

function(freecad_stage_qt_host_tool out_var tool_executable)
    if(NOT WIN32 OR NOT EXISTS "${tool_executable}")
        set(${out_var} "${tool_executable}" PARENT_SCOPE)
        return()
    endif()

    get_filename_component(_tool_name "${tool_executable}" NAME)
    get_filename_component(_qt6_dir "${tool_executable}" DIRECTORY)
    get_filename_component(_library_dir "${_qt6_dir}" DIRECTORY)
    get_filename_component(_prefix_dir "${_library_dir}" DIRECTORY)
    set(_runtime_dir "${_prefix_dir}/bin")
    set(_stage_dir "${CMAKE_BINARY_DIR}/qt-host-tools")
    set(_staged_tool "${_stage_dir}/${_tool_name}")

    file(MAKE_DIRECTORY "${_stage_dir}")
    configure_file("${tool_executable}" "${_staged_tool}" COPYONLY)
    if(EXISTS "${_runtime_dir}")
        file(COPY "${_runtime_dir}/" DESTINATION "${_stage_dir}"
            FILES_MATCHING
            PATTERN "*.dll"
        )
    endif()

    set(${out_var} "${_staged_tool}" PARENT_SCOPE)
endfunction()

function(freecad_override_imported_qt_tool tool_target staged_tool)
    if(NOT TARGET "${tool_target}" OR NOT EXISTS "${staged_tool}")
        return()
    endif()

    set_property(TARGET "${tool_target}" PROPERTY IMPORTED_LOCATION "${staged_tool}")
    foreach(_config DEBUG RELEASE RELWITHDEBINFO MINSIZEREL)
        set_property(TARGET "${tool_target}" PROPERTY "IMPORTED_LOCATION_${_config}" "${staged_tool}")
    endforeach()
endfunction()

set(FREECAD_QT_COMPONENTS Core Concurrent Network Xml)
if (FREECAD_QT_MAJOR_VERSION EQUAL 6)
    set (Qt6Core_MOC_EXECUTABLE Qt6::moc)
endif()

if(BUILD_GUI)
    if (FREECAD_QT_MAJOR_VERSION EQUAL 5)
        if (WIN32)
            list (APPEND FREECAD_QT_COMPONENTS WinExtras)
        endif()
    elseif (FREECAD_QT_MAJOR_VERSION EQUAL 6)
        list (APPEND FREECAD_QT_COMPONENTS GuiTools)
        list (APPEND FREECAD_QT_COMPONENTS SvgWidgets)
        list (APPEND FREECAD_QT_COMPONENTS OpenGLWidgets)
    endif()

    list (APPEND FREECAD_QT_COMPONENTS OpenGL PrintSupport Svg UiTools Widgets LinguistTools)

    if(BUILD_DESIGNER_PLUGIN)
        list (APPEND FREECAD_QT_COMPONENTS Designer)
    endif()
endif()

if (ENABLE_DEVELOPER_TESTS)
    list (APPEND FREECAD_QT_COMPONENTS Test)
endif ()

foreach(COMPONENT IN LISTS FREECAD_QT_COMPONENTS)
    find_package(Qt${FREECAD_QT_MAJOR_VERSION} REQUIRED COMPONENTS ${COMPONENT})
    set(Qt${COMPONENT}_LIBRARIES ${Qt${FREECAD_QT_MAJOR_VERSION}${COMPONENT}_LIBRARIES})
    set(Qt${COMPONENT}_INCLUDE_DIRS ${Qt${FREECAD_QT_MAJOR_VERSION}${COMPONENT}_INCLUDE_DIRS})
    set(Qt${COMPONENT}_FOUND ${Qt${FREECAD_QT_MAJOR_VERSION}${COMPONENT}_FOUND})
    set(Qt${COMPONENT}_VERSION ${Qt${FREECAD_QT_MAJOR_VERSION}${COMPONENT}_VERSION})
endforeach()

set(CMAKE_AUTOMOC TRUE)
set(CMAKE_AUTOUIC TRUE)
set(QtCore_MOC_EXECUTABLE ${Qt${FREECAD_QT_MAJOR_VERSION}Core_MOC_EXECUTABLE})

if(FREECAD_QT_MAJOR_VERSION EQUAL 6)
    get_target_property(_freecad_qt_moc_executable Qt6::moc LOCATION)
    freecad_stage_qt_host_tool(_freecad_staged_moc "${_freecad_qt_moc_executable}")
    set(Qt6Core_MOC_EXECUTABLE "${_freecad_staged_moc}")
    set(QtCore_MOC_EXECUTABLE "${_freecad_staged_moc}")
    set(CMAKE_AUTOMOC_EXECUTABLE "${_freecad_staged_moc}")
    freecad_override_imported_qt_tool(Qt6::moc "${_freecad_staged_moc}")

    if(TARGET Qt6::uic)
        get_target_property(_freecad_qt_uic_executable Qt6::uic LOCATION)
        freecad_stage_qt_host_tool(_freecad_staged_uic "${_freecad_qt_uic_executable}")
        set(CMAKE_AUTOUIC_EXECUTABLE "${_freecad_staged_uic}")
        freecad_override_imported_qt_tool(Qt6::uic "${_freecad_staged_uic}")
    endif()

    if(TARGET Qt6::rcc)
        get_target_property(_freecad_qt_rcc_executable Qt6::rcc LOCATION)
        freecad_stage_qt_host_tool(_freecad_staged_rcc "${_freecad_qt_rcc_executable}")
        set(CMAKE_AUTORCC_EXECUTABLE "${_freecad_staged_rcc}")
        freecad_override_imported_qt_tool(Qt6::rcc "${_freecad_staged_rcc}")
    endif()
endif()

add_definitions(-DQT_NO_KEYWORDS)

message(STATUS "Set up to compile with Qt ${Qt${FREECAD_QT_MAJOR_VERSION}Core_VERSION}")

# In Qt 5.15 they added more generic names for these functions: "backport" those new names
# so we can migrate to using the non-version-named functions in all instances.
if (Qt${FREECAD_QT_MAJOR_VERSION}Core_VERSION VERSION_LESS 5.15.0)
    message(STATUS "Manually creating qt_wrap_cpp() and qt_add_resources() to support Qt ${Qt${FREECAD_QT_MAJOR_VERSION}Core_VERSION}")

    # Wrapper code adapted from Qt 6's Qt6CoreMacros.cmake file:
    function(qt_add_resources outfiles)
        qt5_add_resources("${outfiles}" ${ARGN})
        if(TARGET ${outfiles})
            cmake_parse_arguments(PARSE_ARGV 1 arg "" "OUTPUT_TARGETS" "")
            if (arg_OUTPUT_TARGETS)
                set(${arg_OUTPUT_TARGETS} ${${arg_OUTPUT_TARGETS}} PARENT_SCOPE)
            endif()
        else()
            set("${outfiles}" "${${outfiles}}" PARENT_SCOPE)
        endif()
    endfunction()

    function(qt_wrap_cpp outfiles)
        qt5_wrap_cpp("${outfiles}" ${ARGN})
        set("${outfiles}" "${${outfiles}}" PARENT_SCOPE)
    endfunction()

    function(qt_add_translation _qm_files)
        qt5_add_translation("${_qm_files}" ${ARGN})
        set("${_qm_files}" "${${_qm_files}}" PARENT_SCOPE)
    endfunction()

    # Since Qt 5.15 Q_DISABLE_COPY_MOVE is defined
    set (HAVE_Q_DISABLE_COPY_MOVE 0)
else()
    # Since Qt 5.15 Q_DISABLE_COPY_MOVE is defined
    set (HAVE_Q_DISABLE_COPY_MOVE 1)
endif()

configure_file(${CMAKE_SOURCE_DIR}/src/QtCore.h.cmake ${CMAKE_BINARY_DIR}/src/QtCore.h)
configure_file(${CMAKE_SOURCE_DIR}/src/QtWidgets.h.cmake ${CMAKE_BINARY_DIR}/src/QtWidgets.h)

function(qt_find_and_add_translation _qm_files _tr_dir _qm_dir)
    file(GLOB _ts_files ${_tr_dir})
    set_source_files_properties(${_ts_files} PROPERTIES OUTPUT_LOCATION ${_qm_dir})
    qt_add_translation("${_qm_files}" ${_ts_files})
    set("${_qm_files}" "${${_qm_files}}" PARENT_SCOPE)
endfunction()

function(qt_create_resource_file outfile)
    set(QRC "<RCC>\n  <qresource>\n")
    foreach (it ${ARGN})
        get_filename_component(qmfile "${it}" NAME)
        string(APPEND QRC "        <file>translations/${qmfile}</file>")
    endforeach()
    string(APPEND QRC "  </qresource>\n</RCC>\n")
    file(WRITE ${outfile} ${QRC})
endfunction()

function(qt_create_resource_file_prefix outfile)
    set(QRC "<RCC>\n  <qresource prefix=\"/translations\">\n")
    foreach (it ${ARGN})
        get_filename_component(qmfile "${it}" NAME)
        string(APPEND QRC "        <file>${qmfile}</file>")
    endforeach()
    string(APPEND QRC "  </qresource>\n</RCC>\n")
    file(WRITE ${outfile} ${QRC})
endfunction()
