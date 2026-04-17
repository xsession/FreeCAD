# SPDX-License-Identifier: LGPL-2.1-or-later

option(FREECAD_BUILD_BENCHMARKS "Build FreeCAD benchmark executables" OFF)

if(NOT FREECAD_BUILD_BENCHMARKS)
    return()
endif()

find_package(benchmark QUIET)
if(NOT benchmark_FOUND)
    message(WARNING "Google Benchmark not found; benchmark targets will not be built")
    return()
endif()

set(FreeCADBenchmarkSources
    RecomputeBenchmarks.cpp
    ExportBenchmarks.cpp
    AssemblyBenchmarks.cpp
)

foreach(src ${FreeCADBenchmarkSources})
    get_filename_component(bench_name ${src} NAME_WE)
    add_executable(${bench_name} ${src})
    target_link_libraries(${bench_name} PRIVATE benchmark::benchmark FreeCADApp)
    target_compile_definitions(${bench_name} PRIVATE FREECAD_BENCHMARK_STUB=1)
    set_target_properties(${bench_name} PROPERTIES
        RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/benchmarks
    )
endforeach()
