// SPDX-License-Identifier: LGPL-2.1-or-later
// Minimal GUI module entry point so MSVC generates a .lib import library for SheetMetalGui.pyd

#include <Python.h>

static PyModuleDef SheetMetalGuiModule = {
    PyModuleDef_HEAD_INIT,
    "SheetMetalGui",
    nullptr,
    -1,
    nullptr
};

PyMODINIT_FUNC PyInit_SheetMetalGui()
{
    return PyModule_Create(&SheetMetalGuiModule);
}
