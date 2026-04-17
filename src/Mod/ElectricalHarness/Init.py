# **************************************************************************
# *   Copyright (c) 2026 Electrical Harness contributors                   *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# **************************************************************************

"""Electrical Harness & Schematics Workbench - app-level initialization."""

import os
import sys
import types

import FreeCAD


def _find_module_dir() -> str:
    for mod_dir in FreeCAD.__ModDirs__:
        if os.path.basename(mod_dir) == "ElectricalHarness":
            return mod_dir
    return os.path.join(FreeCAD.getHomePath(), "Mod", "ElectricalHarness")


def _bootstrap_namespace(module_dir: str) -> None:
    if module_dir not in sys.path:
        sys.path.append(module_dir)
    namespace = "electrical_harness"
    if namespace not in sys.modules:
        pkg = types.ModuleType(namespace)
        pkg.__path__ = [module_dir]
        sys.modules[namespace] = pkg


MODULE_DIR = _find_module_dir()
_bootstrap_namespace(MODULE_DIR)

FreeCAD.addImportType(
    "Electrical Harness Project (*.ehproj.json)",
    "electrical_harness.App.import_export",
)
FreeCAD.addExportType(
    "Electrical Harness Project (*.ehproj.json)",
    "electrical_harness.App.import_export",
)

if hasattr(FreeCAD, "__unit_test__"):
    FreeCAD.__unit_test__ += ["Tests.TestElectricalHarness"]
