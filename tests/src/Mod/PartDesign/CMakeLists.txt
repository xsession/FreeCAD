# SPDX-License-Identifier: LGPL-2.1-or-later

add_subdirectory(App)
add_subdirectory(Gui)

target_link_libraries(PartDesign_tests_run
        gtest_main
        ${Google_Tests_LIBS}
        PartDesign
        Sketcher
)
