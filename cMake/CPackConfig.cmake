# SPDX-License-Identifier: LGPL-2.1-or-later
#
# CPack configuration for cross-platform FreeCAD packaging.
# Supports NSIS (Windows), DEB/RPM (Linux), DMG (macOS), and source packages.

set(CPACK_PACKAGE_NAME "FreeCAD")
set(CPACK_PACKAGE_VENDOR "FreeCAD Community")
set(CPACK_PACKAGE_DESCRIPTION_SUMMARY "FreeCAD - A free and open-source parametric 3D CAD modeler")
set(CPACK_PACKAGE_DESCRIPTION "FreeCAD is a general-purpose parametric 3D computer-aided design (CAD) modeler and a building information modeling (BIM) software with finite element method (FEM) support.")
set(CPACK_PACKAGE_HOMEPAGE_URL "https://www.freecad.org")
set(CPACK_PACKAGE_CONTACT "FreeCAD Community <info@freecad.org>")
set(CPACK_RESOURCE_FILE_LICENSE "${CMAKE_SOURCE_DIR}/LICENSE")
set(CPACK_RESOURCE_FILE_README "${CMAKE_SOURCE_DIR}/README.md")

# Version from CMake project
set(CPACK_PACKAGE_VERSION_MAJOR "${FREECAD_VERSION_MAJOR}")
set(CPACK_PACKAGE_VERSION_MINOR "${FREECAD_VERSION_MINOR}")
set(CPACK_PACKAGE_VERSION_PATCH "${FREECAD_VERSION_PATCH}")
set(CPACK_PACKAGE_VERSION "${CPACK_PACKAGE_VERSION_MAJOR}.${CPACK_PACKAGE_VERSION_MINOR}.${CPACK_PACKAGE_VERSION_PATCH}")

# Component-based packaging
set(CPACK_COMPONENTS_ALL freecad tests)
set(CPACK_COMPONENT_FREECAD_DISPLAY_NAME "FreeCAD")
set(CPACK_COMPONENT_FREECAD_DESCRIPTION "FreeCAD application and core modules")
set(CPACK_COMPONENT_FREECAD_REQUIRED TRUE)
set(CPACK_COMPONENT_TESTS_DISPLAY_NAME "Test Suite")
set(CPACK_COMPONENT_TESTS_DESCRIPTION "Automated test executables (optional)")
set(CPACK_COMPONENT_TESTS_DISABLED TRUE)

# ---- Windows NSIS Configuration ----
if(WIN32)
    set(CPACK_GENERATOR "NSIS")
    set(CPACK_NSIS_DISPLAY_NAME "FreeCAD ${CPACK_PACKAGE_VERSION}")
    set(CPACK_NSIS_PACKAGE_NAME "FreeCAD")
    set(CPACK_NSIS_HELP_LINK "https://wiki.freecad.org")
    set(CPACK_NSIS_URL_INFO_ABOUT "https://www.freecad.org")
    set(CPACK_NSIS_MODIFY_PATH ON)
    set(CPACK_NSIS_ENABLE_UNINSTALL_BEFORE_INSTALL ON)
    set(CPACK_NSIS_MUI_FINISHPAGE_RUN "FreeCAD.exe")

    # File associations for .FCStd
    set(CPACK_NSIS_EXTRA_INSTALL_COMMANDS "
        WriteRegStr HKCR '.FCStd' '' 'FreeCAD.Document'
        WriteRegStr HKCR 'FreeCAD.Document' '' 'FreeCAD Document'
        WriteRegStr HKCR 'FreeCAD.Document\\\\shell\\\\open\\\\command' '' '\\\"$INSTDIR\\\\bin\\\\FreeCAD.exe\\\" \\\"%1\\\"'
    ")
    set(CPACK_NSIS_EXTRA_UNINSTALL_COMMANDS "
        DeleteRegKey HKCR '.FCStd'
        DeleteRegKey HKCR 'FreeCAD.Document'
    ")
endif()

# ---- Linux DEB Configuration ----
if(UNIX AND NOT APPLE)
    set(CPACK_DEBIAN_PACKAGE_MAINTAINER "FreeCAD Community <info@freecad.org>")
    set(CPACK_DEBIAN_PACKAGE_SECTION "science")
    set(CPACK_DEBIAN_PACKAGE_PRIORITY "optional")
    set(CPACK_DEBIAN_PACKAGE_DEPENDS "libocct-data-exchange-7.6, libocct-modeling-algorithms-7.6, python3, libqt5widgets5, libcoin80v5")
    set(CPACK_DEBIAN_PACKAGE_SHLIBDEPS ON)

    set(CPACK_RPM_PACKAGE_LICENSE "LGPL-2.1-or-later")
    set(CPACK_RPM_PACKAGE_GROUP "Applications/Engineering")
    set(CPACK_RPM_PACKAGE_REQUIRES "opencascade, python3, qt5-qtbase, Coin4")
endif()

# ---- macOS DMG Configuration ----
if(APPLE)
    set(CPACK_GENERATOR "DragNDrop")
    set(CPACK_DMG_VOLUME_NAME "FreeCAD ${CPACK_PACKAGE_VERSION}")
    set(CPACK_DMG_FORMAT "UDBZ")
    set(CPACK_BUNDLE_NAME "FreeCAD")
    set(CPACK_BUNDLE_PLIST "${CMAKE_SOURCE_DIR}/src/MacAppBundle/Info.plist")
endif()

# ---- Source Package ----
set(CPACK_SOURCE_GENERATOR "TGZ;ZIP")
set(CPACK_SOURCE_IGNORE_FILES
    "/\\\\.git/"
    "/build/"
    "/\\\\.pixi/"
    "/\\\\.cache/"
    "\\\\.pyc$"
    "__pycache__"
    "/\\\\.vs/"
    "/\\\\.vscode/"
)

include(CPack)
